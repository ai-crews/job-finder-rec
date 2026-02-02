import json
import os
from typing import List, Dict, Union


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
