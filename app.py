
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="PulseIQ | Workforce Dashboard",
    page_icon="📊",
    layout="wide"
)

DATA_DIR = Path(__file__).parent / "public_data"
HEADCOUNT_FILE = DATA_DIR / "headcount_monthly.parquet"
FORECAST_FILE = DATA_DIR / "forecasts.parquet"


# --------------------------------------------------
# LOAD PUBLIC DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    headcount = pd.read_parquet(HEADCOUNT_FILE)
    forecasts = pd.read_parquet(FORECAST_FILE)

    headcount["month_start_date"] = pd.to_datetime(
        headcount["month_start_date"]
    )

    forecasts["forecast_month"] = pd.to_datetime(
        forecasts["forecast_month"]
    )

    return headcount, forecasts


try:
    headcount, forecasts = load_data()

except Exception as exc:
    st.error(f"Could not load dashboard data: {exc}")
    st.stop()


# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------

st.title("📊 PulseIQ Workforce Dashboard")

st.caption(
    "Workforce overview | Privacy-safe aggregate data"
)

latest_available = headcount["month_start_date"].max()

st.info(
    f"Historical data available through: "
    f"**{latest_available.strftime('%B %Y')}**"
)


# --------------------------------------------------
# DEPARTMENT FILTER
# --------------------------------------------------

departments = sorted(
    headcount["department_id"].unique().tolist()
)

selected_department = st.sidebar.selectbox(
    "Select Department",
    ["All departments"] + departments
)

if selected_department == "All departments":
    filtered = headcount.copy()
    forecast_department = "ALL"
else:
    filtered = headcount[
        headcount["department_id"] == selected_department
    ].copy()

    forecast_department = selected_department


if filtered.empty:
    st.warning("No data available for this selection.")
    st.stop()


# --------------------------------------------------
# HEADCOUNT KPIs
# --------------------------------------------------

latest_month = filtered["month_start_date"].max()

previous_month = latest_month - pd.DateOffset(months=1)

latest_data = filtered[
    filtered["month_start_date"] == latest_month
]

previous_data = filtered[
    filtered["month_start_date"] == previous_month
]

latest_count = int(latest_data["headcount_end"].sum())

previous_count = int(previous_data["headcount_end"].sum())

change = latest_count - previous_count

c1, c2, c3 = st.columns(3)

c1.metric(
    "Latest visible headcount",
    f"{latest_count:,}"
)

c2.metric(
    "Previous month",
    f"{previous_count:,}"
)

c3.metric(
    "Month-on-month change",
    f"{change:+,}"
)


# --------------------------------------------------
# HISTORICAL HEADCOUNT TREND
# --------------------------------------------------

st.divider()

st.subheader("1. Historical Headcount Trend")

trend = (
    filtered.groupby("month_start_date", as_index=False)
    ["headcount_end"]
    .sum()
    .sort_values("month_start_date")
)

st.line_chart(
    trend.set_index("month_start_date")["headcount_end"],
    y_label="Headcount"
)


# --------------------------------------------------
# DEPARTMENT COMPARISON
# --------------------------------------------------

st.subheader("2. Department Headcount")

latest_all = headcount[
    headcount["month_start_date"] == latest_available
]

department_comparison = (
    latest_all.groupby("department_id", as_index=False)
    ["headcount_end"]
    .sum()
    .sort_values("headcount_end", ascending=False)
)

st.bar_chart(
    department_comparison.set_index("department_id")["headcount_end"],
    horizontal=True
)


# --------------------------------------------------
# HEADCOUNT FORECAST
# --------------------------------------------------

st.divider()

st.subheader("3. Headcount Forecast")

forecast_data = forecasts[
    forecasts["department_id"] == forecast_department
].copy()

forecast_data = forecast_data.sort_values("forecast_month")

if not forecast_data.empty:

    st.line_chart(
        forecast_data.set_index("forecast_month")["forecast_value"],
        y_label="Forecast headcount"
    )

    st.write("Forecast details")

    display_forecast = forecast_data[
        [
            "forecast_month",
            "forecast_value",
            "lower_80",
            "upper_80"
        ]
    ].copy()

    display_forecast["forecast_month"] = (
        display_forecast["forecast_month"].dt.strftime("%B %Y")
    )

    display_forecast = display_forecast.rename(
        columns={
            "forecast_month": "Month",
            "forecast_value": "Forecast",
            "lower_80": "Lower range (80%)",
            "upper_80": "Upper range (80%)"
        }
    )

    st.dataframe(
        display_forecast,
        hide_index=True,
        use_container_width=True
    )

    st.caption(
        "Forecast estimates are based on the available baseline model. "
        "The lower and upper values represent the 80% forecast interval."
    )

else:
    st.warning(
        "No forecast is available for this department."
    )


# --------------------------------------------------
# PRIVACY AND METHODOLOGY
# --------------------------------------------------

st.divider()

st.subheader("About this Dashboard")

st.write(
    "PulseIQ presents historical workforce information and "
    "headcount forecasts using privacy-filtered aggregate data."
)

st.caption(
    "Employee-level records, personal identifiers, salaries and "
    "confidential database tables are not included in this public dashboard. "
    "Small department groups are excluded from publication."
)
