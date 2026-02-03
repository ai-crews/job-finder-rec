from dataclasses import dataclass
from datetime import datetime
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
    '''
    전처리된 고정 스키마를 속성으로 접근하기 위함
    '''
    group_name: str
    company_name: str
    job_title: str
    position_name: str
    processed_position_name: str

    min_experience_level: str
    max_experience_level: str
    employment_type: str

    min_education_level: str
    max_education_level: str

    application_start_date: Optional[str]
    application_deadline_date: Optional[str]
    application_deadline_time: Optional[str]

    team_introduction: Optional[str]
    job_duties: Optional[str]
    qualifications: Optional[str]
    preferred_qualifications: Optional[str]

    work_location: Optional[str]
    work_department: Optional[str]
    recruitment_process: Optional[str]
    other_details: Optional[str]

    application_link: Optional[str]
    image_filename: Optional[str]
    crawling_datetime: Optional[str]

    # 파생 필드: 마감기한 datetime
    deadline: Optional[datetime] = None

    # 디버깅/추적용 원본
    raw: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class RecommendationItem:
    job: JobPosting
    is_preferred_company: bool
    score: float = 0.0