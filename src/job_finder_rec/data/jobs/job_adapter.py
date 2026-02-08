from typing import Any, Dict, List
from job_finder_rec.recommender.types import JobPosting


def adapt_jobs(raw_jobs: List[Dict[str, Any]]) -> List[JobPosting]:
    return [JobPosting.from_dict(d) for i, d in enumerate(raw_jobs)]
