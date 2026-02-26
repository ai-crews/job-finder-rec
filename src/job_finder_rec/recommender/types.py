from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Dict, FrozenSet, List, Optional


@dataclass(frozen=True)
class UserPreferences:
    email: str
    target_jobs: List[str]                 # ["데이터 분석", "ML 엔지니어", ...]
    target_employment_types: List[str]     # ["정규직", "인턴", ...]
    sort: str                              # "deadline", "recommend" (폼 값 그대로)
    raw: Dict[str, Any]                    # 원본 record 보관(디버깅/추적용)
    name: Optional[str] = None
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    current_education: List[str] = field(default_factory=list)  # ["학사 졸업(예정)", "석사 졸업(예정)", ...]
    preferred_company_sizes: List[str] = field(default_factory=list)
    interested_industries: List[str] = field(default_factory=list)
    has_english_score: Optional[str] = None  # "예", "아니오"


@dataclass(frozen=True, eq=False)
class JobPosting:
    '''
    전처리된 고정 스키마를 속성으로 접근하기 위함
    '''
    company_name: str
    job_title: str
    processed_position_name: List[str]              # ["ML엔지니어", "AI개발자"]

    processed_experience_level: str
    processed_employment_type: List[str]            # ["정규직"]
    
    processed_language_score_required: str

    processed_education_level_list: List[str]

    industry: Optional[str] = None
    company_size: Optional[str] = None
    application_deadline_date: Optional[str] = None
    application_deadline_time: Optional[str] = None

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

        processed_language_score_required = src.get("processed_language_score_required") or ""

        processed_education_level_list = src.get("processed_education_level_list") or []
        if isinstance(processed_education_level_list, str):
            processed_education_level_list = [processed_education_level_list] if processed_education_level_list else []

        industry = src.get("industry")
        company_size = src.get("company_size")

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
            processed_language_score_required=processed_language_score_required,
            processed_education_level_list=processed_education_level_list,
            industry=industry,
            company_size=company_size,
            application_deadline_date=application_deadline_date,
            application_deadline_time=application_deadline_time,
            deadline=deadline,
            raw=src,
        )


@dataclass(frozen=True)
class RecommendationItem:
    job: JobPosting
    job_priority_rank: Optional[int] = None  # 직무 우선순위 버킷 (1/2/3, None=미매칭)


class SortOption(str, Enum):
    DEADLINE = "deadline"
    RECOMMENDATION = "recommend"


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
    """감사(audit) 기반 필터링 결과

    - audit: 각 공고 → 탈락 사유 집합 (빈 집합 = 전체 통과)
    - passed: 탈락 사유가 없는 공고 목록 (하드 필터 통과) [property]
    - rejected: 탈락한 (공고, 사유) 쌍 목록 [property]
    - counts: 사유별 탈락 카운트 (디버깅/로깅용) [property]
    """
    audit: Dict["JobPosting", FrozenSet["FilterReason"]]

    @property
    def passed(self) -> List["JobPosting"]:
        """탈락 사유가 하나도 없는 공고 (하드 필터 전체 통과)"""
        return [j for j, reasons in self.audit.items() if not reasons]

    @property
    def rejected(self) -> List["RejectedJob"]:
        """탈락한 공고 + 사유 목록 (모든 사유 포함, 공고 중복 가능)"""
        result = []
        for job, reasons in self.audit.items():
            for reason in reasons:
                result.append(RejectedJob(job=job, reason=reason))
        return result

    @property
    def counts(self) -> Dict[str, int]:
        """사유별 탈락 카운트"""
        from collections import Counter
        c: Counter = Counter()
        for reasons in self.audit.values():
            for r in reasons:
                c[r.value] += 1
        return dict(c)


@dataclass(frozen=True)
class RecommendRequest:
    sort: SortOption = SortOption.RECOMMENDATION