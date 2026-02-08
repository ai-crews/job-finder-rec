from typing import List

from job_finder_rec.recommender.types import RecommendRequest, PersonalizedMethod, JobPosting, RecommendationItem, UserPreferences


def _simple_filter(user: UserPreferences, jobs: List[JobPosting]) -> List[JobPosting]:
    """
    가장 기본적인 필터링:
    - 정렬/점수화 없음
    - 너무 빡세게 자르면 결과가 0이 될 수 있으니 최소 필터만 적용
    """
    filtered = jobs

    # 고용형태 필터 : 비어있거나 "확인불가" 이거나 사용자가 원하는 것만
    if user.target_employment_types:
        filtered = [
            j for j in filtered
            if (j.employment_type in ("", "확인불가") or j.employment_type in user.target_employment_types)
        ]

    # 직무 키워드 필터 : processed_position_name에 포함되는 것만
    if user.target_jobs:
        def norm(s: str) -> str:
            return (s or "").replace(" ", "").lower()
        keywords = [norm(x) for x in user.target_jobs if x]
        filtered = [
            j for j in filtered
            if any(k in norm(j.processed_position_name) for k in keywords)
        ]

    return filtered


def recommend_personalized(user: UserPreferences, jobs: List[JobPosting], req: "RecommendRequest") -> List[RecommendationItem]:
    """
    맞춤형 추천
    - method에 따라 분기
    - 정렬/점수화는 추후 이슈에서 구현
    """
    if req.method == "embedding":
        # TODO: 임베딩 기반 유사 추천 구현
        # 지금은 filter fallback
        selected = _simple_filter(user, jobs)
    else:
        selected = _simple_filter(user, jobs)

    items: List[RecommendationItem] = []
    for j in selected[: req.top_n]:
        items.append(RecommendationItem(job=j, is_preferred_company=False, score=0.0))
    return items
