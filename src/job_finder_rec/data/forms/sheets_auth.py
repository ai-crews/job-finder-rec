from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import gspread
import pickle
import os

# Google Sheets + Drive API 스코프
SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def authenticate_sheets_oauth():
    """Google Sheets OAuth 인증 (Gmail과 동일한 credentials.json 사용)"""
    creds = None
    token_file = "sheets_token.pickle"

    print("🔐 Google Sheets OAuth 인증 중...")

    # 기존 토큰이 있으면 로드
    if os.path.exists(token_file):
        try:
            with open(token_file, "rb") as token:
                creds = pickle.load(token)
            print("📁 기존 Sheets 토큰 발견")
        except Exception as e:
            print(f"⚠️ 기존 토큰 로드 실패: {e}")
            creds = None

    # 유효한 자격 증명이 없으면 로그인 플로우 실행
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Sheets 토큰 갱신 중...")
            try:
                creds.refresh(Request())
                print("✅ Sheets 토큰 갱신 성공")
            except Exception as e:
                print(f"❌ 토큰 갱신 실패: {e}")
                creds = None

        if not creds:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "credentials.json 파일이 필요합니다.\n"
                    "Gmail API와 동일한 OAuth 클라이언트를 사용합니다."
                )

            print("🌐 브라우저에서 Google Sheets 권한 승인...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SHEETS_SCOPES
            )
            creds = flow.run_local_server(
                port=0, prompt="select_account", access_type="offline"
            )
            print("✅ Google Sheets 권한 승인 완료")

        # 토큰 저장
        try:
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)
            print(f"✅ Sheets 토큰이 {token_file}에 저장되었습니다")
        except Exception as e:
            print(f"⚠️ 토큰 저장 실패: {e}")

    return gspread.authorize(creds)
