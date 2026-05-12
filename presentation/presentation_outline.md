# 🎓 Presentation Outline — India Education Hub Analytics

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
