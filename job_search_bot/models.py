import hashlib
from dataclasses import dataclass
from typing import Optional


@dataclass
class JobPosting:
    source: str
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    salary: Optional[str] = None
    posted_date: Optional[str] = None

    @property
    def uid(self) -> str:
        return hashlib.sha256(self.url.encode("utf-8")).hexdigest()[:16]
