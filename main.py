from __future__ import annotations

import os
import sys


def _ensure_src_on_path() -> None:
    """
    루트에서 python main.py로 실행할 때 src/ 경로가 import에 안 잡히는 경우가 많아서
    방어적으로 sys.path에 추가.
    """
    root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


_ensure_src_on_path()


# ===== imports (after sys.path) =====
from job_finder_rec.data.jobs.job_loader import load_all_job_data
from job_finder_rec.data.jobs.job_adapter import adapt_jobs

from job_finder_rec.recommender.engine import recommend
from job_finder_rec.recommender.types import FeedType, PersonalizedMethod

from job_finder_rec.data.forms.user_adapter import normalize_users
from job_finder_rec.recommender.utils import build_requests_for_user, load_sheet_records, dummy_user_records
# 구글시트 로더는 프로젝트에 따라 함수명이 다를 수 있어서 런타임에서 탐색


def main() -> None:
    # ===== 1) 공고 로드 =====
    jobs_folder = os.getenv("JOBS_DATA_FOLDER", "data/prod")
    raw_jobs = load_all_job_data(jobs_folder)
    if not raw_jobs:
        print(f"❌ 공고 데이터가 없습니다. JOBS_DATA_FOLDER={jobs_folder}")
        return

    jobs = adapt_jobs(raw_jobs)
    print(f"✅ 공고 로드 완료: {len(jobs)}개 (from {jobs_folder})")

    # ===== 2) 유저 로드 (시트 → 실패시 더미) =====
    records = load_sheet_records()
    if records is None:
        records = dummy_user_records()
        print(f"✅ 더미 유저 records 사용: {len(records)}명")
    else:
        print(f"✅ 구글시트 유저 records 로드: {len(records)}명")

    users = normalize_users(records)
    print(f"✅ 유저 정규화 완료: {len(users)}명")

    # ===== 3) 고정 추천 설정 =====
    feed_type = FeedType.PERSONALIZED
    method = PersonalizedMethod.FILTER
    top_n = 10

    # ===== 4) 유저별 요청 생성 및 실행 =====
    for i, u in enumerate(users):
        req = build_requests_for_user(u, feed_type, method, top_n)

        recs = recommend(u, jobs, req)

        print("\n==============================")
        print(f"👤USER {i+1} : {u.email} | feed={req.feed_type.value} | method={req.method.value} | sort={req.sort.value} | top_n={req.top_n}")
        print(f"추천 결과: {len(recs)}개")

        for i, item in enumerate(recs[: req.top_n], 1):
            j = item.job
            print(f"{i:02d}. [{j.company_name}] {j.job_title} | {j.processed_position_name}")
            # if j.application_link:
            #     print(f"    - link: {j.application_link}")
            if j.application_deadline_date:
                # deadline(datetime)은 types에 있지만, 출력은 원본 키로도 충분
                t = j.application_deadline_time or ""
                print(f"    - deadline: {j.application_deadline_date} {t}".strip())

    print("\n✅ main pipeline done.")


if __name__ == "__main__":
    main()
