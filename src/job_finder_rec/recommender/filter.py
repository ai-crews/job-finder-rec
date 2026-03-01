from datetime import datetime
from datetime import date as _date
from typing import Any, Dict, FrozenSet, List, Optional, Set

from job_finder_rec.recommender.types import (
    FilterResult, FilterReason,
    JobPosting, UserPreferences,
)
from job_finder_rec.recommender.utils import map_education_level


# ---------------------------------------------------------------------------
# 하드 필터 (마감일·직무·학력) — 실제 제거, 이유 기록 없음
# ---------------------------------------------------------------------------

def _deadline_filter(
    jobs: List[Any],
    today: Optional[_date] = None,
) -> List[Any]:
    """마감일 하드 필터:
    - 발송일(today) 기준으로 deadline_date가 하루 이상 남은 공고만 포함
    - 마감일이 없는 공고는 통과
    - 파싱 실패 시 안전하게 통과
    """
    if today is None:
        today = _date.today()

    result = []
    for j in jobs:
        deadline_date = getattr(j, "deadline_date", None)
        if not deadline_date:
            result.append(j)
            continue
        try:
            d = deadline_date.date() if hasattr(deadline_date, "date") else deadline_date
            if d > today:
                result.append(j)
        except (ValueError, TypeError):
            result.append(j)
    return result


def _position_filter(
    user: UserPreferences,
    jobs: List[Any],
) -> List[Any]:
    """직무 하드 필터: 직무 불일치 공고를 후보에서 제거

    - 사용자가 직무를 선택하지 않은 경우 → 전부 통과
    - 공고의 직무와 사용자 직무 Top3의 교집합이 없으면 → 제거
    """
    if not user.top3_position:
        return jobs

    return [
        j for j in jobs
        if any(pos in user.top3_position for pos in j.processed_position_name)
    ]


def _education_filter(
    user: UserPreferences,
    jobs: List[Any],
) -> List[Any]:
    """학력 하드 필터: 학력 요건 불일치 공고를 후보에서 제거

    - 사용자가 학력을 선택하지 않은 경우 → 전부 통과
    - 공고에 "학력무관"이 있으면 → 통과
    - 공고와 사용자 학력 교집합이 있으면 → 통과
    - 그 외 → 제거
    """
    if not user.education_level or not isinstance(user.education_level, list):
        return jobs

    user_education_keywords: Set[str] = set()
    for edu_str in user.education_level:
        keyword = map_education_level(edu_str)
        if keyword:
            user_education_keywords.add(keyword)

    if not user_education_keywords:
        return jobs

    result = []
    for j in jobs:
        job_education_list = j.processed_education_level or []
        if isinstance(job_education_list, str):
            job_education_list = [job_education_list]

        if not job_education_list:
            result.append(j)
            continue

        job_education_keywords: Set[str] = set()
        for job_edu in job_education_list:
            keyword = map_education_level(job_edu)
            if keyword:
                job_education_keywords.add(keyword)

        if "학력무관" in job_education_keywords:
            result.append(j)
            continue

        if job_education_keywords & user_education_keywords:
            result.append(j)

    return result


# ---------------------------------------------------------------------------
# 소프트 감사 필터 (고용형태·기업규모·산업) — 이유 누적, 제거 없음
# ---------------------------------------------------------------------------

def _employment_type_audit(
    user: UserPreferences,
    jobs: List[Any],
) -> Dict[Any, FilterReason]:
    """고용형태 감사: 사용자 고용형태와 불일치하는 공고 → FilterReason.EMPLOYMENT"""
    if not user.employment_type:
        return {}

    failed: Dict[Any, FilterReason] = {}
    for j in jobs:
        if not j.processed_employment_type:
            continue
        if not any(emp in user.employment_type for emp in j.processed_employment_type):
            failed[j] = FilterReason.EMPLOYMENT
    return failed


def _company_size_audit(
    user: UserPreferences,
    jobs: List[Any],
) -> Dict[Any, FilterReason]:
    """기업규모 감사: 기업규모 불일치 공고 → FilterReason.COMPANY_SIZE"""
    if not user.company_size:
        return {}

    failed: Dict[Any, FilterReason] = {}
    for j in jobs:
        if j.company_size and j.company_size not in user.company_size:
            failed[j] = FilterReason.COMPANY_SIZE
    return failed


def _industry_audit(
    user: UserPreferences,
    jobs: List[Any],
) -> Dict[Any, FilterReason]:
    """산업 감사: 산업 불일치 공고 → FilterReason.INDUSTRY"""
    if not user.company_industry:
        return {}

    failed: Dict[Any, FilterReason] = {}
    for j in jobs:
        if j.industry and j.industry not in user.company_industry:
            failed[j] = FilterReason.INDUSTRY
    return failed


# ---------------------------------------------------------------------------
# 감사 결과 통합
# ---------------------------------------------------------------------------

def _build_audit(
    jobs: List[Any],
    *partial_audits: Dict[Any, FilterReason],
) -> Dict[Any, FrozenSet[FilterReason]]:
    """여러 소프트 감사 결과를 공고별 이유 집합으로 통합"""
    combined: Dict[Any, Set[FilterReason]] = {j: set() for j in jobs}
    for partial in partial_audits:
        for job, reason in partial.items():
            combined[job].add(reason)
    return {j: frozenset(r) for j, r in combined.items()}


# ---------------------------------------------------------------------------
# 전체 필터 적용 함수
# ---------------------------------------------------------------------------

def apply_filters(user: UserPreferences, jobs: List[JobPosting]) -> FilterResult:
    """필터 전체 적용

    1단계 — 하드 필터 (실제 제거, 이유 기록 없음):
        마감일 → 직무 → 학력

    2단계 — 소프트 감사 (제거 없이 이유 누적):
        고용형태 / 기업규모 / 산업

    personalized 추천: FilterResult.passed  (audit 이유 없는 공고)
    explore 추천:      FilterResult.audit   (audit 이유 없는 공고 제외)

    Returns:
        FilterResult: audit 기반 결과
    """
    # 1단계: 하드 필터 — 후보 축소
    candidates = _deadline_filter(jobs)
    candidates = _position_filter(user, candidates)
    candidates = _education_filter(user, candidates)

    # 2단계: 소프트 감사 — 이유 누적
    audit = _build_audit(
        candidates,
        _employment_type_audit(user, candidates),
        _company_size_audit(user, candidates),
        _industry_audit(user, candidates),
    )
    return FilterResult(audit=audit)

