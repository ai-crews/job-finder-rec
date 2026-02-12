from typing import List

from job_finder_rec.recommender.types import JobPosting, RecommendationItem, UserPreferences, RecommendRequest
from job_finder_rec.recommender.utils import global_deadline_filter


def recommend_explore(user: UserPreferences, jobs: List[JobPosting], req: RecommendRequest) -> List[RecommendationItem]:
    """
    탐색형 placeholder:
    - 정렬/랭킹 정책은 추후 확정
    - 지금은 단순히 앞에서 top_n개 반환
    """
    # apply global hard filters (deadline)
    result = global_deadline_filter(jobs)

    # optional: expose rejected counts for debugging
    if result.rejected:
        _ = result.counts

    items: List[RecommendationItem] = []
    for j in result.passed[: req.top_n]:
        items.append(RecommendationItem(job=j, is_preferred_company=False, score=0.0))
    return items
