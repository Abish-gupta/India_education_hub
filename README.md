# 🎓 India Student Migration & Education Hubs

> **Portfolio-grade data analytics project** mapping interstate student migration patterns and identifying which Indian states function as higher education hubs.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Pandas](https://img.shields.io/badge/Pandas-2.2-green?style=flat-square)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-purple?style=flat-square)
![Data](https://img.shields.io/badge/Source-NIRF%202024%20%2B%20AISHE%202021--22-orange?style=flat-square)

---

## Problem Statement

India's 35 million higher education students are not uniformly distributed. Some states attract massive student inflows (education hubs), while others hemorrhage talent to distant states (education exporters). This project quantifies those flows, identifies the structural drivers, and ranks every Indian state on an **Education Hub Index**.

**Key Questions:**
1. Which states attract the most out-of-state students?
2. Which states are losing students — and why?
3. Which cities dominate higher education?
4. Does NIRF ranking predict student attraction?
5. Is South India structurally dominant?
6. Government vs private institution dynamics
7. Tuition affordability vs enrollment popularity

---

## Data Sources

| Source | What | How |
|--------|------|-----|
| **NIRF 2024** | College rankings, scores, city, state, type | PDF extraction (`pdfplumber`) |
| **AISHE 2021-22** | State-wise enrollment, GER, GPI, institutions | PDF + curated seed |
| **Migration Index** | Net in/out migration per state | Derived from AISHE domicile tables |

**PDF-first strategy:** Official government PDFs are more stable than HTML pages. `pdfplumber` extracts tables directly. HTML scraping used only as secondary fallback.

---

## Methodology

```
PDF Reports (NIRF + AISHE)
        ↓
  PDF Table Extraction (pdfplumber)
        ↓
  Data Cleaning (state normalization, imputation, type inference)
        ↓
  Feature Engineering (Hub Index, ROI Score, Hotspot Score, Migration Score)
        ↓
  Statistical Analysis (correlations, comparisons, segmentation)
        ↓
  Visualizations (12 charts: bar, heatmap, choropleth, sankey, bubble)
        ↓
  Insight Report (Markdown) + Presentation Outline
```

**Education Hub Index (composite):**
```
Hub Index = 0.40 × Net Migration Score (norm)
          + 0.30 × Gross Enrolment Ratio (norm)
          + 0.20 × Avg NIRF Score (norm)
          + 0.10 × Private Institution Ratio
```

---

## Key Insights

### 🏆 Top Hub States
Delhi, Chandigarh, Tamil Nadu, Karnataka, Telangana consistently rank as the top student-attracting states. Delhi alone shows ~27.6% net in-migration.

### 📤 Major Exporters
Bihar (-19.6%), Arunachal Pradesh (-15.5%), Mizoram (-13.9%) lose the most students proportionally. Bihar's structural gap — ~600K students, only ~870 institutions — is the starkest case of institutional underinvestment in India.

### 🌴 South India Dominance
South India (5 states) holds ~30% of all NIRF-ranked institutions despite ~28% of population. Average GER is ~42% vs ~31% for the rest of India. Tamil Nadu alone has 6,131 colleges.

### 💰 ROI Leaders
Government IITs/NITs deliver the highest education ROI — top-decile NIRF scores at ₹1-2L/year vs ₹8-25L/year at equivalent private institutions.

### 🔥 Top Hotspot Cities
Chennai → Bengaluru → Mumbai → Delhi/NCR → Hyderabad

---

## Visualizations Generated

| File | Type | Shows |
|------|------|-------|
| `01_top_hub_states.png` | Horizontal bar | Net migration by state |
| `02_student_exporters.png` | Horizontal bar | Exporter states |
| `03_enrollment_heatmap.png` | Heatmap | Enrollment by region × state |
| `04_correlation_matrix.png` | Heatmap | Feature correlations |
| `05_state_institution_count.png` | Grouped bar | Govt vs private by state |
| `06_choropleth_migration.html` | Interactive map | India migration choropleth |
| `07_hub_index_bubble.html` | Bubble chart | GER vs migration, sized by enrollment |
| `08_roi_analysis.png` | Horizontal bar | Best value institutions |
| `09_gender_parity.png` | Horizontal bar | GPI by state |
| `10_sankey_migration.html` | Sankey diagram | Exporter → Hub flows |
| `11_south_vs_rest.png` | Grouped bar | South India vs rest |
| `12_hotspot_cities.png` | Horizontal bar | City hotspot scores |

---

## Folder Structure

```
india_education_hub/
│
├── data/
│   ├── raw/              ← Downloaded PDFs + extracted CSVs
│   └── processed/        ← Cleaned & merged master dataset
│
├── scraper/
│   ├── pdf_scraper.py    ← PRIMARY: pdfplumber PDF extraction
│   ├── nirf_scraper.py   ← FALLBACK: HTML + seed dataset
│   └── aishe_scraper.py  ← AISHE state data + migration index
│
├── src/
│   ├── data_cleaner.py   ← Normalization, imputation, feature engineering
│   ├── analyzer.py       ← All 8 research question analyses
│   ├── visualizer.py     ← 12 production-ready charts
│   └── report_generator.py ← Markdown insight report
│
├── notebooks/
│   └── eda.ipynb         ← Exploratory analysis notebook
│
├── visuals/              ← All chart outputs (PNG + HTML)
├── presentation/         ← insights_report.md + outline
│
├── main.py               ← Run everything
├── requirements.txt
└── README.md
```

---

## Installation

```bash
# 1. Clone / download project
cd india_education_hub

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## How to Run

```bash
# Full pipeline (collection → cleaning → analysis → visuals → report)
python main.py

# Individual modules
python scraper/pdf_scraper.py       # PDF extraction only
python scraper/nirf_scraper.py      # NIRF HTML/seed scraping
python scraper/aishe_scraper.py     # AISHE data + migration index

# Jupyter notebook (EDA)
jupyter notebook notebooks/eda.ipynb
```

**Outputs:**
- `data/processed/master_dataset.csv` — merged analytical dataset
- `visuals/` — all 12 charts
- `presentation/insights_report.md` — full written analysis
- `pipeline.log` — execution trace
---

## Tech Stack

`Python 3.11` · `pandas` · `numpy` · `pdfplumber` · `requests` · `BeautifulSoup4` · `matplotlib` · `seaborn` · `plotly` · `geopandas`


