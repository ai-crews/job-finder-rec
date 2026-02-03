from dataclasses import dataclass
from enum import Enum
from typing import List

from job_finder_rec.recommender.types import JobPosting, RecommendationItem, UserPreferences
from job_finder_rec.recommender.personalized import recommend_personalized
from job_finder_rec.recommender.explore import recommend_explore


class FeedType(str, Enum):
    PERSONALIZED = "personalized"
    EXPLORE = "explore"


class SortOption(str, Enum):
    DEADLINE = "deadline"        # 마감기한순
    RECOMMENDATION = "recommend" # 추천순


class PersonalizedMethod(str, Enum):
    FILTER = "filter"            # 필터 기반
    EMBEDDING = "embedding"      # 임베딩 기반


@dataclass(frozen=True)
class RecommendRequest:
    feed_type: FeedType = FeedType.PERSONALIZED
    sort: SortOption = SortOption.RECOMMENDATION
    method: PersonalizedMethod = PersonalizedMethod.FILTER
    top_n: int = 10


def recommend(user: UserPreferences, jobs: List[JobPosting], req: RecommendRequest) -> List[RecommendationItem]:
    if req.feed_type == FeedType.EXPLORE:
        return recommend_explore(user, jobs, req)
    return recommend_personalized(user, jobs, req)
