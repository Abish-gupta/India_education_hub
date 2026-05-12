"""
src/analyzer.py
===============
LOGIC | Analytical Engine

Runs all key analyses:
  1. Hub identification
  2. Migration flow analysis
  3. State-wise comparisons
  4. Correlation studies
  5. ROI & affordability analysis
  6. Education Hotspot Scoring
"""

import logging
import pandas as pd
import numpy as np
from tabulate import tabulate

log = logging.getLogger(__name__)


# ── 1. Hub Identification ──────────────────────────────────

def identify_education_hubs(master: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Rank states by Education Hub Index (composite score).
    Returns top_n hub states with detailed metrics.
    """
    cols = ["state", "education_hub_index", "hub_category",
            "net_migration_score", "gross_enrolment_ratio",
            "total_enrollment_k", "num_ranked_institutions",
            "avg_nirf_score", "region"]

    available_cols = [c for c in cols if c in master.columns]
    hubs = (
        master[available_cols]
        .dropna(subset=["education_hub_index"])
        .sort_values("education_hub_index", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    hubs.index = hubs.index + 1  # 1-based rank

    log.info(f"\n{'='*60}")
    log.info("TOP EDUCATION HUB STATES")
    log.info(f"{'='*60}")
    log.info("\n" + tabulate(
        hubs[["state", "education_hub_index", "hub_category", "region"]],
        headers="keys", tablefmt="rounded_outline"
    ))
    return hubs


# ── 2. Migration Flow Analysis ─────────────────────────────

def analyze_migration_flows(migration: pd.DataFrame) -> dict:
    """
    Identify exporter vs hub states.
    Returns dict with exporters, hubs, and transition states.
    """
    exporters = migration[migration["net_migration_score"] < -5].sort_values("net_migration_score")
    hubs      = migration[migration["net_migration_score"] > 5].sort_values("net_migration_score", ascending=False)
    neutral   = migration[migration["net_migration_score"].between(-5, 5)]

    log.info(f"\n{'='*60}")
    log.info("MIGRATION FLOW ANALYSIS")
    log.info(f"{'='*60}")
    log.info(f"Major Student Exporters  : {len(exporters)} states")
    log.info(f"Education Hubs (Attractors): {len(hubs)} states")
    log.info(f"Neutral States           : {len(neutral)} states")

    log.info("\nTop 5 Student-Exporting States:")
    log.info(exporters.head(5)[["state", "net_migration_score", "out_migration_pct"]].to_string(index=False))

    log.info("\nTop 5 Student-Attracting States:")
    log.info(hubs.head(5)[["state", "net_migration_score", "in_migration_pct"]].to_string(index=False))

    return {"exporters": exporters, "hubs": hubs, "neutral": neutral}


# ── 3. State Comparison ────────────────────────────────────

def state_comparison(master: pd.DataFrame) -> pd.DataFrame:
    """
    Multi-dimensional state comparison table.
    Ranks states on 5 dimensions and creates a composite rank.
    """
    metrics = ["total_enrollment_k", "gross_enrolment_ratio",
               "num_ranked_institutions", "avg_nirf_score", "gpi"]

    available = [m for m in metrics if m in master.columns]
    comp = master[["state", "region"] + available].copy().dropna(subset=available[:2])

    # Rank each metric (1 = best)
    for m in available:
        comp[f"rank_{m}"] = comp[m].rank(ascending=(m != "gpi"), method="min")

    rank_cols = [f"rank_{m}" for m in available]
    comp["composite_rank"] = comp[rank_cols].mean(axis=1).round(1)
    comp = comp.sort_values("composite_rank").reset_index(drop=True)
    comp.index = comp.index + 1

    return comp


# ── 4. Correlation Analysis ────────────────────────────────

def correlation_analysis(master: pd.DataFrame) -> pd.DataFrame:
    """
    Pearson correlation between numeric features.
    Focus: what drives student attraction?
    """
    numeric_cols = master.select_dtypes(include=[np.number]).columns.tolist()
    # Remove normalized helper columns
    exclude = ["net_migration_norm", "ger_norm", "nirf_norm", "priv_norm"]
    numeric_cols = [c for c in numeric_cols if c not in exclude]

    corr = master[numeric_cols].corr()

    # Focus on correlation with net_migration_score
    if "net_migration_score" in corr.columns:
        target_corr = (
            corr["net_migration_score"]
            .drop("net_migration_score", errors="ignore")
            .sort_values(key=abs, ascending=False)
        )
        log.info(f"\n{'='*60}")
        log.info("CORRELATIONS WITH NET MIGRATION SCORE")
        log.info(f"{'='*60}")
        for feat, val in target_corr.items():
            bar = "█" * int(abs(val) * 20)
            sign = "+" if val > 0 else "-"
            log.info(f"  {feat:<35} {sign}{abs(val):.3f}  {bar}")

    return corr


# ── 5. ROI & Affordability Analysis ───────────────────────

def roi_analysis(nirf: pd.DataFrame) -> pd.DataFrame:
    """
    Compute ROI proxy for institutions:
      ROI Score = NIRF Score / (Annual Fees in lakhs)
    
    Higher score = better value-per-rupee education.
    """
    df = nirf.copy()
    df["fees_lakh"] = df["est_annual_fees_inr"] / 100_000
    df["roi_score"] = (df["score"] / df["fees_lakh"]).round(2)

    roi_top = (
        df.sort_values("roi_score", ascending=False)
        [["name", "state", "category", "type", "score", "fees_lakh", "roi_score"]]
        .head(20)
    )

    log.info(f"\n{'='*60}")
    log.info("TOP 20 INSTITUTIONS BY ROI (Score per Lakh Invested)")
    log.info(f"{'='*60}")
    log.info("\n" + tabulate(roi_top, headers="keys", tablefmt="rounded_outline", floatfmt=".2f"))
    return roi_top


# ── 6. Hotspot Scoring ─────────────────────────────────────

def compute_hotspot_scores(master: pd.DataFrame, nirf: pd.DataFrame) -> pd.DataFrame:
    """
    City-level hotspot analysis.
    Cities with multiple ranked institutions = education hotspots.
    """
    city_stats = (
        nirf.groupby(["city", "state"])
        .agg(
            num_institutions=("name", "count"),
            avg_score=("score", "mean"),
            categories=("category", lambda x: ", ".join(sorted(set(x)))),
            has_iit=("name", lambda x: any("IIT" in n for n in x)),
            has_aiims=("name", lambda x: any("AIIMS" in n for n in x)),
            has_iim=("name", lambda x: any("IIM" in n for n in x)),
        )
        .reset_index()
    )

    # Hotspot score: weighted by institution count + quality
    city_stats["hotspot_score"] = (
        city_stats["num_institutions"] * 2 +
        city_stats["avg_score"] * 0.3 +
        city_stats["has_iit"].astype(int) * 5 +
        city_stats["has_aiims"].astype(int) * 4 +
        city_stats["has_iim"].astype(int) * 4
    ).round(2)

    city_stats = city_stats.sort_values("hotspot_score", ascending=False).reset_index(drop=True)
    city_stats.index = city_stats.index + 1

    log.info(f"\n{'='*60}")
    log.info("TOP EDUCATION HOTSPOT CITIES")
    log.info(f"{'='*60}")
    log.info("\n" + tabulate(
        city_stats.head(15)[["city", "state", "num_institutions", "avg_score", "hotspot_score"]],
        headers="keys", tablefmt="rounded_outline", floatfmt=".2f"
    ))
    return city_stats


# ── 7. Southern India Deep Dive ────────────────────────────

def southern_india_analysis(master: pd.DataFrame, nirf: pd.DataFrame) -> dict:
    """
    Focused analysis on whether Southern India is a dominant education hub.
    """
    south_states = ["Tamil Nadu", "Karnataka", "Kerala", "Telangana", "Andhra Pradesh", "Puducherry"]

    south_master = master[master["state"].isin(south_states)]
    other_master = master[~master["state"].isin(south_states)]

    south_nirf = nirf[nirf["state"].isin(south_states)]

    metrics = {
        "avg_gross_enrolment_ratio": (
            south_master["gross_enrolment_ratio"].mean(),
            other_master["gross_enrolment_ratio"].mean()
        ),
        "avg_net_migration_score": (
            south_master["net_migration_score"].mean(),
            other_master["net_migration_score"].mean()
        ),
        "total_ranked_institutions": (
            len(south_nirf),
            len(nirf) - len(south_nirf)
        ),
        "avg_nirf_score": (
            south_nirf["score"].mean(),
            nirf[~nirf["state"].isin(south_states)]["score"].mean()
        ),
    }

    log.info(f"\n{'='*60}")
    log.info("SOUTH INDIA vs REST OF INDIA ANALYSIS")
    log.info(f"{'='*60}")
    for metric, (south_val, other_val) in metrics.items():
        advantage = "South ✓" if south_val > other_val else "Other ✓"
        log.info(f"  {metric:<35} South={south_val:.2f}  Other={other_val:.2f}  [{advantage}]")

    return {
        "south_master": south_master,
        "south_nirf": south_nirf,
        "comparison": metrics
    }


# ── 8. Govt vs Private Trend ──────────────────────────────

def govt_vs_private_analysis(nirf: pd.DataFrame, aishe: pd.DataFrame) -> dict:
    """
    Compare government and private institutions across quality, fees, and geography.
    """
    # Institution quality split
    type_quality = nirf.groupby("type").agg(
        count=("name", "count"),
        avg_score=("score", "mean"),
        avg_rank=("rank", "mean"),
        avg_fees=("est_annual_fees_inr", "mean"),
    ).round(2)

    # State-level private dominance
    state_type = nirf.groupby(["state", "type"]).size().unstack(fill_value=0)
    if "Private" in state_type.columns and "Government" in state_type.columns:
        state_type["private_dominance"] = state_type["Private"] > state_type["Government"]

    log.info(f"\n{'='*60}")
    log.info("GOVERNMENT vs PRIVATE INSTITUTION ANALYSIS")
    log.info(f"{'='*60}")
    log.info("\n" + tabulate(type_quality, headers="keys", tablefmt="rounded_outline", floatfmt=".2f"))

    return {"quality_split": type_quality, "state_split": state_type}


# ── Run All Analyses ───────────────────────────────────────

def run_all_analyses(
    master: pd.DataFrame,
    nirf: pd.DataFrame,
    aishe: pd.DataFrame,
    migration: pd.DataFrame
) -> dict:
    """Run the full analytical suite. Returns all result objects."""
    return {
        "hubs":         identify_education_hubs(master),
        "migration":    analyze_migration_flows(migration),
        "comparison":   state_comparison(master),
        "correlation":  correlation_analysis(master),
        "roi":          roi_analysis(nirf),
        "hotspots":     compute_hotspot_scores(master, nirf),
        "south":        southern_india_analysis(master, nirf),
        "govt_private": govt_vs_private_analysis(nirf, aishe),
    }
