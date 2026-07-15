import hashlib
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse


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
        normalized = self._normalized_url()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def _normalized_url(self) -> str:
        parsed = urlparse(self.url)
        qs = parse_qs(parsed.query)
        # Indeed agrega un parámetro de tracking ("bb") que cambia en cada
        # visita a la misma vacante, aunque el "jk" (job key) sea el mismo.
        # Usamos el jk como identificador real y descartamos el resto de la
        # query string en general, que suele ser tracking (utm_*, etc.).
        if "jk" in qs:
            return f"{parsed.netloc}/jk={qs['jk'][0]}"
        return f"{parsed.netloc}{parsed.path}"
