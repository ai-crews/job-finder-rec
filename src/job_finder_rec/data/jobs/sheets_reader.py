import os

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
