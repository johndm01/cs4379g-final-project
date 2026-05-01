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

# ── Theme state ───────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

is_dark = st.session_state.theme == "dark"

# ── Filter state (single source of truth) ────────────────────────────────────
_min_year    = int(df_all["disc_year"].min())
_max_year    = int(df_all["disc_year"].max())
_all_methods = sorted(df_all["discoverymethod"].dropna().unique().tolist())

if "f_habitable" not in st.session_state:
    st.session_state.f_habitable = False
if "f_classes"  not in st.session_state:
    st.session_state.f_classes  = list(STAR_ORDER)
if "f_years"    not in st.session_state:
    st.session_state.f_years    = (_min_year, _max_year)
if "f_methods"  not in st.session_state:
    st.session_state.f_methods  = _all_methods

def _sync(src, dst, state):
    st.session_state[state] = st.session_state[src]
    if dst in st.session_state:
        del st.session_state[dst]

def on_sb_hab():      _sync("_sb_hab",      "_il_hab",      "f_habitable")
def on_il_hab():      _sync("_il_hab",      "_sb_hab",      "f_habitable")
def on_sb_classes():  _sync("_sb_classes",  "_il_classes",  "f_classes")
def on_il_classes():  _sync("_il_classes",  "_sb_classes",  "f_classes")
def on_sb_years():    _sync("_sb_years",    "_il_years",    "f_years")
def on_il_years():    _sync("_il_years",    "_sb_years",    "f_years")
def on_sb_methods():  _sync("_sb_methods",  "_il_methods",  "f_methods")
def on_il_methods():  _sync("_il_methods",  "_sb_methods",  "f_methods")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    btn_label = "Switch to Dark Mode" if not is_dark else "Switch to Light Mode"
    st.button(btn_label, on_click=toggle_theme, use_container_width=True)

    st.divider()
    st.header("Filters")

    st.checkbox(
        "Possibly habitable planets only",
        value=st.session_state.f_habitable,
        key="_sb_hab", on_change=on_sb_hab,
        help="Limits every chart to planets inside the Goldilocks Zone (insolation flux 0.36–1.11 × Earth).",
    )
    st.divider()
    st.multiselect(
        "Host Star Type",
        options=STAR_ORDER,
        default=st.session_state.f_classes,
        format_func=lambda x: STAR_CLASS_LABELS[x],
        key="_sb_classes", on_change=on_sb_classes,
        help="The type of star the planet orbits. Our Sun is a G-type star.",
    )
    st.divider()
    st.slider(
        "Discovery Year",
        min_value=_min_year, max_value=_max_year,
        value=st.session_state.f_years,
        key="_sb_years", on_change=on_sb_years,
        help="Filter by the year a planet was first discovered.",
    )
    st.divider()
    st.multiselect(
        "Discovery Method",
        options=_all_methods,
        default=st.session_state.f_methods,
        key="_sb_methods", on_change=on_sb_methods,
        help="How the planet was detected. 'Transit' is by far the most common method.",
    )
    st.divider()
    st.caption("Data sourced live from the NASA Exoplanet Archive.")

# ── Neobrutalist theme CSS ────────────────────────────────────────────────────
if is_dark:
    BG          = "#242219"
    SIDEBAR_BG  = "#2c2a20"
    CARD_BG     = "#363328"
    TEXT        = "#f5f0e0"
    BORDER      = "#c4b08a"
    SHADOW      = "#8a7055"
    ACCENT      = "#c8960c"
    ACCENT_TEXT = "#ffffff"
    MULTI_BG    = "#7a2525"
else:
    BG          = "#fffdf0"
    SIDEBAR_BG  = "#f5f0e0"
    CARD_BG     = "#ffffff"
    TEXT        = "#0a0a0a"
    BORDER      = "#000000"
    SHADOW      = "#000000"
    ACCENT      = "#ffe500"
    ACCENT_TEXT = "#000000"
    MULTI_BG    = "#ff4b4b"

