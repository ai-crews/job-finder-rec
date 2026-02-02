import json
import os
from typing import List, Dict


def extract_company_from_filename( filename: str) -> str:
    """
    파일명에서 회사명 추출
    ex)
        대한항공1.json -> 대한항공
        대한항공2.json -> 대한항공
    """
    parts = filename.replace(".json", "").split("_")
    if len(parts) >= 2:
        return parts[0]
    return ""


def load_all_job_data(data_folder: str) -> List[Dict]:
    """
    data_folder 아래의 모든 JSON 파일을 로드하여 공고 리스트로 반환
    """
    job_data: List[Dict] = []
    print(f"데이터 폴더 경로: {data_folder}")

    for root, _, files in os.walk(data_folder):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)
            print(f"JSON 파일 로딩: {file_path}")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    company_name = data.get("company_name", "")
                    print(f"성공: 회사명={company_name}")
                    
                    # company_name 보정: 비어있으면 파일명에서 추출
                    if "company_name" not in data or not data["company_name"]:
                        company_from_filename = (
                            extract_company_from_filename(filename)
                        )
                        if company_from_filename:
                            data["company_name_from_file"] = (
                                company_from_filename
                            )
                            print(f"파일명에서 추출한 회사명: {company_from_filename}")
                    job_data.append(data)
            except Exception as e:
                print(f"파일 로드 실패 {filename}: {e}")
    
    print(f"총 로드된 공고 수: {len(job_data)}")
    return job_data