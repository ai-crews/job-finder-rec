from typing import Any, Dict, List, Optional
from job_finder_rec.recommender.types import UserPreferences
import re


# ── 시트 컬럼명 상수 ──────────────────────────────────────────
EMAIL_KEYS            = "이메일 주소"

Q_NAME                = "메일에 표시될 닉네임을 입력해주세요.\n입력하신 닉네임은 메일에서 이렇게 사용돼요.\n예: 📬 홍길동님, 3월 1주차 채용공고가 도착했어요!"
Q_EDUCATION_LEVEL     = "찾고 계신 학력 정보를 선택해주세요. "
Q_EMPLOYMENT_TYPE     = "찾고 계신 고용 형태를 선택해주세요. (복수 선택 가능) "
Q_JOB_1               = "1순위 희망 직무를 선택해주세요."
Q_JOB_2               = "2순위 희망 직무를 선택해주세요.  (없으면 선택하지 않으셔도 됩니다.) "
Q_JOB_3               = "3순위 희망 직무를 선택해주세요.  (없으면 선택하지 않으셔도 됩니다.) "
Q_COMPANY_SIZE        = "선호하시는 기업 규모를 선택해주세요. (복수 선택 가능)"
Q_COMPANY_INDUSTRY    = "관심 있는 산업군을 선택해주세요. (복수 선택 가능)\n\n찾으시는 산업군이 없다면, '기타'에 직접 입력해 주세요.\n(예: 건설, 제조, 로봇, 반도체 등)"
Q_HAS_LANGUAGE_SCORE  = "영어 성적이 필수인 공고도 함께 보내드릴까요? \n\n영어 성적을 보유하고 계실 경우, ‘예’를 선택해주세요.\n없다면 해당 공고는 제외해 보내드려요."
Q_SORT                = "메일 서비스에서 채용 공고를 어떤 기준으로 정렬해 드릴까요?"


# ── 파싱 헬퍼 ─────────────────────────────────────────────────
def _normalize_key(k: str) -> str:
    if k is None:
        return ""
    k = k.replace("\ufeff", "")
    k = k.strip()
    k = re.sub(r"\s+", " ", k)
    return k.lower()


def _get_by_key_variants(record: Dict[str, Any], key: str) -> Optional[Any]:
    if not isinstance(record, dict):
        return None

    # direct
    if key in record:
        return record.get(key)

    nk = _normalize_key(key)
    for rk, v in record.items():
        if not isinstance(rk, str):
            continue
        if _normalize_key(rk) == nk:
            return v

    sk = key.strip()
    if sk in record:
        return record.get(sk)

    return None


def _split_csv(s: str) -> List[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x and x.strip()]


def _normalize_industry(raw: str) -> str:
    """
    구글 폼 산업 라벨에서 괄호 이하 예시 텍스트를 제거해 공고 industry 값과 맞춤

    예:
    - "IT (네이버, 카카오, 삼성SDS 등)"  → "IT"
    - "바이오 및 의료 (삼성바이오 등)"   → "바이오 및 의료"
    - "게임"                             → "게임"  (괄호 없으면 그대로)
    """
    return raw.split("(")[0].strip()


def _split_industries(s: str) -> List[str]:
    """
    산업 필드는 콤마 구분 CSV로 오지만, 라벨 자체 괄호 안에 콤마가 포함되어 있어
    단순 split(",")이 잘못 쪼갤 수 있음
    괄호 depth를 추적해 depth=0인 콤마에서만 분리 후 정규화

    예:
    - "IT (네이버, 카카오 등), 금융 (KB, 비바리퍼블리카(토스) 등)"  → ["IT", "금융"]
    """
    if not s:
        return []

    parts: List[str] = []
    depth = 0
    current: List[str] = []

    for char in s:
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(_normalize_industry(part))
            current = []
        else:
            current.append(char)

    # 마지막 항목
    part = "".join(current).strip()
    if part:
        parts.append(_normalize_industry(part))

    return parts


def _normalize_sort_value(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip().lower()

    if s in ("deadline", "recommend"):
        return s
    if "마감" in s:
        return "deadline"
    if "추천" in s:
        return "recommend"
    return ""


def _get_email(record: Dict[str, Any]) -> Optional[str]:
    v = _get_by_key_variants(record, EMAIL_KEYS)
    if isinstance(v, str) and "@" in v:
        return v.strip()
    return None


# ── 퍼블릭 API ────────────────────────────────────────────────
def normalize_user(record: Dict[str, Any]) -> UserPreferences:
    email = _get_email(record)
    
    target_jobs = [
        (_get_by_key_variants(record, Q_JOB_1) or "").strip(),
        (_get_by_key_variants(record, Q_JOB_2) or "").strip(),
        (_get_by_key_variants(record, Q_JOB_3) or "").strip(),
    ]
    # 빈 값 제거 + 1순위 > 2순위 > 3순위 순서를 유지하면서 중복 제거
    seen: set = set()
    target_jobs = [j for j in target_jobs if j and not (j in seen or seen.add(j))]
    
    prefs = UserPreferences(
        email=email,
        name=(_get_by_key_variants(record, Q_NAME) or "").strip(),
        education_level=_split_csv(( _get_by_key_variants(record, Q_EDUCATION_LEVEL) or "").strip()),
        employment_type=_split_csv(( _get_by_key_variants(record, Q_EMPLOYMENT_TYPE) or "").strip()),
        top3_position=target_jobs,
        company_size=_split_csv(( _get_by_key_variants(record, Q_COMPANY_SIZE) or "").strip()),
        company_industry=_split_industries(( _get_by_key_variants(record, Q_COMPANY_INDUSTRY) or "").strip()),
        has_language_score=(_get_by_key_variants(record, Q_HAS_LANGUAGE_SCORE) or "").strip() or None,
        sort=_normalize_sort_value((_get_by_key_variants(record, Q_SORT) or "").strip()),
        raw=record,
    )
    return prefs


def normalize_users(records: List[Dict[str, Any]]) -> List[UserPreferences]:
    return [normalize_user(r) for r in records]
