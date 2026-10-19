import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

st.set_page_config(page_title="Stock Comparison Dashboard - CPS 5745", layout="wide")

st.title("Interactive Stock Comparison Dashboard")
st.markdown("**Author:** Karanpreet Singh | **Developed for CPS 5745**")

# Shared Filters
st.sidebar.header("Shared Filters")
default_tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]
selected_tickers = st.sidebar.multiselect(
    "Select Companies (at least 3):",
    options=default_tickers,
    default=["AAPL", "MSFT", "NVDA"]
)

start_date = st.sidebar.date_input("Start Date", value=date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("End Date", value=date.today())

if len(selected_tickers) < 3:
    st.warning("Please select at least 3 companies to compare.")
    st.stop()

if start_date >= end_date:
    st.warning("Start Date must be before End Date.")
    st.stop()

@st.cache_data(ttl="1h")
def load_data(tickers, start, end):
    frames = []
    for t in tickers:
        df = yf.download(t, start=start, end=end, progress=False, auto_adjust=True)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.reset_index()
            df["Company"] = t
            df["Daily Return (%)"] = df["Close"].pct_change() * 100
            df["Normalized Price (Base 100)"] = (df["Close"] / df["Close"].iloc[0]) * 100
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

data = load_data(selected_tickers, start_date, end_date)

if data.empty:
    st.error("No price data returned for the selected companies and dates. Try a wider date range.")
    st.stop()

# 1. Normalized Stock Price Trend (Line Chart)
fig1 = px.line(
    data, x="Date", y="Normalized Price (Base 100)", color="Company",
    title="1. Normalized Stock Price Comparison (Base = 100)",
    labels={"Normalized Price (Base 100)": "Normalized Price Index (Base 100)", "Date": "Date"}
)

# 2. Trading Volume Over Time (Grouped Bar Chart)
monthly_vol = data.copy()
monthly_vol["Month"] = monthly_vol["Date"].dt.to_period("M").astype(str)
vol_summary = monthly_vol.groupby(["Month", "Company"], as_index=False)["Volume"].mean()
fig2 = px.bar(
    vol_summary, x="Month", y="Volume", color="Company", barmode="group",
    title="2. Average Daily Trading Volume by Month (Shares)",
    labels={"Volume": "Average Volume (Shares)", "Month": "Month"}
)

# 3. Daily Return Volatility Distribution (Box Plot)
fig3 = px.box(
    data.dropna(subset=["Daily Return (%)"]), x="Company", y="Daily Return (%)", color="Company",
    title="3. Daily Return Volatility Distribution (%)",
    labels={"Daily Return (%)": "Daily Return (%)"}
)

# 4. Closing Price vs. Trading Volume (Scatter Plot)
fig4 = px.scatter(
    data, x="Volume", y="Close", color="Company", opacity=0.7,
    title="4. Closing Price (USD) vs. Daily Trading Volume (Shares)",
    labels={"Volume": "Daily Volume (Shares)", "Close": "Closing Price (USD)"}
)

# 5. Cumulative Return Comparison (Horizontal Bar Chart)
cum_returns = data.groupby("Company")["Close"].agg(
    lambda c: (c.iloc[-1] - c.iloc[0]) / c.iloc[0] * 100
).reset_index(name="Cumulative Return (%)")
fig5 = px.bar(
    cum_returns.sort_values("Cumulative Return (%)"),
    x="Cumulative Return (%)", y="Company", color="Company", orientation="h",
    title="5. Total Cumulative Return Over Selected Period (%)",
    labels={"Cumulative Return (%)": "Total Return (%)"}
)

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig1, width="stretch")
    st.plotly_chart(fig3, width="stretch")
with col2:
    st.plotly_chart(fig2, width="stretch")
    st.plotly_chart(fig4, width="stretch")

st.plotly_chart(fig5, width="stretch")

st.subheader("Key Differences Revealed by the Visualizations")
st.write(
    "Across the selected date range, the normalized price chart and cumulative return bar chart reveal which company "
    "delivered the strongest relative capital appreciation regardless of absolute share price differences. "
    "The box plot highlights differences in risk and daily return dispersion, while the volume bar and scatter charts "
    "illustrate liquidity differences and how trading activity correlates with price levels across the selected companies."
)
