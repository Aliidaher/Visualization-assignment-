import pandas as pd
import streamlit as st
import plotly.express as px

# Try to enable trendline if statsmodels is available
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
    # Standardize expected columns if necessary
    rename_map = {
        "Total number of hotels": "Total number of hotels",
        "Total number of restaurants": "Total number of restaurants",
        "Tourism Index": "Tourism Index",
        "Town": "Town",
    }
    df = df.rename(columns=rename_map)
    # Ensure numeric types
    for c in ["Total number of hotels", "Total number of restaurants", "Tourism Index"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Drop rows with missing critical fields
    df = df.dropna(subset=["Town", "Total number of hotels", "Total number of restaurants", "Tourism Index"])
    # Clean town names
    df["Town"] = df["Town"].astype(str).str.strip()
    return df

df = load_data(DATA_URL)

# ---------- Sidebar Controls ----------
st.sidebar.header("Filters")
towns = sorted(df["Town"].unique().tolist())
default_towns = towns  # preselect all

selected_towns = st.sidebar.multiselect("Select Towns", towns, default=default_towns)
min_restaurants = st.sidebar.slider(
    "Minimum number of restaurants",
    int(df["Total number of restaurants"].min()),
    int(df["Total number of restaurants"].max()),
    int(df["Total number of restaurants"].min()),
    step=1
)
show_trendline = st.sidebar.checkbox("Show trendline on scatter (OLS)", value=True)
sort_metric = st.sidebar.radio(
    "Sort bar chart by",
    options=["Total number of hotels", "Town"],
    index=0
)
# Use checkbox for wide compatibility with Streamlit versions
ascending = st.sidebar.checkbox("Sort ascending", value=False)

# ---------- Apply Filters ----------
filtered = df.copy()
if selected_towns:
    filtered = filtered[filtered["Town"].isin(selected_towns)]
filtered = filtered[filtered["Total number of restaurants"] >= min_restaurants]

# Guard: no data after filters
if filtered.empty:
    st.title("Lebanon Tourism Explorer")
    st.warning("No data matches your filters. Adjust filters to see results.")
    st.stop()

# ---------- Header & Description ----------
st.title("Lebanon Tourism Explorer")
st.markdown('''
This page presents two related visualizations to explore the tourism landscape across towns.
- **Bar chart:** Total number of hotels by town (infrastructure view).
- **Scatter plot:** Relationship between number of restaurants and Tourism Index (attractiveness view).

Use the filters on the left to interactively change the data shown in both charts.
''')

# ---------- KPI Row ----------
k1, k2, k3 = st.columns(3)
k1.metric("Towns in view", f"{filtered['Town'].nunique():,}")
k2.metric("Hotels (sum)", f"{int(filtered['Total number of hotels'].sum()):,}")
k3.metric("Avg Tourism Index", f"{filtered['Tourism Index'].mean():.2f}")

# ---------- Charts ----------
c1, c2 = st.columns(2)

# Bar chart
with c1:
    st.subheader("Total Number of Hotels by Town")
    if sort_metric == "Total number of hotels":
        plot_df = filtered.sort_values(by="Total number of hotels", ascending=ascending)
    else:
        plot_df = filtered.sort_values(by="Town", ascending=ascending)

    fig_bar = px.bar(
        plot_df,
        x="Town",
        y="Total number of hotels",
        hover_data=["Total number of restaurants", "Tourism Index"],
        labels={"Total number of hotels": "Hotels"},
        title=None,
    )
    fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title=None)
    st.plotly_chart(fig_bar, use_container_width=True)

# Scatter plot
with c2:
    st.subheader("Tourism Index vs. Number of Restaurants")
    trend = "ols" if (show_trendline and HAS_SM) else None
    if show_trendline and not HAS_SM:
        st.info("Trendline requires 'statsmodels'. Add it to requirements.txt to enable.")

    fig_scatter = px.scatter(
        filtered,
        x="Total number of restaurants",
        y="Tourism Index",
        hover_name="Town",
        trendline=trend,
        labels={"Total number of restaurants": "Restaurants", "Tourism Index": "Tourism Index"},
        title=None,
    )
    fig_scatter.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ---------- Data Download ----------
st.divider()
st.subheader("Download current view")
st.download_button(
    label="Download filtered data as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_tourism_data.csv",
    mime="text/csv"
)

st.caption("Source: AUB Linked Open Data | App by Streamlit + Plotly")
