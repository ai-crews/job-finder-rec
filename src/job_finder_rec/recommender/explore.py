from typing import Dict, FrozenSet, List, Tuple

from job_finder_rec.recommender.types import FilterReason, FilterResult, JobPosting, RecommendationItem

_SOFT_REASONS: FrozenSet[FilterReason] = frozenset({
    FilterReason.EMPLOYMENT,
    FilterReason.COMPANY_SIZE,
    FilterReason.INDUSTRY,
})


def _sort_explore(audit: Dict[JobPosting, FrozenSet[FilterReason]]) -> List[JobPosting]:
    """
    soft reason(고용형태·기업규모·산업) 불만족 개수 기준 오름차순 정렬

    - audit에 남아있는 공고들은 이미 하드 필터(마감일·직무·학력)를 통과한 상태
    - soft reason이 0개인 공고(= personalized 공고)는 제외
    - 불만족 1개 → 2개 → 3개 순
    """
    ranked: List[Tuple[JobPosting, int]] = []
    for job, reasons in audit.items():
        soft_count = len(reasons & _SOFT_REASONS)
        if soft_count == 0:
            continue  # explore에서 제외 > personalized 추천으로 이미 포함된 공고
        ranked.append((job, soft_count))
    ranked.sort(key=lambda x: x[1])
    return [j for j, _ in ranked]


def recommend_explore(filter_result: FilterResult) -> List[RecommendationItem]:
    """
    탐색형 추천 — engine에서 이미 실행된 FilterResult를 받아 사용

    - 하드 필터(마감일·직무·학력)는 이미 제거된 상태
    - soft reason(고용형태·기업규모·산업) 불만족 개수 기준 오름차순 정렬
      (불만족 1개 → 2개 → 3개 순)
    """
    items: List[RecommendationItem] = []
    for j in _sort_explore(filter_result.audit)[:5]:
        items.append(RecommendationItem(job=j))
    return items
