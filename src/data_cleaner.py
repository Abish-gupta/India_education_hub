"""
src/data_cleaner.py
===================
ARCHIE | Data Cleaning & Standardization Layer

Responsibilities:
  - Normalize state names across NIRF & AISHE datasets
  - Handle missing values with domain-aware imputation
  - Engineer features for analysis
  - Produce a single merged master DataFrame
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path

log = logging.getLogger(__name__)

RAW_DIR       = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ── State Name Canonicalization ────────────────────────────

STATE_ALIASES: dict[str, str] = {
    "tamilnadu":          "Tamil Nadu",
    "tamilnādu":          "Tamil Nadu",
    "andhra":             "Andhra Pradesh",
    "ap":                 "Andhra Pradesh",
    "telangana":          "Telangana",
    "ts":                 "Telangana",
    "karnataka":          "Karnataka",
    "maharashtra":        "Maharashtra",
    "kerala":             "Kerala",
    "delhi":              "Delhi",
    "nct of delhi":       "Delhi",
    "new delhi":          "Delhi",
    "west bengal":        "West Bengal",
    "westbengal":         "West Bengal",
    "up":                 "Uttar Pradesh",
    "uttarpradesh":       "Uttar Pradesh",
    "mp":                 "Madhya Pradesh",
    "madhyapradesh":      "Madhya Pradesh",
    "rajasthan":          "Rajasthan",
    "gujarat":            "Gujarat",
    "punjab":             "Punjab",
    "haryana":            "Haryana",
    "odisha":             "Odisha",
    "orissa":             "Odisha",
    "bihar":              "Bihar",
    "jharkhand":          "Jharkhand",
    "assam":              "Assam",
    "uttarakhand":        "Uttarakhand",
    "himachal pradesh":   "Himachal Pradesh",
    "chandigarh":         "Chandigarh",
    "goa":                "Goa",
    "chhattisgarh":       "Chhattisgarh",
    "j&k":                "Jammu & Kashmir",
    "jammu and kashmir":  "Jammu & Kashmir",
    "puducherry":         "Puducherry",
    "pondicherry":        "Puducherry",
}


def normalize_state(name: str) -> str:
    """Canonicalize a state name using the alias map."""
    if pd.isna(name):
        return "Unknown"
    key = str(name).strip().lower()
    return STATE_ALIASES.get(key, str(name).strip().title())


# ── NIRF Cleaning ──────────────────────────────────────────

def clean_nirf(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and enrich NIRF dataset.
    
    Steps:
      1. Normalize state names
      2. Cast rank & score to numeric
      3. Impute missing scores with category median
      4. Engineer tier labels (Tier 1 / 2 / 3)
      5. Add region mapping
    """
    log.info("Cleaning NIRF dataset...")
    df = df.copy()

    # 1. Normalize states
    df["state"] = df["state"].apply(normalize_state)
    df["city"]  = df["city"].str.strip().str.title()
    df["name"]  = df["name"].str.strip()

    # 2. Numeric casts
    df["rank"]  = pd.to_numeric(df["rank"], errors="coerce")
    df["score"] = pd.to_numeric(df["score"], errors="coerce")

    # 3. Impute missing scores
    df["score"] = df.groupby("category")["score"].transform(
        lambda x: x.fillna(x.median())
    )

    # 4. Tier engineering
    def assign_tier(row):
        if row["rank"] <= 10:
            return "Tier 1 — Elite"
        elif row["rank"] <= 50:
            return "Tier 2 — Premier"
        else:
            return "Tier 3 — Good"

    df["tier"] = df.apply(assign_tier, axis=1)

    # 5. Region mapping
    df["region"] = df["state"].map(_region_map())

    # 6. Estimated intake capacity (proxy based on category)
    intake_proxy = {
        "Engineering": 480,
        "University":  1200,
        "Medical":     150,
        "Management":  240,
        "Law":         120,
    }
    df["est_intake"] = df["category"].map(intake_proxy)

    # 7. Estimated annual fees (INR, proxy)
    def est_fees(row):
        base = {"Engineering": 120000, "University": 80000,
                "Medical": 60000, "Management": 300000, "Law": 100000}
        b = base.get(row["category"], 100000)
        if row["type"] == "Private":
            b *= 3.5
        # adjust by rank: top ranked → more premium (private) or subsidized (govt)
        rank_factor = max(0.6, 1 - (row["rank"] or 50) * 0.005)
        return int(b * rank_factor)

    df["est_annual_fees_inr"] = df.apply(est_fees, axis=1)

    log.info(f"NIRF cleaned: {len(df)} rows, {df['state'].nunique()} states")
    return df


def _region_map() -> dict[str, str]:
    return {
        "Tamil Nadu":       "South India",
        "Kerala":           "South India",
        "Karnataka":        "South India",
        "Telangana":        "South India",
        "Andhra Pradesh":   "South India",
        "Puducherry":       "South India",
        "Maharashtra":      "West India",
        "Gujarat":          "West India",
        "Goa":              "West India",
        "Rajasthan":        "North-West India",
        "Punjab":           "North India",
        "Haryana":          "North India",
        "Delhi":            "North India",
        "Uttar Pradesh":    "North India",
        "Uttarakhand":      "North India",
        "Himachal Pradesh": "North India",
        "Chandigarh":       "North India",
        "Jammu & Kashmir":  "North India",
        "Ladakh":           "North India",
        "West Bengal":      "East India",
        "Odisha":           "East India",
        "Bihar":            "East India",
        "Jharkhand":        "East India",
        "Assam":            "North-East India",
        "Manipur":          "North-East India",
        "Meghalaya":        "North-East India",
        "Nagaland":         "North-East India",
        "Tripura":          "North-East India",
        "Arunachal Pradesh":"North-East India",
        "Mizoram":          "North-East India",
        "Sikkim":           "North-East India",
        "Madhya Pradesh":   "Central India",
        "Chhattisgarh":     "Central India",
    }


