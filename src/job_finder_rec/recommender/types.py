from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class UserPreferences:
    email: str
    target_jobs: List[str]                 # ["데이터 분석", "ML 엔지니어", ...]
    target_employment_types: List[str]     # ["정규직", "인턴", ...]
    sort: str                              # "deadline", "recommend" (폼 값 그대로)
    raw: Dict[str, Any]                    # 원본 record 보관(디버깅/추적용)
    # optional demographic / profile fields from the form
    name: Optional[str] = None
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    current_education: List[str] = field(default_factory=list)  # ["학사 졸업(예정)", "석사 졸업(예정)", ...]
    preferred_company_sizes: List[str] = field(default_factory=list)
    interested_industries: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class JobPosting:
    '''
    전처리된 고정 스키마를 속성으로 접근하기 위함
    '''
    # group_name: str
    company_name: str
    job_title: str
    # position_name: str
    processed_position_name: List[str]              # ["ML엔지니어", "AI개발자"]

    # min_experience_level: str
    # max_experience_level: str
    processed_experience_level: str
    processed_employment_type: List[str]            # ["정규직"]
    
    processed_language_required: str

    # min_education_level: str
    # max_education_level: str
    processed_education_level_list: List[str]

    industry: Optional[str] = None
    company_size: Optional[str] = None
    application_start_date: Optional[str] = None
    application_deadline_date: Optional[str] = None
    application_deadline_time: Optional[str] = None

    # team_introduction: Optional[str]
    # job_duties: Optional[str]
    # qualifications: Optional[str]
    # preferred_qualifications: Optional[str]

    # work_location: Optional[str]
    # work_department: Optional[str]
    # recruitment_process: Optional[str]
    # other_details: Optional[str]

    # application_link: Optional[str]
    # image_filename: Optional[str]
    # crawling_datetime: Optional[str]

    # 파생 필드: 마감기한 datetime
    deadline: Optional[datetime] = None

    # 디버깅/추적용 원본
    raw: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "JobPosting":
        """Create a JobPosting from a raw dict.

        - Parses `application_deadline_date` and optional `application_deadline_time` into `deadline`.
        - Returns an instance with `raw` set to the original dict.
        """
        company_name = src.get("company_name") or ""
        job_title = src.get("job_title") or ""

        processed_position_name = src.get("processed_position_name") or []
        if isinstance(processed_position_name, str):
            processed_position_name = [processed_position_name] if processed_position_name else []

        processed_experience_level = src.get("processed_experience_level") or ""

        processed_employment_type = src.get("processed_employment_type") or []
        if isinstance(processed_employment_type, str):
            processed_employment_type = [processed_employment_type] if processed_employment_type else []

        processed_language_required = src.get("processed_language_required") or ""

        processed_education_level_list = src.get("processed_education_level_list") or []
        if isinstance(processed_education_level_list, str):
            processed_education_level_list = [processed_education_level_list] if processed_education_level_list else []

        industry = src.get("industry")
        company_size = src.get("company_size")

        application_start_date = src.get("application_start_date")
        application_deadline_date = src.get("application_deadline_date")
        application_deadline_time = src.get("application_deadline_time")

        # parse deadline into datetime when possible
        deadline: Optional[datetime] = None
        if application_deadline_date:
            try:
                if application_deadline_time:
                    dt_str = f"{application_deadline_date} {application_deadline_time}"
                    try:
                        deadline = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # try without seconds
                        try:
                            deadline = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                        except ValueError:
                            deadline = None
                else:
                    deadline = datetime.strptime(application_deadline_date, "%Y-%m-%d")
            except Exception:
                deadline = None

        return cls(
            company_name=company_name,
            job_title=job_title,
            processed_position_name=processed_position_name,
            processed_experience_level=processed_experience_level,
            processed_employment_type=processed_employment_type,
            processed_language_required=processed_language_required,
            processed_education_level_list=processed_education_level_list,
            industry=industry,
            company_size=company_size,
            application_start_date=application_start_date,
            application_deadline_date=application_deadline_date,
            application_deadline_time=application_deadline_time,
            deadline=deadline,
            raw=src,
        )


@dataclass(frozen=True)
class RecommendationItem:
    job: JobPosting
    is_preferred_company: bool
    score: float = 0.0


class FeedType(str, Enum):
    PERSONALIZED = "personalized"
    EXPLORE = "explore"


class SortOption(str, Enum):
    DEADLINE = "deadline"
    RECOMMENDATION = "recommend"


class PersonalizedMethod(str, Enum):
    FILTER = "filter"
    EMBEDDING = "embedding"


class FilterReason(str, Enum):
    """필터링 탈락 사유 (하드필터)"""
    DEADLINE = "deadline"              # 마감일 필터
    JOB = "job"                        # 직무 필터
    EMPLOYMENT = "employment"          # 고용형태 필터
    COMPANY_SIZE = "company_size"      # 기업규모 필터
    INDUSTRY = "industry"              # 산업 필터
    EDUCATION = "education"            # 학력 필터


@dataclass(frozen=True)
class RejectedJob:
    """필터링에서 탈락한 공고 기록"""
    job: JobPosting
    reason: FilterReason
    

@dataclass(frozen=True)
class FilterResult:
    """필터링 결과 추적
    
    - passed: 필터를 통과한 공고 목록
    - rejected: 탈락한 공고 + 탈락 사유
    - counts: 사유별 탈락 카운트 (디버깅/로깅용)
    """
    passed: List[JobPosting]
    rejected: List[RejectedJob] = field(default_factory=list)
    
    @property
    def counts(self) -> Dict[str, int]:
        """사유별 탈락 카운트"""
        from collections import Counter
        return dict(Counter(r.reason.value for r in self.rejected))


@dataclass(frozen=True)
class RecommendRequest:
    feed_type: FeedType = FeedType.PERSONALIZED
    sort: SortOption = SortOption.RECOMMENDATION
    method: PersonalizedMethod = PersonalizedMethod.FILTER
    top_n: int = 10