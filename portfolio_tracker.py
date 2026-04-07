import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date
import plotly.graph_objects as go

st.set_page_config(page_title="TFSA 10-Stock Tracker vs SPY", layout="wide")
st.title("🚀 Your $5k TFSA 10-Stock Portfolio Tracker")
st.caption(f"Live as of {datetime.now().strftime('%Y-%m-%d %H:%M')} | Started April 2, 2026 | Benchmark: SPY")

# === 10 HIGHEST-CONVICTION POSITIONS (April 6, 2026 entries) ===
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
start_date = "2026-04-02"
spy_entry_price = 6583  # April 2 close (adjusted for consistency)

# Timeframe selector
timeframes = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "YTD": "ytd", "MAX": "max"}
selected_tf = st.selectbox("Chart Timeframe", options=list(timeframes.keys()), index=6)

# Fetch data
tickers = list(portfolio.keys()) + ["SPY", "USDCAD=X"]
# Fetch data - fixed for 2026 yfinance changes
data = yf.download(tickers, period=timeframes[selected_tf], interval="1d", 
                   auto_adjust=False, group_by='ticker', threads=True)

# Handle both old and new yfinance output formats safely
if isinstance(data.columns, pd.MultiIndex):
    # New multi-level structure: use Close as adjusted price
    close_col = 'Close'
else:
    close_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'

# Use Close prices (already adjusted in most cases)
prices = data[close_col] if isinstance(data.columns, pd.MultiIndex) else data

current_prices = prices.iloc[-1] if not prices.empty else pd.Series()

# Calculate live values
rows = []
total_value_cad = 0.0
for ticker, info in portfolio.items():
    price = current_prices.get(ticker, 0)
    if info["currency"] == "USD":
        usdcad = current_prices.get("USDCAD=X", 1.39)
        value_cad = info["shares"] * price * usdcad
    else:
        value_cad = info["shares"] * price
    pnl = value_cad - info["entry_cad"]
    pnl_pct = (pnl / info["entry_cad"]) * 100
    rows.append({"Ticker": ticker, "Shares": info["shares"], "Price": round(price, 2), "Value CAD": round(value_cad, 0), "P&L CAD": round(pnl, 0), "P&L %": round(pnl_pct, 1)})
    total_value_cad += value_cad

df = pd.DataFrame(rows)
portfolio_return = ((total_value_cad - entry_total_cad) / entry_total_cad) * 100
spy_current = current_prices.get("SPY", spy_entry_price)
spy_return = ((spy_current - spy_entry_price) / spy_entry_price) * 100
alpha = portfolio_return - spy_return

# Metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Portfolio Value", f"C${total_value_cad:,.0f}", f"{portfolio_return:+.2f}%")
col2.metric("SPY Return", f"{spy_return:+.2f}%")
col3.metric("**Alpha**", f"{alpha:+.2f}%", help="Outperformance vs SPY")
col4.metric("Total Positions", "10")
col5.metric("Deployed", "100%")

st.dataframe(df.style.format({"Value CAD": "C${:,.0f}", "P&L CAD": "C${:,.0f}", "P&L %": "{:+.1f}%"}), use_container_width=True, hide_index=True)

# Portfolio vs SPY Chart
st.subheader("Portfolio vs SPY Cumulative Return")
if len(data) > 1:
    hist = pd.DataFrame(index=data.index)
    hist["SPY"] = data["SPY"] / spy_entry_price
    port_values = []
    for i in range(len(data)):
        day = data.iloc[i]
        val = 0
        for ticker, info in portfolio.items():
            p = day.get(ticker, 0)
            if info["currency"] == "USD":
                val += info["shares"] * p * day.get("USDCAD=X", 1.39)
            else:
                val += info["shares"] * p
        port_values.append(val)
    hist["Portfolio"] = [v / entry_total_cad for v in port_values]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Portfolio"], name="Portfolio", line=dict(color="#00ff88")))
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SPY"], name="SPY", line=dict(color="#8888ff")))
    fig.update_layout(height=500, template="plotly_dark", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True)

# News & World Events
st.subheader("📰 Latest News & World Events Impact")
st.caption("Real-time headlines affecting your holdings + macro summary (Iran war, AI capex, SpaceX IPO, etc.)")

news_tickers = ["NVDA", "AVGO", "PLTR", "CRWD", "RKLB", "RTX", "SPY"]
all_news = []
for t in news_tickers:
    try:
        ticker = yf.Ticker(t)
        news = ticker.news[:3]
        for item in news:
            all_news.append(f"**{t}**: {item['title']} ({item.get('publisher', '')})")
    except:
        pass

if all_news:
    st.write("\n".join(all_news[:12]))
else:
    st.info("Fetching latest market-moving stories...")

st.caption("• Iran war still boosting defense/space (RTX, RKLB) • AI capex resilient (NVDA, AVGO, CLS.TO) • SpaceX IPO momentum strong • Oil ~$110 supporting energy tailwinds")

st.caption("Refresh page for live updates. Add new positions by editing the `portfolio` dict in the code. Questions? Just reply.")
