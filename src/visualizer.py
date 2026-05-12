"""
src/visualizer.py
=================
PIXEL | Visualization Layer — Professional, presentation-ready charts.
All visuals saved to visuals/ directory as high-res PNGs + HTML (Plotly).
"""

import logging
import warnings
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

warnings.filterwarnings("ignore")
matplotlib.rcParams["figure.dpi"] = 150
log = logging.getLogger(__name__)

VISUALS_DIR = Path(__file__).parent.parent / "visuals"
VISUALS_DIR.mkdir(parents=True, exist_ok=True)

# ── Design System ──────────────────────────────────────────
PALETTE = {
    "primary":    "#4F46E5",  # Indigo 600
    "secondary":  "#0EA5E9",  # Sky 500
    "accent":     "#F43F5E",  # Rose 500
    "warn":       "#F59E0B",  # Amber 500
    "bg":         "#F9FAFB",  # Gray 50
    "surface":    "#FFFFFF",  # White
    "text":       "#111827",  # Gray 900
    "muted":      "#9CA3AF",  # Gray 400
}

HUB_COLORS = {
    "Major Hub":     "#4F46E5",
    "Hub":           "#10B981",  # Emerald
    "Minor Hub":     "#0EA5E9",
    "Neutral":       "#94A3B8",  # Slate 400
    "Exporter":      "#F59E0B",
    "Major Exporter":"#EF4444",  # Red 500
}

REGION_COLORS = {
    "South India":       "#4F46E5",
    "North India":       "#0EA5E9",
    "West India":        "#F43F5E",
    "East India":        "#F59E0B",
    "Central India":     "#10B981",
    "North-East India":  "#8B5CF6",
    "North-West India":  "#06B6D4",
}

def _light_fig(figsize=(14, 7)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["surface"])
    ax.tick_params(colors=PALETTE["text"], labelsize=10)
    ax.xaxis.label.set_color(PALETTE["text"])
    ax.yaxis.label.set_color(PALETTE["text"])
    ax.title.set_color(PALETTE["text"])
    for spine in ax.spines.values():
        spine.set_edgecolor(PALETTE["muted"])
        spine.set_linewidth(0.5)
    return fig, ax

def _save(fig, name: str):
    path = VISUALS_DIR / name
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    log.info(f"  ✔ Saved → visuals/{name}")


