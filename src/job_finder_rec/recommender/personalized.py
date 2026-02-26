from typing import List, Optional

from job_finder_rec.recommender.types import (
    RecommendRequest, FilterResult, JobPosting, RecommendationItem,
    UserPreferences, SortOption,
)


def _get_job_priority_rank(job: JobPosting, user: UserPreferences) -> Optional[int]:
    """
    직무 우선순위 rank 계산

    사용자의 target_jobs 순서(1~3순위) 기준으로, 공고의 processed_position_name과 비교

    Returns:
        int: 1, 2, 3 중 하나
    """
    if not user.target_jobs or not job.processed_position_name:
        return None

    for rank, target_job in enumerate(user.target_jobs[:3], start=1):
        if not target_job:
            continue
        if target_job in job.processed_position_name:
            return rank

    return None


def _sort_personalized(items: List[RecommendationItem], sort: SortOption) -> List[RecommendationItem]:
    """정렬 옵션에 따라 맞춤형 추천 결과 정렬

    DEADLINE: 마감일 오름차순 (마감일 없는 공고는 맨 뒤)
    RECOMMENDATION: 직무 우선순위 → 마감일 tie-break
        1차: job_priority_rank 오름차순 (1→2→3, None은 맨 뒤 → 4로 처리)
        2차: 마감일 오름차순
    """
    if sort == SortOption.DEADLINE:
        return sorted(
            items,
            key=lambda x: (x.job.deadline is None, x.job.deadline),
        )
    else:  # SortOption.RECOMMENDATION
        return sorted(
            items,
            key=lambda x: (
                x.job_priority_rank if x.job_priority_rank is not None else 4,
                x.job.deadline is None,
                x.job.deadline,
            ),
        )


def recommend_personalized(user: UserPreferences, filter_result: FilterResult, req: "RecommendRequest") -> List[RecommendationItem]:
    """
    맞춤형 추천 — engine에서 이미 실행된 FilterResult를 받아 사용

    filter_result.passed: 하드 필터(마감일·직무·학력) + 소프트 조건 모두 통과한 공고
    """
    items: List[RecommendationItem] = []
    for j in filter_result.passed:
        rank = _get_job_priority_rank(j, user)
        items.append(RecommendationItem(job=j, job_priority_rank=rank))
    return _sort_personalized(items, req.sort)
