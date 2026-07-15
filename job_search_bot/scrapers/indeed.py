import logging
from typing import List, Optional
from urllib.parse import urlencode

from ..models import JobPosting
from .base import BaseScraper

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_DOMAINS = [{"domain": "ar.indeed.com", "locations": ["Argentina", "Buenos Aires", "Remoto"]}]


class IndeedScraper(BaseScraper):
    """
    Usa Playwright (navegador real headless) en vez de requests simples, porque
    Indeed devuelve 403 a la mayoría de los pedidos hechos con librerías HTTP.

    Cada dominio (ej. ar.indeed.com, indeed.es) puede tener su propia lista de
    ubicaciones — así indeed.es solo se busca en "Remoto" en vez de repetir
    ubicaciones argentinas que no tienen sentido ahí.
    """

    name = "indeed"

    def __init__(self, domains: Optional[List[dict]] = None, delay: float = 2.0):
        self.domains = domains or DEFAULT_DOMAINS
        self.delay = delay

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
            page = browser.new_page(user_agent=USER_AGENT)
            try:
                for entry in self.domains:
                    domain = entry["domain"]
                    for location in entry.get("locations", ["Remoto"]):
                        jobs.extend(self._search_one(page, domain, keyword, location, max_results))
            finally:
                browser.close()

        return jobs

    def _search_one(self, page, domain: str, keyword: str, location: str, max_results: int) -> List[JobPosting]:
        params = {"q": keyword, "l": location}
        url = f"https://{domain}/jobs?{urlencode(params)}"

        jobs: List[JobPosting] = []
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(int(self.delay * 1000))

        if page.query_selector("#challenge-form") or "verify you are a human" in page.content().lower():
            logger.warning(
                "Indeed (%s): mostró una pantalla de verificación/captcha para %r en %r. "
                "Esperá un rato antes de volver a correr el bot.",
                domain,
                keyword,
                location,
            )
            return []

        cards = page.query_selector_all("div.job_seen_beacon") or page.query_selector_all("td.resultContent")
        if not cards:
            logger.warning(
                "Indeed (%s): no se encontraron resultados para %r en %r. Es posible que Indeed "
                "haya cambiado el HTML, o que ese dominio no tenga resultados para esa ubicación.",
                domain,
                keyword,
                location,
            )

        for card in cards[:max_results]:
            title_el = card.query_selector("h2.jobTitle span") or card.query_selector("h2.jobTitle a")
            company_el = card.query_selector('span[data-testid="company-name"]') or card.query_selector(
                ".companyName"
            )
            location_el = card.query_selector('div[data-testid="text-location"]') or card.query_selector(
                ".companyLocation"
            )
            link_el = card.query_selector("h2.jobTitle a")
            salary_el = card.query_selector('div[data-testid="attribute_snippet_testid"]')

            if not (title_el and link_el):
                continue

            href = link_el.get_attribute("href") or ""
            full_url = href if href.startswith("http") else f"https://{domain}{href}"

            jobs.append(
                JobPosting(
                    source=f"{self.name} ({domain})",
                    title=title_el.inner_text().strip(),
                    company=company_el.inner_text().strip() if company_el else "N/D",
                    location=location_el.inner_text().strip() if location_el else location,
                    url=full_url,
                    salary=salary_el.inner_text().strip() if salary_el else None,
                )
            )

        return jobs
