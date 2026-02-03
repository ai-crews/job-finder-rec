from typing import Any, Dict, List, Optional
from job_finder_rec.recommender.types import UserPreferences

EMAIL_KEYS = "이메일 주소"

Q_JOB_1 = "희망 직무 1순위 (필수응답)"
Q_JOB_2 = "희망 직무 2순위 "
Q_JOB_3 = "희망 직무 3순위 "
Q_EMPLOYMENT = "희망 고용 형태 (복수선택)"
Q_CAREER = "찾고 계신 공고의 경력 조건을 선택해주세요."
Q_EDUCATION = "찾고 계신 공고의 학력 조건을 선택해주세요. (졸업예정자도 선택 가능, 복수선택)"


def _split_csv(s: str) -> List[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x and x.strip()]


def _get_email(record: Dict[str, Any]) -> Optional[str]:
    v = record.get(EMAIL_KEYS)
    if isinstance(v, str) and "@" in v:
        return v.strip()
    return None


def extract_target_companies(record: Dict[str, Any]) -> List[str]:
    return []


def normalize_user(record: Dict[str, Any]) -> UserPreferences:
    email = _get_email(record) or "unknown@example.com"

    target_jobs = [
        (record.get(Q_JOB_1) or "").strip(),
        (record.get(Q_JOB_2) or "").strip(),
        (record.get(Q_JOB_3) or "").strip(),
    ]
    target_jobs = [j for j in target_jobs if j]

    prefs = UserPreferences(
        email=email,
        target_jobs=target_jobs,
        target_employment_types=_split_csv((record.get(Q_EMPLOYMENT) or "").strip()),
        target_education_levels=_split_csv((record.get(Q_EDUCATION) or "").strip()),
        career_pref=_split_csv((record.get(Q_CAREER) or "").strip()),
        target_companies=extract_target_companies(record),
        raw=record,
    )
    return prefs


def normalize_users(records: List[Dict[str, Any]]) -> List[UserPreferences]:
    return [normalize_user(r) for r in records]
