from typing import List, Tuple

from job_finder_rec.recommender.types import JobPosting, RecommendationItem, UserPreferences, RecommendRequest
from job_finder_rec.recommender.filter import apply_filters
from job_finder_rec.recommender.personalized import recommend_personalized
from job_finder_rec.recommender.explore import recommend_explore


def recommend(
    user: UserPreferences,
    jobs: List[JobPosting],
    req: RecommendRequest,
) -> Tuple[List[RecommendationItem], List[RecommendationItem]]:
    """
    1단계: personalized 추천 — 하드+소프트 조건 모두 통과한 공고, req.sort 기준 정렬
    2단계: explore 추천 — soft reason 불만족 1개 이상인 공고, 불만족 개수 기준 정렬

    Returns:
        (personalized_items, explore_items)
    """
    filter_result = apply_filters(user, jobs)

    personalized_items = recommend_personalized(user, filter_result, req)
    explore_items = recommend_explore(filter_result)

    return personalized_items, explore_items
