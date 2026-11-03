import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Marketing ROI & Attribution", page_icon="📈", layout="wide")

NAVY = "#102A43"
BLUE = "#2563EB"
TEAL = "#0F766E"
MUTED = "#64748B"

st.markdown("""
<style>
    .stApp { background: #F5F8FC; }
    [data-testid="stMetric"] { background: white; padding: 18px 20px; border: 1px solid #E5EAF1; border-radius: 14px; }
    .hero { padding: 24px 28px; background: linear-gradient(110deg,#102A43,#1D4ED8); border-radius: 18px; color: white; margin-bottom: 18px; }
    .hero h1 { color: white; margin: 0; font-size: 2rem; }
    .hero p { color: #DBEAFE; margin: 8px 0 0 0; }
    .small-note { color: #64748B; font-size: .86rem; }
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).parent
@st.cache_data
def load_data():
    perf = pd.read_csv(ROOT / "data" / "campaign_performance.csv", parse_dates=["date"])
    journeys = pd.read_csv(ROOT / "data" / "customer_journeys.csv", parse_dates=["touchpoint_date"])
    return perf, journeys

perf, journeys = load_data()

st.markdown("""
<div class="hero">
  <h1>Marketing Campaign ROI & Attribution</h1>
  <p>Understand channel efficiency, compare attribution models, and make smarter budget allocation decisions.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Dashboard controls")
    date_min, date_max = perf.date.min().date(), perf.date.max().date()
    date_range = st.date_input("Campaign date range", value=(date_min, date_max), min_value=date_min, max_value=date_max)
    selected_channels = st.multiselect("Marketing channels", sorted(perf.channel.unique()), default=sorted(perf.channel.unique()))
    st.caption("Demo data is synthetic. Replace the CSV files with your own consistently structured data.")

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = date_min, date_max

filtered = perf[
    (perf.date.dt.date >= start_date) &
    (perf.date.dt.date <= end_date) &
    (perf.channel.isin(selected_channels))
].copy()
journey_filtered = journeys[
    (journeys.touchpoint_date.dt.date >= start_date) &
    (journeys.touchpoint_date.dt.date <= end_date) &
    (journeys.channel.isin(selected_channels))
].copy()

if filtered.empty:
    st.warning("No campaign data matches these filters. Adjust the date range or channels.")
    st.stop()

def channel_summary(df):
    out = df.groupby("channel", as_index=False).agg(
        spend=("ad_spend","sum"), revenue=("revenue","sum"),
        conversions=("conversions","sum"), clicks=("clicks","sum"),
        impressions=("impressions","sum")
    )
    out["roi"] = np.where(out.spend > 0, (out.revenue-out.spend)/out.spend*100, 0)
    out["cpa"] = np.where(out.conversions > 0, out.spend/out.conversions, np.nan)
    out["roas"] = np.where(out.spend > 0, out.revenue/out.spend, 0)
    return out

summary = channel_summary(filtered)
total_spend = filtered.ad_spend.sum()
total_revenue = filtered.revenue.sum()
total_conv = filtered.conversions.sum()
overall_roi = (total_revenue-total_spend)/total_spend*100 if total_spend else 0
overall_cpa = total_spend/total_conv if total_conv else 0

st.subheader("Executive overview")
m1,m2,m3,m4 = st.columns(4)
m1.metric("Total ad spend", f"${total_spend:,.0f}")
m2.metric("Attributed revenue", f"${total_revenue:,.0f}")
m3.metric("Overall ROI", f"{overall_roi:,.1f}%")
m4.metric("Blended CPA", f"${overall_cpa:,.2f}")
st.caption("ROI = (Revenue − Ad Spend) ÷ Ad Spend. ROAS = Revenue ÷ Ad Spend. CPA = Ad Spend ÷ Conversions.")

left,right = st.columns([1.2,1])
with left:
    st.subheader("Channel performance")
    fig = px.bar(summary.sort_values("revenue", ascending=False), x="channel", y=["spend","revenue"],
                 barmode="group", labels={"value":"Amount (USD)","variable":"Metric","channel":"Channel"},
                 color_discrete_sequence=[BLUE,TEAL])
    fig.update_layout(legend_title="", plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("ROI by channel")
    fig = px.bar(summary.sort_values("roi"), x="roi", y="channel", orientation="h",
                 labels={"roi":"ROI (%)","channel":""}, color="roi", color_continuous_scale="Blues")
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=20,b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Attribution model comparison")
st.write("The models distribute each converting customer's revenue across the channels in their journey.")
converting = journeys[journeys.converted == 1].copy()
converting = converting[converting.channel.isin(selected_channels)]
# Filter by conversion journey date proxy: last touch date.
last_dates = converting.groupby("customer_id").touchpoint_date.max()
valid_ids = last_dates[(last_dates.dt.date >= start_date) & (last_dates.dt.date <= end_date)].index
converting = converting[converting.customer_id.isin(valid_ids)]

def attribution_table(touches):
    records = []
    for cid, g in touches.sort_values("touchpoint_order").groupby("customer_id"):
        # Revenue is stored only on the final touchpoint.
        value = float(g.conversion_value.sum())
        if value <= 0 or g.empty:
            continue
        channels_path = g.channel.tolist()
        n = len(channels_path)
        first = {channels_path[0]: 1.0}
        last = {channels_path[-1]: 1.0}
        weights = np.arange(1, n+1, dtype=float)
        weights = weights / weights.sum()  # position-based linear multi-touch
        multi = {}
        for ch, w in zip(channels_path, weights):
            multi[ch] = multi.get(ch, 0) + float(w)
        for model, alloc in [("First-Touch", first), ("Last-Touch", last), ("Multi-Touch", multi)]:
            for ch, weight in alloc.items():
                records.append({"customer_id":cid,"model":model,"channel":ch,"attributed_revenue":value*weight})
    if not records:
        return pd.DataFrame(columns=["model","channel","attributed_revenue"])
    return pd.DataFrame(records).groupby(["model","channel"],as_index=False).attributed_revenue.sum()

attr = attribution_table(converting)
if attr.empty:
    st.info("No converting journeys are available for the current filters.")
else:
    fig = px.bar(attr, x="channel", y="attributed_revenue", color="model", barmode="group",
                 labels={"attributed_revenue":"Attributed revenue (USD)","channel":"Channel"},
                 color_discrete_sequence=[BLUE,TEAL,"#F59E0B"])
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", legend_title="", margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig, use_container_width=True)
    pivot = attr.pivot(index="channel", columns="model", values="attributed_revenue").fillna(0)
    st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)

st.divider()
st.subheader("Campaign-level efficiency")
campaign_summary = filtered.groupby(["channel","campaign"],as_index=False).agg(
    spend=("ad_spend","sum"), revenue=("revenue","sum"), conversions=("conversions","sum"),
    clicks=("clicks","sum")
)
campaign_summary["CPA"] = np.where(campaign_summary.conversions>0,campaign_summary.spend/campaign_summary.conversions,np.nan)
campaign_summary["ROI (%)"] = np.where(campaign_summary.spend>0,(campaign_summary.revenue-campaign_summary.spend)/campaign_summary.spend*100,0)
campaign_summary["ROAS"] = np.where(campaign_summary.spend>0,campaign_summary.revenue/campaign_summary.spend,0)
st.dataframe(campaign_summary.sort_values("ROI (%)",ascending=False).style.format({
    "spend":"${:,.0f}","revenue":"${:,.0f}","CPA":"${:,.2f}","ROI (%)":"{:.1f}%","ROAS":"{:.2f}x"
}), use_container_width=True, hide_index=True)

st.divider()
st.subheader("Budget reallocation recommendation")
st.write("A simple planning heuristic: rank channels by ROI and shift a configurable share of the budget toward the top-performing channel. Validate against incrementality, capacity, and seasonality before acting.")
shift_pct = st.slider("Budget to reallocate from the lowest-ROI channel", 0, 30, 10, 5)
ranked = summary.sort_values("roi", ascending=False).copy()
if len(ranked) >= 2:
    best = ranked.iloc[0]
    worst = ranked.iloc[-1]
    proposed = summary[["channel","spend"]].copy()
    move = float(worst.spend) * shift_pct/100
    proposed.loc[proposed.channel==worst.channel,"proposed_spend"] = float(worst.spend)-move
    proposed.loc[proposed.channel==best.channel,"proposed_spend"] = float(best.spend)+move
    proposed["proposed_spend"] = proposed["proposed_spend"].fillna(proposed.spend)
    c1,c2,c3 = st.columns(3)
    c1.metric("Top ROI channel", best.channel)
    c2.metric("Lowest ROI channel", worst.channel)
    c3.metric("Illustrative shift", f"${move:,.0f}")
    st.dataframe(proposed.rename(columns={"spend":"Current spend","proposed_spend":"Proposed spend"}).style.format({
        "Current spend":"${:,.0f}","Proposed spend":"${:,.0f}"
    }), use_container_width=True, hide_index=True)
else:
    st.info("Select at least two channels to view a budget reallocation scenario.")

st.caption("Important: This is a descriptive demo, not a causal lift model. Attribution rules allocate observed revenue; they do not prove that a channel caused the conversion.")
