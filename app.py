import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import datetime
import time
import streamlit.components.v1 as components

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="BAUDASH",
    layout="wide",
    page_icon="💎",
    initial_sidebar_state="collapsed"
)

# --- AUTO-REFRESH (Every 5 Minutes) ---
st.markdown("""
    <meta http-equiv="refresh" content="300">
    """, unsafe_allow_html=True)

# --- CSS "BAUDASH" THEME ---
st.markdown("""
<style>
    /* 1. GLOBAL SETTINGS */
    .stApp { 
        background-color: #000000; 
        color: #FFFFFF; 
        font-family: 'Arial', sans-serif;
    }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }

    /* 2. MAIN TITLE */
    .baudash-title {
        font-size: 5rem;
        font-weight: 900;
        text-align: center;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 8px;
        text-shadow: 0 0 20px #2962FF; 
        margin-bottom: 40px;
    }

    /* 3. MACRO CARD (Container) */
    .macro-card {
        background: #080808; 
        border: 3px solid #2962FF; /* Blue Border */
        border-radius: 35px; 
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 0 25px rgba(41, 98, 255, 0.15); 
        position: relative;
    }

    /* 4. CARD HEADER (Inside the box) */
    .card-header {
        font-size: 1.8rem;
        color: #2962FF; 
        font-weight: 900;
        text-transform: uppercase;
        margin-bottom: 25px;
        border-bottom: 2px solid #333;
        padding-bottom: 15px;
        letter-spacing: 1px;
    }

    /* 5. METRIC BOXES */
    .metric-box {
        background: #0a0a0a;
        border: 2px solid #ffffff; 
        border-radius: 30px; 
        padding: 20px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.8);
    }
    .metric-lbl { 
        font-size: 1.2rem; 
        color: #2962FF; 
        font-weight: 900; 
        text-transform: uppercase; 
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    .metric-val { 
        font-size: 2.8rem; 
        font-weight: 900; 
        color: #fff; 
    }
    .metric-chg {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 5px;
    }

    /* 6. ASSET TITLES */
    h2 { 
        font-size: 2.5rem !important; 
        font-weight: 900; 
        color: #fff; 
        text-shadow: 0 0 10px rgba(255,255,255,0.2);
        margin: 0; 
    }

    /* 7. RING CHART */
    .progress-ring {
        position: relative;
        width: 160px; 
        height: 160px;
        border-radius: 50%;
        background: conic-gradient(var(--color) var(--p), #222 0);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        box-shadow: 0 0 15px rgba(0,0,0,0.8);
    }
    .progress-ring::after {
        content: attr(data-score);
        position: absolute;
        width: 135px; 
        height: 135px;
        background: #080808;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        font-size: 2.2rem; 
        color: #fff;
    }

    /* 8. NEWS LINKS */
    .news-link { 
        font-size: 1.5rem !important; 
        color: #fff !important; 
        text-decoration: none; 
        font-weight: 700; 
        display: block;
        margin-bottom: 8px;
        transition: color 0.2s;
    }
    .news-link:hover { color: #2962FF !important; }
    
    .news-time { 
        font-size: 1.1rem; 
        color: #888; 
        margin-bottom: 25px; 
        display: block;
        border-bottom: 1px solid #333;
        padding-bottom: 10px;
    }
    
    .factor-text { font-size: 1.3rem; color: #e0e0e0; line-height: 1.7; margin-top: 15px; }

</style>
""", unsafe_allow_html=True)

# --- MAIN TITLE ---
st.markdown('<div class="baudash-title">BAUDASH</div>', unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=120) 
def get_data():
    tickers = ["^TNX", "^VIX", "DX-Y.NYB", "GBPUSD=X", "JPY=X", "^DJI"]
    data = yf.download(tickers, period="5d", interval="1d", progress=False)
    try:
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs('Close', axis=1, level=0)
    except: pass
    res = {}
    for t in tickers:
        try:
            s = data[t].dropna()
            change = ((s.iloc[-1] - s.iloc[-2])/s.iloc[-2])*100
            res[t] = {"price": s.iloc[-1], "change": change}
        except:
            res[t] = {"price": 0.0, "change": 0.0}
    return res

@st.cache_data(ttl=600)
def get_news():
    feed_url = "https://www.cnbc.com/id/10000664/device/rss/rss.html"
    feed = feedparser.parse(feed_url)
    return feed.entries[:4]

market = get_data()
news_data = get_news()

# --- 1. TOP METRICS ROW ---
c1, c2, c3, c4 = st.columns(4)

