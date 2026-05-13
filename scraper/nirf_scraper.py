# scraper/nirf_scraper.py

import requests
import time
import random
import logging
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── HTTP config ───────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── NIRF 2024 category pages (use new Rankings paths) ─────
# Right now we only know the correct Overall URL for sure.
# You can update/add others once you confirm them in the browser.
NIRF_CATEGORIES: dict[str, str] = {
    "Overall": "https://www.nirfindia.org/Rankings/2024/OverallRanking.html",
    # "Engineering": "https://www.nirfindia.org/Rankings/2024/EngineeringRanking.html",
    # "University":  "https://www.nirfindia.org/Rankings/2024/UniversityRanking.html",
    # "Medical":     "https://www.nirfindia.org/Rankings/2024/MedicalRanking.html",
    # "Management":  "https://www.nirfindia.org/Rankings/2024/ManagementRanking.html",
    # "Law":         "https://www.nirfindia.org/Rankings/2024/LawRanking.html",
}


# ── Helpers ───────────────────────────────────────────────
def _polite_get(url: str, retries: int = 3) -> requests.Response | None:
    """
    HTTP GET with retry logic and polite random delay.
    Live only: returns None if all retries fail.
    """
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(1.5, 3.5))
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            log.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
    return None


def _infer_type(name: str) -> str:
    """
    Heuristically classify institution as Government or Private based on name.
    """
    govt_keywords = [
        "IIT", "NIT", "AIIMS", "IIM", "Central", "National",
        "Government", "Govt", "State", "University of",
    ]
    name_upper = name.upper()
    for kw in govt_keywords:
        if kw.upper() in name_upper:
            return "Government"
    return "Private"


def parse_nirf_table(html: str, category: str) -> list[dict]:
    """
    Parse NIRF ranking table rows from a category page into a list of dicts.

    Assumes the table structure like the 'India Rankings 2024: Overall' page:

    | Institute ID | Name | City | State | Score | Rank |
    """
    soup = BeautifulSoup(html, "lxml")
    records: list[dict] = []

    # NIRF usually has a single main table on the page
    table = soup.find("table")
    if table is None:
        log.warning(f"No table found for category: {category}")
        return records

    rows = table.find_all("tr")[1:]  # skip header row

    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        # Expecting at least 6 columns: id, name, city, state, score, rank
        if len(cols) >= 6:
            institute_id = cols[0]
            name = cols[1]
            city = cols[2]
            state = cols[3]
            score = cols[4]
            rank = cols[5]

            records.append(
                {
                    "institute_id": institute_id,
                    "name": name,
                    "city": city,
                    "state": state,
                    "score": score,
                    "rank": rank,
                    "category": category,
                    "type": _infer_type(name),
                }
            )

    return records


# ── Main entrypoint ───────────────────────────────────────
def scrape_nirf() -> pd.DataFrame:
    """
    Scrape NIRF 2024 rankings for all configured categories.

    - Live scraping only (no dummy data).
    - If a category fails, it logs an error and continues with others.
    - If no data at all is scraped, raises RuntimeError.
    """
    all_records: list[dict] = []

    for category, url in NIRF_CATEGORIES.items():
        log.info(f"Scraping NIRF [{category}] → {url}")
        response = _polite_get(url)

        if not response:
            log.error(f"✗ Failed to fetch {category} from {url}")
            continue

        records = parse_nirf_table(response.text, category)
        log.info(f"✔ {len(records)} records found for {category}")
        all_records.extend(records)

    if not all_records:
        # Hard fail: nothing scraped from any category
        raise RuntimeError(
            "No NIRF data scraped for any category. "
            "Check network or NIRF site structure."
        )

    df = pd.DataFrame(all_records)
    out_path = RAW_DIR / "nirf_raw.csv"
    df.to_csv(out_path, index=False)
    log.info(f"Saved {len(df)} rows → {out_path}")
    return df


if __name__ == "__main__":
    df = scrape_nirf()
    print(df.head(10).to_string(index=False))
