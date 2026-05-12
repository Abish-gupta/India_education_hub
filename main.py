"""
main.py
=======
India's Student Migration & Education Hubs — Master Orchestrator

Execution Order:
  1. PDF extraction (NIRF/AISHE official reports)
  2. HTML scraping fallback (if PDF fails)
  3. Data cleaning & feature engineering
  4. Statistical analysis
  5. Visualization generation
  6. Insight report export
"""

import sys
import logging
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

# ── Logging Setup ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", mode="w"),
    ],
)
log = logging.getLogger(__name__)

# ── Project Imports ────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from scraper.pdf_scraper    import extract_from_pdfs, extract_aishe_from_pdf
from scraper.nirf_scraper   import scrape_nirf, _seed_dataset
from scraper.aishe_scraper  import scrape_aishe_statewise, scrape_student_migration
from src.data_cleaner       import run_cleaning_pipeline
from src.analyzer           import run_all_analyses
from src.visualizer         import run_all_visualizations
from src.report_generator   import generate_insight_report

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   🎓 INDIA EDUCATION HUB ANALYTICS — v1.0                  ║
║   Mapping Student Migration Patterns Across Indian States   ║
║   Data Sources: NIRF 2024 + AISHE 2021-22                  ║
╚══════════════════════════════════════════════════════════════╝
"""


def run_data_collection() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Stage 1: Data Collection
    Priority: PDF extraction → HTML scraping → Seed dataset
    """
    log.info("━━━ STAGE 1: DATA COLLECTION ━━━━━━━━━━━━━━━━━━━━━━━━━")

    # ── NIRF Data ──────────────────────────────────────────
    log.info("[NIRF] Attempting PDF extraction first...")
    df_nirf_pdf, pdf_success = extract_from_pdfs()

    if pdf_success and len(df_nirf_pdf) > 20:
        log.info(f"[NIRF] ✅ PDF extraction succeeded: {len(df_nirf_pdf)} records")
        df_nirf = df_nirf_pdf
    else:
        log.info("[NIRF] PDF unavailable — trying HTML scraping...")
        df_nirf = scrape_nirf()  # Falls back to seed internally

        if df_nirf.empty:
            log.warning("[NIRF] HTML scraping failed — loading embedded seed")
            df_nirf = _seed_dataset()

    log.info(f"[NIRF] Final: {len(df_nirf)} institutions across {df_nirf['state'].nunique()} states")

    # ── AISHE Data ─────────────────────────────────────────
    log.info("[AISHE] Loading state-wise enrollment data...")
    df_aishe = scrape_aishe_statewise()
    log.info(f"[AISHE] {len(df_aishe)} states loaded")

    # ── Migration Data ─────────────────────────────────────
    log.info("[MIGRATION] Loading inter-state migration data...")
    df_migration = scrape_student_migration()
    log.info(f"[MIGRATION] {len(df_migration)} states loaded")

    return df_nirf, df_aishe, df_migration


def run_pipeline():
    """Master pipeline controller."""
    print(BANNER)

    # ── Stage 1: Collection ────────────────────────────────
    df_nirf, df_aishe, df_migration = run_data_collection()

    # ── Stage 2: Cleaning ──────────────────────────────────
    log.info("\n━━━ STAGE 2: DATA CLEANING & ENGINEERING ━━━━━━━━━━━━━")
    nirf_clean, aishe_clean, migration_clean, master = run_cleaning_pipeline(
        df_nirf, df_aishe, df_migration
    )
    log.info(f"Master dataset: {len(master)} rows × {len(master.columns)} columns")

    # ── Stage 3: Analysis ──────────────────────────────────
    log.info("\n━━━ STAGE 3: STATISTICAL ANALYSIS ━━━━━━━━━━━━━━━━━━━━")
    results = run_all_analyses(master, nirf_clean, aishe_clean, migration_clean)

    # ── Stage 4: Visualization ─────────────────────────────
    log.info("\n━━━ STAGE 4: VISUALIZATION GENERATION ━━━━━━━━━━━━━━━━")
    run_all_visualizations(nirf_clean, aishe_clean, migration_clean, master, results)

    # ── Stage 5: Insight Report ────────────────────────────
    log.info("\n━━━ STAGE 5: INSIGHT REPORT ━━━━━━━━━━━━━━━━━━━━━━━━━━")
    generate_insight_report(master, nirf_clean, migration_clean, results)

    log.info("\n" + "═" * 62)
    log.info("🎉 PIPELINE COMPLETE")
    log.info("  📁 Processed data  → data/processed/")
    log.info("  📊 Visualizations  → visuals/")
    log.info("  📝 Insight report  → presentation/insights_report.md")
    log.info("  📋 Pipeline log    → pipeline.log")
    log.info("═" * 62)


if __name__ == "__main__":
    run_pipeline()
