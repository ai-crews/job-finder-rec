from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class UserPreferences:
    email: str
    target_jobs: List[str]                 # ["데이터 분석", "ML 엔지니어", ...]
    target_employment_types: List[str]     # ["정규직", "인턴", ...]
    target_education_levels: List[str]     # ["학사", "석사", ...]
    career_pref: List[str]                 # ["신입"] or ["경력"] 등 (폼 값 그대로)
    target_companies: List[str]            # ["KB손해보험", "네이버", ...]
    raw: Dict[str, Any]                    # 원본 record 보관(디버깅/추적용)


@dataclass(frozen=True)
class JobPosting:
    # 전처리된 고정 스키마를 "속성"으로 접근하기 위한 타입
    job_id: str
    title: str
    company_name: str

    processed_position_name: str
    min_experience_level: str
    employment_type: str
    min_education_level: str

    url: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

    @staticmethod
    def from_dict(d: Dict[str, Any], fallback_id: str) -> "JobPosting":
        # 전처리로 키가 항상 동일하니, 여기서만 딱 한 번 매핑해주면 됨
        return JobPosting(
            job_id=str(d.get("job_id") or fallback_id),
            title=str(d.get("title") or "").strip(),
            company_name=str(d.get("company_name") or "").strip(),
            processed_position_name=str(d.get("processed_position_name") or "").strip(),
            min_experience_level=str(d.get("min_experience_level") or "").strip(),
            employment_type=str(d.get("employment_type") or "").strip(),
            min_education_level=str(d.get("min_education_level") or "").strip(),
            url=(str(d.get("url")).strip() if d.get("url") else None),
            raw=d,
        )


@dataclass(frozen=True)
class RecommendationItem:
    job: JobPosting
    is_preferred_company: bool
    score: int
