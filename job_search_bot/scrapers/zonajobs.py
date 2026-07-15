import logging
from typing import List, Optional

from ..freshness import extract_date_text
from ..models import JobPosting
from .base import BaseScraper

logger = logging.getLogger(__name__)

DEFAULT_LOCATIONS = ["Argentina"]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class ZonaJobsScraper(BaseScraper):
    """
    ZonaJobs/Bumeran están detrás de Cloudflare, que bloquea navegadores headless
    directamente ("Sorry, you have been blocked") — confirmado revisando el HTML
    que devolvía. No es un problema de selectores, es un bloqueo activo.

    Usamos playwright-stealth para que el navegador se parezca más a uno real
    (mismo espíritu que el User-Agent, pero más completo). Si Cloudflare sigue
    bloqueando con esto, no tiene sentido insistir con técnicas más agresivas:
    mejor sacar este sitio de la búsqueda automática.
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

        try:
            from playwright_stealth import stealth_sync
        except ImportError:
            stealth_sync = None
            logger.warning(
                "Falta 'playwright-stealth' (pip install playwright-stealth). "
                "Sin esto es más probable que Cloudflare bloquee la request."
            )

        jobs: List[JobPosting] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=USER_AGENT,
                locale="es-AR",
                viewport={"width": 1366, "height": 900},
            )
            if stealth_sync:
                stealth_sync(page)
            try:
                for location in self.locations:
                    jobs.extend(self._search_one(page, keyword, location, max_results))
            finally:
                browser.close()

        return jobs

    def _extract_title(self, card) -> str:
        # El link de la tarjeta suele empezar con "Publicado hace X días" /
        # "Actualizado hace X días" antes del título real, así que lo salteamos.
        heading = card.query_selector("h2") or card.query_selector("h3")
        if heading:
            text = heading.inner_text().strip()
            if text:
                return text

        attr_title = card.get_attribute("title")
        if attr_title:
            return attr_title.strip()

        lines = [line.strip() for line in (card.inner_text() or "").split("\n") if line.strip()]
        lines = [
            line
            for line in lines
            if not line.lower().startswith("publicado")
            and not line.lower().startswith("actualizado")
        ]
        return lines[0] if lines else "N/D"

    def _search_one(self, page, keyword: str, location: str, max_results: int) -> List[JobPosting]:
        slug = keyword.strip().lower().replace(" ", "-")
        url = f"{self.base_url}/empleos-busqueda-{slug}.html"

        jobs: List[JobPosting] = []
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(int(self.delay * 1000))

        if "Attention Required" in page.title() or page.query_selector("#cf-wrapper"):
            logger.warning(
                "ZonaJobs: Cloudflare bloqueó la request para %r (mismo bloqueo que "
                "viste en el navegador). No hay selector que arregle esto — es un "
                "bloqueo activo del sitio, no un cambio de HTML.",
                keyword,
            )
            return []

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
            card_text = card.inner_text() or ""
            title = self._extract_title(card)
            posted_date = extract_date_text(card_text)
            full_url = href if href.startswith("http") else f"{self.base_url}{href}"
            jobs.append(
                JobPosting(
                    source=self.name,
                    title=title.strip(),
                    company="N/D",
                    location=location,
                    url=full_url,
                    posted_date=posted_date,
                )
            )

        return jobs
