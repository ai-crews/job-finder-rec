from typing import List, Optional

from job_finder_rec.recommender.types import (
    RecommendRequest, PersonalizedMethod, JobPosting, RecommendationItem, 
    UserPreferences, FilterResult, FilterReason, RejectedJob
)
from job_finder_rec.recommender.utils import global_deadline_filter





def _employment_type_filter(user: UserPreferences, result: FilterResult) -> FilterResult:
    """
    [맞춤형 필터] 고용형태 필터
    
    - 사용자가 고용형태를 선택하지 않으면 필터링 안함
    - 공고의 고용형태가 비어있거나 "확인불가"이면 통과
    - 공고의 고용형태가 사용자 선택목록에 있으면 통과
    """
    if not user.target_employment_types:
        return result
    
    new_passed = []
    new_rejected = list(result.rejected)
    
    for j in result.passed:
        if j.employment_type in ("", "확인불가") or j.employment_type in user.target_employment_types:
            new_passed.append(j)
        else:
            new_rejected.append(RejectedJob(job=j, reason=FilterReason.EMPLOYMENT))
    
    return FilterResult(passed=new_passed, rejected=new_rejected)


def _job_filter(user: UserPreferences, result: FilterResult) -> FilterResult:
    """
    [맞춤형 필터] 직무 필터
    
    - processed_position_name에 사용자 직무 키워드가 포함되어야 함
    """
    if not user.target_jobs:
        return result
    
    def norm(s: str) -> str:
        return (s or "").replace(" ", "").lower()
    
    keywords = [norm(x) for x in user.target_jobs if x]
    new_passed = []
    new_rejected = list(result.rejected)
    
    for j in result.passed:
        if any(k in norm(j.processed_position_name) for k in keywords):
            new_passed.append(j)
        else:
            new_rejected.append(RejectedJob(job=j, reason=FilterReason.JOB))
    
    return FilterResult(passed=new_passed, rejected=new_rejected)


def _simple_filter(user: UserPreferences, jobs: List[JobPosting]) -> FilterResult:
    """
    필터링: 전역 하드필터 + 맞춤형 필터 (Reason 기록 포함)
    
    **전역 하드필터(절대조건):**
    - 마감일: 하루 이상 남은 공고만
    
    **맞춤형 필터(개인화):**
    - 고용형태: 사용자 선택 유형만 (미선택/확인불가는 통과)
    - 직무: processed_position_name에 사용자 직무 키워드 포함
    
    Returns:
        FilterResult: 필터 결과 (통과한 공고 + 탈락 공고들의 사유)
    """
    # 1) 전역 하드필터: 마감일
    result = global_deadline_filter(jobs)
    
    # 2) 맞춤형 필터: 고용형태
    result = _employment_type_filter(user, result)
    
    # 3) 맞춤형 필터: 직무 키워드
    result = _job_filter(user, result)
    
    return result


def recommend_personalized(user: UserPreferences, jobs: List[JobPosting], req: "RecommendRequest") -> List[RecommendationItem]:
    """
    맞춤형 추천
    - method에 따라 분기
    - 정렬/점수화는 추후 이슈에서 구현
    - 필터링 결과와 탈락 사유를 추적
    """
    if req.method == "embedding":
        # TODO: 임베딩 기반 유사 추천 구현
        # 지금은 filter fallback
        filter_result = _simple_filter(user, jobs)
    else:
        filter_result = _simple_filter(user, jobs)

    # 디버깅용: 필터링 결과 로깅 (선택)
    if filter_result.rejected:
        count_by_reason = filter_result.counts
        # print(f"[필터링] 통과: {len(filter_result.passed)}, 탈락: {len(filter_result.rejected)}")
        # print(f"[탈락 사유] {count_by_reason}")

    items: List[RecommendationItem] = []
    for j in filter_result.passed[: req.top_n]:
        items.append(RecommendationItem(job=j, is_preferred_company=False, score=0.0))
    return items
