import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="TFSA 10-Stock Tracker", layout="wide")
st.title("🚀 Your $5k TFSA 10-Stock Portfolio Tracker vs SPY")
st.caption(f"Live as of {datetime.now().strftime('%Y-%m-%d %H:%M')} | Started April 2, 2026 | Benchmark: SPY")

# 10 Highest-Conviction Positions (April 6 targets)
portfolio = {
    "NVDA":  {"entry_cad": 700, "shares": 3.95, "currency": "USD"},
    "AVGO":  {"entry_cad": 650, "shares": 2.06, "currency": "USD"},
    "CLS.TO":{"entry_cad": 600, "shares": 1.46, "currency": "CAD"},
    "SHOP.TO":{"entry_cad": 550, "shares": 3.33, "currency": "CAD"},
    "KXS.TO":{"entry_cad": 500, "shares": 3.50, "currency": "CAD"},
    "PLTR":  {"entry_cad": 450, "shares": 2.90, "currency": "USD"},
    "ARM":   {"entry_cad": 450, "shares": 3.00, "currency": "USD"},
    "CRWD":  {"entry_cad": 400, "shares": 1.00, "currency": "USD"},
    "RKLB":  {"entry_cad": 400, "shares": 5.88, "currency": "USD"},
    "RTX":   {"entry_cad": 300, "shares": 2.31, "currency": "USD"},
}

entry_total_cad = 5000.0
spy_entry_price = 6583.0

timeframes = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "YTD": "ytd", "MAX": "max"}
selected_tf = st.selectbox("Chart Timeframe", options=list(timeframes.keys()), index=6)

tickers = list(portfolio.keys()) + ["SPY", "USDCAD=X"]

# Safe data download for Streamlit Cloud + 2026 yfinance
data = yf.download(tickers, period=timeframes[selected_tf], interval="1d", 
                   auto_adjust=False, group_by='ticker', threads=False)

# Safe Close price extraction
if isinstance(data.columns, pd.MultiIndex):
    close_prices = data.xs('Close', level=1, axis=1)
else:
    close_prices = data.get('Close', data)

prices = close_prices
current_prices = prices.iloc[-1] if not prices.empty else pd.Series()

# Portfolio calculations
rows = []
total_value_cad = 0.0
for ticker, info in portfolio.items():
    price = float(current_prices.get(ticker, 0))
    usdcad = float(current_prices.get("USDCAD=X", 1.39))
    if info["currency"] == "USD":
        value_cad = info["shares"] * price * usdcad
    else:
        value_cad = info["shares"] * price
    pnl = value_cad - info["entry_cad"]
    pnl_pct = (pnl / info["entry_cad"]) * 100 if info["entry_cad"] != 0 else 0
    rows.append({
        "Ticker": ticker,
        "Shares": round(info["shares"], 4),
        "Price": round(price, 2),
        "Value CAD": round(value_cad, 0),
        "P&L CAD": round(pnl, 0),
        "P&L %": round(pnl_pct, 1)
    })
    total_value_cad += value_cad

df = pd.DataFrame(rows)
portfolio_return = ((total_value_cad - entry_total_cad) / entry_total_cad) * 100
spy_current = float(current_prices.get("SPY", spy_entry_price))
spy_return = ((spy_current - spy_entry_price) / spy_entry_price) * 100
alpha = portfolio_return - spy_return

# Metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Portfolio Value", f"C${total_value_cad:,.0f}", f"{portfolio_return:+.2f}%")
col2.metric("SPY Return", f"{spy_return:+.2f}%")
col3.metric("**Alpha vs SPY**", f"{alpha:+.2f}%")
col4.metric("Positions", "10")
col5.metric("Deployed", "100%")

st.dataframe(df.style.format({"Value CAD": "C${:,.0f}", "P&L CAD": "C${:,.0f}", "P&L %": "{:+.1f}%"}), 
             use_container_width=True, hide_index=True)

# Chart
st.subheader("Portfolio vs SPY Cumulative Return")
if len(prices) > 1:
    hist = pd.DataFrame(index=prices.index)
    hist["SPY"] = prices["SPY"] / spy_entry_price
    port_values = []
    for i in range(len(prices)):
        day = prices.iloc[i]
        val = 0.0
        for ticker, info in portfolio.items():
            p = float(day.get(ticker, 0))
            usdcad_day = float(day.get("USDCAD=X", 1.39))
            if info["currency"] == "USD":
                val += info["shares"] * p * usdcad_day
            else:
                val += info["shares"] * p
        port_values.append(val)
    hist["Portfolio"] = [v / entry_total_cad for v in port_values]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Portfolio"], name="Portfolio", line=dict(color="#00ff88")))
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SPY"], name="SPY", line=dict(color="#8888ff")))
    fig.update_layout(height=500, template="plotly_dark", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True)

# News section
st.subheader("📰 Latest News & World Events")
st.caption("Impact from Iran war, AI capex, SpaceX IPO, oil prices, etc.")
news_tickers = ["NVDA", "AVGO", "PLTR", "CRWD", "RKLB", "RTX", "SPY"]
for t in news_tickers:
    try:
        news = yf.Ticker(t).news[:2]
        for item in news:
            st.write(f"**{t}**: {item.get('title', '')}")
    except:
        pass

st.caption("Refresh page for latest data. Iran conflict helping defense/space names. AI spend remains strong.")
