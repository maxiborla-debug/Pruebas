import os
from pathlib import Path

from .models import JobPosting

DEFAULT_MODEL = "claude-sonnet-5"


def load_cv(cv_path: str) -> str:
    path = Path(cv_path)
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el CV en {cv_path}. Guardá tu CV como texto plano ahí "
            "(copiá el contenido desde el PDF/Word)."
        )
    return path.read_text(encoding="utf-8")


def generate_cover_letter(job: JobPosting, cv_text: str, model: str = DEFAULT_MODEL) -> str:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta ANTHROPIC_API_KEY en el entorno. Copiá .env.example a .env y completá tu API key."
        )

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Sos un asistente que ayuda a redactar cartas de presentación breves y concretas.

CV del candidato:
---
{cv_text}
---

Vacante:
- Puesto: {job.title}
- Empresa: {job.company}
- Ubicación: {job.location}
- Descripción: {job.description or "No disponible"}

Escribí un borrador de carta de presentación en español, de máximo 200 palabras,
que conecte la experiencia del CV con los requisitos de la vacante. Tono
profesional y directo, sin frases genéricas de relleno. No inventes experiencia
que no esté en el CV."""

    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
