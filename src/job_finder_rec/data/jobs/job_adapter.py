from typing import Any, Dict, List
from job_finder_rec.recommender.types import JobPosting


def adapt_jobs(raw_jobs: List[Dict[str, Any]]) -> List[JobPosting]:
    return [JobPosting.from_dict(d, fallback_id=f"job_{i+1}") for i, d in enumerate(raw_jobs)]
