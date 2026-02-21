from typing import List, Tuple

from job_finder_rec.recommender.types import JobPosting, RecommendationItem, UserPreferences, RecommendRequest, FeedType, SortOption, PersonalizedMethod
from job_finder_rec.recommender.personalized import recommend_personalized
from job_finder_rec.recommender.explore import recommend_explore


def _sort_recommendations(items: List[RecommendationItem], sort: SortOption) -> List[RecommendationItem]:
    """
    정렬 옵션에 따라 추천 결과 정렬
    """
    if sort == SortOption.DEADLINE:
        # 마감순: deadline이 있는 것 먼저, 없으면 끝으로
        return sorted(
            items,
            key=lambda x: (x.job.deadline is None, x.job.deadline)
        )
    else:  # SortOption.RECOMMENDATION
        # 추천순 (직무 우선순위 기반)
        # 1차: job_priority_rank 오름차순 (1→2→3, None은 맨 뒤 → 4로 처리)
        # 2차: 마감일 오름차순 tie-break (가까운 순, deadline 없는 공고는 맨 뒤)
        # 3차: 입력 순서 유지 (Python stable sort 보장)
        return sorted(
            items,
            key=lambda x: (
                x.job_priority_rank if x.job_priority_rank is not None else 4,
                x.job.deadline is None,
                x.job.deadline,
            )
        )


def recommend(
    user: UserPreferences,
    jobs: List[JobPosting],
    req: RecommendRequest,
) -> Tuple[List[RecommendationItem], List[RecommendationItem]]:
    """
    1단계: personalized 추천 (전체 공고 대상)
    2단계: personalized 결과에 포함되지 않은 나머지 공고로 explore 추천

    Returns:
        (personalized_items, explore_items) — 각각 정렬 완료된 리스트
    """
    personalized_items = recommend_personalized(user, jobs, req)

    # personalized 결과에 포함된 공고 객체 식별
    personalized_job_ids = {id(item.job) for item in personalized_items}

    # 나머지 공고로 explore 실행
    remaining_jobs = [j for j in jobs if id(j) not in personalized_job_ids]
    explore_items = recommend_explore(user, remaining_jobs, req)

    return (
        _sort_recommendations(personalized_items, req.sort),
        _sort_recommendations(explore_items, req.sort),
    )