def big_metric(col, label, key, inv=False, is_pct=False):
    d = market[key]
    val_fmt = f"{d['price']:.2f}%" if is_pct else f"{d['price']:.2f}"
    chg = d['change']
    
    if inv:
        color = "#00E676" if chg < 0 else "#FF1744" 
    else:
        color = "#00E676" if chg > 0 else "#FF1744"
        
    icon = "▼" if chg < 0 else "▲"
    
    col.markdown(f"""
    <div class="metric-box">
        <div class="metric-lbl">{label}</div>
        <div class="metric-val">{val_fmt}</div>
        <div class="metric-chg" style="color: {color};">
            {icon} {abs(chg):.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

big_metric(c1, "US 10Y YIELD", "^TNX", inv=True, is_pct=True)
big_metric(c2, "VIX (FEAR)", "^VIX", inv=True)
big_metric(c3, "DOLLAR DXY", "DX-Y.NYB", inv=True)
big_metric(c4, "GBP CABLE", "GBPUSD=X", inv=False)

st.markdown("<div style='margin-bottom: 40px'></div>", unsafe_allow_html=True)

# --- 2. ASSET ANALYSIS ROW ---
col_us, col_gj = st.columns(2)

# === US30 LOGIC ===
with col_us:
    us_score = 50
    tnx_c = market['^TNX']['change']
    vix_p = market['^VIX']['price']
    
    # Scoring
    if tnx_c < -0.5: us_score += 25
    elif tnx_c > 0.5: us_score -= 25
    if vix_p < 16: us_score += 25
    elif vix_p > 22: us_score -= 25
    us_score = max(0, min(100, us_score))
    
    u_color = "#00E676" if us_score > 60 else "#FF1744" if us_score < 40 else "#FFCC00"
    u_bias = "BULLISH" if us_score > 60 else "BEARISH" if us_score < 40 else "NEUTRAL"
    
    st.markdown(f"""
    <div class="macro-card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:30px;">
            <div>
                <h2>US30 (DOW)</h2>
                <div style="color:{u_color}; font-weight:900; font-size:2rem; letter-spacing:2px; margin-top:10px;">{u_bias}</div>
            </div>
            <div class="progress-ring" style="--p: {us_score}%; --color: {u_color};" data-score="{us_score}%"></div>
        </div>
        <div class="factor-text">
            <b>🔑 KEY DRIVERS:</b><br>
            • Yields: <span style="color:{'#00E676' if tnx_c < 0 else '#FF1744'}; font-weight:bold;">{tnx_c:+.2f}%</span> (Dropping is Bullish)<br>
            • VIX: <span style="font-weight:bold; color:{'#00E676' if vix_p < 20 else '#FF1744'}">{vix_p:.2f}</span> (Risk Threshold: 20.00)
        </div>
    </div>
    """, unsafe_allow_html=True)

# === GBPJPY LOGIC ===
with col_gj:
    gj_score = 50
    gbp_c = market['GBPUSD=X']['change']
    jpy_c = market['JPY=X']['change']
    
    # Scoring
    if gbp_c > 0.1: gj_score += 20
    elif gbp_c < -0.1: gj_score -= 20
    if jpy_c > 0.1: gj_score += 30
    elif jpy_c < -0.1: gj_score -= 30
    gj_score = max(0, min(100, gj_score))
    
    g_color = "#00E676" if gj_score > 60 else "#FF1744" if gj_score < 40 else "#FFCC00"
    g_bias = "BUY / LONG" if gj_score > 60 else "SELL / SHORT" if gj_score < 40 else "RANGING"

    st.markdown(f"""
    <div class="macro-card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:30px;">
            <div>
                <h2>GBPJPY</h2>
                <div style="color:{g_color}; font-weight:900; font-size:2rem; letter-spacing:2px; margin-top:10px;">{g_bias}</div>
            </div>
            <div class="progress-ring" style="--p: {gj_score}%; --color: {g_color};" data-score="{gj_score}%"></div>
        </div>
        <div class="factor-text">
            <b>🔑 KEY DRIVERS:</b><br>
            • GBP Strength: <span style="color:{'#00E676' if gbp_c > 0 else '#FF1744'}; font-weight:bold;">{gbp_c:+.2f}%</span><br>
            • Yen Weakness: <span style="color:{'#00E676' if jpy_c > 0 else '#FF1744'}; font-weight:bold;">{jpy_c:+.2f}%</span> (Carry Trade)
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 3. NEWS & CALENDAR ROW ---
c_news, c_cal = st.columns([1, 1])

with c_news:
    # 1. Start the Card
    st.markdown('<div class="macro-card">', unsafe_allow_html=True)
    # 2. Put the Header INSIDE the Card
    st.markdown('<div class="card-header">📰 TOP MACRO HEADLINES</div>', unsafe_allow_html=True)
    
    if news_data:
        for item in news_data:
            # Format Date with Day Name (e.g., Monday, 19 Jan)
            try:
                dt_struct = item.published_parsed
                # Format: Monday, 19 Jan • 14:30
                nice_date = time.strftime("%A, %d %b • %H:%M", dt_struct)
            except:
                nice_date = item.published[:16]

            st.markdown(f"""
            <a href="{item.link}" target="_blank" class="news-link">{item.title}</a>
            <span class="news-time">🕒 {nice_date}</span>
            """, unsafe_allow_html=True)
    else:
        st.write("No news fetched currently.")
    
    # 3. Close the Card
    st.markdown('</div>', unsafe_allow_html=True)

with c_cal:
    # 1. Start the Card
    st.markdown('<div class="macro-card" style="padding: 10px; padding-top: 30px;">', unsafe_allow_html=True)
    # 2. Header INSIDE
    st.markdown('<div class="card-header" style="margin-left: 20px;">📅 FTMO RED FOLDER (UK TIME)</div>', unsafe_allow_html=True)
    
    components.html("""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "width": "100%",
      "height": "600",
      "colorTheme": "dark",
      "isTransparent": true,
      "locale": "en",
      "importanceFilter": "1",
      "currencyFilter": "USD,GBP,JPY",
      "timeZone": "Europe/London"
    }
      </script>
    </div>
    """, height=600)
    st.markdown('</div>', unsafe_allow_html=True)
