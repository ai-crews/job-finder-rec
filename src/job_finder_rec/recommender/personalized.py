from typing import List, Optional

from job_finder_rec.recommender.types import (
    RecommendRequest, PersonalizedMethod, JobPosting, RecommendationItem,
    UserPreferences,
)
from job_finder_rec.recommender.filter import apply_hard_filter



def _get_job_priority_rank(job: JobPosting, user: UserPreferences) -> Optional[int]:
    """
    직무 우선순위 rank 계산

    사용자의 target_jobs 순서(1~3순위) 기준으로, 공고의 processed_position_name과 비교

    Returns:
        int: 1, 2, 3 중 하나
        None: 매칭 없음 (직무 무관 공고 혹은 사용자 직무 미설정)
    """
    if not user.target_jobs or not job.processed_position_name:
        return None

    for rank, target_job in enumerate(user.target_jobs[:3], start=1):
        if not target_job:
            continue
        if target_job in job.processed_position_name:
            return rank

    return None


def recommend_personalized(user: UserPreferences, jobs: List[JobPosting], req: "RecommendRequest") -> List[RecommendationItem]:
    """
    맞춤형 추천
    """
    
    filter_result = apply_hard_filter(user, jobs)

    items: List[RecommendationItem] = []
    for j in filter_result.passed:
        rank = _get_job_priority_rank(j, user)
        items.append(RecommendationItem(job=j, score=0.0, job_priority_rank=rank))
    return items
