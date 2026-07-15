import logging
from typing import List, Optional

from ..models import JobPosting
from .base import BaseScraper

logger = logging.getLogger(__name__)

DEFAULT_LOCATIONS = ["Argentina"]


class ZonaJobsScraper(BaseScraper):
    """
    ZonaJobs / Bumeran (grupo Navent) renderizan los resultados con JavaScript
    (React), así que requests + BeautifulSoup no alcanza: usamos Playwright para
    cargar la página como un navegador real.

    La URL de búsqueda se confirmó que carga bien; lo que falta ajustar son los
    selectores CSS de cada tarjeta de aviso (ver README para cómo conseguirlos
    con "Inspeccionar" en el navegador).
    """

    name = "zonajobs"

    def __init__(
        self,
        base_url: str = "https://www.zonajobs.com.ar",
        delay: float = 3.0,
        locations: Optional[List[str]] = None,
    ):
        self.base_url = base_url
        self.delay = delay
        self.locations = locations or DEFAULT_LOCATIONS

    def search(self, keyword: str, max_results: int = 25) -> List[JobPosting]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error(
                "Falta 'playwright'. Instalá con: pip install playwright && playwright install chromium"
            )
            return []

        jobs: List[JobPosting] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                for location in self.locations:
                    jobs.extend(self._search_one(page, keyword, location, max_results))
            finally:
                browser.close()

        return jobs

    def _search_one(self, page, keyword: str, location: str, max_results: int) -> List[JobPosting]:
        slug = keyword.strip().lower().replace(" ", "-")
        url = f"{self.base_url}/empleos-busqueda-{slug}.html"

        jobs: List[JobPosting] = []
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(int(self.delay * 1000))

        cards = page.query_selector_all("a[data-qa='JobListing_Item']")
        if not cards:
            cards = page.query_selector_all("a[href*='/empleos/']")

        if not cards:
            logger.warning(
                "ZonaJobs: no se encontraron resultados para %r. El sitio "
                "probablemente cambió su HTML: revisá "
                "job_search_bot/scrapers/zonajobs.py y actualizá el selector.",
                keyword,
            )

        seen_urls = set()
        for card in cards[:max_results]:
            href = card.get_attribute("href") or ""
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)
            title = card.get_attribute("title") or (card.inner_text() or "").split("\n")[0]
            full_url = href if href.startswith("http") else f"{self.base_url}{href}"
            jobs.append(
                JobPosting(
                    source=self.name,
                    title=title.strip(),
                    company="N/D",
                    location=location,
                    url=full_url,
                )
            )

        return jobs
