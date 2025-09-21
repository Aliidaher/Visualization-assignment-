import pandas as pd
import streamlit as st
import plotly.express as px

# Trendline needs statsmodels; app still works without it
try:
    import statsmodels.api as sm  # noqa: F401
    HAS_SM = True
except Exception:
    HAS_SM = False

st.set_page_config(page_title="Lebanon Tourism Explorer", layout="wide")

DATA_URL = "https://linked.aub.edu.lb/pkgcube/data/551015b5649368dd2612f795c2a9c2d8_20240902_115953.csv"

@st.cache_data(show_spinner=False)
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    # Ensure expected columns and types
    for c in ["Total number of hotels", "Total number of restaurants", "Tourism Index"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Town", "Total number of hotels", "Total number of restaurants", "Tourism Index"])
    df["Town"] = df["Town"].astype(str).str.strip()
    return df

df = load_data(DATA_URL)

# Sidebar filters
st.sidebar.header("Filters")
towns = sorted(df["Town"].unique().tolist())
selected_towns = st.sidebar.multiselect("Select Towns", towns, default=towns)
min_restaurants = st.sidebar.slider(
    "Minimum number of restaurants",
    int(df["Total number of restaurants"].min()),
    int(df["Total number of restaurants"].max()),
    int(df["Total number of restaurants"].min()),
    step=1
)
show_trendline = st.sidebar.checkbox("Show trendline on scatter (OLS)", value=True)
sort_metric = st.sidebar.radio("Sort bar chart by", ["Total number of hotels", "Town"], index=0)
ascending = st.sidebar.checkbox("Sort ascending", value=False)

# Apply filters
filtered = df.copy()
if selected_towns:
    filtered = filtered[filtered["Town"].isin(selected_towns)]
filtered = filtered[filtered["Total number of restaurants"] >= min_restaurants]

if filtered.empty:
    st.title("Lebanon Tourism Explorer")
    st.warning("No data matches your filters. Adjust filters to see results.")
    st.stop()

# Header
st.title("Lebanon Tourism Explorer")
st.markdown("""
- **Bar chart:** Total number of hotels by town (infrastructure view).  
- **Scatter plot:** Restaurants vs. Tourism Index (attractiveness view).  
Use the filters on the left to interactively change the data shown in both charts.
""")

# KPIs
k1, k2, k3 = st.columns(3)
k1.metric("Towns in view", f"{filtered['Town'].nunique():,}")
k2.metric("Hotels (sum)", f"{int(filtered['Total number of hotels'].sum()):,}")
k3.metric("Avg Tourism Index", f"{filtered['Tourism Index'].mean():.2f}")

# Charts
c1, c2 = st.columns(2)

with c1:
    st.subheader("Total Number of Hotels by Town")
    plot_df = (filtered.sort_values("Total number of hotels", ascending=ascending)
               if sort_metric == "Total number of hotels"
               else filtered.sort_values("Town", ascending=ascending))
    fig_bar = px.bar(
        plot_df,
        x="Town",
        y="Total number of hotels",
        hover_data=["Total number of restaurants", "Tourism Index"],
        labels={"Total number of hotels": "Hotels"},
    )
    fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title=None)
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.subheader("Tourism Index vs. Number of Restaurants")
    trend = "ols" if (show_trendline and HAS_SM) else None
    if show_trendline and not HAS_SM:
        st.info("Trendline requires `statsmodels`. Add it to requirements.txt to enable.")
    fig_scatter = px.scatter(
        filtered,
        x="Total number of restaurants",
        y="Tourism Index",
        hover_name="Town",
        trendline=trend,
        labels={"Total number of restaurants": "Restaurants", "Tourism Index": "Tourism Index"},
    )
    fig_scatter.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()
st.subheader("Download current view")
st.download_button(
    "Download filtered data as CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    "filtered_tourism_data.csv",
    "text/csv",
)

st.caption("Source: AUB Linked Open Data | App by Streamlit + Plotly")
