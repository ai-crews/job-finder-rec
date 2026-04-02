import os
from datetime import datetime

from job_finder_rec.data.sheets_auth import authenticate_sheets_oauth


def load_user_records_from_sheet(spreadsheet_id: str = None, worksheet_name: str = None):
    """
    Google Sheets에서 유저 설문 records를 로드해 List[Dict]로 반환
    - spreadsheet_id / worksheet_name 미전달 시 환경변수 USER_SPREADSHEET_ID / USER_WORKSHEET_NAME 사용
    - 환경변수도 없거나 실패 시 None 반환
    """
    spreadsheet_id = spreadsheet_id or os.getenv("USER_SPREADSHEET_ID", "").strip()
    worksheet_name = worksheet_name or os.getenv("USER_WORKSHEET_NAME", "").strip()

    if not spreadsheet_id or not worksheet_name:
        return None

    try:
        gc = authenticate_sheets_oauth()
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(worksheet_name)
        records = ws.get_all_records()
        print(f"✅ 구글시트 유저 로드 완료: {len(records)}명 (from '{worksheet_name}')")
        return records if records else None
    except Exception as e:
        print(f"❌ Google Sheets 유저 로드 실패: {e}")
        return None


def load_recipients_from_sheet(spreadsheet_id, worksheet_name):
    """OAuth를 사용한 Google Sheets 데이터 로드"""
    try:
        gc = authenticate_sheets_oauth()
        print("✅ Google Sheets 인증 성공")

        # 스프레드시트 열기
        try:
            sh = gc.open_by_key(spreadsheet_id)
            print(f"📊 스프레드시트 열기 성공: {sh.title}")
        except Exception as e:
            print(f"❌ 스프레드시트 열기 실패: {e}")
            print(f"SPREADSHEET_ID 확인 필요: {spreadsheet_id}")
            return [], None, None

        # 워크시트 선택
        try:
            ws = sh.worksheet(worksheet_name)
            print(f"📄 워크시트 선택 성공: {worksheet_name}")
        except Exception as e:
            print(f"❌ 워크시트 선택 실패: {e}")
            print(f"사용 가능한 워크시트: {[ws.title for ws in sh.worksheets()]}")
            return [], sh, None

        # 데이터 가져오기
        records = ws.get_all_records()
        print(f"총 행 수: {len(records)}")

        if not records:
            print("시트에 데이터가 없습니다.")
            return [], sh, ws

        # 이메일 컬럼 찾기
        email_col = "이메일 주소"
        print(f"✅ '{email_col}' 컬럼에서 이메일 추출 중...")

        # 이메일 주소 추출 및 유효성 검사
        email_list = []
        for i, record in enumerate(records, 2):
            email = record.get(email_col, "").strip()
            if email and "@" in email and "." in email:
                print(f"행 {i}: {email}")
                email_list.append(email)
            elif email:
                print(f"행 {i}: {email} (유효하지 않은 이메일 형식)")

        return email_list, records, sh, ws

    except Exception as e:
        print(f"❌ Google Sheets 로드 실패: {e}")
        return [], None, None