# ── Chart 1: Top Student-Attracting States (Bar) ───────────
def chart_top_hub_states(migration: pd.DataFrame):
    hubs = migration.sort_values("net_migration_score", ascending=False).head(15)
    colors = [HUB_COLORS.get(c, PALETTE["primary"]) for c in hubs["hub_category"]]

    fig, ax = _light_fig((14, 7))
    bars = ax.barh(hubs["state"][::-1], hubs["net_migration_score"][::-1],
                   color=colors[::-1], edgecolor="none", height=0.65)

    # Value labels
    for bar, val in zip(bars, hubs["net_migration_score"][::-1]):
        ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height()/2,
                f"+{val:.1f}%", va="center", color=PALETTE["text"], fontsize=9, fontweight="bold")

    ax.set_xlabel("Net Student In-Migration (%)", fontsize=11, labelpad=10)
    ax.set_title("🎓 Top Student-Attracting States in India\n(Net Migration Score — Higher = More Students Drawn In)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.axvline(0, color=PALETTE["muted"], lw=1, linestyle="--", alpha=0.5)
    ax.grid(axis="x", color=PALETTE["muted"], alpha=0.2, linestyle="--")

    # Legend
    legend_patches = [mpatches.Patch(color=v, label=k) for k, v in HUB_COLORS.items() if k in hubs["hub_category"].values]
    ax.legend(handles=legend_patches, loc="lower right", facecolor=PALETTE["surface"],
              edgecolor=PALETTE["muted"], labelcolor=PALETTE["text"], fontsize=9)

    fig.text(0.99, 0.01, "Source: AISHE 2021-22 | Analysis: India Education Hub Project",
             ha="right", fontsize=8, color=PALETTE["muted"])
    _save(fig, "01_top_hub_states.png")


# ── Chart 2: Major Student Exporters (Bar) ─────────────────
def chart_student_exporters(migration: pd.DataFrame):
    exporters = migration.sort_values("net_migration_score").head(12)
    colors = [HUB_COLORS.get(c, PALETTE["warn"]) for c in exporters["hub_category"]]

    fig, ax = _light_fig((14, 7))
    bars = ax.barh(exporters["state"][::-1], exporters["net_migration_score"][::-1],
                   color=colors[::-1], edgecolor="none", height=0.65)

    for bar, val in zip(bars, exporters["net_migration_score"][::-1]):
        ax.text(bar.get_width() - 0.4, bar.get_y() + bar.get_height()/2,
                f"{val:.1f}%", va="center", ha="right", color=PALETTE["bg"],
                fontsize=9, fontweight="bold")

    ax.set_xlabel("Net Student Out-Migration (%)", fontsize=11, labelpad=10)
    ax.set_title("📤 Major Student-Exporting States\n(States Losing Students to Other Educational Hubs)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.axvline(0, color=PALETTE["muted"], lw=1, linestyle="--", alpha=0.5)
    ax.grid(axis="x", color=PALETTE["muted"], alpha=0.2, linestyle="--")
    fig.text(0.99, 0.01, "Source: AISHE 2021-22 | Analysis: India Education Hub Project",
             ha="right", fontsize=8, color=PALETTE["muted"])
    _save(fig, "02_student_exporters.png")


# ── Chart 3: Enrollment Heatmap by Region ─────────────────
def chart_enrollment_heatmap(aishe: pd.DataFrame):
    pivot_data = aishe[aishe["region"].notna()].copy()
    region_state = pivot_data.pivot_table(
        index="region", columns="state",
        values="total_enrollment_k", aggfunc="sum"
    )

    fig, ax = plt.subplots(figsize=(20, 6), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["surface"])

    cmap = sns.color_palette("mako", as_cmap=True)
    sns.heatmap(
        region_state.fillna(0), ax=ax, cmap=cmap,
        linewidths=0.5, linecolor=PALETTE["bg"],
        annot=False, fmt=".0f",
        cbar_kws={"label": "Enrollment (Thousands)", "shrink": 0.8}
    )

    ax.set_title("📊 Student Enrollment Heatmap — State × Region\n(AISHE 2021-22)",
                 fontsize=14, fontweight="bold", color=PALETTE["text"], pad=15)
    ax.tick_params(colors=PALETTE["text"], labelsize=8)
    ax.set_xlabel("State", fontsize=10, color=PALETTE["text"])
    ax.set_ylabel("Region", fontsize=10, color=PALETTE["text"])
    plt.xticks(rotation=45, ha="right")
    _save(fig, "03_enrollment_heatmap.png")


# ── Chart 4: Correlation Matrix ────────────────────────────
def chart_correlation_matrix(master: pd.DataFrame):
    key_cols = ["total_enrollment_k", "gross_enrolment_ratio", "net_migration_score",
                "num_ranked_institutions", "avg_nirf_score", "private_ratio",
                "gpi", "education_hub_index", "govt_ratio"]
    available = [c for c in key_cols if c in master.columns]
    corr = master[available].corr()

    labels = {
        "total_enrollment_k": "Total Enrollment",
        "gross_enrolment_ratio": "Gross Enrol. Ratio",
        "net_migration_score": "Net Migration Score",
        "num_ranked_institutions": "# Ranked Institutions",
        "avg_nirf_score": "Avg NIRF Score",
        "private_ratio": "Private Inst. Ratio",
        "gpi": "Gender Parity Index",
        "education_hub_index": "Hub Index",
        "govt_ratio": "Govt Inst. Ratio",
    }
    corr = corr.rename(index=labels, columns=labels)

    fig, ax = plt.subplots(figsize=(12, 10), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["surface"])

    mask = np.triu(np.ones_like(corr, dtype=bool))
    cmap = sns.diverging_palette(250, 15, s=85, l=40, n=9, as_cmap=True)
    sns.heatmap(corr, ax=ax, mask=mask, cmap=cmap, center=0,
                annot=True, fmt=".2f", annot_kws={"size": 9},
                linewidths=0.5, linecolor=PALETTE["bg"],
                cbar_kws={"shrink": 0.8, "label": "Pearson Correlation"})

    ax.set_title("🔗 Correlation Matrix — Education Drivers\nWhat factors predict student migration?",
                 fontsize=14, fontweight="bold", color=PALETTE["text"], pad=15)
    ax.tick_params(colors=PALETTE["text"], labelsize=9)
    plt.xticks(rotation=45, ha="right")
    _save(fig, "04_correlation_matrix.png")


# ── Chart 5: State-wise NIRF Institution Count ─────────────
def chart_state_institution_count(nirf: pd.DataFrame):
    state_counts = (nirf.groupby(["state", "type"])
                    .size().unstack(fill_value=0).reset_index())

    # Sort by total
    state_counts["total"] = state_counts.get("Government", 0) + state_counts.get("Private", 0)
    state_counts = state_counts.sort_values("total", ascending=False).head(20)

    fig, ax = _light_fig((14, 8))
    x = np.arange(len(state_counts))
    w = 0.35

    if "Government" in state_counts.columns:
        ax.bar(x - w/2, state_counts["Government"], w, label="Government",
               color=PALETTE["secondary"], alpha=0.9, edgecolor="none")
    if "Private" in state_counts.columns:
        ax.bar(x + w/2, state_counts["Private"], w, label="Private",
               color=PALETTE["accent"], alpha=0.9, edgecolor="none")

    ax.set_xticks(x)
    ax.set_xticklabels(state_counts["state"], rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Number of NIRF-Ranked Institutions", fontsize=11)
    ax.set_title("🏛️ Government vs Private Ranked Institutions by State\n(NIRF 2024)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.legend(facecolor=PALETTE["surface"], edgecolor=PALETTE["muted"],
              labelcolor=PALETTE["text"], fontsize=10)
    ax.grid(axis="y", color=PALETTE["muted"], alpha=0.2, linestyle="--")
    _save(fig, "05_state_institution_count.png")


# ── Chart 6: Plotly Choropleth Map ─────────────────────────
def chart_choropleth_migration(migration: pd.DataFrame):
    """Interactive India choropleth using Plotly."""
    fig = px.choropleth(
        migration,
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
        locations="state",
        featureidkey="properties.ST_NM",
        color="net_migration_score",
        color_continuous_scale=["#D63031", "#FDCB6E", "#FFFFFF", "#00B894", "#6C5CE7"],
        color_continuous_midpoint=0,
        range_color=(-25, 40),
        title="🗺️ India Student Migration Map<br><sub>Net Migration Score: Purple=Hub, Red=Exporter</sub>",
        hover_data=["hub_category", "in_migration_pct", "out_migration_pct"],
    )
    fig.update_geos(
        visible=False, fitbounds="locations",
        bgcolor=PALETTE["bg"]
    )
    fig.update_layout(
        geo=dict(bgcolor=PALETTE["bg"]),
        paper_bgcolor=PALETTE["bg"],
        plot_bgcolor=PALETTE["bg"],
        font=dict(color=PALETTE["text"], family="Inter, sans-serif"),
        title_font_size=18,
        coloraxis_colorbar=dict(title="Net Migration Score"),
        margin=dict(l=0, r=0, t=60, b=0),
        height=600,
    )
    path = VISUALS_DIR / "06_choropleth_migration.html"
    fig.write_html(str(path))
    log.info(f"  ✔ Saved → visuals/06_choropleth_migration.html")


# ── Chart 7: Education Hub Index — Bubble Chart ────────────
def chart_hub_index_bubble(master: pd.DataFrame):
    df = master.dropna(subset=["education_hub_index", "gross_enrolment_ratio",
                                "net_migration_score"]).copy()
    df["bubble_size"] = df["total_enrollment_k"].fillna(50).clip(upper=2000)
    df["region"] = df["region"].fillna("Other")

    fig = px.scatter(
        df,
        x="gross_enrolment_ratio",
        y="net_migration_score",
        size="bubble_size",
        color="region",
        color_discrete_map=REGION_COLORS,
        text="state",
        title="🎯 Education Hub Landscape<br><sub>Bubble Size = Total Enrollment | X = GER | Y = Net Migration</sub>",
        labels={
            "gross_enrolment_ratio": "Gross Enrolment Ratio (%)",
            "net_migration_score": "Net Migration Score",
            "region": "Region",
        },
        hover_data=["education_hub_index", "hub_category", "total_institutions"],
        size_max=60,
    )
    fig.update_traces(textposition="top center", textfont_size=10)
    fig.update_layout(
        paper_bgcolor=PALETTE["bg"],
        plot_bgcolor=PALETTE["surface"],
        font=dict(color=PALETTE["text"], family="Inter, sans-serif"),
        title_font_size=18,
        height=650,
        xaxis=dict(gridcolor=PALETTE["muted"], gridwidth=0.3),
        yaxis=dict(gridcolor=PALETTE["muted"], gridwidth=0.3),
    )
    fig.add_hline(y=0, line_dash="dash", line_color=PALETTE["muted"], opacity=0.6)
    path = VISUALS_DIR / "07_hub_index_bubble.html"
    fig.write_html(str(path))
    log.info(f"  ✔ Saved → visuals/07_hub_index_bubble.html")


# ── Chart 8: ROI Bar Chart ─────────────────────────────────
def chart_roi(roi_df: pd.DataFrame):
    top = roi_df.head(15).copy()
    colors = [PALETTE["secondary"] if t == "Government" else PALETTE["accent"]
              for t in top["type"]]

    fig, ax = _light_fig((14, 7))
    bars = ax.barh(
        [f"{n[:35]}..." if len(n) > 35 else n for n in top["name"]][::-1],
        top["roi_score"][::-1],
        color=colors[::-1], edgecolor="none", height=0.65
    )

    for bar, val in zip(bars, top["roi_score"][::-1]):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                f"{val:.1f}", va="center", color=PALETTE["text"], fontsize=8)

    ax.set_xlabel("ROI Score (NIRF Score / Annual Fee in Lakhs)", fontsize=11, labelpad=10)
    ax.set_title("💰 Best Value-for-Money Institutions\n(Higher ROI Score = More Education per Rupee)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(axis="x", color=PALETTE["muted"], alpha=0.2, linestyle="--")

    legend_patches = [
        mpatches.Patch(color=PALETTE["secondary"], label="Government"),
        mpatches.Patch(color=PALETTE["accent"], label="Private"),
    ]
    ax.legend(handles=legend_patches, facecolor=PALETTE["surface"],
              edgecolor=PALETTE["muted"], labelcolor=PALETTE["text"])
    _save(fig, "08_roi_analysis.png")


# ── Chart 9: Gender Parity Comparison ─────────────────────
def chart_gender_parity(aishe: pd.DataFrame):
    df = aishe.sort_values("gpi", ascending=False).head(20)

    fig, ax = _light_fig((14, 7))
    colors = [PALETTE["accent"] if g >= 1 else PALETTE["primary"] for g in df["gpi"]]
    bars = ax.barh(df["state"][::-1], df["gpi"][::-1],
                   color=colors[::-1], edgecolor="none", height=0.65)

    ax.axvline(1.0, color=PALETTE["warn"], lw=2, linestyle="--", alpha=0.8, label="GPI = 1 (Parity)")
    for bar, val in zip(bars, df["gpi"][::-1]):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                f"{val:.3f}", va="center", color=PALETTE["text"], fontsize=8)

    ax.set_xlabel("Gender Parity Index (Female/Male Enrollment)", fontsize=11, labelpad=10)
    ax.set_title("⚥ Gender Parity in Higher Education\n(>1.0 = Female-favoring | <1.0 = Male-favoring)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(axis="x", color=PALETTE["muted"], alpha=0.2, linestyle="--")
    ax.legend(facecolor=PALETTE["surface"], edgecolor=PALETTE["muted"], labelcolor=PALETTE["text"])
    _save(fig, "09_gender_parity.png")


# ── Chart 10: Sankey Migration Flow ───────────────────────
def chart_sankey_migration(migration: pd.DataFrame):
    """Sankey diagram: Student Exporters → Student Hubs."""
    exporters = migration[migration["net_migration_score"] < -8].nsmallest(6, "net_migration_score")
    hubs = migration[migration["net_migration_score"] > 8].nlargest(6, "net_migration_score")

    all_nodes = list(exporters["state"]) + list(hubs["state"])
    node_idx = {n: i for i, n in enumerate(all_nodes)}

    # Simulate flow values proportional to migration scores
    sources, targets, values, colors = [], [], [], []
    for _, exp_row in exporters.iterrows():
        for _, hub_row in hubs.iterrows():
            flow = abs(exp_row["net_migration_score"]) * hub_row["net_migration_score"] * 0.02
            if flow > 0:
                sources.append(node_idx[exp_row["state"]])
                targets.append(node_idx[hub_row["state"]])
                values.append(round(flow, 2))
                colors.append("rgba(108,92,231,0.3)")

    node_colors = ["rgba(214,48,49,0.8)"] * len(exporters) + ["rgba(108,92,231,0.8)"] * len(hubs)

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=20, thickness=20,
            line=dict(color="black", width=0.5),
            label=all_nodes,
            color=node_colors,
            hovertemplate="%{label}<extra></extra>",
        ),
        link=dict(source=sources, target=targets, value=values, color=colors),
    ))

    fig.update_layout(
        title_text="🌊 Student Migration Flow Diagram<br><sub>Exporting States → Receiving Hub States</sub>",
        font=dict(size=13, color=PALETTE["text"], family="Inter, sans-serif"),
        paper_bgcolor=PALETTE["bg"],
        plot_bgcolor=PALETTE["bg"],
        title_font_size=18,
        height=550,
    )

    path = VISUALS_DIR / "10_sankey_migration.html"
    fig.write_html(str(path))
    log.info(f"  ✔ Saved → visuals/10_sankey_migration.html")


