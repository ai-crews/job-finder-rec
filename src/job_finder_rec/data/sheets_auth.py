import os
import gspread
from google.oauth2.service_account import Credentials

SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def authenticate_sheets_oauth():
    """서비스 계정(credentials.json)으로 Google Sheets 인증"""
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"서비스 계정 키 파일을 찾을 수 없습니다: {credentials_path}\n"
            "GOOGLE_CREDENTIALS_PATH 환경변수로 경로를 지정하거나\n"
            "루트에 credentials.json을 두세요."
        )

    creds = Credentials.from_service_account_file(credentials_path, scopes=SHEETS_SCOPES)
    return gspread.authorize(creds)
