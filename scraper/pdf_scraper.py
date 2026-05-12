"""
scraper/pdf_scraper.py
======================
LOGIC | PDF-Based Data Extraction (RAG-style)
Primary data source: NIRF & AISHE official PDF reports.

Strategy:
  1. Download PDFs from official government portals
  2. Extract tables using pdfplumber (handles multi-column layouts)
  3. Parse and normalize extracted text into DataFrames
  4. Fall back to seed dataset if PDF structure changes

Sources:
  - NIRF 2024: https://www.nirfindia.org/2024/Ranking2024.html (PDFs linked per category)
  - AISHE 2021-22: https://aishe.gov.in/aishe/reports
"""

import io
import re
import logging
import requests
import pdfplumber
import pandas as pd
from pathlib import Path
from tqdm import tqdm

log = logging.getLogger(__name__)

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── Known PDF URLs ─────────────────────────────────────────
# These are official government report PDFs — stable, not behind login

NIRF_PDF_URLS = {
    "Engineering": "https://www.nirfindia.org/nirfpdfcdn/2024/pdf/Engineering.pdf",
    "University":  "https://www.nirfindia.org/nirfpdfcdn/2024/pdf/University.pdf",
    "Medical":     "https://www.nirfindia.org/nirfpdfcdn/2024/pdf/Medical.pdf",
    "Management":  "https://www.nirfindia.org/nirfpdfcdn/2024/pdf/Management.pdf",
    "Law":         "https://www.nirfindia.org/nirfpdfcdn/2024/pdf/Law.pdf",
}

AISHE_PDF_URL = (
    "https://aishe.gov.in/aishe/reports"
    # Primary: AISHE 2021-22 consolidated report
)


# ── PDF Download ───────────────────────────────────────────

