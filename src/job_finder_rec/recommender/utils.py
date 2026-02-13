import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from datetime import date as _date

from job_finder_rec.recommender.types import FilterResult, RejectedJob, FilterReason


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


def global_deadline_filter(jobs: List[Any], today: Optional[_date] = None) -> FilterResult:
    """
    전역 하드필터: 마감일 필터

    - 발송일(today) 기준으로 `application_deadline_date`가 하루 이상 남은 공고만 포함
    - `application_deadline_time`은 판단에 사용하지 않음 (날짜만 비교)
    - 마감일이 없는 공고는 필터 적용 안함 (통과시킴)
    - 파싱 실패 시 안전을 위해 통과
    """
    if today is None:
        today = _date.today()

    passed: List[Any] = []
    rejected: List[RejectedJob] = []

    for j in jobs:
        adate = getattr(j, "application_deadline_date", None)
        if not adate:
            passed.append(j)
            continue
        try:
            deadline_date = datetime.strptime(adate, "%Y-%m-%d").date()
            if deadline_date > today:
                passed.append(j)
            else:
                rejected.append(RejectedJob(job=j, reason=FilterReason.DEADLINE))
        except (ValueError, TypeError):
            passed.append(j)

    return FilterResult(passed=passed, rejected=rejected)


def build_deadline(deadline_date: Optional[str], deadline_time: Optional[str]) -> Optional[datetime]:
    """
    application_deadline_date: "YYYY-MM-DD"
    application_deadline_time: "HH:MM:SS" (없으면 23:59:59로 처리)
    """
    if not deadline_date:
        return None

    d = deadline_date.strip()
    t = (deadline_time or "").strip()

    # time이 없거나 비정상이면 기본값
    if not t:
        t = "23:59:59"

    # date만 들어오는 경우도 방어
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(f"{d} {t}", fmt)
        except Exception:
            pass

    # 마지막 fallback: 날짜만 파싱
    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except Exception:
        return None


def safe_enum(enum_cls, value, fallback):
    """
    Safely convert a value to an enum member.
    - If value is already an enum member, return it.
    - If value is a string, match by value or name (case-insensitive).
    - Otherwise, return fallback.
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


def build_requests_for_user(user, feed_type, method, top_n):
    """
    Create a RecommendRequest from a UserPreferences object.
    
    Reads user.raw to extract:
    - sort: 'deadline', 'recommend'
    
    feed_type and method are fixed (not read from user).
    """
    from job_finder_rec.recommender.types import RecommendRequest, SortOption

    raw = getattr(user, "raw", {}) or {}

    sort = safe_enum(SortOption, raw.get("희망 정렬 기준"), SortOption.RECOMMENDATION)

    req = RecommendRequest(feed_type=feed_type, method=method, sort=sort, top_n=top_n)
    return req



def load_sheet_records() -> Optional[List[Dict[str, Any]]]:
    """
    구글시트에서 records를 로드 시도
    - SPREADSHEET_ID, WORKSHEET_NAME이 있을 때만 시도
    - sheets_reader.py의 함수명/리턴 형태가 달라도 최대한 흡수
    """
    spreadsheet_id = os.getenv("SPREADSHEET_ID", "").strip()
    worksheet_name = os.getenv("WORKSHEET_NAME", "").strip()

    if not spreadsheet_id or not worksheet_name:
        return None

    try:
        from job_finder_rec.data.forms import sheets_reader  # type: ignore
    except Exception as e:
        print(f"⚠️ sheets_reader import 실패 → 더미 유저로 대체합니다. ({e})")
        return None

    fn = "load_recipients_from_sheet"

    try:
        result = getattr(sheets_reader, fn)(spreadsheet_id, worksheet_name)
        # 케이스 1) records만 반환
        if isinstance(result, list):
            return result

        # 케이스 2) (records, sh, ws) 또는 (email_list, records, sh, ws)
        if isinstance(result, tuple):
            # tuple에서 list[dict]로 보이는 걸 찾아 반환
            for item in result:
                if isinstance(item, list) and (len(item) == 0 or isinstance(item[0], dict)):
                    return item

        print("⚠️ 시트 로더 반환값을 해석하지 못해 더미 유저로 대체합니다.")
        return None

    except Exception as e:
        print(f"⚠️ 구글시트 로드 실패 → 더미 유저로 대체합니다. ({e})")
        return None


def dummy_user_records() -> List[Dict[str, Any]]:
    """
    유저 데이터가 없을 때도 파이프라인이 돌아가도록 더미 records 생성
    - user_adapter.normalize_user가 읽는 키들만 최소한으로 맞춰줌
    """
    # 우선 환경변수로 폴더를 지정할 수 있게 하고, 기본은 data/prod/users
    users_folder = os.getenv("USERS_DATA_FOLDER", os.path.join(os.getcwd(), "data", "prod", "users"))

    def _load_from_file(path: str) -> Optional[List[Dict[str, Any]]]:
        try:
            if path.lower().endswith(('.xls', '.xlsx')):
                try:
                    import pandas as pd

                    try:
                        df = pd.read_excel(path, dtype=str)
                    except Exception:
                        # explicit fallback to openpyxl engine if default engine fails
                        try:
                            df = pd.read_excel(path, dtype=str, engine="openpyxl")
                        except Exception as e:
                            print(f"⚠️ pandas.read_excel 실패: {e}")
                            return None

                    df = df.fillna("")
                    return df.to_dict(orient="records")
                except Exception as e:
                    print(f"⚠️ pandas import 또는 엑셀 파싱 실패: {e}")
                    return None

        except Exception:
            return None

    # 찾기: users_folder 내부의 첫 번째 적합한 파일을 사용
    try:
        if os.path.isdir(users_folder):
            for fname in os.listdir(users_folder):
                fpath = os.path.join(users_folder, fname)
                if os.path.isfile(fpath) and fname.lower().endswith((".json", ".csv", ".xls", ".xlsx")):
                    records = _load_from_file(fpath)
                    if records:
                        print(f"✅ 유저 샘플 로드: {fpath} -> {len(records)} records")
                        return records
    except Exception:
        pass

    # fallback: 기존 더미
    return [
        {
            "이메일 주소": "demo1@example.com",
            "희망 직무 1순위 (필수응답)": "Data Scientist",
            "희망 직무 2순위 ": "데이터 분석",
            "희망 직무 3순위 ": "",
            "희망 고용 형태 (복수선택)": "정규직",
            "찾고 계신 공고의 경력 조건을 선택해주세요.": "신입",
            "찾고 계신 공고의 학력 조건을 선택해주세요. (졸업예정자도 선택 가능, 복수선택)": "학사",
            "희망 정렬 기준" : "deadline",
        },
        {
            "이메일 주소": "demo2@example.com",
            "희망 직무 1순위 (필수응답)": "Data Scientist",
            "희망 직무 2순위 ": "",
            "희망 직무 3순위 ": "",
            "희망 고용 형태 (복수선택)": "",
            "찾고 계신 공고의 경력 조건을 선택해주세요.": "신입",
            "찾고 계신 공고의 학력 조건을 선택해주세요. (졸업예정자도 선택 가능, 복수선택)": "",
            "희망 정렬 기준" : "recommend",
        },
    ]
