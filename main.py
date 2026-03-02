from __future__ import annotations

import os
import sys
import json
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
from job_finder_rec.recommender.utils import build_requests_for_user, dummy_user_records



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

    # ===== 2) 유저 로드 (시트 → 실패시 더미) =====
    records = load_user_records_from_sheet()
    if records is None:
        records = dummy_user_records()
        print(f"✅ 더미 유저 records 사용: {len(records)}명")
    else:
        print(f"✅ 구글시트 유저 records 로드: {len(records)}명")

    users = normalize_users(records)
    print(f"✅ 유저 정규화 완료: {len(users)}명")

    # ===== 4) 유저별 요청 생성 및 실행 + 결과 수집 =====
    all_results = []
    
    for i, u in enumerate(users):
        req = build_requests_for_user(u)
        personalized_recs, explore_recs = recommend(u, jobs, req)

        print("\n==============================")
        print(f"👤USER {i+1} : {u.email} | sort={req.sort.value} | target_job={u.top3_position}")
        print(f"[personalized] {len(personalized_recs)}개 | [explore] {len(explore_recs)}개")

        def _build_rec_list(recs, start_rank=1):
            result = []
            for rank, item in enumerate(recs, start_rank):
                j = item.job
                priority_label = f"P{item.job_priority_rank}" if item.job_priority_rank else "P-"
                print(f"{rank:02d}. [{priority_label}] [{j.company_name}] {j.job_title} | {j.processed_position_name}")
                if j.deadline_date:
                    d = j.deadline_date.strftime("%Y-%m-%d")
                    t = j.deadline_time.strftime("%H:%M") if j.deadline_time else ""
                    print(f"    - deadline: {d} {t}".strip())
                deadline_str = None
                if j.deadline_date:
                    d = j.deadline_date.strftime("%Y-%m-%d")
                    t = j.deadline_time.strftime("%H:%M") if j.deadline_time else ""
                    deadline_str = f"{d} {t}".strip()
                result.append({
                    "rank": rank,
                    "job_priority_rank": item.job_priority_rank,
                    "company_name": j.company_name,
                    "job_title": j.job_title,
                    "position_name": j.processed_position_name,
                    "employment_type": j.processed_employment_type,
                    "education_level": j.processed_education_level,
                    "company_size": j.company_size,
                    "industry": j.industry,
                    "deadline": deadline_str,
                })
            return result

        print("\n--- [PERSONALIZED] ---")
        p_recs = _build_rec_list(personalized_recs, start_rank=1)
        print("\n--- [EXPLORE] ---")
        e_recs = _build_rec_list(explore_recs, start_rank=1)

        all_results.append({
            "email": u.email,
            "sort_method": req.sort.value,
            # 유저 필터 조건
            "filter_criteria": {
                "target_jobs": u.top3_position,
                "target_employment_types": u.employment_type,
                "current_education": u.education_level,
                "preferred_company_sizes": u.company_size,
                "interested_industries": u.company_industry,
                "has_english_score": u.has_language_score,
            },
            "personalized_total": len(p_recs),
            "personalized_recommendations": p_recs,
            "explore_total": len(e_recs),
            "explore_recommendations": e_recs,
        })

    # ===== 5) 결과 내보내기 =====
    _export_recommendations(all_results)
    print("\n✅ main pipeline done.")


def _export_recommendations(results: list) -> None:
    """추천 결과를 JSON 파일로 내보내기"""
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"recommendations_{timestamp}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 추천 결과 내보내기: {output_file}")


if __name__ == "__main__":
    main()
