import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import datetime
import time
import streamlit.components.v1 as components

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Macro Dashboard",
    layout="wide",
    page_icon="💎",
    initial_sidebar_state="collapsed"
)

# --- AUTO-REFRESH (5 Minutes) ---
st.markdown("""
    <meta http-equiv="refresh" content="300">
    """, unsafe_allow_html=True)

# --- CSS STYLING ---
st.markdown("""
<style>
    /* 1. BACKGROUND */
    .stApp { 
        background-color: #050505; 
        color: #E0E0E0; 
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* 2. METRIC CARDS (Top Row) */
    .metric-box {
        background: #0F0F0F;
        border: 1px solid #333; 
        border-radius: 12px; 
        padding: 20px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 120px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-lbl { 
        font-size: 0.85rem; 
        color: #888; 
        font-weight: 700; 
        text-transform: uppercase; 
        margin-bottom: 8px;
    }
    .metric-val { font-size: 1.8rem; font-weight: 800; color: #fff; }

    /* 3. MACRO CARDS (Blue Border) */
    .macro-card-container {
        border: 2px solid #2962FF;
        border-radius: 15px;
        background-color: #0a0a0a;
        overflow: hidden;
        margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(41, 98, 255, 0.1);
    }
    
    .card-header {
        background: rgba(41, 98, 255, 0.15);
        padding: 15px 20px;
        border-bottom: 1px solid #2962FF;
        font-weight: 900;
        font-size: 1.1rem;
        color: #fff;
        text-transform: uppercase;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .card-body {
        padding: 20px;
    }

    /* 4. ASSET ANALYSIS STYLES */
    .verdict-box {
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        margin-bottom: 20px;
    }
    .verdict-text { font-size: 2rem; font-weight: 900; }
    
    .factor-table {
        background: #111;
        border-radius: 8px;
        padding: 15px;
        width: 100%;
    }
    .factor-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #333;
        font-size: 0.9rem;
    }
    .factor-row:last-child { border-bottom: none; }
    .factor-label { color: #aaa; }
    .factor-value { font-weight: bold; }

    /* 5. NEWS STYLES */
    .news-item {
        padding: 12px 0;
        border-bottom: 1px solid #222;
    }
    .news-link {
        color: #fff;
        text-decoration: none;
        font-weight: 600;
        font-size: 1.05rem;
        display: block;
        margin-bottom: 4px;
    }
    .news-link:hover { color: #2962FF; }
    .news-date { font-size: 0.8rem; color: #666; }

    /* RING CHART CSS */
    .ring-container {
        position: relative;
        width: 100px; height: 100px;
        border-radius: 50%;
        background: conic-gradient(var(--ring-color) var(--ring-pct), #222 0);
        display: flex; align-items: center; justify-content: center;
    }
    .ring-inner {
        width: 84px; height: 84px;
        background: #0a0a0a;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; color: white; font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA ENGINE (ROBUST VERSION) ---
@st.cache_data(ttl=300) 
def get_data():
    # Fallback list: If T5YIE fails, we use TNX.
    tickers = ["^TNX", "^IRX", "^T5YIE", "^VIX", "DX-Y.NYB", "GBPUSD=X", "JPY=X", "^DJI"]
    
    try:
        data = yf.download(tickers, period="5d", interval="1d", progress=False)
        # Flatten MultiIndex if present
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs('Close', axis=1, level=0)
    except Exception as e:
        return {}

    res = {}
    for t in tickers:
        try:
            s = data[t].dropna()
            if len(s) >= 2:
                latest = s.iloc[-1]
                prev = s.iloc[-2]
                change = ((latest - prev) / prev) * 100
                res[t] = {"price": latest, "change": change}
            else:
                # Fallback for empty data
                res[t] = {"price": 0.0, "change": 0.0}
        except:
            res[t] = {"price": 0.0, "change": 0.0}
            
    # CRITICAL FIX: If Breakeven Inflation (T5YIE) is 0 (Yahoo bug), use 10Y Yield as proxy
    if res.get("^T5YIE", {}).get("price", 0) == 0:
        res["^T5YIE"] = res["^TNX"] 

    return res

@st.cache_data(ttl=600)
def get_news():
    feed_url = "https://www.cnbc.com/id/10000664/device/rss/rss.html"
    try:
        feed = feedparser.parse(feed_url)
        return feed.entries[:6]
    except:
        return []

market = get_data()
news_data = get_news()

# --- TOP METRICS ---
c1, c2, c3, c4 = st.columns(4)

def render_metric(col, title, key, invert=False, is_pct=False):
    d = market.get(key, {'price':0.0, 'change':0.0})
    val = f"{d['price']:.2f}%" if is_pct else f"{d['price']:.2f}"
    chg = d['change']
    
    # Color Logic
    color = "#00E676" # Green
    if invert: # For VIX/Inflation, UP is RED
        if chg > 0: color = "#FF1744"
    else: # For Asset, DOWN is RED
        if chg < 0: color = "#FF1744"
        
    arrow = "▲" if chg > 0 else "▼"
    
    col.markdown(f"""
    <div class="metric-box">
        <div class="metric-lbl">{title}</div>
        <div class="metric-val">{val}</div>
        <div style="color:{color}; font-weight:bold; font-size:0.9rem; margin-top:5px;">
            {arrow} {abs(chg):.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

# RENDER TOP ROW
render_metric(c1, "MKT INFLATION (5Y)", "^T5YIE", invert=True, is_pct=True)
render_metric(c2, "FED PROXY (13W)", "^IRX", invert=True, is_pct=True)
render_metric(c3, "RISK (VIX)", "^VIX", invert=True)
render_metric(c4, "DOLLAR (DXY)", "DX-Y.NYB", invert=True)

st.markdown("<div style='margin-bottom: 25px'></div>", unsafe_allow_html=True)

# --- ASSET CARDS ---
col_us, col_gj = st.columns(2)

# === US30 LOGIC & RENDER ===
with col_us:
    # Logic
    us_score = 50
    inf = market.get('^T5YIE', {'change':0})['change']
    rates = market.get('^IRX', {'change':0})['change']
    vix_p = market.get('^VIX', {'price':0})['price']
    
    if inf > 0.5: us_score -= 20
    elif inf < -0.5: us_score += 20
    if rates > 1.0: us_score -= 20
    elif rates < -1.0: us_score += 20
    if vix_p < 16: us_score += 15
    elif vix_p > 21: us_score -= 25
    
    us_score = max(0, min(100, us_score))
    u_color = "#00E676" if us_score > 60 else "#FF1744" if us_score < 40 else "#FFCC00"
    u_txt = "BULLISH" if us_score > 60 else "BEARISH" if us_score < 40 else "NEUTRAL"
    
    # HTML Render
    st.markdown(f"""
    <div class="macro-card-container">
        <div class="card-header">
            <span>🇺🇸 US30 (Dow Jones)</span>
            <span style="font-size:0.8rem; opacity:0.7">EQUITY MODEL</span>
        </div>
        <div class="card-body">
            <div class="verdict-box">
                <div>
                    <div class="verdict-text" style="color:{u_color}">{u_txt}</div>
                    <div style="color:#666; font-size:0.8rem;">Algorithmic Verdict</div>
                </div>
                <div class="ring-container" style="--ring-color:{u_color}; --ring-pct:{us_score}%;">
                    <div class="ring-inner">{us_score}%</div>
                </div>
            </div>
            <div class="factor-table">
                <div class="factor-row">
                    <span class="factor-label">Inflation Breakevens</span>
                    <span class="factor-value" style="color:{'#FF1744' if inf > 0 else '#00E676'}">{inf:+.2f}%</span>
                </div>
                <div class="factor-row">
                    <span class="factor-label">Fed Rate Proxy (13W)</span>
                    <span class="factor-value" style="color:{'#FF1744' if rates > 0 else '#00E676'}">{rates:+.2f}%</span>
                </div>
                <div class="factor-row">
                    <span class="factor-label">Risk Premium (VIX)</span>
                    <span class="factor-value" style="color:{'#FF1744' if vix_p > 20 else '#00E676'}">{vix_p:.2f}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# === GBPJPY LOGIC & RENDER ===
with col_gj:
    # Logic
    gj_score = 50
    gbp = market.get('GBPUSD=X', {'change':0})['change']
    jpy = market.get('JPY=X', {'change':0})['change'] # Positive = Yen Weak
    
    if gbp > 0.1: gj_score += 20
    elif gbp < -0.1: gj_score -= 20
    if jpy > 0.1: gj_score += 30
    elif jpy < -0.1: gj_score -= 30
    
    gj_score = max(0, min(100, gj_score))
    g_color = "#00E676" if gj_score > 60 else "#FF1744" if gj_score < 40 else "#FFCC00"
    g_txt = "LONG (BUY)" if gj_score > 60 else "SHORT (SELL)" if gj_score < 40 else "RANGING"

    st.markdown(f"""
    <div class="macro-card-container">
        <div class="card-header">
            <span>💱 GBPJPY (The Beast)</span>
            <span style="font-size:0.8rem; opacity:0.7">YIELD SPREAD MODEL</span>
        </div>
        <div class="card-body">
            <div class="verdict-box">
                <div>
                    <div class="verdict-text" style="color:{g_color}">{g_txt}</div>
                    <div style="color:#666; font-size:0.8rem;">Algorithmic Verdict</div>
                </div>
                <div class="ring-container" style="--ring-color:{g_color}; --ring-pct:{gj_score}%;">
                    <div class="ring-inner">{gj_score}%</div>
                </div>
            </div>
            <div class="factor-table">
                <div class="factor-row">
                    <span class="factor-label">GBP Strength</span>
                    <span class="factor-value" style="color:{'#00E676' if gbp > 0 else '#FF1744'}">{gbp:+.2f}%</span>
                </div>
                <div class="factor-row">
                    <span class="factor-label">Yen Weakness (Carry)</span>
                    <span class="factor-value" style="color:{'#00E676' if jpy > 0 else '#FF1744'}">{jpy:+.2f}%</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- NEWS & CALENDAR (FIXED LAYOUT) ---
c_news, c_cal = st.columns(2)

with c_news:
    # Build the HTML list first
    news_html = ""
    if news_data:
        for item in news_data:
            try:
                dt = time.strftime("%a, %d %b %H:%M", item.published_parsed)
            except: dt = "Recent"
            news_html += f"""
            <div class="news-item">
                <a href="{item.link}" target="_blank" class="news-link">{item.title}</a>
                <span class="news-date">{dt}</span>
            </div>
            """
    else:
        news_html = "<div style='padding:20px; color:#666;'>No news available.</div>"

    # Render Entire Card at Once
    st.markdown(f"""
    <div class="macro-card-container" style="height: 600px;">
        <div class="card-header">📰 Macro Headlines</div>
        <div class="card-body" style="overflow-y:auto; height:540px;">
            {news_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c_cal:
    # We use a container to apply the border style, then embed the iframe inside
    today_str = datetime.datetime.now().strftime("%A, %d %B")
    
    # 1. Open the card container using HTML
    st.markdown(f"""
    <div class="macro-card-container" style="height: 600px; display:flex; flex-direction:column;">
        <div class="card-header">
            <span>📅 FTMO Radar</span>
            <span style="font-size:0.8rem; background:#2962FF; padding:2px 8px; border-radius:4px;">{today_str}</span>
        </div>
        <div style="flex-grow:1; background:#000;">
    """, unsafe_allow_html=True)
    
    # 2. Inject the Iframe directly
    components.html("""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "width": "100%",
      "height": "100%",
      "colorTheme": "dark",
      "isTransparent": true,
      "locale": "en",
      "importanceFilter": "1",
      "currencyFilter": "USD,GBP,JPY",
      "timeZone": "Europe/London"
    }
      </script>
    </div>
    """, height=540)
    
    # 3. Close the card container
    st.markdown("</div></div>", unsafe_allow_html=True)
