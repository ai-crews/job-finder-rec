from datetime import datetime, time
from typing import Any, Dict, List, Optional, Tuple

from job_finder_rec.recommender.types import JobPosting

# ── 시트 컬럼명 상수 ──────────────────────────────────────────
COL_POST_ID                = "post_id"
COL_JOB_TITLE              = "job_title"
COL_COMPANY_NAME           = "company_name"
COL_INDUSTRY               = "industry"
COL_COMPANY_SIZE           = "company_size"
COL_DEADLINE_DATE          = "deadline_date"
COL_DEADLINE_TIME          = "deadline_time"
COL_POSITION_NAME          = "processed_position_name"
COL_EDUCATION_LEVEL        = "processed_education_level_list"
COL_EXPERIENCE_LEVEL       = "processed_experience_level"
COL_EMPLOYMENT_TYPE        = "processed_employment_type"
COL_LANGUAGE_REQUIRED      = "processed_language_score_required"
COL_JSON_FILE_NAME         = "json_file_name"


# ── 파싱 헬퍼 ─────────────────────────────────────────────────
def _parse_str(record: Dict[str, Any], key: str) -> str:
    v = record.get(key)
    return (v or "").strip() if isinstance(v, str) else str(v or "").strip()


def _parse_list(record: Dict[str, Any], key: str) -> List[str]:
    import ast
    v = record.get(key)
    if isinstance(v, list):
        return [str(x).strip() for x in v if x]
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        # 시트에서 "['ML엔지니어', 'AI개발자']" 형태로 오는 경우 파싱
        if s.startswith("["):
            try:
                parsed = ast.literal_eval(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if x]
            except Exception:
                pass
        return [s]
    return []


def _parse_bool(record: Dict[str, Any], key: str) -> bool:
    v = record.get(key)
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes", "예")
    return bool(v)


def _parse_deadline(
    record: Dict[str, Any],
) -> Tuple[Optional[datetime], Optional[time], Optional[datetime]]:
    """(deadline_date, deadline_time, combined_deadline) 반환."""
    date_str = _parse_str(record, COL_DEADLINE_DATE)
    time_str = _parse_str(record, COL_DEADLINE_TIME)

    deadline_date: Optional[datetime] = None
    deadline_time: Optional[time] = None
    deadline: Optional[datetime] = None

    if date_str:
        try:
            deadline_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pass

    if time_str:
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                deadline_time = datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                pass

    if date_str:
        try:
            if time_str:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                    try:
                        deadline = datetime.strptime(f"{date_str} {time_str}", fmt)
                        break
                    except ValueError:
                        pass
            else:
                deadline = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            pass

    return deadline_date, deadline_time, deadline


# ── 퍼블릭 API ────────────────────────────────────────────────
def normalize_job(record: Dict[str, Any]) -> JobPosting:
    deadline_date, deadline_time, deadline = _parse_deadline(record)
    return JobPosting(
        post_id=_parse_str(record, COL_POST_ID),
        job_title=_parse_str(record, COL_JOB_TITLE),
        company_name=_parse_str(record, COL_COMPANY_NAME),
        industry=_parse_str(record, COL_INDUSTRY),
        company_size=_parse_str(record, COL_COMPANY_SIZE),
        processed_position_name=_parse_list(record, COL_POSITION_NAME),
        processed_education_level=_parse_list(record, COL_EDUCATION_LEVEL),
        processed_experience_level=_parse_str(record, COL_EXPERIENCE_LEVEL),
        processed_employment_type=_parse_list(record, COL_EMPLOYMENT_TYPE),
        processed_language_required=_parse_bool(record, COL_LANGUAGE_REQUIRED),
        json_file_name=_parse_str(record, COL_JSON_FILE_NAME),
        deadline_date=deadline_date,
        deadline_time=deadline_time,
        deadline=deadline,
        raw=record,
    )


def normalize_jobs(records: List[Dict[str, Any]]) -> List[JobPosting]:
    return [normalize_job(r) for r in records]
