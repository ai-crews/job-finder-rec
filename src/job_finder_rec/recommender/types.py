from dataclasses import dataclass
from enum import Enum
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
    sort: str                              # "deadline", "recommend" (폼 값 그대로)
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

    @classmethod
    def from_dict(cls, src: Dict[str, Any], fallback_id: Optional[str] = None) -> "JobPosting":
        """Create a JobPosting from a raw dict.

        - Uses `fallback_id` when `group_name` is missing/empty.
        - Parses `application_deadline_date` and optional `application_deadline_time` into `deadline`.
        - Returns an instance with `raw` set to the original dict.
        """
        group_name = src.get("group_name") or fallback_id or ""
        company_name = src.get("company_name") or ""
        job_title = src.get("job_title") or ""
        position_name = src.get("position_name") or ""
        processed_position_name = src.get("processed_position_name") or ""

        min_experience_level = src.get("min_experience_level") or ""
        max_experience_level = src.get("max_experience_level") or ""
        employment_type = src.get("employment_type") or ""

        min_education_level = src.get("min_education_level") or ""
        max_education_level = src.get("max_education_level") or ""

        application_start_date = src.get("application_start_date")
        application_deadline_date = src.get("application_deadline_date")
        application_deadline_time = src.get("application_deadline_time")

        team_introduction = src.get("team_introduction")
        job_duties = src.get("job_duties")
        qualifications = src.get("qualifications")
        preferred_qualifications = src.get("preferred_qualifications")

        work_location = src.get("work_location")
        work_department = src.get("work_department")
        recruitment_process = src.get("recruitment_process")
        other_details = src.get("other_details")

        application_link = src.get("application_link")
        image_filename = src.get("image_filename")
        crawling_datetime = src.get("crawling_datetime")

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
            group_name=group_name,
            company_name=company_name,
            job_title=job_title,
            position_name=position_name,
            processed_position_name=processed_position_name,
            min_experience_level=min_experience_level,
            max_experience_level=max_experience_level,
            employment_type=employment_type,
            min_education_level=min_education_level,
            max_education_level=max_education_level,
            application_start_date=application_start_date,
            application_deadline_date=application_deadline_date,
            application_deadline_time=application_deadline_time,
            team_introduction=team_introduction,
            job_duties=job_duties,
            qualifications=qualifications,
            preferred_qualifications=preferred_qualifications,
            work_location=work_location,
            work_department=work_department,
            recruitment_process=recruitment_process,
            other_details=other_details,
            application_link=application_link,
            image_filename=image_filename,
            crawling_datetime=crawling_datetime,
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


@dataclass(frozen=True)
class RecommendRequest:
    feed_type: FeedType = FeedType.PERSONALIZED
    sort: SortOption = SortOption.RECOMMENDATION
    method: PersonalizedMethod = PersonalizedMethod.FILTER
    top_n: int = 10