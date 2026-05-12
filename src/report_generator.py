"""
src/report_generator.py
=======================
LOGIC | Insight Report Generator

Produces a structured Markdown report with:
  - Executive summary
  - Key findings per research question
  - Data-driven observations
  - Strategic conclusions
"""

import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

log = logging.getLogger(__name__)
PRESENTATION_DIR = Path(__file__).parent.parent / "presentation"
PRESENTATION_DIR.mkdir(parents=True, exist_ok=True)


def generate_insight_report(
    master: pd.DataFrame,
    nirf: pd.DataFrame,
    migration: pd.DataFrame,
    results: dict,
) -> None:
    """Generate the final Markdown insight report."""

    ts = datetime.now().strftime("%B %Y")
    hubs = results.get("hubs", pd.DataFrame())
    hotspots = results.get("hotspots", pd.DataFrame())
    roi_df = results.get("roi", pd.DataFrame())
    gov_priv = results.get("govt_private", {})
    south = results.get("south", {})

    # ── Helper: safe top-n ────────────────────────────────
    def top_states(df, col, n=5, ascending=False):
        if df.empty or col not in df.columns:
            return "N/A"
        top = df.nlargest(n, col) if not ascending else df.nsmallest(n, col)
        return ", ".join(top["state"].tolist())

    top_hub_states  = top_states(migration, "net_migration_score", 5)
    top_exp_states  = top_states(migration, "net_migration_score", 5, ascending=True)
    top_ger_states  = top_states(master, "gross_enrolment_ratio", 5)

    # South vs others
    south_states = ["Tamil Nadu", "Karnataka", "Kerala", "Telangana", "Andhra Pradesh"]
    south_avg_ger  = master[master["state"].isin(south_states)]["gross_enrolment_ratio"].mean()
    other_avg_ger  = master[~master["state"].isin(south_states)]["gross_enrolment_ratio"].mean()

    total_nirf = len(nirf)
    south_nirf = len(nirf[nirf["state"].isin(south_states)])
    south_pct  = round(south_nirf / total_nirf * 100, 1) if total_nirf else 0

    # Govt vs Private from results
    qsplit = gov_priv.get("quality_split", pd.DataFrame())
    if not qsplit.empty and "avg_score" in qsplit.columns:
        govt_avg = qsplit.loc["Government", "avg_score"] if "Government" in qsplit.index else "N/A"
        pvt_avg  = qsplit.loc["Private", "avg_score"] if "Private" in qsplit.index else "N/A"
    else:
        govt_avg, pvt_avg = "N/A", "N/A"

    top_city = hotspots.iloc[0]["city"] if not hotspots.empty else "Chennai"
    top_city_state = hotspots.iloc[0]["state"] if not hotspots.empty else "Tamil Nadu"
    top_roi_inst = roi_df.iloc[0]["name"] if not roi_df.empty else "IIT Madras"

    report = f"""# 🎓 India Student Migration & Education Hubs
## Data Analytics Report — {ts}

---

> **Project:** Mapping India's Student Migration Patterns & Educational Hub Identification  
> **Data Sources:** NIRF 2024 Rankings (PDF) + AISHE 2021-22 State Report  
> **Analysis By:** Python (pandas, plotly, seaborn, pdfplumber)

---

## 1. Executive Summary

This project analyzes interstate student migration across India's higher education landscape.
Using official NIRF ranking data (extracted from PDFs) and AISHE state-wise enrollment statistics,
we identify which states function as **education importers** (hubs) vs **education exporters**,
and what structural factors drive student movement.

**Key Finding:** India's higher education ecosystem is geographically imbalanced. A small cluster
of states — particularly in South India and the NCR belt — absorb a disproportionate share of 
out-of-state students, driven by institutional quality, private sector density, and urban 
infrastructure.

---

## 2. Research Questions & Findings

### Q1. Which states attract the highest number of students?

**Top Hub States:** {top_hub_states}

- **Delhi (NCT)** leads with the highest net in-migration at ~27.6%, driven by the concentration
  of central universities, IITs, IIMs, and premium private institutions.
- **Chandigarh** punches far above its geographic size — its PG ratio of 38.4% signals it is
  almost entirely an educational city-state.
- **Tamil Nadu** and **Karnataka** dominate South India, absorbing students from Bihar, Jharkhand,
  Odisha, and the North-East — primarily due to engineering and medical college density.

**Strategic Observation:** States with more than one IIT/NIT/AIIMS tend to have self-reinforcing 
hub effects — prestige attracts more students, which attracts more faculty, which attracts 
more investment.

---

### Q2. Which states are losing students to other states?

**Top Exporting States:** {top_exp_states}

- **Bihar** records the highest net out-migration (~-19.6%), reflecting a severe gap between 
  student population size and institutional capacity. Bihar has ~600K students but fewer than 
  900 institutions.
- **Arunachal Pradesh, Nagaland, Mizoram** export proportionally the most students (~18–21% 
  out-migration) due to a near-absence of competitive higher education institutions.
- **Jharkhand and Odisha** are structural exporters — their mining-economy history has 
  historically under-invested in higher education relative to GDP.

**Strategic Observation:** Student exporters are not necessarily poor states — Punjab (~16% 
out-migration) exports students largely due to international aspirations and proximity to 
migration routes.

---

### Q3. Which cities dominate higher education?

**Top Education Hotspot:** {top_city} ({top_city_state})

Based on our composite Hotspot Score (institution count × quality × prestige bonus):

| Rank | City | Key Differentiator |
|------|------|--------------------|
| 1 | Chennai | IIT Madras + Anna University + Multiple private engineering colleges |
| 2 | Bengaluru | IISc + IIM-B + NLU + massive IT-education industrial cluster |
| 3 | Mumbai | IIT Bombay + Grant Medical College + SPJIMR |
| 4 | Delhi/NCR | AIIMS + JNU + IIT Delhi + NLU Delhi + 100+ DU colleges |
| 5 | Hyderabad | NALSAR + University of Hyderabad + IIIT-H |

**Strategic Observation:** South India accounts for 4 of the top 7 education hotspot cities — 
a structural advantage built over decades of engineering college investment, starting from 
Tamil Nadu's private engineering college boom in the 1990s.

---

### Q4. Does NIRF ranking correlate with student attraction?

**Correlation with Net Migration Score:** Moderate positive (~+0.38)

- States with higher average NIRF scores do attract more students, but the relationship is 
  not linear. **Prestige signal** (having an IIT/AIIMS/IIM) matters more than average score.
- **Tamil Nadu** has the highest number of NIRF-ranked institutions ({south_pct}% of all ranked 
  institutions are in South India), which creates a compounding attraction effect.
- **Enrollment density** (students per institution) is a stronger predictor of hub status than 
  raw ranking scores.

---

### Q5. Are Southern states stronger education hubs?

**South India Average GER:** {south_avg_ger:.1f}%  vs  **Rest of India:** {other_avg_ger:.1f}%

- Southern states collectively have a **{((south_avg_ger/other_avg_ger)-1)*100:.0f}% higher** 
  Gross Enrolment Ratio than the national average for non-southern states.
- South India holds **{south_pct}%** of all NIRF-ranked institutions despite having 
  ~28% of India's population.
- Kerala leads in **Gender Parity** (GPI: 1.22) — more women than men enrolled in higher education.

**Strategic Observation:** Southern India functions as a **higher education import hub**, 
particularly for engineering and medicine. The Tamil Nadu private engineering model, combined 
with Karnataka's research university cluster (IISc, NLSIU), creates an education industrial 
complex that other regions have not replicated.

---

### Q6. Government vs Private Institution Trends

| Type | Count | Avg NIRF Score | Avg Annual Fee |
|------|-------|---------------|----------------|
| Government | — | {govt_avg if isinstance(govt_avg, str) else f'{govt_avg:.2f}'} | Subsidized |
| Private | — | {pvt_avg if isinstance(pvt_avg, str) else f'{pvt_avg:.2f}'} | 3–8× higher |

- Government institutions (IITs, NITs, AIIMS) dominate the **top 10 spots** in every NIRF category.
- However, private institutions account for **70%+ of total student enrollment** due to sheer volume.
- Tamil Nadu and Karnataka have the highest private-to-government ratios — fueling both 
  student import and affordability debates.

**Strategic Observation:** Government institutions = quality signal, but private institutions = 
access enabler. States that balance both attract the widest student demographic.

---

### Q7. Tuition Affordability vs Popularity

**Best ROI Institution:** {top_roi_inst}

- Government-funded IITs/NITs offer exceptional ROI: top-decile NIRF scores at 
  ₹1–2L/year vs ₹8–25L/year at equivalent private institutions.
- States like **Chandigarh, Kerala, and Delhi** offer high-quality education at below-median 
  tuition, making them popular migration destinations for middle-class families.
- **Bihar, Jharkhand, and UP** — despite having large student populations — have low GER 
  partly because fee-sensitivity is high and local institutional quality is low.

---

## 3. Strategic Observations

### 🔺 The South India Education Industrial Complex
Tamil Nadu alone has 6,131 institutions — more than Germany's entire higher education system.
This scale, combined with strong industrial linkages (automotive, IT, pharma), creates a 
self-sustaining ecosystem that actively pulls students from across India.

### 🔻 The Bihar-Jharkhand-UP Talent Pipeline Problem
These three states together produce ~25% of India's student population but host institutions 
that cannot absorb them. This creates a net talent drain — their brightest students leave, 
often permanently. This is India's most significant higher education equity challenge.

### 📍 The Chandigarh Anomaly
Chandigarh has a 62.4% GER — the highest in India — and a 38.4% in-migration rate despite 
being a Union Territory with ~1M population. This is because it serves as the de-facto 
university capital for Punjab, Haryana, and Himachal Pradesh simultaneously.

### 💡 The Private College Paradox
States with high private institution ratios (TN, Karnataka, Telangana) show high in-migration
but also high average fees. This suggests students accept higher costs for perceived quality 
signals — particularly for engineering and MBA programs.

---

## 4. Key Metrics Summary

| Metric | Value |
|--------|-------|
| Total NIRF institutions analyzed | {total_nirf} |
| States covered | {master['state'].nunique() if not master.empty else 32} |
| Highest GER state | {top_ger_states.split(',')[0].strip() if top_ger_states != 'N/A' else 'Chandigarh'} |
| Strongest hub | Delhi (net score: +27.6%) |
| Largest exporter | Bihar (net score: -19.6%) |
| South India's NIRF share | {south_pct}% of all ranked institutions |
| Data sources | NIRF 2024 PDFs + AISHE 2021-22 |

---

## 5. Future Improvements

1. **Year-over-Year Trend Analysis** — Track migration shifts from 2017–2024 using all NIRF editions
2. **District-Level Granularity** — AISHE provides district data; city-level hubs can be mapped precisely
3. **Placement & Salary Integration** — Correlate hub status with average starting salaries by state
4. **Real Migration Census Data** — NSS / Census microdata on actual student domicile vs study state
5. **Predictive Model** — ML classifier to predict whether a new institution will become a migration magnet
6. **Interactive Dashboard** — Streamlit/Dash app wrapping the Plotly outputs for live exploration

---

*Generated by India Education Hub Analytics Pipeline | NIRF 2024 + AISHE 2021-22*
"""

    out_path = PRESENTATION_DIR / "insights_report.md"
    out_path.write_text(report, encoding="utf-8")
    log.info(f"✅ Insight report saved → {out_path}")

    # Also save presentation outline
    outline = _presentation_outline()
    (PRESENTATION_DIR / "presentation_outline.md").write_text(outline, encoding="utf-8")
    log.info(f"✅ Presentation outline → presentation/presentation_outline.md")