def download_pdf(url: str, save_path: Path) -> bytes | None:
    """Download a PDF and cache it locally. Returns bytes or None on failure."""
    if save_path.exists():
        log.info(f"  ↩ Using cached PDF: {save_path.name}")
        return save_path.read_bytes()

    try:
        log.info(f"  ⬇ Downloading: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        resp.raise_for_status()

        content = b""
        for chunk in tqdm(resp.iter_content(chunk_size=8192),
                          desc=f"  {save_path.name}", unit="KB", leave=False):
            content += chunk

        save_path.write_bytes(content)
        log.info(f"  ✔ Saved: {save_path} ({len(content)//1024} KB)")
        return content

    except requests.RequestException as e:
        log.warning(f"  ✗ PDF download failed [{url}]: {e}")
        return None


# ── NIRF PDF Parser ────────────────────────────────────────

def parse_nirf_pdf(pdf_bytes: bytes, category: str) -> list[dict]:
    """
    Extract ranking table from NIRF PDF report.

    NIRF PDF table structure (2024 format):
      Col 0: Rank | Col 1: Institute ID | Col 2: Name | Col 3: City | Col 4: State | Col 5: Score
    """
    records = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract tables with bounding-box tolerance
                tables = page.extract_tables({
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 4,
                    "join_tolerance": 4,
                })

                for table in tables:
                    for row in table:
                        if not row or len(row) < 5:
                            continue

                        # Skip header rows
                        first = str(row[0] or "").strip()
                        if not first.isdigit():
                            continue

                        rank  = first
                        name  = _clean_cell(row[2] if len(row) > 2 else row[1])
                        city  = _clean_cell(row[3] if len(row) > 3 else "")
                        state = _clean_cell(row[4] if len(row) > 4 else "")
                        score = _parse_score(row[5] if len(row) > 5 else "")

                        if name and state:
                            records.append({
                                "rank":     rank,
                                "name":     name,
                                "city":     city,
                                "state":    state,
                                "score":    score,
                                "category": category,
                                "type":     _infer_type(name),
                            })

    except Exception as e:
        log.error(f"  ✗ PDF parse error for {category}: {e}")

    log.info(f"  → Extracted {len(records)} records from {category} PDF")
    return records


def _clean_cell(val) -> str:
    """Normalize a PDF cell value."""
    if val is None:
        return ""
    return re.sub(r"\s+", " ", str(val)).strip()


def _parse_score(val) -> float | None:
    """Extract numeric score from PDF cell."""
    try:
        return float(re.sub(r"[^\d.]", "", str(val)))
    except (ValueError, TypeError):
        return None


def _infer_type(name: str) -> str:
    """Classify institution type from name patterns."""
    govt_kws = ["IIT", "NIT", "AIIMS", "IIM", "Central", "National",
                "Government", "Govt", "State", "Jawaharlal", "JIPMER",
                "PGIMER", "SGPGI", "Banaras", "Aligarh", "Osmania"]
    name_up = name.upper()
    return "Government" if any(k.upper() in name_up for k in govt_kws) else "Private"


# ── AISHE PDF Parser ───────────────────────────────────────

def parse_aishe_pdf(pdf_bytes: bytes) -> pd.DataFrame:
    """
    Extract state-wise enrollment table from AISHE PDF report.

    Targets Table 2 / Table 3 in AISHE consolidated report:
    "Number of Institutions, Enrolment by State/UT"
    """
    records = []
    target_keywords = ["enrollment", "enrolment", "institutions", "state"]

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            log.info(f"  AISHE PDF: {len(pdf.pages)} pages")

            for page_num, page in enumerate(pdf.pages):
                text = (page.extract_text() or "").lower()

                # Only process pages likely to contain enrollment tables
                if not any(kw in text for kw in target_keywords):
                    continue

                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or len(row) < 4:
                            continue
                        state_cell = _clean_cell(row[0])
                        if not state_cell or state_cell.lower() in ("state", "sl.no", "s.no"):
                            continue

                        # Try to extract numeric enrollment values
                        nums = []
                        for cell in row[1:]:
                            try:
                                val = float(re.sub(r"[^\d.]", "", str(cell or "")))
                                nums.append(val)
                            except ValueError:
                                nums.append(None)

                        if nums and any(n is not None for n in nums):
                            records.append({
                                "state": state_cell,
                                "raw_values": nums,
                            })

    except Exception as e:
        log.error(f"  ✗ AISHE PDF parse error: {e}")

    if records:
        log.info(f"  → Extracted {len(records)} state rows from AISHE PDF")
        return pd.DataFrame(records)

    log.warning("  AISHE PDF parse yielded no data; falling back to seed")
    return pd.DataFrame()


# ── Main PDF Extraction Pipeline ──────────────────────────

def extract_from_pdfs() -> tuple[pd.DataFrame, bool]:
    """
    Master pipeline: download + parse all NIRF PDFs.
    Returns (DataFrame, used_pdf:bool).
    """
    all_records = []
    any_success = False

    log.info("\n📄 PDF Extraction Pipeline Starting...")
    log.info("=" * 55)

    for category, url in NIRF_PDF_URLS.items():
        pdf_path = RAW_DIR / f"nirf_{category.lower()}.pdf"
        pdf_bytes = download_pdf(url, pdf_path)

        if pdf_bytes:
            records = parse_nirf_pdf(pdf_bytes, category)
            if records:
                all_records.extend(records)
                any_success = True
        else:
            log.warning(f"  Skipping {category} — PDF unavailable")

    if all_records:
        df = pd.DataFrame(all_records)
        out_path = RAW_DIR / "nirf_from_pdf.csv"
        df.to_csv(out_path, index=False)
        log.info(f"\n✅ PDF extraction complete: {len(df)} institutions → {out_path}")
        return df, True

    log.info("\n⚠️  PDF extraction failed — will use embedded seed dataset")
    return pd.DataFrame(), False


def extract_aishe_from_pdf() -> pd.DataFrame:
    """
    Attempt AISHE PDF extraction. Returns raw DataFrame or empty.
    Caller should merge with seed data for completeness.
    """
    # AISHE direct download link (consolidated 2021-22 report)
    aishe_url  = "https://aishe.gov.in/aishe/reports/AISHE_FINAL_REPORT_2021-22.pdf"
    aishe_path = RAW_DIR / "aishe_report_2021_22.pdf"

    pdf_bytes = download_pdf(aishe_url, aishe_path)
    if pdf_bytes:
        return parse_aishe_pdf(pdf_bytes)

    log.warning("AISHE PDF unavailable — using seed data")
    return pd.DataFrame()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    df, used_pdf = extract_from_pdfs()
    if not df.empty:
        print(f"\nExtracted {len(df)} records from PDFs")
        print(df.head(10).to_string(index=False))
    else:
        print("No PDF data extracted. Run main.py to use seed fallback.")
