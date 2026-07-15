from typing import List

from .freshness import days_ago
from .models import JobPosting


def matches(job: JobPosting, criteria: dict) -> bool:
    text = f"{job.title} {job.description}".lower()

    keywords = [k.lower() for k in criteria.get("keywords", [])]
    if keywords and not any(k in text for k in keywords):
        return False

    exclude = [k.lower() for k in criteria.get("exclude_keywords", [])]
    if any(k in text for k in exclude):
        return False

    locations = [l.lower() for l in criteria.get("locations", [])]
    loc_text = job.location.lower()
    is_remote = "remot" in loc_text
    if criteria.get("remote_only", False):
        if not is_remote:
            return False
    elif locations and not is_remote and not any(l in loc_text for l in locations):
        return False

    max_days_old = criteria.get("max_days_old")
    if max_days_old is not None:
        age = days_ago(job.posted_date) if job.posted_date else None
        # Si no pudimos determinar la antigüedad, la dejamos pasar (mejor no
        # perder una vacante real por un formato de fecha que no reconocimos)
        # en vez de descartarla a ciegas.
        if age is not None and age > max_days_old:
            return False

    return True


def filter_jobs(jobs: List[JobPosting], criteria: dict) -> List[JobPosting]:
    return [j for j in jobs if matches(j, criteria)]