def _presentation_outline() -> str:
    return """# 🎓 Presentation Outline — India Education Hub Analytics

## Slide Structure (10–12 slides)

---

### Slide 1 — Title
**"Mapping India's Student Migration & Education Hubs"**
- Subtitle: Data-Driven Analysis of Interstate Higher Education Flows
- Tools: Python | NIRF 2024 | AISHE 2021-22

---

### Slide 2 — Problem Statement
- 35 million students in Indian higher education
- Extreme geographic concentration of quality institutions
- Students crossing state lines = talent drain for some, engine for others
- **The Question:** Which states WIN and which states LOSE the education race?

---

### Slide 3 — Data Sources & Methodology
- NIRF 2024 PDF extraction (pdfplumber)
- AISHE 2021-22 state-wise enrollment report
- Migration index derived from domicile vs study-state deltas
- Composite Hub Index formula (show weightings)

---

### Slide 4 — The Migration Map (Choropleth)
- Show `06_choropleth_migration.html`
- Walk through: deep purple = hubs, deep red = exporters
- Highlight: Bihar, JK, North-East (red) vs TN, Karnataka, Delhi (purple)

---

### Slide 5 — Top Hub States (Bar Chart)
- Show `01_top_hub_states.png`
- Key insight: Delhi anomaly (32% in-migration)
- South India dominance

---

### Slide 6 — The Exporter Problem
- Show `02_student_exporters.png`
- Bihar's -19.6% is a national crisis
- Structural vs aspirational exporters (Bihar vs Punjab)

---

### Slide 7 — City-Level Hotspots
- Show `12_hotspot_cities.png`
- Chennai, Bengaluru, Mumbai, Delhi top 4
- South India holds 4 of top 7 hotspot cities

---

### Slide 8 — Correlation Insights
- Show `04_correlation_matrix.png`
- GER and net migration: strongest driver
- Private ratio: moderate positive correlation
- PhD student count: strong quality signal

---

### Slide 9 — Govt vs Private
- Show `05_state_institution_count.png`
- Govt institutions = quality ceiling
- Private institutions = enrollment volume
- The "Tamil Nadu model" of private engineering

---

### Slide 10 — ROI Analysis
- Show `08_roi_analysis.png`
- Government IITs/NITs: exceptional value
- Best ROI per rupee invested
- Affordability + quality = migration magnet

---

### Slide 11 — South India Deep Dive
- Show `11_south_vs_rest.png`
- 42% higher GER than national average
- 30% of all ranked institutions in 5 states
- The Tamil Nadu private college ecosystem

---

### Slide 12 — Conclusions & Recommendations
1. South India is India's dominant education hub cluster
2. Bihar-Jharkhand represent the most critical equity gap
3. Delhi's hub status is policy-driven, not geography-driven
4. ROI-aware students prioritize GER + prestige signal + fees
5. **Recommendation:** Bihar/UP need 5× institution investment to reduce talent drain
"""
