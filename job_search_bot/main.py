import argparse
import logging

from dotenv import load_dotenv

from .config import load_config
from .cover_letter import generate_cover_letter, load_cv
from .db import JobDB
from .matcher import filter_jobs
from .report import write_reports
from .scrapers.indeed import IndeedScraper
from .scrapers.linkedin import LinkedInScraper
from .scrapers.zonajobs import ZonaJobsScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SCRAPER_CLASSES = {
    "indeed": IndeedScraper,
    "linkedin": LinkedInScraper,
    "zonajobs": ZonaJobsScraper,
}


def build_scrapers(config: dict):
    scrapers = []
    sites = config.get("sites", {})
    for name, cls in SCRAPER_CLASSES.items():
        site_cfg = sites.get(name, {})
        if not site_cfg.get("enabled", False):
            continue
        kwargs = {k: v for k, v in site_cfg.items() if k != "enabled"}
        scrapers.append(cls(**kwargs))
    return scrapers


def _open_report(html_path, notif_cfg: dict) -> None:
    if notif_cfg.get("open_in_browser", True):
        import webbrowser

        webbrowser.open(html_path.resolve().as_uri())


def main():
    parser = argparse.ArgumentParser(description="Buscador semi-automático de empleo")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--no-cover-letters", action="store_true")
    parser.add_argument(
        "--all-matches",
        action="store_true",
        help="No busca nada nuevo: genera un reporte con TODAS las vacantes que "
        "matchearon tus criterios en cualquier corrida anterior (no solo las nuevas).",
    )
    args = parser.parse_args()

    load_dotenv()
    config = load_config(args.config)
    search_cfg = config["search"]
    notif_cfg = config.get("notification", {})

    db = JobDB(config["db"]["path"])

    if args.all_matches:
        all_matched = db.get_all_matched()
        logger.info("Total de vacantes que matchearon alguna vez: %d", len(all_matched))
        md_path, html_path = write_reports(all_matched, {}, notif_cfg.get("output_dir", "data/reports"))
        logger.info("Reporte guardado en %s y %s", md_path, html_path)
        _open_report(html_path, notif_cfg)
        db.close()
        return

    scrapers = build_scrapers(config)

    if not scrapers:
        logger.error("No hay sitios habilitados en la config (sites.*.enabled: true).")
        return

    new_matches = []
    for scraper in scrapers:
        for keyword in search_cfg["keywords"]:
            logger.info("[%s] buscando %r...", scraper.name, keyword)
            results = scraper.search(keyword, max_results=search_cfg.get("max_results_per_site", 25))
            for job in results:
                if not db.is_new(job):
                    continue
                is_match = bool(filter_jobs([job], search_cfg))
                db.save(job, matched=is_match)
                if is_match:
                    new_matches.append(job)

    logger.info("Encontradas %d vacantes nuevas que matchean tus criterios.", len(new_matches))

    cover_letters = {}
    cl_cfg = config.get("cover_letter", {})
    if cl_cfg.get("enabled") and not args.no_cover_letters and new_matches:
        cv_text = load_cv(cl_cfg["cv_path"])
        model = cl_cfg.get("anthropic_model", "claude-sonnet-5")
        for job in new_matches:
            try:
                cover_letters[job.uid] = generate_cover_letter(job, cv_text, model=model)
            except Exception as exc:
                logger.warning("No se pudo generar carta para %r: %s", job.title, exc)

    md_path, html_path = write_reports(new_matches, cover_letters, notif_cfg.get("output_dir", "data/reports"))
    logger.info("Reporte guardado en %s y %s", md_path, html_path)
    _open_report(html_path, notif_cfg)

    db.close()


if __name__ == "__main__":
    main()
