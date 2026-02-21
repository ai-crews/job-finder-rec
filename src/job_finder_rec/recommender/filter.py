from datetime import datetime
from datetime import date as _date
from typing import Any, List, Optional

from job_finder_rec.recommender.types import (
    FilterResult, FilterReason, RejectedJob,
    JobPosting, UserPreferences,
)
from job_finder_rec.recommender.utils import map_education_level


# ---------------------------------------------------------------------------
# 전역 하드필터
# ---------------------------------------------------------------------------

def global_deadline_filter(jobs: List[Any], today: Optional[_date] = None) -> FilterResult:
    """
    전역 하드필터: 마감일 필터

    - 발송일(today) 기준으로 `application_deadline_date`가 하루 이상 남은 공고만 포함
    - `application_deadline_time`은 판단에 사용하지 않음 (날짜만 비교)
    - 마감일이 없는 공고는 필터 적용 안함 (통과시킴)
    - 파싱 실패 시 안전을 위해 통과
    """
    if today is None:
        today = _date.today()

    passed: List[Any] = []
    rejected: List[RejectedJob] = []

    for j in jobs:
        adate = getattr(j, "application_deadline_date", None)
        if not adate:
            passed.append(j)
            continue
        try:
            deadline_date = datetime.strptime(adate, "%Y-%m-%d").date()
            if deadline_date > today:
                passed.append(j)
            else:
                rejected.append(RejectedJob(job=j, reason=FilterReason.DEADLINE))
        except (ValueError, TypeError):
            passed.append(j)

    return FilterResult(passed=passed, rejected=rejected)


# ---------------------------------------------------------------------------
# 맞춤형 하드필터 (개별)
# ---------------------------------------------------------------------------

def _position_filter(user: UserPreferences, result: FilterResult) -> FilterResult:
    """
    [하드 필터] 직무 필터

    사용자의 직무 Top3과 공고의 직무를 정규화하여 비교

    통과 조건:
    1. 사용자가 직무를 선택하지 않은 경우 → 필터링 안함 (항상 통과)
    2. 공고의 직무 리스트와 사용자 직무 Top3의 교집합이 있으면 → 통과
    3. 그 외 → 탈락

    예시:
    - 사용자 직무: ["데이터분석가", "ML엔지니어"]
    - 공고1: ["ML엔지니어"] → 통과 (교집합 존재)
    - 공고2: ["AI기획자"] → 탈락 (교집합 없음)
    - 공고3: ["데이터분석가", "AI기획자"] → 통과 (교집합 존재)

    Returns:
        FilterResult: 필터 결과
    """
    if not user.target_jobs:
        return result

    new_passed = []
    new_rejected = list(result.rejected)

    for j in result.passed:
        if any(pos in user.target_jobs for pos in j.processed_position_name):
            new_passed.append(j)
        else:
            new_rejected.append(RejectedJob(job=j, reason=FilterReason.JOB))

    return FilterResult(passed=new_passed, rejected=new_rejected)


def _employment_type_filter(user: UserPreferences, result: FilterResult) -> FilterResult:
    """
    [하드 필터] 고용형태 필터

    사용자가 선택한 고용형태와 공고의 고용형태를 비교

    통과 조건:
    1. 사용자가 고용형태를 선택하지 않은 경우 → 필터링 안함 (항상 통과)
    2. 공고의 고용형태가 없으면 → 항상 통과
    3. 공고의 고용형태와 사용자 선택 고용형태에 교집합이 있으면 → 통과
    4. 그 외 → 탈락

    예시:
    - 사용자: ["계약직", "인턴"]
    - 공고1: [] → 통과 (고용형태 없음)
    - 공고2: ["계약직"] → 통과 (교집합 존재)
    - 공고3: ["정규직"] → 탈락 (교집합 없음)

    Returns:
        FilterResult: 필터 결과
    """
    if not user.target_employment_types:
        return result

    new_passed = []
    new_rejected = list(result.rejected)

    for j in result.passed:
        if not j.processed_employment_type:
            new_passed.append(j)
            continue

        if any(emp in user.target_employment_types for emp in j.processed_employment_type):
            new_passed.append(j)
        else:
            new_rejected.append(RejectedJob(job=j, reason=FilterReason.EMPLOYMENT))

    return FilterResult(passed=new_passed, rejected=new_rejected)


