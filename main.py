from __future__ import annotations

import os
import sys
import csv
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()


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
from job_finder_rec.data.jobs.job_adapter import normalize_jobs
from job_finder_rec.data.jobs.sheets_reader import load_job_records_from_sheet, write_job_records_to_sheet
from job_finder_rec.data.forms.sheets_reader import load_user_records_from_sheet
from job_finder_rec.recommender.engine import recommend
from job_finder_rec.data.forms.user_adapter import normalize_users
from job_finder_rec.recommender.utils import build_requests_for_user



def main() -> None:
    # ===== 1) 공고 로드 (구글 시트) =====
    raw_jobs = load_job_records_from_sheet()
    if not raw_jobs:
        print("❌ 공고 데이터가 없습니다. JOB_SPREADSHEET_ID / JOB_WORKSHEET_NAME 환경변수를 확인하세요.")
        return

    # 수시채용(마감일 9999-12-31) 분리 → 별도 시트로 기록 후 추천 대상에서 제외
    _ROLLING_DATE_STR = "9999-12-31"
    raw_rolling = [r for r in raw_jobs if str(r.get("deadline_date", "")).strip() == _ROLLING_DATE_STR]
    raw_regular = [r for r in raw_jobs if str(r.get("deadline_date", "")).strip() != _ROLLING_DATE_STR]
    print(f"ℹ️  수시채용 분리: rolling={len(raw_rolling)}개, regular={len(raw_regular)}개")
    if raw_rolling and raw_jobs:
        sample_keys = list(raw_jobs[0].keys())
        print(f"ℹ️  raw_jobs 샘플 키: {sample_keys[:8]}")

    if raw_rolling:
        print(f"ℹ️  수시채용 공고 {len(raw_rolling)}개 분리 → 별도 시트 기록 중...")
        write_job_records_to_sheet(raw_rolling)

    jobs = normalize_jobs(raw_regular)
    print(f"✅ 공고 정규화 완료: {len(jobs)}개 (수시채용 {len(raw_rolling)}개 제외)")

    # ===== 2) 유저 로드 =====
    records = load_user_records_from_sheet()
    print(f"✅ 구글시트 유저 records 로드: {len(records)}명")

    users = normalize_users(records)
    print(f"✅ 유저 정규화 완료: {len(users)}명")

    # ===== 3) 유저별 요청 생성 및 실행 + 결과 수집 =====
    flat_rows: list = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for i, u in enumerate(users):
        req = build_requests_for_user(u)
        personalized_recs, explore_recs = recommend(u, jobs, req)

        total_count = len(personalized_recs) + len(explore_recs)

        print("\n==============================")
        print(f"👤USER {i+1} : {u.email} | sort={req.sort.value} | target_job={u.top3_position}")
        print(f"[personalized] {len(personalized_recs)}개 | [explore] {len(explore_recs)}개")

        def _make_rows(recs, layer_label, _u=u, _req=req, _total=total_count):
            rows = []
            for rank, item in enumerate(recs, 1):
                j = item.job
                priority_label = f"P{item.job_priority_rank}" if item.job_priority_rank else "P-"
                print(f"{rank:02d}. [{priority_label}] [{j.company_name}] {j.job_title} | {j.processed_position_name}")
                rows.append({
                    "추천일자": today_str,
                    "닉네임": _u.name,
                    "이메일": _u.email,
                    "추천 기업명 (company_name)": j.company_name,
                    "추천 공고명 (job_title)": j.job_title,
                    "레이어 구분": layer_label,
                    "정렬 구분": _req.sort.value,
                    "rank": rank,
                    "유저 당 총 추천개수": _total,
                    "채용공고URL (job_url)": j.job_url or "",
                    "마감기한 일자 (deadline_date)": j.deadline_date.strftime("%Y-%m-%d") if j.deadline_date else "",
                    "마감기한 시간 (deadline_time)": j.deadline_time.strftime("%H:%M") if j.deadline_time else "",
                    "job_company_size": j.company_size,
                    "job_company_industry": j.industry,
                    "job_processed_position_name": str(j.processed_position_name),
                    "job_processed_education_level": str(j.processed_education_level),
                    "job_processed_experience_level": j.processed_experience_level,
                    "job_processed_employment_type": str(j.processed_employment_type),
                    "job_processed_language_required": j.processed_language_required,
                    "user_company_size": str(_u.company_size),
                    "user_company_industry": str(_u.company_industry),
                    "user_top3_position": str(_u.top3_position),
                    "user_education_level": str(_u.education_level),
                    "user_employment_type": str(_u.employment_type),
                    "user_has_language_score": _u.has_language_score or "",
                })
            return rows

        print("\n--- [PERSONALIZED] ---")
        flat_rows.extend(_make_rows(personalized_recs, "personalized"))
        print("\n--- [EXPLORE] ---")
        flat_rows.extend(_make_rows(explore_recs, "explore"))

    # ===== 4) 결과 내보내기 =====
    _export_recommendations(flat_rows)
    print("\n✅ main pipeline done.")


def _export_recommendations(rows: list) -> None:
    """추천 결과를 CSV 파일로 내보내기"""
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"recommendations_{timestamp}.csv")

    columns = [
        "추천일자", "닉네임", "이메일",
        "추천 기업명 (company_name)", "추천 공고명 (job_title)",
        "레이어 구분", "정렬 구분", "rank", "유저 당 총 추천개수",
        "채용공고URL (job_url)",
        "마감기한 일자 (deadline_date)", "마감기한 시간 (deadline_time)",
        "job_company_size", "job_company_industry",
        "job_processed_position_name", "job_processed_education_level",
        "job_processed_experience_level", "job_processed_employment_type",
        "job_processed_language_required",
        "user_company_size", "user_company_industry",
        "user_top3_position", "user_education_level",
        "user_employment_type", "user_has_language_score",
    ]

    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ 추천 결과 내보내기: {output_file}")


if __name__ == "__main__":
    main()
