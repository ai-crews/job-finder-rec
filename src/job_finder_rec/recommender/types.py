from dataclasses import dataclass
from enum import Enum
from datetime import datetime, time
from typing import Any, Dict, FrozenSet, List, Optional


@dataclass(frozen=True)
class UserPreferences:
    email: str
    name: str
    education_level: List[str]       # ["학사 졸업(예정)", "석사 졸업(예정)", ...]
    employment_type: List[str]       # ["정규직", "인턴", ...]
    top3_position: List[str]         # ["데이터 분석", "ML 엔지니어", ...]
    company_size: List[str]
    company_industry: List[str]
    has_language_score: Optional[str]  # "예", "아니오"
    sort: str                        # "deadline", "recommend" (폼 값 그대로)
    raw: Dict[str, Any]              # 원본 record 보관(디버깅/추적용)


@dataclass(frozen=True, eq=False)
class JobPosting:
    # ── 필수 필드 ──────────────────────────────────────────────
    post_id: str
    job_title: str
    company_name: str
    industry: str
    company_size: str
    processed_position_name: List[str]              # ["ML엔지니어", "AI개발자"]
    processed_education_level: List[str]
    processed_experience_level: str
    processed_employment_type: List[str]            # ["정규직"]
    processed_language_required: bool
    json_file_name: str

    # ── 선택 필드 (파싱 실패 시 None) ─────────────────────────
    deadline_date: Optional[datetime] = None        # 마감일 (date 부분)
    deadline_time: Optional[time] = None            # 마감시각 (time 부분만)
    deadline: Optional[datetime] = None             # 파생: date+time 합산

    # ── 디버깅/추적용 원본 ────────────────────────────────────
    raw: Optional[Dict[str, Any]] = None


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