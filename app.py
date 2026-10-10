from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# NASSAU CANDY | 3D PROFITABILITY COMMAND CENTER
# Expected data file: data/cleaned_nassau_candy.csv
# Run: streamlit run app.py
# ============================================================

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "cleaned_nassau_candy.csv"

st.set_page_config(
    page_title="Nassau Candy | 3D Profitability",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------- UI THEME -------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --bg:#080d19; --panel:#101a2b; --muted:#8fa3c7; --cyan:#53e0ff; --violet:#a78bfa; }
.stApp {
  background:
    radial-gradient(ellipse at 12% 0%, rgba(37,99,235,.20), transparent 34%),
    radial-gradient(ellipse at 92% 12%, rgba(139,92,246,.16), transparent 30%),
    linear-gradient(145deg,#070b14 0%,#0a1222 55%,#090d18 100%);
  color:#eaf2ff; font-family:'DM Sans',sans-serif;
}
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.035em; }
.block-container { padding-top:1.4rem; padding-bottom:2rem; max-width:1600px; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1729,#080d18); border-right:1px solid #1b2b46; }
[data-testid="stMetric"] {
  background:linear-gradient(145deg,rgba(23,39,64,.92),rgba(13,22,39,.95));
  border:1px solid rgba(113,153,210,.22); padding:18px 18px 15px;
  border-radius:18px; box-shadow:0 12px 30px rgba(0,0,0,.22);
}
[data-testid="stMetricLabel"] { color:#9bb1d5 !important; font-size:.82rem; }
[data-testid="stMetricValue"] { color:#f4f8ff !important; font-family:'Space Grotesk',sans-serif; }
.stTabs [data-baseweb="tab-list"] { gap:7px; background:rgba(15,26,44,.75); padding:7px; border-radius:14px; }
.stTabs [data-baseweb="tab"] { background:transparent; border-radius:10px; color:#a8bad7; padding:10px 14px; }
.stTabs [aria-selected="true"] { background:linear-gradient(100deg,#174c70,#42316f) !important; color:white !important; }
div[data-testid="stPlotlyChart"] { border:1px solid rgba(105,143,195,.17); border-radius:16px; overflow:hidden; }
div[data-testid="stDataFrame"] { border:1px solid #22314a; border-radius:12px; }
.hero {
  padding:25px 28px; margin-bottom:20px; border-radius:22px;
  background:linear-gradient(115deg,rgba(17,44,74,.92),rgba(34,26,67,.90) 70%,rgba(11,26,45,.95));
  border:1px solid rgba(105,183,255,.27); box-shadow:0 18px 50px rgba(0,0,0,.25);
}
.hero-kicker { color:#53e0ff; text-transform:uppercase; font-size:.74rem; font-weight:700; letter-spacing:.18em; }
.hero-title { font-family:'Space Grotesk',sans-serif; font-size:clamp(1.7rem,3vw,2.7rem); font-weight:700; line-height:1.08; margin:8px 0; color:#f5f8ff; }
.hero-sub { color:#aabbd8; max-width:850px; font-size:.96rem; }
.section-note { color:#9db0cf; font-size:.9rem; }
.pill { display:inline-block; border:1px solid #2b5275; color:#83e7ff; background:#10283a; padding:5px 10px; border-radius:999px; font-size:.75rem; margin-right:5px; }
</style>
""", unsafe_allow_html=True)

# ------------------------- HELPERS -------------------------
MONEY = "${:,.2f}"
PLOT_BG = "rgba(0,0,0,0)"
GRID = "rgba(133,160,200,.14)"
FONT = "DM Sans, sans-serif"

def fmt_money(value):
    return f"${value:,.0f}"

def style_fig(fig, height=420, legend=True):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=PLOT_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family=FONT, color="#dce8ff"),
        title=dict(font=dict(size=17, color="#edf4ff"), x=.02, xanchor="left"),
        margin=dict(l=20, r=20, t=60, b=35),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) if legend else None,
        hoverlabel=dict(bgcolor="#101b2d", bordercolor="#456080", font=dict(color="#f4f8ff")),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    return fig

@st.cache_data
def load_data(path_string, modified_time):
    df = pd.read_csv(path_string)
    required = ["Order Date", "Sales", "Cost", "Gross Profit", "Units", "Order ID",
                "Product ID", "Product Name", "Division", "Factory"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing required column(s): " + ", ".join(missing))
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    if "Ship Date" in df.columns:
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")
    for col in ["Sales", "Cost", "Gross Profit", "Units"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Order Date", "Sales", "Cost", "Gross Profit", "Units"])
    return df

def product_summary(df):
    p = df.groupby(["Product ID", "Product Name", "Division", "Factory"], as_index=False).agg(
        Sales=("Sales", "sum"),
        Cost=("Cost", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Units=("Units", "sum"),
        Orders=("Order ID", "nunique"),
    )
    p["Gross_Margin"] = np.divide(p["Gross_Profit"], p["Sales"], out=np.zeros(len(p)), where=p["Sales"].to_numpy()!=0)
    p["Profit_per_Unit"] = np.divide(p["Gross_Profit"], p["Units"], out=np.zeros(len(p)), where=p["Units"].to_numpy()!=0)
    p["Revenue_Contribution"] = p["Sales"] / p["Sales"].sum() if p["Sales"].sum() else 0
    p["Profit_Contribution"] = p["Gross_Profit"] / p["Gross_Profit"].sum() if p["Gross_Profit"].sum() else 0
    p["Cost_Ratio"] = np.divide(p["Cost"], p["Sales"], out=np.zeros(len(p)), where=p["Sales"].to_numpy()!=0)
    p["Risk"] = np.select(
        [p["Gross_Margin"] < .20, p["Gross_Margin"] < .50, p["Gross_Margin"] < .60],
        ["Critical", "High", "Watch"], default="Healthy"
    )
    p["Suggested_Action"] = np.select(
        [p["Gross_Margin"] < .20, p["Gross_Margin"] < .50, p["Gross_Margin"] < .60],
        ["Urgent repricing / discontinue review", "Reprice or renegotiate supplier cost", "Monitor and test pricing"],
        default="Maintain / scale selectively"
    )
    return p

def money_table(df, columns):
    formats = {}
    for col in columns:
        if col in df.columns:
            formats[col] = "${:,.2f}"
    if "Gross_Margin" in df.columns: formats["Gross_Margin"] = "{:.1%}"
    if "Cost_Ratio" in df.columns: formats["Cost_Ratio"] = "{:.1%}"
    if "Revenue_Contribution" in df.columns: formats["Revenue_Contribution"] = "{:.1%}"
    if "Profit_Contribution" in df.columns: formats["Profit_Contribution"] = "{:.1%}"
    if "CumShare" in df.columns: formats["CumShare"] = "{:.1%}"
    return df.style.format(formats)

def empty_message():
    st.warning("No records match these filters. Widen the date range or select more divisions.")
    st.stop()

# ------------------------- LOAD -------------------------
if not DATA.exists():
    st.error(f"Dataset not found: `{DATA}`")
    st.markdown("""
    **Expected project structure**
    ```text
    your_project/
    ├── app.py
    └── data/
        └── cleaned_nassau_candy.csv
    ```
    Put `cleaned_nassau_candy.csv` inside the `data` folder, then rerun the app.
    """)
    st.stop()

try:
    raw = load_data(str(DATA), DATA.stat().st_mtime)
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

if raw.empty:
    st.error("The dataset contains no valid transaction rows.")
    st.stop()

# ------------------------- SIDEBAR FILTERS -------------------------
with st.sidebar:
    st.markdown("## 🍬 Control Center")
    st.caption("Nassau Candy · Profitability intelligence")
    st.divider()
    min_date = raw["Order Date"].min().date()
    max_date = raw["Order Date"].max().date()
    date_range = st.date_input(
        "Order date range", value=(min_date, max_date),
        min_value=min_date, max_value=max_date
    )
    divisions_all = sorted(raw["Division"].dropna().astype(str).unique().tolist())
    divisions = st.multiselect("Division", divisions_all, default=divisions_all)
    margin_threshold = st.slider("Margin risk threshold", 0, 100, 50, 1) / 100
    search = st.text_input("Search product", placeholder="e.g. chocolate").strip().lower()
    st.divider()
    st.markdown("**Display settings**")
    chart_height = st.slider("Chart height", 320, 600, 430, 10)
    st.caption("3D charts can be rotated, zoomed, and inspected with hover details.")
    st.caption("Data note: shipment dates are not used to infer delivery time because their range may be inconsistent with order dates.")

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

df = raw[
    raw["Order Date"].dt.date.between(start_date, end_date)
    & raw["Division"].astype(str).isin(divisions)
].copy()

if search:
    df = df[df["Product Name"].astype(str).str.lower().str.contains(search, na=False)]

if df.empty:
    empty_message()

p = product_summary(df)
total_sales = df["Sales"].sum()
total_profit = df["Gross Profit"].sum()
total_cost = df["Cost"].sum()
total_units = df["Units"].sum()
gross_margin = total_profit / total_sales if total_sales else 0
profit_unit = total_profit / total_units if total_units else 0
risk_count = int((p["Gross_Margin"] < margin_threshold).sum())

# ------------------------- HEADER -------------------------
st.markdown(f"""
<div class="hero">
  <div class="hero-kicker">Interactive analytics suite · 3D product intelligence</div>
  <div class="hero-title">Profitability Command Center</div>
  <div class="hero-sub">Nassau Candy Distributor — explore product economics, division performance, margin risk, cost structure, and revenue concentration.</div>
  <div style="margin-top:15px">
    <span class="pill">{len(df):,} transactions</span>
    <span class="pill">{p['Product Name'].nunique():,} products</span>
    <span class="pill">{len(divisions)} divisions selected</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ------------------------- KPI STRIP -------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sales", fmt_money(total_sales))
k2.metric("Gross Profit", fmt_money(total_profit), help="Sales minus recorded cost, based on the dataset's Gross Profit field.")
k3.metric("Gross Margin", f"{gross_margin:.1%}")
k4.metric("Units Sold", f"{total_units:,.0f}")
k5.metric("Profit / Unit", f"${profit_unit:,.2f}")

st.caption(f"Current selection: {start_date:%d %b %Y} — {end_date:%d %b %Y} · Cost base {fmt_money(total_cost)} · {risk_count} products below the {margin_threshold:.0%} margin threshold.")

tabs = st.tabs([
    "🌌 3D Overview", "🏭 Division Performance", "🧪 Cost & Margin",
    "📈 Pareto Concentration", "🗂️ Data Explorer"
])

# ========================= TAB 1: 3D OVERVIEW =========================
with tabs[0]:
    st.subheader("Product economics in 3D")
    st.markdown('<p class="section-note">Rotate the scene to investigate the relationship between sales, cost, and gross profit. Bubble size represents units; color represents gross margin.</p>', unsafe_allow_html=True)
    plot3d = p.copy()
    plot3d["Units_Size"] = np.maximum(plot3d["Units"].clip(lower=0), 1)
    fig3d = px.scatter_3d(
        plot3d, x="Sales", y="Cost", z="Gross_Profit",
        color="Gross_Margin", size="Units_Size",
        hover_name="Product Name",
        hover_data={"Division": True, "Factory": True, "Gross_Margin": ":.1%", "Profit_per_Unit": ":$,.2f",
                    "Orders": True, "Units_Size": False},
        color_continuous_scale=["#fb7185", "#fbbf24", "#34d399", "#53e0ff"],
        size_max=22, opacity=.88,
        title="3D Product Profitability Map"
    )
    fig3d.update_layout(
        scene=dict(
            xaxis_title="Sales ($)", yaxis_title="Cost ($)", zaxis_title="Gross Profit ($)",
            bgcolor="rgba(7,12,24,.2)",
            xaxis=dict(backgroundcolor="rgba(10,18,34,.25)", gridcolor=GRID, color="#a9c2e7"),
            yaxis=dict(backgroundcolor="rgba(10,18,34,.25)", gridcolor=GRID, color="#a9c2e7"),
            zaxis=dict(backgroundcolor="rgba(10,18,34,.25)", gridcolor=GRID, color="#a9c2e7"),
            camera=dict(eye=dict(x=1.65, y=1.65, z=1.15)),
        ),
        coloraxis_colorbar=dict(title="Margin", tickformat=".0%"),
    )
    style_fig(fig3d, chart_height)
    st.plotly_chart(fig3d, use_container_width=True, theme=None, config={"displaylogo": False, "scrollZoom": True})

    left, right = st.columns([1.1, 1])
    with left:
        top = p.nlargest(12, "Gross_Profit").sort_values("Gross_Profit")
        fig = px.bar(top, x="Gross_Profit", y="Product Name", orientation="h",
                     color="Gross_Margin", color_continuous_scale="Tealgrn",
                     hover_data=["Sales", "Cost", "Profit_per_Unit"],
                     title="Top products by gross profit")
        fig.update_layout(xaxis_title="Gross profit ($)", yaxis_title="")
        style_fig(fig, chart_height)
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with right:
        margin = p.nsmallest(15, "Gross_Margin").sort_values("Gross_Margin", ascending=True)
        fig = px.bar(margin, x="Gross_Margin", y="Product Name", orientation="h",
                     color="Gross_Margin", color_continuous_scale=["#fb7185", "#fbbf24", "#34d399"],
                     title="Lowest-margin products")
        fig.add_vline(x=margin_threshold, line_dash="dash", line_color="#53e0ff",
                      annotation_text=f"Threshold {margin_threshold:.0%}")
        fig.update_layout(xaxis_tickformat=".0%", xaxis_title="Gross margin", yaxis_title="")
        style_fig(fig, chart_height)
        st.plotly_chart(fig, use_container_width=True, theme=None)

    st.subheader("Margin risk watchlist")
    risk = p[p["Gross_Margin"] < margin_threshold].sort_values("Gross_Margin")
    if risk.empty:
        st.success("No products fall below the selected margin threshold.")
    else:
        risk_cols = ["Product Name", "Division", "Factory", "Sales", "Gross_Profit", "Gross_Margin", "Profit_per_Unit", "Risk"]
        st.dataframe(money_table(risk[risk_cols], ["Sales", "Gross_Profit", "Profit_per_Unit"]), use_container_width=True, hide_index=True)

# ========================= TAB 2: DIVISION =========================
with tabs[1]:
    st.subheader("Division-level performance")
    d = df.groupby("Division", as_index=False).agg(
        Sales=("Sales", "sum"), Gross_Profit=("Gross Profit", "sum"),
        Cost=("Cost", "sum"), Units=("Units", "sum"), Orders=("Order ID", "nunique")
    )
    d["Gross_Margin"] = np.divide(d["Gross_Profit"], d["Sales"], out=np.zeros(len(d)), where=d["Sales"].to_numpy()!=0)
    d["Revenue_Share"] = d["Sales"] / d["Sales"].sum() if d["Sales"].sum() else 0
    d["Profit_Share"] = d["Gross_Profit"] / d["Gross_Profit"].sum() if d["Gross_Profit"].sum() else 0
    a, b = st.columns(2)
    with a:
        melted = d.melt(id_vars="Division", value_vars=["Sales", "Gross_Profit"], var_name="Metric", value_name="Value")
        fig = px.bar(melted, x="Division", y="Value", color="Metric", barmode="group",
                     color_discrete_map={"Sales": "#53e0ff", "Gross_Profit": "#a78bfa"},
                     title="Sales vs gross profit by division")
        style_fig(fig, chart_height)
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with b:
        fig = px.bar(d.sort_values("Gross_Margin"), x="Gross_Margin", y="Division", orientation="h",
                     color="Gross_Margin", color_continuous_scale="Tealgrn",
                     text=d.sort_values("Gross_Margin")["Gross_Margin"].map(lambda x: f"{x:.1%}"),
                     title="Gross margin by division")
        fig.update_layout(xaxis_tickformat=".0%", xaxis_title="Gross margin", yaxis_title="")
        style_fig(fig, chart_height)
        st.plotly_chart(fig, use_container_width=True, theme=None)
    st.subheader("Division scorecard")
    st.dataframe(money_table(d, ["Sales", "Gross_Profit", "Cost"]), use_container_width=True, hide_index=True)

    # 3D division view
    fig = px.scatter_3d(d, x="Sales", y="Cost", z="Gross_Profit", color="Division",
                        size="Units", hover_name="Division", hover_data=["Gross_Margin", "Orders"],
                        title="3D division comparison")
    fig.update_layout(scene=dict(xaxis_title="Sales ($)", yaxis_title="Cost ($)", zaxis_title="Gross profit ($)", bgcolor="rgba(0,0,0,0)"))
    style_fig(fig, chart_height)
    st.plotly_chart(fig, use_container_width=True, theme=None)

# ========================= TAB 3: DIAGNOSTICS =========================
with tabs[2]:
    st.subheader("Cost structure and margin diagnostics")
    a, b = st.columns(2)
    with a:
        fig = px.scatter(p, x="Sales", y="Cost", size="Gross_Profit", color="Gross_Margin",
                         hover_name="Product Name", hover_data=["Division", "Factory", "Profit_per_Unit"],
                         color_continuous_scale=["#fb7185", "#fbbf24", "#34d399"],
                         title="Cost vs sales (bubble = gross profit)")
        max_val = max(float(p["Sales"].max()), float(p["Cost"].max()), 1) * 1.05
        fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines", name="Cost = Sales",
                                 line=dict(dash="dash", color="#e879f9", width=2)))
        fig.update_layout(xaxis_title="Sales ($)", yaxis_title="Cost ($)")
        style_fig(fig, chart_height)
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with b:
        fig = px.scatter(p, x="Sales", y="Gross_Margin", size="Gross_Profit", color="Division",
                         hover_name="Product Name", hover_data=["Cost", "Profit_per_Unit"],
                         title="Sales vs margin: volume can hide risk")
        fig.add_hline(y=margin_threshold, line_dash="dash", line_color="#53e0ff",
                      annotation_text=f"Risk threshold {margin_threshold:.0%}")
        fig.update_layout(yaxis_tickformat=".0%", xaxis_title="Sales ($)", yaxis_title="Gross margin")
        style_fig(fig, chart_height)
        st.plotly_chart(fig, use_container_width=True, theme=None)

    st.subheader("Recommended actions")
    diag = p.sort_values(["Gross_Margin", "Sales"])
    cols = ["Product Name", "Division", "Factory", "Sales", "Cost", "Gross_Profit", "Gross_Margin", "Cost_Ratio", "Suggested_Action"]
    st.dataframe(money_table(diag[cols], ["Sales", "Cost", "Gross_Profit"]), use_container_width=True, hide_index=True)

    st.info("Interpretation: margin bands are configurable rules of thumb, not forecasts. Validate pricing, cost allocation, contracts, and product strategy before making commercial decisions.")

# ========================= TAB 4: PARETO =========================
with tabs[3]:
    st.subheader("Revenue and profit concentration")
    metric = st.radio("Pareto metric", ["Gross Profit", "Sales"], horizontal=True)
    col = "Gross_Profit" if metric == "Gross Profit" else "Sales"
    par = p.sort_values(col, ascending=False).copy()
    denominator = par[col].sum()
    par["CumShare"] = par[col].cumsum() / denominator if denominator else 0
    par["Rank"] = np.arange(1, len(par) + 1)
    threshold_count = int((par["CumShare"] < .8).sum() + 1) if len(par) else 0

    fig = go.Figure()
    fig.add_bar(x=par["Product Name"], y=par[col], name=metric, marker_color="#53e0ff",
                hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>")
    fig.add_scatter(x=par["Product Name"], y=par["CumShare"], name="Cumulative share",
                    yaxis="y2", mode="lines+markers", line=dict(color="#c4b5fd", width=3),
                    marker=dict(size=5), hovertemplate="%{x}<br>%{y:.1%}<extra></extra>")
    fig.add_hline(y=.8, yref="y2", line_dash="dash", line_color="#fbbf24",
                  annotation_text="80% cumulative share")
    fig.update_layout(
        title=f"{metric} Pareto analysis",
        xaxis=dict(tickangle=-45, title="Product"),
        yaxis=dict(title=f"{metric} ($)", gridcolor=GRID),
        yaxis2=dict(title="Cumulative share", overlaying="y", side="right", tickformat=".0%", range=[0, 1.05]),
        margin=dict(l=20, r=30, t=65, b=120), height=max(chart_height, 470),
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG, font=dict(family=FONT, color="#dce8ff"),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)
    if len(par):
        st.info(f"{threshold_count} of {len(par)} products ({threshold_count / len(par):.1%}) reach approximately 80% of {metric.lower()} under the current filters. The exact count depends on the distribution and rounding.")
    st.dataframe(
        money_table(par[["Rank", "Product Name", col, "CumShare"]], [col]),
        use_container_width=True, hide_index=True
    )

# ========================= TAB 5: DATA EXPLORER =========================
with tabs[4]:
    st.subheader("Filtered transaction explorer")
    st.caption("Download the exact filtered transaction set or inspect it below.")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download filtered transactions (CSV)", data=csv,
        file_name="nassau_filtered_transactions.csv", mime="text/csv",
        use_container_width=False
    )
    st.dataframe(df, use_container_width=True, hide_index=True, height=520)
    st.caption(f"Rows: {len(df):,} · Columns: {len(df.columns)} · Products: {p['Product Name'].nunique():,}")

st.divider()
st.markdown(
    '<div style="text-align:center;color:#7186a8;font-size:.8rem;">Nassau Candy Profitability Command Center · Built with Streamlit + Plotly · Interactive charts are exploratory, not financial advice.</div>',
    unsafe_allow_html=True
)
