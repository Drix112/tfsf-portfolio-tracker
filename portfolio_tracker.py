import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="TFSA 10-Stock Tracker", layout="wide")
st.title("🚀 Your $5k TFSA 10-Stock Portfolio Tracker vs SPY")
st.caption(f"Live as of {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Start Date: April 7, 2026** | Benchmark: SPY")

# === 10 HIGHEST-CONVICTION POSITIONS ===
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
start_date = "2026-04-07"

timeframes = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "YTD": "ytd", "MAX": "max"}
selected_tf = st.selectbox("📅 Chart Timeframe", options=list(timeframes.keys()), index=3)

@st.cache_data(ttl=180)
def get_history(ticker, period):
    try:
        return yf.Ticker(ticker).history(period=period, start=start_date)
    except:
        return pd.DataFrame()

tickers = list(portfolio.keys()) + ["SPY", "USDCAD=X"]
data = {t: get_history(t, timeframes[selected_tf]) for t in tickers}

current_prices = {t: df['Close'].iloc[-1] if not df.empty else 0 for t, df in data.items()}

# Anchor SPY entry price to first trading day after April 7
spy_df = data["SPY"]
spy_entry_price = spy_df['Close'].iloc[0] if not spy_df.empty else current_prices.get("SPY", 658.0)

# Portfolio calculations
rows = []
total_value_cad = 0.0
for ticker, info in portfolio.items():
    price = current_prices.get(ticker, 0)
    usdcad = current_prices.get("USDCAD=X", 1.39)
    value_cad = info["shares"] * price * (usdcad if info["currency"] == "USD" else 1)
    pnl = value_cad - info["entry_cad"]
    pnl_pct = (pnl / info["entry_cad"]) * 100
    weight = round((value_cad / (total_value_cad + 0.0001)) * 100, 1) if total_value_cad > 0 else 0
    rows.append({
        "Ticker": ticker,
        "Shares": round(info["shares"], 4),
        "Price": round(price, 2),
        "Value CAD": round(value_cad, 0),
        "P&L CAD": round(pnl, 0),
        "P&L %": round(pnl_pct, 1),
        "Weight %": weight
    })
    total_value_cad += value_cad

df = pd.DataFrame(rows)
portfolio_return = ((total_value_cad - entry_total_cad) / entry_total_cad) * 100
spy_current = current_prices.get("SPY", spy_entry_price)
spy_return = ((spy_current - spy_entry_price) / spy_entry_price) * 100
alpha = portfolio_return - spy_return

# Chart at top
st.subheader("Portfolio vs SPY Cumulative Return (since April 7, 2026)")
if not spy_df.empty:
    hist = pd.DataFrame(index=spy_df.index)
    hist["SPY"] = spy_df['Close'] / spy_entry_price
    
    port_values = []
    for idx in hist.index:
        val = 0.0
        for ticker, info in portfolio.items():
            df_t = data[ticker]
            if idx in df_t.index:
                p = df_t.loc[idx]['Close']
                usdcad_day = data["USDCAD=X"].loc[idx]['Close'] if idx in data["USDCAD=X"].index else 1.39
                val += info["shares"] * p * (usdcad_day if info["currency"] == "USD" else 1)
        port_values.append(val)
    hist["Portfolio"] = [v / entry_total_cad for v in port_values]
    hist = hist.dropna()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Portfolio"], name="Portfolio", line=dict(color="#00ff88", width=3)))
    fig.add_trace(go.Scatter(x=hist.index, y=hist["SPY"], name="SPY", line=dict(color="#8888ff", width=3)))
    fig.update_layout(height=500, template="plotly_dark", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True)

# Metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Portfolio Value", f"C${total_value_cad:,.0f}", f"{portfolio_return:+.2f}%")
col2.metric("SPY Return (since Apr 7)", f"{spy_return:+.2f}%")
col3.metric("**Alpha vs SPY**", f"{alpha:+.2f}%", "Outperformance since start date")
col4.metric("Positions", "10")
col5.metric("Deployed", "100%")

# Color-coded P&L table
def color_pnl(val):
    if val > 0:
        return 'color: #00ff88'
    elif val < 0:
        return 'color: #ff4444'
    return 'color: white'

st.dataframe(
    df.style.format({
        "Value CAD": "C${:,.0f}", 
        "P&L CAD": "C${:,.0f}", 
        "P&L %": "{:+.1f}%", 
        "Weight %": "{:.1f}%"
    }).map(color_pnl, subset=["P&L %"]),
    use_container_width=True, 
    hide_index=True
)

# Advanced Metrics
with st.expander("📊 Advanced Performance Metrics"):
    st.write("Since April 7, 2026")
    if len(hist) > 5:
        port_ret = hist["Portfolio"].pct_change().dropna()
        spy_ret = hist["SPY"].pct_change().dropna()
        correlation = port_ret.corr(spy_ret) if len(port_ret) > 1 else 0
        beta = (port_ret.cov(spy_ret) / spy_ret.var()) if spy_ret.var() != 0 else 0
        vol = port_ret.std() * 100 * (252 ** 0.5)
        sharpe = (port_ret.mean() / port_ret.std()) * (252 ** 0.5) if port_ret.std() != 0 else 0
        max_dd = ((hist["Portfolio"] / hist["Portfolio"].cummax()) - 1).min() * 100
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Beta", f"{beta:.2f}")
        m2.metric("Annualized Volatility", f"{vol:.1f}%")
        m3.metric("Correlation to SPY", f"{correlation:.2f}")
        m4.metric("Sharpe Ratio", f"{sharpe:.2f}")
        st.metric("Max Drawdown", f"{max_dd:.1f}%")

# News
st.subheader("📰 Latest News & World Events Impact")
st.caption("Real-time headlines + macro summary (Iran war, AI capex, SpaceX IPO, oil ~$110)")
news_tickers = ["NVDA", "AVGO", "PLTR", "CRWD", "RKLB", "RTX", "SPY"]
news_found = False
for t in news_tickers:
    try:
        news_list = yf.Ticker(t).news
        if news_list:
            for item in news_list[:2]:
                st.write(f"**{t}**: {item.get('title', 'No title')}")
                news_found = True
    except:
        pass
if not news_found:
    st.info("News feed temporarily limited. Key macro points:")
    st.write("• Iran conflict → tailwinds for RTX & RKLB")
    st.write("• AI infrastructure capex remains strong")
    st.write("• SpaceX IPO momentum building")
    st.write("• Oil ~$110 supporting related names")

st.caption("Refresh for live data. Built specifically for your 10-stock TFSA to beat the S&P 500 over 3+ years.")
