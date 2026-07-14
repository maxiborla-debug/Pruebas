from abc import ABC, abstractmethod
from typing import List

from ..models import JobPosting


class BaseScraper(ABC):
    name: str = "base"

    @abstractmethod
    def search(self, keyword: str, location: str, max_results: int = 25) -> List[JobPosting]:
        ...
