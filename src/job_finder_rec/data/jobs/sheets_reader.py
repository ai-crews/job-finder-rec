import os
from datetime import datetime

from job_finder_rec.data.sheets_auth import authenticate_sheets_oauth


def load_job_records_from_sheet(spreadsheet_id: str = None, worksheet_name: str = None):
    """
    Google Sheets에서 공고 records를 로드해 List[Dict]로 반환.
    - spreadsheet_id / worksheet_name 미전달 시 환경변수 JOB_SPREADSHEET_ID / JOB_WORKSHEET_NAME 사용
    - 환경변수도 없거나 실패 시 None 반환
    """
    spreadsheet_id = spreadsheet_id or os.getenv("JOB_SPREADSHEET_ID", "").strip()
    worksheet_name = worksheet_name or os.getenv("JOB_WORKSHEET_NAME", "").strip()

    if not spreadsheet_id or not worksheet_name:
        return None

    try:
        gc = authenticate_sheets_oauth()
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_name)
        records = ws.get_all_records()
        print(f"✅ 구글시트 공고 로드 완료: {len(records)}개 (from '{worksheet_name}')")
        return records if records else None
    except Exception as e:
        import traceback
        print(f"❌ Google Sheets 공고 로드 실패: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def write_job_records_to_sheet(
    records: list,
    spreadsheet_id: str = None,
    worksheet_name: str = None,
) -> bool:
    """
    records(List[Dict])를 Google Sheets 워크시트에 누적 적재.
    - job_title 기준으로 이미 시트에 존재하는 공고는 건너뜀
    - 신규 공고만 시트 하단에 append
    - 시트가 비어있으면 헤더 포함하여 초기 작성
    - spreadsheet_id / worksheet_name 미전달 시 환경변수 사용
    """
    spreadsheet_id = spreadsheet_id or os.getenv("ROLLING_RECRUITMENT_SPREADSHEET_ID", "").strip()
    worksheet_name = worksheet_name or os.getenv("ROLLING_RECRUITMENT_WORKSHEET_NAME", "").strip()

    if not spreadsheet_id or not worksheet_name:
        print("⚠️  ROLLING_RECRUITMENT_SPREADSHEET_ID / ROLLING_RECRUITMENT_WORKSHEET_NAME 환경변수가 없어 수시채용 시트 쓰기를 건너뜁니다.")
        return False
    if not records:
        return True

    try:
        gc = authenticate_sheets_oauth()
        sh = gc.open_by_key(spreadsheet_id)
        try:
            ws = sh.worksheet(worksheet_name)
        except Exception:
            ws = sh.add_worksheet(title=worksheet_name, rows=1000, cols=30)

        # 기존 시트에서 post_id 집합 수집 (빈 값 제외)
        existing_records = ws.get_all_records()
        existing_ids = {str(r.get("post_id", "")).strip() for r in existing_records if str(r.get("post_id", "")).strip()}

        # 신규 공고만 필터링 (post_id 기준 중복 제외)
        new_records = [
            r for r in records
            if str(r.get("post_id", "")).strip() not in existing_ids
        ]

        if not new_records:
            print(f"ℹ️  수시채용 공고 {len(records)}개 모두 이미 시트에 존재 — 추가 없음")
            return True

        load_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        headers = ["load_date"] + list(records[0].keys())

        if not existing_records:
            # 시트가 비어있으면 헤더 포함 전체 작성
            rows = [headers] + [[load_date_str] + [str(r.get(h, "")) for h in headers[1:]] for r in new_records]
            ws.update(rows, value_input_option="RAW")
        else:
            # 기존 데이터가 있으면 하단에만 append
            rows = [[load_date_str] + [str(r.get(h, "")) for h in headers[1:]] for r in new_records]
            ws.append_rows(rows, value_input_option="RAW")

        print(f"✅ 수시채용 신규 공고 {len(new_records)}개 적재 완료 (기존 {len(existing_ids)}개 중복 제외)")
        return True
    except Exception as e:
        import traceback
        print(f"❌ 수시채용 시트 쓰기 실패: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False
