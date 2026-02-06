from typing import List

from job_finder_rec.recommender.types import JobPosting, RecommendationItem, UserPreferences, RecommendRequest, FeedType, SortOption, PersonalizedMethod
from job_finder_rec.recommender.personalized import recommend_personalized
from job_finder_rec.recommender.explore import recommend_explore


def recommend(user: UserPreferences, jobs: List[JobPosting], req: RecommendRequest) -> List[RecommendationItem]:
    if req.feed_type == FeedType.EXPLORE:
        return recommend_explore(user, jobs, req)
    return recommend_personalized(user, jobs, req)
