import logging
import time
from typing import List
from urllib.parse import urlencode

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
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}


class IndeedScraper(BaseScraper):
    """
    Scraping HTML directo (Indeed no ofrece API pública para búsqueda de empleo).
    Los selectores de abajo son los usados por Indeed en los últimos años, pero
    pueden cambiar sin aviso. Si `search` deja de devolver resultados, corré con
    logging en DEBUG y revisá el HTML crudo para actualizar los selectores.
    """

    name = "indeed"

    def __init__(self, domain: str = "ar.indeed.com", delay: float = 2.0):
        self.domain = domain
        self.delay = delay

    def search(self, keyword: str, location: str, max_results: int = 25) -> List[JobPosting]:
        params = {"q": keyword, "l": location}
        url = f"https://{self.domain}/jobs?{urlencode(params)}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Indeed: falló la request para %r (%s)", keyword, exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.job_seen_beacon") or soup.select("td.resultContent")
        if not cards:
            logger.warning(
                "Indeed: no se encontraron resultados para %r. Es posible que Indeed "
                "haya cambiado el HTML o esté mostrando un captcha: revisá "
                "job_search_bot/scrapers/indeed.py y actualizá los selectores.",
                keyword,
            )
            return []

        jobs = []
        for card in cards[:max_results]:
            title_el = card.select_one("h2.jobTitle span") or card.select_one("h2.jobTitle a")
            company_el = card.select_one('span[data-testid="company-name"]') or card.select_one(".companyName")
            location_el = card.select_one('div[data-testid="text-location"]') or card.select_one(".companyLocation")
            link_el = card.select_one("h2.jobTitle a")
            salary_el = card.select_one('div[data-testid="attribute_snippet_testid"]')

            if not (title_el and link_el):
                continue

            href = link_el.get("href", "")
            full_url = href if href.startswith("http") else f"https://{self.domain}{href}"

            jobs.append(
                JobPosting(
                    source=self.name,
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "N/D",
                    location=location_el.get_text(strip=True) if location_el else location,
                    url=full_url,
                    salary=salary_el.get_text(strip=True) if salary_el else None,
                )
            )

        time.sleep(self.delay)
        return jobs
