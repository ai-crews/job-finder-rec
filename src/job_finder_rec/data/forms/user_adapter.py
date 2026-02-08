from typing import Any, Dict, List, Optional
from job_finder_rec.recommender.types import UserPreferences
import re

EMAIL_KEYS = "이메일 주소"

Q_NAME = "성함을 입력해주세요."
Q_GENDER = "성별을 선택해주세요."
Q_BIRTH_YEAR = "출생연도를 입력해주세요. (ex.2003)"
Q_CURRENT_EDU = "현재 학력 정보를 선택해주세요."
Q_EMPLOYMENT = "희망하시는 고용형태를 선택해주세요. (복수 선택 가능)"
Q_JOB_1 = "희망 직무 1순위 (필수응답)"
Q_JOB_2 = "희망 직무 2순위"
Q_JOB_3 = "희망 직무 3순위"
Q_COMPANY_SIZE = "선호하시는 기업 규모를 선택해주세요. (복수 선택 가능)"
Q_INDUSTRIES = "관심 있는 산업군을 선택해주세요."
Q_SORT = "희망 정렬 기준"


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


def _get_email(record: Dict[str, Any]) -> Optional[str]:
    v = _get_by_key_variants(record, EMAIL_KEYS)
    if isinstance(v, str) and "@" in v:
        return v.strip()
    return None


def normalize_user(record: Dict[str, Any]) -> UserPreferences:
    email = _get_email(record) or "unknown@example.com"

    target_jobs = [
        (_get_by_key_variants(record, Q_JOB_1) or "").strip(),
        (_get_by_key_variants(record, Q_JOB_2) or "").strip(),
        (_get_by_key_variants(record, Q_JOB_3) or "").strip(),
    ]
    target_jobs = [j for j in target_jobs if j]

    # parse birth year safely
    by_raw = _get_by_key_variants(record, Q_BIRTH_YEAR)
    birth_year = None
    try:
        if by_raw is not None:
            s = str(by_raw).strip()
            if s.isdigit():
                birth_year = int(s)
    except Exception:
        birth_year = None

    prefs = UserPreferences(
        email=email,
        target_jobs=target_jobs,
        target_employment_types=_split_csv(( _get_by_key_variants(record, Q_EMPLOYMENT) or "").strip()),
        sort=(_get_by_key_variants(record, Q_SORT) or "recommend").strip(),
        raw=record,
        name=(_get_by_key_variants(record, Q_NAME) or "").strip() or None,
        gender=(_get_by_key_variants(record, Q_GENDER) or "").strip() or None,
        birth_year=birth_year,
        current_education=(_get_by_key_variants(record, Q_CURRENT_EDU) or "").strip() or None,
        preferred_company_sizes=_split_csv(( _get_by_key_variants(record, Q_COMPANY_SIZE) or "").strip()),
        interested_industries=_split_csv(( _get_by_key_variants(record, Q_INDUSTRIES) or "").strip()),
    )
    return prefs


def normalize_users(records: List[Dict[str, Any]]) -> List[UserPreferences]:
    return [normalize_user(r) for r in records]