# ── Chart 11: South vs Rest Comparison ────────────────────
def chart_south_vs_rest(master: pd.DataFrame):
    south_states = ["Tamil Nadu", "Karnataka", "Kerala", "Telangana", "Andhra Pradesh", "Puducherry"]
    df = master.copy()
    df["group"] = df["state"].apply(
        lambda s: "🌴 South India" if s in south_states else "🗺️ Rest of India"
    )

    metrics = ["gross_enrolment_ratio", "avg_nirf_score", "private_ratio"]
    avail = [m for m in metrics if m in df.columns]
    grouped = df.groupby("group")[avail].mean()

    fig, axes = plt.subplots(1, len(avail), figsize=(16, 6), facecolor=PALETTE["bg"])
    if len(avail) == 1:
        axes = [axes]

    titles = {
        "gross_enrolment_ratio": "Gross Enrolment Ratio",
        "avg_nirf_score": "Avg NIRF Score",
        "private_ratio": "Private Inst. Ratio",
    }
    colors = [PALETTE["primary"], PALETTE["secondary"]]

    for ax, metric in zip(axes, avail):
        ax.set_facecolor(PALETTE["surface"])
        bars = ax.bar(grouped.index, grouped[metric], color=colors, edgecolor="none", width=0.5)
        for bar, val in zip(bars, grouped[metric]):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f"{val:.2f}", ha="center", color=PALETTE["text"], fontsize=10, fontweight="bold")
        ax.set_title(titles.get(metric, metric), color=PALETTE["text"], fontsize=11, pad=10)
        ax.tick_params(colors=PALETTE["text"])
        ax.set_facecolor(PALETTE["surface"])
        for spine in ax.spines.values():
            spine.set_edgecolor(PALETTE["muted"])
        ax.grid(axis="y", color=PALETTE["muted"], alpha=0.2, linestyle="--")

    fig.suptitle("🆚 South India vs Rest of India — Education Metrics",
                 fontsize=15, fontweight="bold", color=PALETTE["text"], y=1.02)
    fig.patch.set_facecolor(PALETTE["bg"])
    _save(fig, "11_south_vs_rest.png")


