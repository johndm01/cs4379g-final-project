import io
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Exoplanet Habitability Explorer",
    page_icon="🪐",
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