st.markdown(
    '<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">',
    unsafe_allow_html=True,
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700;800&display=swap');

@font-face {{
    font-family: 'Material Icons';
    font-style: normal;
    font-weight: 400;
    src: url(https://fonts.gstatic.com/s/materialicons/v140/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2) format('woff2');
}}
.material-icons,
[data-testid="stIconMaterial"] {{
    font-family: 'Material Icons' !important;
    font-weight: normal;
    font-style: normal;
    font-size: 24px;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    -webkit-font-smoothing: antialiased;
}}

/* ── Override Streamlit's primary color (used by slider, etc.) ── */
:root {{
    --primary-color: {ACCENT} !important;
}}

/* ── Base ── */
html, body, .stApp {{
    background-color: {BG} !important;
    font-family: 'Space Grotesk', sans-serif !important;
    color: {TEXT} !important;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: {SIDEBAR_BG} !important;
    border-right: 3px solid {BORDER} !important;
}}

/* ── Main content block ── */
[data-testid="stMainBlockContainer"] {{
    background-color: {BG} !important;
}}

/* ── All text ── */
p, li, span, div, label, caption,
.stMarkdown, [data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] p {{
    color: {TEXT} !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}

h1, h2, h3, h4, h5, h6 {{
    color: {TEXT} !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px;
}}

/* ── Buttons ── */
.stButton > button,
.stButton > button p,
.stButton > button span {{
    color: {ACCENT_TEXT} !important;
}}
.stButton > button {{
    background-color: {ACCENT} !important;
    color: {ACCENT_TEXT} !important;
    border: 3px solid {BORDER} !important;
    box-shadow: 4px 4px 0px {SHADOW} !important;
    border-radius: 0px !important;
    font-weight: 800 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: box-shadow 0.08s, transform 0.08s !important;
}}
.stButton > button:hover {{
    transform: translate(2px, 2px) !important;
    box-shadow: 2px 2px 0px {SHADOW} !important;
}}
.stButton > button:active {{
    transform: translate(4px, 4px) !important;
    box-shadow: 0px 0px 0px {SHADOW} !important;
}}

/* ── Metric cards ── */
[data-testid="stMetric"] {{
    background-color: {CARD_BG} !important;
    border: 3px solid {BORDER} !important;
    box-shadow: 5px 5px 0px {SHADOW} !important;
    border-radius: 0px !important;
    padding: 16px 20px !important;
}}
[data-testid="stMetricValue"],
[data-testid="stMetricLabel"] {{
    color: {TEXT} !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}
[data-testid="stMetricValue"] {{
    font-weight: 800 !important;
}}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 3px solid {BORDER} !important;
    gap: 4px;
}}
button[role="tab"] {{
    color: {TEXT} !important;
    font-weight: 700 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    border-radius: 0px !important;
    border: 2px solid transparent !important;
    padding: 8px 20px !important;
}}
button[role="tab"][aria-selected="true"] {{
    background-color: {ACCENT} !important;
    color: {ACCENT_TEXT} !important;
    border: 2px solid {BORDER} !important;
    box-shadow: 3px 3px 0px {SHADOW} !important;
    font-weight: 800 !important;
}}
button[role="tab"]:hover {{
    background-color: {ACCENT} !important;
    color: {ACCENT_TEXT} !important;
    opacity: 0.8;
}}
[data-baseweb="tab-highlight"] {{
    background-color: {'#bf3838' if is_dark else MULTI_BG} !important;
}}

/* ── Checkbox ── */
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > span:first-child {{
    border: 2px solid {BORDER} !important;
    border-radius: 0px !important;
    background-color: {CARD_BG} !important;
    box-shadow: 2px 2px 0px {SHADOW} !important;
}}
[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:checked) > span:first-child {{
    background-color: {'#bf3838' if is_dark else MULTI_BG} !important;
    border-color: {BORDER} !important;
}}

/* ── Multiselect tags and container ── */
.stMultiSelect [data-baseweb="select"] > div {{
    background-color: {MULTI_BG} !important;
}}
[data-baseweb="tag"] {{
    background-color: {MULTI_BG} !important;
    border: 2px solid {BORDER} !important;
    border-radius: 0px !important;
}}
[data-baseweb="tag"] span {{
    color: #ffffff !important;
}}
[data-baseweb="tag"] svg {{
    fill: #ffffff !important;
}}

/* ── Inputs (multiselect, sliders) ── */
[data-testid="stWidgetLabel"] p {{
    color: {TEXT} !important;
    font-weight: 700 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}
.stMultiSelect [data-baseweb="select"] > div,
.stSelectbox [data-baseweb="select"] > div {{
    border: 2px solid {BORDER} !important;
    border-radius: 0px !important;
    background-color: {CARD_BG} !important;
    box-shadow: 3px 3px 0px {SHADOW} !important;
}}

/* Slider track/fill — darkened in dark mode via CSS filter */
[data-testid="stSlider"] [data-baseweb="slider"] > div:first-child {{
    filter: {f'brightness(0.75)' if is_dark else 'none'} !important;
}}

/* Slider thumb */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"],
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {{
    background-color: {ACCENT} !important;
    border-color: {BORDER} !important;
    border-radius: 0px !important;
    outline: none !important;
    box-shadow: inset 0 0 0 1px {BORDER}, 1px 1px 0px {SHADOW} !important;
    filter: {'brightness(1.33)' if is_dark else 'none'} !important;
}}

/* ── Tooltip icons & dropdown arrows ── */
[data-testid="stTooltipIcon"] svg,
[data-testid="stTooltipIcon"] button {{
    color: {BORDER} !important;
    stroke: {BORDER} !important;
}}
[data-baseweb="select"] svg,
[data-baseweb="select"] [data-testid="stIconMaterial"] {{
    fill: {BORDER} !important;
    color: {BORDER} !important;
}}

/* ── Dividers ── */
hr {{
    border-color: {BORDER} !important;
    border-width: 2px !important;
    margin: 12px 0 !important;
}}

/* ── Dataframe / table ── */
[data-testid="stDataFrame"] {{
    border: 3px solid {BORDER} !important;
    box-shadow: 5px 5px 0px {SHADOW} !important;
}}

/* ── Top header bar ── */
header[data-testid="stHeader"] {{
    background-color: {BG} !important;
    border-bottom: 3px solid {BORDER} !important;
}}
[data-testid="stToolbar"] {{
    background-color: {BG} !important;
}}

/* Deploy button */
[data-testid="stToolbar"] button,
.stDeployButton button {{
    background-color: {ACCENT} !important;
    color: {ACCENT_TEXT} !important;
    border: 2px solid {BORDER} !important;
    box-shadow: 3px 3px 0px {SHADOW} !important;
    border-radius: 0px !important;
    font-weight: 800 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    text-transform: uppercase !important;
}}
[data-testid="stToolbar"] button:hover {{
    transform: translate(2px, 2px) !important;
    box-shadow: 1px 1px 0px {SHADOW} !important;
}}

/* Three-dot menu button */
[data-testid="stToolbar"] [data-testid="stMainMenuButton"],
button[data-testid="stMainMenuButton"] {{
    background-color: {CARD_BG} !important;
    border: 2px solid {BORDER} !important;
    box-shadow: 3px 3px 0px {SHADOW} !important;
    border-radius: 0px !important;
    color: {TEXT} !important;
}}

/* ── Sidebar collapse/expand button — always visible ── */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
button[data-testid="stBaseButton-headerNoPadding"] {{
    opacity: 1 !important;
    visibility: visible !important;
}}

/* ── Three-dot dropdown menu ── */
[data-baseweb="popover"],
[data-testid="stMainMenuPopover"],
[data-testid="stMainMenuPopover"] > div {{
    border: 3px solid {BORDER} !important;
    box-shadow: 5px 5px 0px {SHADOW} !important;
    border-radius: 0px !important;
    background-color: {BG} !important;
}}
[data-baseweb="popover"] [data-baseweb="menu"],
[data-testid="stMainMenuPopover"] [role="menu"] {{
    background-color: {BG} !important;
    border-radius: 0px !important;
    padding: 4px 0 !important;
}}
[data-baseweb="popover"] ul,
[data-testid="stMainMenuPopover"] ul {{
    background-color: {BG} !important;
    border-radius: 0px !important;
}}
[data-baseweb="popover"] li,
[data-testid="stMainMenuPopover"] li,
[data-testid="stMainMenuPopover"] button {{
    background-color: {BG} !important;
    color: {TEXT} !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 0px !important;
}}
[data-baseweb="popover"] li:hover,
[data-testid="stMainMenuPopover"] li:hover,
[data-testid="stMainMenuPopover"] button:hover {{
    background-color: {ACCENT} !important;
    color: {ACCENT_TEXT} !important;
}}
[data-baseweb="popover"] li span,
[data-baseweb="popover"] li p,
[data-baseweb="popover"] li div,
[data-testid="stMainMenuPopover"] span,
[data-testid="stMainMenuPopover"] p {{
    color: inherit !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}
[data-baseweb="popover"] hr,
[data-testid="stMainMenuPopover"] hr,
[data-baseweb="popover"] [role="separator"],
[data-testid="stMainMenuPopover"] [role="separator"] {{
    border-color: {BORDER} !important;
    background-color: {BORDER} !important;
    border-width: 1px !important;
    margin: 4px 0 !important;
}}

/* ── Hide Streamlit's built-in theme selector (we use our own toggle) ── */
[data-testid="stMainMenuItem-theme-System"],
[data-testid="stMainMenuItem-theme-Light"],
[data-testid="stMainMenuItem-theme-Dark"] {{
    display: none !important;
}}

/* ── Expander ── */
[data-testid="stExpander"] {{
    border: 2px solid {BORDER} !important;
    border-radius: 0px !important;
    background-color: {CARD_BG} !important;
}}
[data-testid="stExpander"] summary {{
    background-color: {CARD_BG} !important;
    color: {TEXT} !important;
    outline: none !important;
    box-shadow: none !important;
}}
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:focus,
[data-testid="stExpander"] summary:active {{
    background-color: {CARD_BG} !important;
    outline: none !important;
    box-shadow: none !important;
}}

/* ── Warning / error boxes ── */
[data-testid="stAlert"] {{
    border: 2px solid {BORDER} !important;
    border-radius: 0px !important;
    box-shadow: 4px 4px 0px {SHADOW} !important;
}}
</style>
""", unsafe_allow_html=True)


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

# ── Inline filters ────────────────────────────────────────────────────────────
fc1, fc2, fc3, fc4 = st.columns([1, 1.5, 1.5, 2])

with fc1:
    st.checkbox(
        "Habitable only",
        value=st.session_state.f_habitable,
        key="_il_hab", on_change=on_il_hab,
        help="Limits every chart to planets inside the Goldilocks Zone (insolation flux 0.36–1.11 × Earth).",
    )
with fc2:
    st.multiselect(
        "Host Star Type",
        options=STAR_ORDER,
        default=st.session_state.f_classes,
        format_func=lambda x: STAR_CLASS_LABELS[x],
        key="_il_classes", on_change=on_il_classes,
        help="The type of star the planet orbits. Our Sun is a G-type star.",
    )
with fc3:
    st.slider(
        "Discovery Year",
        min_value=_min_year, max_value=_max_year,
        value=st.session_state.f_years,
        key="_il_years", on_change=on_il_years,
        help="Filter by the year a planet was first discovered.",
    )
with fc4:
    st.multiselect(
        "Discovery Method",
        options=_all_methods,
        default=st.session_state.f_methods,
        key="_il_methods", on_change=on_il_methods,
        help="How the planet was detected. 'Transit' is by far the most common method.",
    )

# Apply filters
df = df_all.copy()
if st.session_state.f_habitable:
    df = df[df["habitable"]]
if st.session_state.f_classes:
    df = df[df["host_star_class"].isin(st.session_state.f_classes)]
df = df[df["disc_year"].between(st.session_state.f_years[0], st.session_state.f_years[1])]
if st.session_state.f_methods:
    df = df[df["discoverymethod"].isin(st.session_state.f_methods)]

if df.empty:
    st.warning("No planets match your current filters — try adjusting the filters above.")
    st.stop()

st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_planets  = len(df)
hab_candidates = int(df["habitable"].sum())
top_method     = df["discoverymethod"].mode()[0]
peak_year      = int(df.groupby("disc_year").size().idxmax())

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    label="Exoplanets in View",
    value=f"{total_planets:,}",
    help="Total planets matching your current sidebar filters.",
)
k2.metric(
    label="Habitable Candidates",
    value=f"{hab_candidates:,}",
    help="Planets inside the Goldilocks Zone (insolation flux 0.36–1.11 × Earth).",
)
k3.metric(
    label="Top Discovery Method",
    value=top_method,
    help="The detection technique responsible for the most discoveries in the current filter.",
)
k4.metric(
    label="Peak Discovery Year",
    value=str(peak_year),
    help="The year with the highest number of new exoplanet discoveries in the current filter.",
)

st.divider()

# ── Chart helpers ──────────────────────────────────────────────────────────────
STAR_COLORS = {"F": "#ffd97d", "G": "#f4a261", "K": "#e76f51", "M": "#c1440e"}
GRID_COLOR  = "#4a4540" if is_dark else "#e0ddd0"

def styled(fig):
    """Apply neobrutalist theme to a Plotly figure."""
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor =CARD_BG,
        font         =dict(color=TEXT, family="Space Grotesk", size=13),
        title_font   =dict(color=TEXT, family="Space Grotesk", size=16),
        legend       =dict(bgcolor=CARD_BG, bordercolor=BORDER, borderwidth=2,
                           font=dict(color=TEXT)),
        margin       =dict(l=40, r=40, t=60, b=40),
    )
    fig.update_xaxes(
        gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR,
        color=TEXT, tickfont=dict(color=TEXT), title_font=dict(color=TEXT),
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR,
        color=TEXT, tickfont=dict(color=TEXT), title_font=dict(color=TEXT),
    )
    return fig

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Goldilocks Zone",
    "Discovery Timeline",
    "Temperature by Star",
    "3D Explorer",
])

# ── Tab 1: Goldilocks Zone Scatter ────────────────────────────────────────────
with tab1:
    scatter_df = df.dropna(subset=["pl_insol", "pl_rade"])
    fig1 = px.scatter(
        scatter_df,
        x="pl_insol",
        y="pl_rade",
        color="hab_label",
        color_discrete_map={
            HAB_LABEL_MAP[True]:  "#2ecc71",
            HAB_LABEL_MAP[False]: "#5dade2",
        },
        log_x=True,
        log_y=True,
        hover_name="pl_name",
        hover_data={"pl_insol": ":.2f", "pl_rade": ":.2f", "hab_label": False},
        labels={
            "pl_insol":  "Insolation Flux (Earth = 1, log scale)",
            "pl_rade":   "Planet Radius (Earth Radii, log scale)",
            "hab_label": "",
        },
        title="Finding Earth-Analogs: Insolation Flux vs. Planet Radius",
    )
    fig1.add_shape(
        type="rect",
        x0=0.36, x1=1.11, y0=0.5, y1=2.5,
        fillcolor="rgba(46, 204, 113, 0.15)",
        line=dict(color="#2ecc71", width=2, dash="dot"),
        layer="below",
    )
    fig1.add_annotation(
        x=0.63, y=2.2,
        text="Goldilocks Zone",
        showarrow=False,
        font=dict(color="#2ecc71", size=12, family="Space Grotesk"),
    )
    fig1.add_scatter(
        x=[1], y=[1],
        mode="markers+text",
        marker=dict(symbol="x", size=14, color=ACCENT, line=dict(width=3)),
        text=["Earth"], textposition="top right",
        textfont=dict(color=TEXT, family="Space Grotesk"),
        name="Earth",
    )
    st.plotly_chart(styled(fig1), use_container_width=True)
    with st.expander("About this chart"):
        st.markdown(
            "Each dot is an exoplanet. The **x-axis** shows how much stellar energy it receives "
            "compared to Earth (Earth = 1), and the **y-axis** shows its size relative to Earth. "
            "The green shaded box is the **Goldilocks Zone** — the range of stellar energy where "
            "liquid water could theoretically exist on a planet's surface. "
            "The vast majority of known exoplanets fall far to the right of this zone, meaning "
            "they receive far too much energy and are too hot to be habitable. "
            "The handful of green dots inside the box are the best candidates we've found so far."
        )

# ── Tab 2: Discovery Timeline ─────────────────────────────────────────────────
with tab2:
    timeline_df = df.dropna(subset=["disc_year", "pl_eqt"])
    fig2 = px.scatter(
        timeline_df,
        x="disc_year",
        y="pl_eqt",
        color="hab_label",
        color_discrete_map={
            HAB_LABEL_MAP[True]:  "#2ecc71",
            HAB_LABEL_MAP[False]: "#5dade2",
        },
        trendline="ols",
        trendline_scope="overall",
        trendline_color_override="#ff6b6b",
        hover_name="pl_name",
        hover_data={"disc_year": True, "pl_eqt": ":.0f", "hab_label": False},
        labels={
            "disc_year": "Year of Discovery",
            "pl_eqt":    "Equilibrium Temperature (K)",
            "hab_label": "",
        },
        title="Evolution of Discovery: Are Cooler Planets Found Over Time?",
    )
    fig2.add_hline(
        y=255, line_dash="dash", line_color="#00d4ff",
        annotation_text="Earth ~255 K",
        annotation_font=dict(color="#00d4ff", family="Space Grotesk"),
    )
    st.plotly_chart(styled(fig2), use_container_width=True)
    with st.expander("About this chart"):
        st.markdown(
            "Each dot is an exoplanet plotted by the year it was discovered and its equilibrium "
            "temperature — the theoretical surface temperature assuming no atmosphere. "
            "The **red trend line** shows a slight downward slope over time, meaning astronomers "
            "are gradually discovering cooler planets as detection technology improves. "
            "Notice that the green (potentially habitable) dots cluster in more recent years — "
            "a sign that our ability to find Earth-like candidates is getting better, "
            "though the trend is still not steep enough to conclude that habitable planets "
            "will become common findings anytime soon."
        )

# ── Tab 3: Temperature by Star Class ─────────────────────────────────────────
with tab3:
    box_df = df.dropna(subset=["pl_eqt", "host_star_class"])
    fig3 = px.box(
        box_df,
        x="host_star_class",
        y="pl_eqt",
        color="host_star_class",
        category_orders={"host_star_class": STAR_ORDER},
        color_discrete_map=STAR_COLORS,
        labels={
            "host_star_class": "Host Star Class (Hottest → Coolest)",
            "pl_eqt":          "Equilibrium Temperature (K)",
        },
        title="Equilibrium Temperature Distribution by Host Star Class",
    )
    fig3.add_hline(
        y=255, line_dash="dash", line_color="#00d4ff",
        annotation_text="Earth ~255 K",
        annotation_font=dict(color="#00d4ff", family="Space Grotesk"),
    )
    st.plotly_chart(styled(fig3), use_container_width=True)
    with st.expander("About this chart"):
        st.markdown(
            "This box plot shows the spread of equilibrium temperatures for planets grouped by "
            "the type of star they orbit, from hottest (F) to coolest (M). "
            "The dashed blue line marks Earth's equilibrium temperature (~255 K). "
            "You might expect planets around cooler M-dwarf stars to be cooler — but the boxes "
            "show that most of them are still far above Earth's temperature. "
            "This is because the **Transit detection method** (by far the most common technique) "
            "is only good at finding planets that orbit very close to their star, "
            "which makes them hot regardless of the star type. "
            "In other words, the scarcity of habitable planets here likely reflects a "
            "**detection bias**, not a true lack of cooler planets."
        )

# ── Tab 4: 3D Explorer ────────────────────────────────────────────────────────
with tab4:
    df3d = df.dropna(subset=["st_teff", "pl_rade", "pl_insol"])
    df3d = df3d[(df3d["pl_rade"] < 30) & (df3d["pl_insol"] < 100)]
    fig4 = px.scatter_3d(
        df3d,
        x="st_teff",
        y="pl_rade",
        z="pl_insol",
        color="host_star_class",
        category_orders={"host_star_class": STAR_ORDER},
        color_discrete_map=STAR_COLORS,
        hover_name="pl_name",
        hover_data={"st_teff": ":.0f", "pl_rade": ":.2f", "pl_insol": ":.2f"},
        labels={
            "st_teff":         "Stellar Temp (K)",
            "pl_rade":         "Planet Radius (Earth Radii)",
            "pl_insol":        "Insolation Flux",
            "host_star_class": "Star Class",
        },
        title="3D Explorer: Stellar Temperature × Planet Size × Stellar Energy",
        opacity=0.8,
    )
    fig4.update_layout(
        scene=dict(
            bgcolor=CARD_BG,
            xaxis=dict(backgroundcolor=CARD_BG, gridcolor=GRID_COLOR, color=TEXT),
            yaxis=dict(backgroundcolor=CARD_BG, gridcolor=GRID_COLOR, color=TEXT),
            zaxis=dict(backgroundcolor=CARD_BG, gridcolor=GRID_COLOR, color=TEXT),
        ),
        paper_bgcolor=CARD_BG,
        font=dict(color=TEXT, family="Space Grotesk"),
        legend=dict(bgcolor=CARD_BG, bordercolor=BORDER, borderwidth=2,
                    font=dict(color=TEXT)),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    st.plotly_chart(fig4, use_container_width=True)
    with st.expander("About this chart"):
        st.markdown(
            "This interactive 3D chart lets you explore three key properties simultaneously: "
            "**stellar temperature** (how hot the host star is), "
            "**planet radius** (how big the planet is relative to Earth), and "
            "**insolation flux** (how much stellar energy the planet receives). "
            "Each dot is colored by star class — from the hotter F-type stars (gold) "
            "to the cooler M-type red dwarfs (dark red). "
            "You can click and drag to rotate the chart, scroll to zoom, and hover over "
            "any point to see the planet's name and exact values. "
            "Look for planets that are low on the insolation flux axis and close to Earth's "
            "radius — those are the most promising habitable candidates."
        )