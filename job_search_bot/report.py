import html as html_lib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .freshness import days_ago
from .models import JobPosting


def _sort_key(job: JobPosting):
    age = days_ago(job.posted_date) if job.posted_date else None
    # Los de antigüedad conocida van primero (los más nuevos arriba de todo);
    # los de antigüedad desconocida quedan al final, no se descartan.
    return (age is None, age if age is not None else 0)


def _age_text(job: JobPosting) -> str:
    if not job.posted_date:
        return "fecha no disponible en el sitio"
    age = days_ago(job.posted_date)
    return f"{job.posted_date} (~{age} días)" if age is not None else job.posted_date


def write_reports(matched: List[JobPosting], cover_letters: Dict[str, str], output_dir: str) -> Tuple[Path, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    matched = sorted(matched, key=_sort_key)

    md_path = _write_markdown(matched, cover_letters, out_dir, ts)
    html_path = _write_html(matched, cover_letters, out_dir, ts)
    return md_path, html_path


def _write_markdown(matched: List[JobPosting], cover_letters: Dict[str, str], out_dir: Path, ts: str) -> Path:
    path = out_dir / f"{ts}.md"
    lines = [f"# Vacantes nuevas — {datetime.now().strftime('%d/%m/%Y %H:%M')} (ordenadas por más recientes)", ""]
    if not matched:
        lines.append("No se encontraron vacantes nuevas que matcheen tus criterios.")

    for job in matched:
        lines.append(f"## {job.title} — {job.company}")
        lines.append(f"- **Fuente:** {job.source}")
        lines.append(f"- **Ubicación:** {job.location}")
        lines.append(f"- **Publicado:** {_age_text(job)}")
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


def _write_html(matched: List[JobPosting], cover_letters: Dict[str, str], out_dir: Path, ts: str) -> Path:
    path = out_dir / f"{ts}.html"

    cards = []
    for job in matched:
        letter = cover_letters.get(job.uid)
        letter_html = ""
        if letter:
            letter_html = (
                "<details><summary>Ver borrador de carta de presentación</summary>"
                f"<p>{html_lib.escape(letter).replace(chr(10), '<br>')}</p></details>"
            )
        salary_html = f'<span class="tag salary">{html_lib.escape(job.salary)}</span>' if job.salary else ""
        cards.append(
            f"""
        <article class="card">
          <h2><a href="{html_lib.escape(job.url)}" target="_blank" rel="noopener">{html_lib.escape(job.title)}</a></h2>
          <div class="meta">
            <span class="tag company">{html_lib.escape(job.company)}</span>
            <span class="tag source">{html_lib.escape(job.source)}</span>
            <span class="tag location">{html_lib.escape(job.location)}</span>
            {salary_html}
          </div>
          <div class="date">Publicado: {html_lib.escape(_age_text(job))}</div>
          {letter_html}
        </article>"""
        )

    body = "".join(cards) if cards else "<p>No se encontraron vacantes nuevas que matcheen tus criterios.</p>"

    page = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vacantes — {ts}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 780px; margin: 2rem auto; padding: 0 1.25rem; line-height: 1.5;
  }}
  h1 {{ font-size: 1.35rem; margin-bottom: 1.5rem; }}
  .card {{
    border: 1px solid rgba(128,128,128,.35); border-radius: 12px;
    padding: 1rem 1.25rem; margin-bottom: 1rem;
  }}
  .card h2 {{ margin: 0 0 .5rem; font-size: 1.05rem; }}
  .card h2 a {{ text-decoration: none; color: inherit; }}
  .card h2 a:hover {{ text-decoration: underline; }}
  .meta {{ display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .5rem; }}
  .tag {{
    font-size: .72rem; padding: .18rem .55rem; border-radius: 999px;
    background: rgba(128,128,128,.18);
  }}
  .tag.salary {{ background: rgba(46,160,67,.25); }}
  .date {{ font-size: .8rem; opacity: .65; }}
  details {{ margin-top: .6rem; font-size: .85rem; }}
  summary {{ cursor: pointer; opacity: .8; }}
  summary:hover {{ opacity: 1; }}
</style>
</head>
<body>
<h1>Vacantes nuevas — {datetime.now().strftime('%d/%m/%Y %H:%M')} (ordenadas por más recientes)</h1>
{body}
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")
    return path
