from datetime import datetime
from typing import Optional


def map_education_level(education_str: Optional[str]) -> str:
    """
    학력 문자열에서 키워드 추출
    
    예:
    - "학사 졸업(예정)" → "학사"
    - "석사 졸업(예정)" → "석사"
    - "박사 졸업(예정)" → "박사"
    - "학력무관" → "학력무관"
    
    Returns:
        str: 추출된 학력 키워드 ("학사", "석사", "박사", "학력무관" 중 하나, 없으면 "")
    """
    if not education_str:
        return ""
    
    s = education_str.strip()
    
    # 박사 확인
    if "박사" in s:
        return "박사"
    
    # 석사 확인
    if "석사" in s:
        return "석사"
    
    # 학사 확인
    if "학사" in s:
        return "학사"
    
    # 학력무관 확인
    if "학력무관" in s:
        return "학력무관"
    
    return ""


def safe_enum(enum_cls, value, fallback):
    """
    값을 안전하게 enum 멤버로 변환
    - value가 이미 enum 멤버이면 그대로 반환
    - value가 문자열이면 value 또는 name으로 대소문자 구분 없이 매칭
    - 그 외의 경우 fallback을 반환
    """
    try:
        if value is None:
            return fallback
        if isinstance(value, enum_cls):
            return value
        if isinstance(value, str):
            s = value.strip().lower()
            for member in enum_cls:
                if member.value.lower() == s or member.name.lower() == s:
                    return member
        return fallback
    except Exception:
        return fallback


def build_requests_for_user(user):
    """
    UserPreferences 객체로부터 RecommendRequest를 생성

    normalize_user()를 통해 이미 정규화된 user.sort를 읽음

    method는 고정값이며 user에서 읽지 않음
    feed_type은 포함하지 않는다 — 엔진은 항상 personalized 후 explore 순서로 실행
    """
    from job_finder_rec.recommender.types import RecommendRequest, SortOption

    sort = safe_enum(SortOption, user.sort, SortOption.RECOMMENDATION)

    req = RecommendRequest(sort=sort)
    return req

