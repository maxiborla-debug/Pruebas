import re
from datetime import date, datetime
from typing import Optional

_ES_PATTERN = re.compile(
    r"hace\s+(?:m[aá]s de\s+)?(\d+)\+?\s*(minutos?|horas?|d[ií]as?|semanas?|meses?)",
    re.IGNORECASE,
)
_EN_PATTERN = re.compile(r"(\d+)\+?\s*(minute|hour|day|week|month)s?\s+ago", re.IGNORECASE)

_UNIT_DAYS = {
    "minuto": 0, "minutos": 0, "minute": 0,
    "hora": 0, "horas": 0, "hour": 0,
    "dia": 1, "día": 1, "dias": 1, "días": 1, "day": 1,
    "semana": 7, "semanas": 7, "week": 7,
    "mes": 30, "meses": 30, "month": 30,
}


def extract_date_text(raw_text: str) -> Optional[str]:
    """Busca una frase de fecha relativa (ej. 'hace 9 días') dentro de un bloque de texto."""
    if not raw_text:
        return None
    for pattern in (_ES_PATTERN, _EN_PATTERN):
        match = pattern.search(raw_text)
        if match:
            return match.group(0).strip()
    return None


def days_ago(raw_text: str) -> Optional[int]:
    """
    Convierte una fecha (relativa tipo 'hace 9 días', o ISO 'YYYY-MM-DD') a
    cantidad de días transcurridos. Devuelve None si no se pudo interpretar.
    """
    if not raw_text:
        return None

    try:
        posted = datetime.strptime(raw_text[:10], "%Y-%m-%d").date()
        return (date.today() - posted).days
    except ValueError:
        pass

    for pattern in (_ES_PATTERN, _EN_PATTERN):
        match = pattern.search(raw_text)
        if match:
            number = int(match.group(1))
            unit = match.group(2).lower()
            per_unit_days = _UNIT_DAYS.get(unit)
            if per_unit_days is None:
                return None
            return number * per_unit_days

    return None
