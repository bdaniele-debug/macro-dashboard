import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="Macro Auto-Pilot", layout="wide", page_icon="⚡")

# --- CUSTOM CSS (Cyberpunk Look) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .metric-card {
        background-color: #1e1e24;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .bull { color: #00ff41; font-weight: bold; font-size: 1.2rem; }
    .bear { color: #ff0055; font-weight: bold; font-size: 1.2rem; }
    .neutral { color: #ffcc00; font-weight: bold; font-size: 1.2rem; }
    h1, h2, h3 { color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# --- 1. DATA FETCHING FUNCTION ---
@st.cache_data(ttl=300) # Cache data for 5 mins to save speed
def get_macro_data():
    # Tickers: US30(DJI), Guppy, 10Y Yield, VIX, DXY
    tickers = ["^DJI", "GBPJPY=X", "^TNX", "^VIX", "DX-Y.NYB", "GBPUSD=X", "JPY=X"]
    data = yf.download(tickers, period="5d", interval="1d")
    
    # Get latest closes
    latest = data['Close'].iloc[-1]
    prev = data['Close'].iloc[-2]
    
    changes = ((latest - prev) / prev) * 100
    
    return latest, changes

# Load Data
try:
    prices, changes = get_macro_data()
except:
    st.error("Error fetching data. Yahoo Finance might be down.")
    st.stop()

# --- 2. AUTOMATED LOGIC ENGINE ---

# US30 LOGIC
# Bullish if: Yields (TNX) are DOWN and VIX is DOWN
us30_score = 0
if changes['^TNX'] < 0: us30_score += 1 # Yields dropping is good for stocks
if prices['^TNX'] < 4.0: us30_score += 1 # Low absolute yields
if changes['^VIX'] < 0: us30_score += 1 # Fear dropping
if prices['^DJI'] > 34000: us30_score += 1 # Trend is up (simple filter)

if us30_score >= 3:
    us30_bias = "BULLISH 🚀"
    us30_color = "bull"
    us30_reason = "Yields are easing and Fear (VIX) is low. Risk-on environment."
elif us30_score <= 1:
    us30_bias = "BEARISH 🩸"
    us30_color = "bear"
    us30_reason = "Rising Yields or High Fear are pressuring equities."
else:
    us30_bias = "CHOPPY ⚠️"
    us30_color = "neutral"
    us30_reason = "Mixed signals. VIX and Yields are diverging."

# GBPJPY LOGIC
# Bullish if: GBP is strong, JPY is weak (Carry Trade)
# JPY=X in Yahoo is usually USD/JPY. If USDJPY is UP, JPY is WEAK.
gj_score = 0
if changes['GBPUSD=X'] > 0: gj_score += 1 # Strong Pound
if changes['JPY=X'] > 0: gj_score += 1 # Weak Yen (USDJPY up)
if prices['^VIX'] < 20: gj_score += 1 # Low volatility favors Carry Trade

if gj_score == 3:
    gj_bias = "STRONG BUY 🟢"
    gj_color = "bull"
    gj_reason = "Perfect Storm: Strong GBP + Weak JPY + Low Risk."
elif gj_score == 0:
    gj_bias = "STRONG SELL 🔴"
    gj_color = "bear"
    gj_reason = "Risk Off: Yen buying is crushing the cross."
else:
    gj_bias = "RANGING ↔️"
    gj_color = "neutral"
    gj_reason = "Currencies are fighting. Wait for clear breakout."

# --- 3. DASHBOARD LAYOUT ---

st.title("⚡ MACRO AUTO-PILOT")
st.markdown("Live Automated Analysis | No Checklists Required")

# Top Row: The Verdicts
c1, c2 = st.columns(2)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>🇺🇸 US30 (DOW)</h3>
        <div class="{us30_color}">{us30_bias}</div>
        <p style="font-size: 0.8rem; margin-top: 10px;">{us30_reason}</p>
        <hr style="border-color: #333;">
        <div style="display:flex; justify-content:space-around;">
            <div>
                <span style="color:#888; font-size:0.8rem;">10Y YIELD</span><br>
                {prices['^TNX']:.2f}% <span style="color:{'#ff4b4b' if changes['^TNX'] > 0 else '#00ff41'}">{changes['^TNX']:+.2f}%</span>
            </div>
            <div>
                <span style="color:#888; font-size:0.8rem;">VIX (FEAR)</span><br>
                {prices['^VIX']:.2f} <span style="color:{'#ff4b4b' if changes['^VIX'] > 0 else '#00ff41'}">{changes['^VIX']:+.2f}%</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>🇬🇧/🇯🇵 GU (GBPJPY)</h3>
        <div class="{gj_color}">{gj_bias}</div>
        <p style="font-size: 0.8rem; margin-top: 10px;">{gj_reason}</p>
        <hr style="border-color: #333;">
        <div style="display:flex; justify-content:space-around;">
            <div>
                <span style="color:#888; font-size:0.8rem;">GBP STRENGTH</span><br>
                <span style="color:{'#00ff41' if changes['GBPUSD=X'] > 0 else '#ff4b4b'}">{changes['GBPUSD=X']:+.2f}%</span>
            </div>
            <div>
                <span style="color:#888; font-size:0.8rem;">YEN WEAKNESS</span><br>
                <span style="color:{'#00ff41' if changes['JPY=X'] > 0 else '#ff4b4b'}">{changes['JPY=X']:+.2f}%</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Middle Row: Charts & News
t1, t2 = st.tabs(["📊 LIVE CHARTS", "📅 FTMO RADAR"])

with t1:
    # Embedding TradingView Advanced Chart Widget
    components.html("""
    <div class="tradingview-widget-container" style="height:500px">
      <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
      {
      "autosize": true,
      "symbol": "FOREXCOM:DJI",
      "interval": "D",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "calendar": false,
      "support_host": "https://www.tradingview.com"
    }
      </script>
    </div>
    """, height=500)

with t2:
    st.warning("⚠️ FTMO RULE: Do not trade 2 minutes before/after Red Folder news.")
    # Embedding TradingView Economic Calendar (Filtered for High Importance)
    components.html("""
    <div class="tradingview-widget-container" style="height:600px">
      <div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "width": "100%",
      "height": "100%",
      "colorTheme": "dark",
      "isTransparent": false,
      "locale": "en",
      "importanceFilter": "1",
      "currencyFilter": "USD,GBP,JPY"
    }
      </script>
    </div>
    """, height=600)
