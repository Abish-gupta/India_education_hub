# scraper/nirf_scraper.py

import requests
import time
import random
import logging
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

log = logging.getLogger(__name__)

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

NIRF_CATEGORIES = {
    "Engineering": "https://www.nirfindia.org/2024/EngineeringRanking.html",
    "University":  "https://www.nirfindia.org/2024/UniversityRanking.html",
    "Medical":     "https://www.nirfindia.org/2024/MedicalRanking.html",
    "Management":  "https://www.nirfindia.org/2024/ManagementRanking.html",
    "Law":         "https://www.nirfindia.org/2024/LawRanking.html",
}

def _polite_get(url: str, retries: int = 3) -> requests.Response | None:
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(1.5, 3.5))
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            log.warning(f"Attempt {attempt+1} failed for {url}: {e}")
    return None

def parse_nirf_table(html: str, category: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    records: list[dict] = []

    table = soup.find("table", {"class": lambda c: c and "ranking" in c.lower()})
    if table is None:
        table = soup.find("table")

    if table is None:
        log.warning(f"No table found for category: {category}")
        return records

    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) >= 5:
            records.append({
                "rank":     cols[0],
                "name":     cols[1],
                "city":     cols[2] if len(cols) > 2 else "Unknown",
                "state":    cols[3] if len(cols) > 3 else "Unknown",
                "score":    cols[4] if len(cols) > 4 else None,
                "category": category,
                "type":     _infer_type(cols[1]),
            })
    return records

def _infer_type(name: str) -> str:
    govt_keywords = [
        "IIT", "NIT", "AIIMS", "IIM", "Central", "National",
        "Government", "Govt", "State", "University of",
    ]
    name_upper = name.upper()
    for kw in govt_keywords:
        if kw.upper() in name_upper:
            return "Government"
    return "Private"

def scrape_nirf() -> pd.DataFrame:
    """
    Main scraper: iterates NIRF categories, parses tables.
    Live scraping only: if site fails, raises error instead of using seed data.
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
        # Hard fail: nothing scraped at all
        raise RuntimeError("No NIRF data scraped. Check network or NIRF site structure.")

    df = pd.DataFrame(all_records)
    df.to_csv(RAW_DIR / "nirf_raw.csv", index=False)
    log.info(f"Saved {len(df)} rows → data/raw/nirf_raw.csv")
    return df

if __name__ == "__main__":
    df = scrape_nirf()
    print(df.head(10).to_string(index=False))
