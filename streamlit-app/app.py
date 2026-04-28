import io
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Exoplanet Habitability Explorer",
    layout="wide",
)

# Constants
STAR_ORDER = ["F", "G", "K", "M"]
STAR_CLASS_LABELS = {
    "F": "F — Hot & bright",
    "G": "G — Sun-like (our Sun)",
    "K": "K — Orange dwarf",
    "M": "M — Red dwarf (coolest)",
}
HAB_LABEL_MAP = {True: "Possibly Habitable", False: "Not Habitable"}

# Data loading
@st.cache_data(show_spinner="Fetching data from NASA Exoplanet Archive…")

def load_data() -> pd.DataFrame:
    columns = ",".join([
        "pl_name", "hostname", "st_spectype",
        "pl_insol", "pl_eqt", "pl_rade",
        "sy_dist", "ra", "dec",
        "st_teff", "st_rad", "st_mass",
        "discoverymethod", "disc_year",
    ])
    url = (
        "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
        f"?query=select+{columns}+from+ps"
        "&format=csv"
    )
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text), comment="#", low_memory=False)

@st.cache_data(show_spinner="Cleaning data…")

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["host_star_class"] = df["st_spectype"].str[0].str.upper()
    df["habitable"]       = df["pl_insol"].between(0.36, 1.11)
    df["hab_label"]       = df["habitable"].map(HAB_LABEL_MAP)
    df = df.dropna(subset=["pl_insol", "pl_eqt", "pl_rade", "host_star_class"])
    df = df[df["host_star_class"].isin(STAR_ORDER)].reset_index(drop=True)
    return df

try:
    raw_df = load_data()
    df_all = clean_data(raw_df)
except Exception as e:
    st.error(f"Could not reach NASA. Check your internet connection.\n\n`{e}`")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("🔭 Filters")

    # 1) Habitable only toggle — most relevant to the dashboard's theme
    habitable_only = st.toggle(
        "Toggle to show potentially habitable planets only",
        value=False,
        help="Limits every chart to planets inside the Goldilocks Zone (insolation flux 0.36–1.11 × Earth).",
    )

    st.divider()

    # 2) Host star class
    selected_classes = st.multiselect(
        "Host Star Type",
        options=STAR_ORDER,
        default=STAR_ORDER,
        format_func=lambda x: STAR_CLASS_LABELS[x],
        help="The type of star the planet orbits. Our Sun is a G-type star.",
    )

    st.divider()

    # 3) Discovery year range
    min_year = int(df_all["disc_year"].min())
    max_year = int(df_all["disc_year"].max())
    year_range = st.slider(
        "Discovery Year",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        help="Filter by the year a planet was first discovered.",
    )

    st.divider()

    # 4) Discovery method
    all_methods = sorted(df_all["discoverymethod"].dropna().unique())
    selected_methods = st.multiselect(
        "Discovery Method",
        options=all_methods,
        default=all_methods,
        help="How the planet was detected. 'Transit' is by far the most common method.",
    )

    st.divider()
    st.caption("Data sourced live from the NASA Exoplanet Archive.")

# Apply filters
df = df_all.copy()

if habitable_only:
    df = df[df["habitable"]]
if selected_classes:
    df = df[df["host_star_class"].isin(selected_classes)]

df = df[df["disc_year"].between(year_range[0], year_range[1])]

if selected_methods:
    df = df[df["discoverymethod"].isin(selected_methods)]

if df.empty:
    st.warning("No planets match your current filters — try loosening the sidebar settings.")
    st.stop()
# Header
st.title("Exoplanet Habitability Explorer")
st.markdown(
    "An **exoplanet** is a planet that orbits a star other than our Sun. "
    "Thousands have been discovered — but could any of them support life? "
    "This dashboard explores data from the [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) "
    "to find out which planets fall inside the **Goldilocks Zone**: "
    "the orbital range where liquid water could theoretically exist on a planet's surface."
)
st.divider()