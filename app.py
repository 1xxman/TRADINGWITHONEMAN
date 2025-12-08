import streamlit as st
from sodapy import Socrata
import pandas as pd

# -----------------------------
# STREAMLIT CONFIG
# -----------------------------
st.set_page_config(page_title="COT Non-Commercial Report", layout="wide")
st.title("📊 COT Non-Commercial Positioning (Latest Data)")

# -----------------------------
# CONFIG
# -----------------------------
DOMAIN = "publicreporting.cftc.gov"
DATASET = "6dca-aqww"

INSTRUMENTS = [
    "EURO FX",
    "BRITISH POUND",
    "JAPANESE YEN",
    "CANADIAN DOLLAR",
    "SWISS FRANC",
    "AUSTRALIAN DOLLAR",
    "NEW ZEALAND DOLLAR",
    "US DOLLAR INDEX",
    "S&P 500",
    "NASDAQ-100",
    "DOW JONES INDUSTRIAL AVERAGE",
    "GOLD",
    "SILVER",
    "CRUDE OIL WTI"
]

# -----------------------------
# DATA FETCH
# -----------------------------
@st.cache_data(ttl=86400)  # Cache for 24h (safe for weekly updates)
def load_data():
    client = Socrata(DOMAIN, None)

    latest_date = client.get(
        DATASET,
        select="max(report_date_as_yyyy_mm_dd)"
    )[0]["max_report_date_as_yyyy_mm_dd"]

    results = client.get(
        DATASET,
        where=f"""
            report_date_as_yyyy_mm_dd = '{latest_date}'
            AND commodity_name in ({','.join([f"'{i}'" for i in INSTRUMENTS])})
        """,
        select="""
            commodity_name,
            noncommercial_long_all,
            change_in_noncommercial_long_all,
            noncommercial_short_all,
            change_in_noncommercial_short_all
        """
    )

    df = pd.DataFrame(results)

    numeric_cols = [
        "noncommercial_long_all",
        "change_in_noncommercial_long_all",
        "noncommercial_short_all",
        "change_in_noncommercial_short_all"
    ]

    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    table = pd.DataFrame()
    table["Instrument"] = df["commodity_name"]
    table["Long Positions"] = df["noncommercial_long_all"]
    table["Change (Long)"] = df["change_in_noncommercial_long_all"]
    table["Short Positions"] = df["noncommercial_short_all"]
    table["Change (Short)"] = df["change_in_noncommercial_short_all"]

    table["Net Positions"] = table["Long Positions"] - table["Short Positions"]
    table["Net Change"] = table["Change (Long)"] - table["Change (Short)"]

    table = table[
        [
            "Instrument",
            "Net Positions",
            "Net Change",
            "Long Positions",
            "Change (Long)",
            "Short Positions",
            "Change (Short)"
        ]
    ]

    return table, latest_date

table, latest_date = load_data()

# -----------------------------
# STYLING
# -----------------------------
def color_net_change(val):
    if val > 0:
        return "color: blue; font-weight: bold"
    elif val < 0:
        return "color: red; font-weight: bold"
    return ""

styled_table = table.style.applymap(
    color_net_change,
    subset=["Net Change"]
)

# -----------------------------
# DISPLAY
# -----------------------------
st.caption(f"📅 Latest CFTC Report: {latest_date}")
st.dataframe(styled_table, use_container_width=True)
