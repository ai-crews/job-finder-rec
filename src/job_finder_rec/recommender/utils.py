from datetime import datetime
from typing import List, Optional


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
