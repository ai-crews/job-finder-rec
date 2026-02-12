from typing import List, Optional
from datetime import datetime, date

from job_finder_rec.recommender.types import RecommendRequest, PersonalizedMethod, JobPosting, RecommendationItem, UserPreferences


def _global_deadline_filter(jobs: List[JobPosting], today: Optional[date] = None) -> List[JobPosting]:
    """
    [전역 하드필터] 마감일 필터
    
    - 발송일(today) 기준으로 application_deadline_date가 하루 이상 남은 공고만 포함
    - 시간은 판단에 사용하지 않음 (날짜만 비교)
    - 마감일이 없는 공고는 필터 적용 안함 (통과시킴)
    
    Args:
        jobs: 필터링할 공고 목록
        today: 기준 날짜 (None이면 오늘 사용)
    
    Returns:
        필터링된 공고 목록
    """
    if today is None:
        today = date.today()
    
    filtered = []
    for j in jobs:
        # 1) 마감일이 없으면 필터 적용 안함 (결과에 포함)
        if not j.application_deadline_date:
            filtered.append(j)
            continue
        
        try:
            # 2) 마감일을 date 객체로 파싱 (시간 정보 무시)
            deadline_date = datetime.strptime(j.application_deadline_date, "%Y-%m-%d").date()
            
            # 3) 마감일 > 오늘 인 경우만 포함 (하루 이상 남음)
            if deadline_date > today:
                filtered.append(j)
        except (ValueError, TypeError):
            # 4) 파싱 실패시 필터 적용 안함 (결과에 포함, 안전성)
            filtered.append(j)
    
    return filtered


def _simple_filter(user: UserPreferences, jobs: List[JobPosting]) -> List[JobPosting]:
    """
    필터링: 전역 하드필터 + 맞춤형 필터
    
    **전역 하드필터(절대조건):**
    - 마감일: 하루 이상 남은 공고만
    
    **맞춤형 필터(개인화):**
    - 고용형태: 사용자 선택 유형만 (미선택/확인불가는 통과)
    - 직무: processed_position_name에 사용자 직무 키워드 포함
    """
    # 1) 전역 하드필터: 마감일
    filtered = _global_deadline_filter(jobs)

    # 2) 맞춤형 필터: 고용형태
    if user.target_employment_types:
        filtered = [
            j for j in filtered
            if (j.employment_type in ("", "확인불가") or j.employment_type in user.target_employment_types)
        ]

    # 3) 맞춤형 필터: 직무 키워드
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
