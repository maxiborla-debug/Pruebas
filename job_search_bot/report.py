from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .models import JobPosting


def write_report(matched: List[JobPosting], cover_letters: Dict[str, str], output_dir: str) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = out_dir / f"{ts}.md"

    lines = [f"# Vacantes nuevas — {datetime.now().strftime('%d/%m/%Y %H:%M')}", ""]
    if not matched:
        lines.append("No se encontraron vacantes nuevas que matcheen tus criterios.")

    for job in matched:
        lines.append(f"## {job.title} — {job.company}")
        lines.append(f"- **Fuente:** {job.source}")
        lines.append(f"- **Ubicación:** {job.location}")
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
