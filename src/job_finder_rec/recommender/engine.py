from dataclasses import dataclass
from enum import Enum



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