# ── AISHE Cleaning ─────────────────────────────────────────

def clean_aishe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and enrich AISHE state-wise dataset.

    Adds:
      - region
      - private_ratio (% of private institutions)
      - female_ratio (% of female students)
      - enrollment_per_institution
    """
    log.info("Cleaning AISHE dataset...")
    df = df.copy()
    df["state"] = df["state"].apply(normalize_state)

    df["private_ratio"] = (
        df["private_institutions"] / df["total_institutions"]
    ).round(3)

    df["female_ratio"] = (
        df["female_enrollment_k"] / df["total_enrollment_k"]
    ).round(3)

    df["enrollment_per_institution"] = (
        (df["total_enrollment_k"] * 1000) / df["total_institutions"]
    ).round(0)

    df["region"] = df["state"].map(_region_map())

    log.info(f"AISHE cleaned: {len(df)} states")
    return df


# ── Migration Cleaning ─────────────────────────────────────

def clean_migration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean migration dataset and derive hub scores.
    """
    log.info("Cleaning migration dataset...")
    df = df.copy()
    df["state"] = df["state"].apply(normalize_state)

    # Normalized hub score [0, 100]
    max_net = df["net_migration_score"].max()
    min_net = df["net_migration_score"].min()
    df["hub_score_normalized"] = (
        (df["net_migration_score"] - min_net) / (max_net - min_net) * 100
    ).round(1)

    df["region"] = df["state"].map(_region_map())
    log.info(f"Migration cleaned: {len(df)} states")
    return df


# ── Master Merge ───────────────────────────────────────────

def build_master_dataset(
    df_nirf: pd.DataFrame,
    df_aishe: pd.DataFrame,
    df_migration: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join all datasets into a single analytical master table.
    
    Merge strategy:
      - NIRF: institution-level (one row = one college)
      - AISHE + Migration: state-level, joined to NIRF by state key
    """
    log.info("Building master dataset...")

    # State-level aggregates from NIRF
    state_nirf = (
        df_nirf.groupby("state")
        .agg(
            num_ranked_institutions=("name", "count"),
            avg_nirf_score=("score", "mean"),
            top_rank_available=("rank", "min"),
            govt_count=("type", lambda x: (x == "Government").sum()),
            private_count=("type", lambda x: (x == "Private").sum()),
        )
        .reset_index()
    )
    state_nirf["avg_nirf_score"] = state_nirf["avg_nirf_score"].round(2)

    # Join AISHE + Migration
    master = df_aishe.merge(df_migration, on="state", how="left", suffixes=("", "_mig"))
    master = master.merge(state_nirf, on="state", how="left")

    # Drop duplicate region column
    if "region_mig" in master.columns:
        master.drop(columns=["region_mig"], inplace=True)

    # Composite Education Hub Index
    # Weighted formula:
    #   40% net migration score (normalized)
    #   30% gross enrolment ratio
    #   20% avg NIRF score (normalized)
    #   10% private ratio (diversity signal)
    master["net_migration_norm"] = master["hub_score_normalized"].fillna(50)
    master["ger_norm"]           = (master["gross_enrolment_ratio"] / master["gross_enrolment_ratio"].max() * 100).round(1)
    master["nirf_norm"]          = (master["avg_nirf_score"] / master["avg_nirf_score"].max() * 100).fillna(0).round(1)
    master["priv_norm"]          = (master["private_ratio"] * 100).round(1)

    master["education_hub_index"] = (
        0.40 * master["net_migration_norm"] +
        0.30 * master["ger_norm"] +
        0.20 * master["nirf_norm"] +
        0.10 * master["priv_norm"]
    ).round(2)

    # Affordability flag: GER > 35 AND avg_fees < median
    # (proxy: government-dominant states tend to be cheaper)
    master["govt_ratio"] = (
        master["govt_institutions"] / master["total_institutions"]
    ).round(3)

    path = PROCESSED_DIR / "master_dataset.csv"
    master.to_csv(path, index=False)
    log.info(f"Master dataset saved → {path} ({len(master)} rows, {len(master.columns)} cols)")
    return master


# ── Entry Point ────────────────────────────────────────────

def run_cleaning_pipeline(
    df_nirf: pd.DataFrame,
    df_aishe: pd.DataFrame,
    df_migration: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Full cleaning pipeline. Returns cleaned individual datasets + master.
    """
    nirf      = clean_nirf(df_nirf)
    aishe     = clean_aishe(df_aishe)
    migration = clean_migration(df_migration)
    master    = build_master_dataset(nirf, aishe, migration)

    # Save individual cleaned files
    nirf.to_csv(PROCESSED_DIR / "nirf_clean.csv", index=False)
    aishe.to_csv(PROCESSED_DIR / "aishe_clean.csv", index=False)
    migration.to_csv(PROCESSED_DIR / "migration_clean.csv", index=False)

    return nirf, aishe, migration, master