def _education_filter(user: UserPreferences, result: FilterResult) -> FilterResult:
    """
    [하드 필터] 학력 필터

    사용자가 선택한 학력과 공고의 요구 학력을 비교

    통과 조건:
    1. 사용자가 학력을 선택하지 않은 경우 → 필터링 안함 (항상 통과)
    2. 공고에 "학력무관"이 있으면 → 항상 통과
    3. 공고의 요구 학력과 사용자 선택 학력에 교집합이 있으면 → 통과
    4. 그 외 → 탈락

    예시:
    - 사용자: ["학사 졸업(예정)", "박사 졸업(예정)"] → {"학사", "박사"}
    - 공고1: ["학력무관"] → 통과 (학력무관)
    - 공고2: ["학사"] → 통과 (교집합 존재)
    - 공고3: ["석사", "박사"] → 통과 (교집합 {"박사"})
    - 공고4: ["석사"] → 탈락 (교집합 없음)

    Returns:
        FilterResult: 필터 결과
    """
    if not user.current_education or not isinstance(user.current_education, list):
        return result

    user_education_keywords = set()
    for edu_str in user.current_education:
        keyword = map_education_level(edu_str)
        if keyword:
            user_education_keywords.add(keyword)

    if not user_education_keywords:
        return result

    new_passed = []
    new_rejected = list(result.rejected)

    for j in result.passed:
        job_education_list = j.processed_education_level_list or []
        if isinstance(job_education_list, str):
            job_education_list = [job_education_list]

        if not job_education_list:
            new_passed.append(j)
            continue

        job_education_keywords = set()
        for job_edu in job_education_list:
            keyword = map_education_level(job_edu)
            if keyword:
                job_education_keywords.add(keyword)

        if "학력무관" in job_education_keywords:
            new_passed.append(j)
            continue

        if job_education_keywords & user_education_keywords:
            new_passed.append(j)
        else:
            new_rejected.append(RejectedJob(job=j, reason=FilterReason.EDUCATION))

    return FilterResult(passed=new_passed, rejected=new_rejected)


def _company_size_filter(user: UserPreferences, result: FilterResult) -> FilterResult:
    """
    [하드 필터] 기업규모 필터

    사용자가 선택한 기업규모와 공고의 기업규모를 비교

    통과 조건:
    1. 사용자가 기업규모를 선택하지 않은 경우 → 필터링 안함 (항상 통과)
    2. 공고의 기업규모가 없으면 → 항상 통과 (안전성)
    3. 공고의 기업규모가 사용자 선택에 포함되면 → 통과
    4. 그 외 → 탈락

    예시:
    - 사용자 선택: ["대기업", "중견기업"]
    - 공고1: 없음 → 통과 (기업규모 없음)
    - 공고2: "대기업" → 통과 (포함)
    - 공고3: "스타트업" → 탈락 (미포함)

    Returns:
        FilterResult: 필터 결과
    """
    if not user.preferred_company_sizes:
        return result

    new_passed = []
    new_rejected = list(result.rejected)

    for j in result.passed:
        if not j.company_size or j.company_size in user.preferred_company_sizes:
            new_passed.append(j)
        else:
            new_rejected.append(RejectedJob(job=j, reason=FilterReason.COMPANY_SIZE))

    return FilterResult(passed=new_passed, rejected=new_rejected)


def _industry_filter(user: UserPreferences, result: FilterResult) -> FilterResult:
    """
    [하드 필터] 산업 필터

    사용자가 선택한 산업과 공고의 산업을 비교

    통과 조건:
    1. 사용자가 산업을 선택하지 않은 경우 → 필터링 안함 (항상 통과)
    2. 공고의 산업이 없으면 → 항상 통과 (안전성)
    3. 공고의 산업이 사용자 선택에 포함되면 → 통과
    4. 그 외 → 탈락

    예시:
    - 사용자 선택: ["IT", "금융"]
    - 공고1: 없음 → 통과 (산업 없음)
    - 공고2: "IT" → 통과 (포함)
    - 공고3: "교육" → 탈락 (미포함)

    Returns:
        FilterResult: 필터 결과
    """
    if not user.interested_industries:
        return result

    new_passed = []
    new_rejected = list(result.rejected)

    for j in result.passed:
        if not j.industry or j.industry in user.interested_industries:
            new_passed.append(j)
        else:
            new_rejected.append(RejectedJob(job=j, reason=FilterReason.INDUSTRY))

    return FilterResult(passed=new_passed, rejected=new_rejected)


# ---------------------------------------------------------------------------
# 필터 묶음 적용
# ---------------------------------------------------------------------------

def apply_hard_filter(user: UserPreferences, jobs: List[JobPosting]) -> FilterResult:
    """
    하드필터 전체 적용: 전역 하드필터 + 맞춤형 하드필터 (탈락 사유 기록)

    personalized 추천에 사용 — 사용자 선호 조건을 모두 강제 적용.

    적용 순서:
    1. 전역 하드필터: 마감일 (하루 이상 남은 공고만)
    2. 맞춤형 하드필터:
        - 직무
        - 고용형태
        - 학력
        - 기업규모
        - 산업

    Returns:
        FilterResult: 필터 결과 (통과한 공고 + 탈락 사유 추적)
    """
    result = global_deadline_filter(jobs)
    result = _position_filter(user, result)
    result = _employment_type_filter(user, result)
    result = _education_filter(user, result)
    result = _company_size_filter(user, result)
    result = _industry_filter(user, result)
    return result


def apply_soft_filter(jobs: List[JobPosting], today: Optional[_date] = None) -> FilterResult:
    """
    소프트필터 전체 적용: 마감일 하드필터만 적용 후 반환

    explore 추천에 사용 — 사용자 선호 조건을 강제하지 않고
    마감 지난 공고만 제외한 전체 공고를 노출.

    Returns:
        FilterResult: 필터 결과
    """
    return global_deadline_filter(jobs, today=today)
