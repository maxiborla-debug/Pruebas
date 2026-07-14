from pathlib import Path

import yaml


def load_config(path: str = "config.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"No se encontró {path}. Copiá config.example.yaml a config.yaml y completá tus criterios."
        )
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
