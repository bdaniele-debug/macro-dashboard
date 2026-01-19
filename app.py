import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import datetime
import streamlit.components.v1 as components

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="BAUDASH",
    layout="wide",
    page_icon="💎",
    initial_sidebar_state="collapsed"
)

# --- CSS "BAUDASH" THEME (Black, Neon Blue, Rounded, GIANT) ---
st.markdown("""
<style>
    /* 1. GLOBAL BACKGROUND & FONT */
    .stApp { 
        background-color: #000000; /* Pitch Black */
        color: #FFFFFF; 
        font-family: 'Arial', sans-serif;
    }
    
    /* Remove default padding for a cleaner look */
    .block-container { padding-top: 2rem; padding-bottom: 5rem; }

    /* 2. TITLE BAUDASH */
    .baudash-title {
        font-size: 5rem;
        font-weight: 900;
        text-align: center;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 8px;
        text-shadow: 0 0 20px #2962FF; /* Strong Neon Blue Glow */
        margin-bottom: 40px;
    }

    /* 3. CARDS (Rounded & Bombato) */
    .macro-card {
        background: #080808; 
        border: 3px solid #2962FF; /* Thick Blue Border */
        border-radius: 35px; /* Super Rounded */
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 0 25px rgba(41, 98, 255, 0.15); /* Blue Halo */
    }

    /* 4. TOP METRICS (Rounded Boxes) */
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
        font-size: 2.8rem; /* GIANT NUMBERS */
        font-weight: 900; 
        color: #fff; 
    }
    .metric-chg {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 5px;
    }

    /* 5. ASSET TITLES */
    h2 { 
        font-size: 2.5rem !important; 
        font-weight: 900; 
        color: #fff; 
        text-shadow: 0 0 10px rgba(255,255,255,0.2);
        margin: 0; 
    }
    
    h3 {
        font-size: 1.5rem !important;
        color: #2962FF !important; 
        font-weight: 800 !important;
        text-transform: uppercase;
        margin-bottom: 15px !important;
    }

    /* 6. RING CHART (Bigger) */
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

    /* 7. NEWS LINKS (Large & Clear) */
    .news-link { 
        font-size: 1.5rem !important; 
        color: #fff !important; 
        text-decoration: none; 
        font-weight: 700; 
        display: block;
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid #333;
        transition: color 0.2s;
    }
    .news-link:hover { color: #2962FF !important; }
    .news-time { font-size: 1.1rem; color: #888; margin-bottom: 20px;}
    
    /* Key Factors Text */
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
    # Fetching Top 4 stories from CNBC Economy
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
    
    # Logic: Green is Good, Red is Bad. 
    # If 'inv' is True (like VIX or Yields), them going DOWN is GREEN.
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
    
    # Colors
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
    
    # Colors
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
    st.markdown("<h3>📰 TOP MACRO HEADLINES</h3>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="macro-card">', unsafe_allow_html=True)
        if news_data:
            for item in news_data:
                st.markdown(f"""
                <a href="{item.link}" target="_blank" class="news-link">{item.title}</a>
                <div class="news-time">🕒 Published: {item.published[:16]}</div>
                """, unsafe_allow_html=True)
        else:
            st.write("No news fetched currently.")
        st.markdown('</div>', unsafe_allow_html=True)

with c_cal:
    st.markdown("<h3>📅 FTMO RED FOLDER (UK TIME)</h3>", unsafe_allow_html=True)
    st.markdown('<div class="macro-card" style="padding: 10px; overflow: hidden;">', unsafe_allow_html=True)
    
    # INCREASED HEIGHT TO 600px TO MAKE IT READABLE
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
