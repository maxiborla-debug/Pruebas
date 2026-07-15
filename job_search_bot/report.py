from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .freshness import days_ago
from .models import JobPosting


def _sort_key(job: JobPosting):
    age = days_ago(job.posted_date) if job.posted_date else None
    # Los de antigüedad conocida van primero (los más nuevos arriba de todo);
    # los de antigüedad desconocida quedan al final, no se descartan.
    return (age is None, age if age is not None else 0)


def write_report(matched: List[JobPosting], cover_letters: Dict[str, str], output_dir: str) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = out_dir / f"{ts}.md"

    matched = sorted(matched, key=_sort_key)

    lines = [f"# Vacantes nuevas — {datetime.now().strftime('%d/%m/%Y %H:%M')} (ordenadas por más recientes)", ""]
    if not matched:
        lines.append("No se encontraron vacantes nuevas que matcheen tus criterios.")

    for job in matched:
        lines.append(f"## {job.title} — {job.company}")
        lines.append(f"- **Fuente:** {job.source}")
        lines.append(f"- **Ubicación:** {job.location}")
        if job.posted_date:
            age = days_ago(job.posted_date)
            age_txt = f" (~{age} días)" if age is not None else ""
            lines.append(f"- **Publicado:** {job.posted_date}{age_txt}")
        else:
            lines.append("- **Publicado:** fecha no disponible en el sitio")
        if job.salary:
            lines.append(f"- **Salario:** {job.salary}")
        lines.append(f"- **Link:** {job.url}")

        letter = cover_letters.get(job.uid)
        if letter:
            lines.append("")
            lines.append("**Borrador de carta de presentación:**")
            lines.append("")
            lines.append("> " + letter.replace("\n", "\n> "))
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