# ── Chart 12: Top Cities Hotspot ──────────────────────────
def chart_hotspot_cities(hotspots: pd.DataFrame):
    top_cities = hotspots.head(15)

    fig, ax = _light_fig((14, 7))
    colors = plt.cm.plasma(np.linspace(0.2, 0.9, len(top_cities)))
    bars = ax.barh(
        top_cities["city"][::-1], top_cities["hotspot_score"][::-1],
        color=colors[::-1], edgecolor="none", height=0.65
    )

    for bar, (_, row) in zip(bars, top_cities[::-1].iterrows()):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                f"{row['hotspot_score']:.1f}  ({row['state']})",
                va="center", color=PALETTE["text"], fontsize=9)

    ax.set_xlabel("Education Hotspot Score", fontsize=11, labelpad=10)
    ax.set_title("🔥 Top Education Hotspot Cities in India\n(Composite: #Institutions + Quality + Prestige Bonus)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(axis="x", color=PALETTE["muted"], alpha=0.2, linestyle="--")
    _save(fig, "12_hotspot_cities.png")


# ── Master Run ─────────────────────────────────────────────

def run_all_visualizations(
    nirf: pd.DataFrame,
    aishe: pd.DataFrame,
    migration: pd.DataFrame,
    master: pd.DataFrame,
    results: dict,
) -> None:
    log.info("\n📊 Generating visualizations...")

    chart_top_hub_states(migration)
    chart_student_exporters(migration)
    chart_enrollment_heatmap(aishe)
    chart_correlation_matrix(master)
    chart_state_institution_count(nirf)
    chart_choropleth_migration(migration)
    chart_hub_index_bubble(master)

    if "roi" in results and not results["roi"].empty:
        chart_roi(results["roi"])

    chart_gender_parity(aishe)
    chart_sankey_migration(migration)
    chart_south_vs_rest(master)

    if "hotspots" in results and not results["hotspots"].empty:
        chart_hotspot_cities(results["hotspots"])

    log.info(f"\n✅ All visualizations saved to: visuals/")
