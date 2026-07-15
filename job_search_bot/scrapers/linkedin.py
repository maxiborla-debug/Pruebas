import logging
import time
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from ..models import JobPosting
from .base import BaseScraper

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

DEFAULT_LOCATIONS = ["Argentina", "Buenos Aires, Argentina", "Remote"]


class LinkedInScraper(BaseScraper):
    """
    Usa el endpoint público ("guest") de búsqueda de empleos de LinkedIn, que NO
    requiere login. Esto evita el riesgo de que te baneen la cuenta personal
    (nunca uses tus credenciales acá), pero sigue siendo scraping no oficial:
    LinkedIn puede bloquear tu IP si hacés muchas requests seguidas. Respetá el
    delay y no lo corras con mucha frecuencia (una vez por día alcanza).

    Las ubicaciones "regionales remotas" (ej. "Spain Remote", "Europe Remote")
    son un mejor esfuerzo: el endpoint público interpreta el texto de forma
    aproximada, no es una búsqueda geográfica estricta. Si alguna de estas
    devuelve poco o nada relevante, avisame y la ajustamos.
    """

    name = "linkedin"

    def __init__(self, locations: Optional[List[str]] = None, delay: float = 3.0):
        self.locations = locations or DEFAULT_LOCATIONS
        self.delay = delay

    def search(self, keyword: str, max_results: int = 25) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        for location in self.locations:
            jobs.extend(self._search_one(keyword, location, max_results))
        return jobs

    def _search_one(self, keyword: str, location: str, max_results: int) -> List[JobPosting]:
        params = {"keywords": keyword, "location": location, "start": 0}
        try:
            resp = requests.get(SEARCH_URL, headers=HEADERS, params=params, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("LinkedIn: falló la request para %r en %r (%s)", keyword, location, exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("li")
        if not cards:
            logger.warning(
                "LinkedIn: no se encontraron resultados para %r en %r. El endpoint público "
                "puede haber cambiado, estar bloqueando la IP, o esa ubicación no resolvió a nada.",
                keyword,
                location,
            )
            time.sleep(self.delay)
            return []

        jobs = []
        for card in cards[:max_results]:
            title_el = card.select_one("h3.base-search-card__title")
            company_el = card.select_one("h4.base-search-card__subtitle")
            location_el = card.select_one("span.job-search-card__location")
            link_el = card.select_one("a.base-card__full-link")

            if not (title_el and link_el):
                continue

            jobs.append(
                JobPosting(
                    source=self.name,
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "N/D",
                    location=location_el.get_text(strip=True) if location_el else location,
                    url=link_el.get("href", "").split("?")[0],
                )
            )

        time.sleep(self.delay)
        return jobs
