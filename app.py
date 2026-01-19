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
    page_icon="📉",
    initial_sidebar_state="collapsed"
)

# --- AUTO-REFRESH (5 Minutes) ---
st.markdown("""
    <meta http-equiv="refresh" content="300">
    """, unsafe_allow_html=True)

# --- CSS STYLING (Mobile Friendly & Integrated Headers) ---
st.markdown("""
<style>
    /* 1. RESET & BACKGROUND */
    .stApp { 
        background-color: #050505; 
        color: #FFFFFF; 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .block-container { padding-top: 1rem; padding-bottom: 3rem; }

    /* 2. MACRO CARD (The Blue Box) */
    .macro-card {
        background: #0a0a0a; 
        border: 2px solid #2962FF; 
        border-radius: 20px; 
        padding: 0; /* Padding handled inside to fix layout */
        margin-bottom: 20px;
        overflow: hidden; /* Keeps content inside curves */
        box-shadow: 0 4px 20px rgba(41, 98, 255, 0.1);
    }

    /* 3. CARD HEADER (Integrated) */
    .card-header-box {
        background: rgba(41, 98, 255, 0.1); /* Slight blue tint */
        border-bottom: 1px solid #2962FF;
        padding: 15px 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .card-title {
        color: #2962FF;
        font-weight: 900;
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 0;
    }
    .card-content {
        padding: 20px;
    }

    /* 4. METRIC BOXES (Responsive) */
    .metric-box {
        background: #0F0F0F;
        border: 1px solid #333; 
        border-radius: 15px; 
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-lbl { 
        font-size: 0.9rem; 
        color: #888; 
        font-weight: 700; 
        text-transform: uppercase; 
        margin-bottom: 5px;
    }
    .metric-val { 
        font-size: 1.8rem; /* Smaller for mobile safety */
        font-weight: 800; 
        color: #fff; 
    }

    /* 5. ASSET TITLES */
    h2 { margin: 0; font-size: 1.8rem; font-weight: 800; }
    
    /* 6. RING CHART */
    .progress-ring {
        position: relative;
        width: 100px; 
        height: 100px;
        border-radius: 50%;
        background: conic-gradient(var(--color) var(--p), #222 0);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .progress-ring::after {
        content: attr(data-score);
        position: absolute;
        width: 84px; 
        height: 84px;
        background: #0a0a0a;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.4rem; 
        color: #fff;
    }

    /* 7. NEWS STYLING */
    .news-item {
        border-bottom: 1px solid #222;
        padding-bottom: 12px;
        margin-bottom: 12px;
    }
    .news-link { 
        font-size: 1.1rem; 
        color: #E0E0E0; 
        text-decoration: none; 
        font-weight: 600; 
        display: block;
        margin-bottom: 4px;
    }
    .news-link:hover { color: #2962FF; }
    .news-date { font-size: 0.85rem; color: #666; }

    /* Key Factors */
    .factor-item { font-size: 0.95rem; margin-bottom: 6px; color: #ccc; }
    .factor-lbl { font-weight: bold; color: #fff; }

</style>
""", unsafe_allow_html=True)

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

# --- 1. TOP METRICS ---
c1, c2, c3, c4 = st.columns(4)

def big_metric(col, label, key, inv=False, is_pct=False):
    d = market[key]
    val_fmt = f"{d['price']:.2f}%" if is_pct else f"{d['price']:.2f}"
    chg = d['change']
    color = "#00E676" if (inv and chg < 0) or (not inv and chg > 0) else "#FF1744"
    icon = "▼" if chg < 0 else "▲"
    
    col.markdown(f"""
    <div class="metric-box">
        <div class="metric-lbl">{label}</div>
        <div class="metric-val">{val_fmt}</div>
        <div style="color: {color}; font-size: 1rem; font-weight: bold; margin-top:5px;">
            {icon} {abs(chg):.2f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

big_metric(c1, "US 10Y YIELD", "^TNX", inv=True, is_pct=True)
big_metric(c2, "VIX (FEAR)", "^VIX", inv=True)
big_metric(c3, "DOLLAR DXY", "DX-Y.NYB", inv=True)
big_metric(c4, "GBP CABLE", "GBPUSD=X", inv=False)

st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

# --- 2. ASSET ANALYSIS ---
col_us, col_gj = st.columns(2)

# === US30 ===
with col_us:
    us_score = 50
    tnx_c = market['^TNX']['change']
    vix_p = market['^VIX']['price']
    
    if tnx_c < -0.5: us_score += 25
    elif tnx_c > 0.5: us_score -= 25
    if vix_p < 16: us_score += 25
    elif vix_p > 22: us_score -= 25
    us_score = max(0, min(100, us_score))
    
    u_color = "#00E676" if us_score > 60 else "#FF1744" if us_score < 40 else "#FFCC00"
    u_bias = "BULLISH" if us_score > 60 else "BEARISH" if us_score < 40 else "NEUTRAL"
    
    st.markdown(f"""
    <div class="macro-card">
        <div class="card-header-box">
            <span style="font-size:1.5rem;">🇺🇸</span>
            <span class="card-title">US30 (DOW)</span>
        </div>
        <div class="card-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div>
                    <div style="font-size:2rem; font-weight:900; color:{u_color};">{u_bias}</div>
                    <div style="color:#666; font-size:0.8rem;">Macro Tendency</div>
                </div>
                <div class="progress-ring" style="--p: {us_score}%; --color: {u_color};" data-score="{us_score}%"></div>
            </div>
            <div>
                <div class="factor-item"><span class="factor-lbl">Yields ({tnx_c:+.2f}%):</span> <span style="color:{'#00E676' if tnx_c < 0 else '#FF1744'}">{'Bullish (Dropping)' if tnx_c < 0 else 'Bearish (Rising)'}</span></div>
                <div class="factor-item"><span class="factor-lbl">VIX ({vix_p:.2f}):</span> <span style="color:{'#00E676' if vix_p < 20 else '#FF1744'}">{'Safe' if vix_p < 20 else 'High Risk'}</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# === GBPJPY ===
with col_gj:
    gj_score = 50
    gbp_c = market['GBPUSD=X']['change']
    jpy_c = market['JPY=X']['change']
    
    if gbp_c > 0.1: gj_score += 20
    elif gbp_c < -0.1: gj_score -= 20
    if jpy_c > 0.1: gj_score += 30
    elif jpy_c < -0.1: gj_score -= 30
    gj_score = max(0, min(100, gj_score))
    
    g_color = "#00E676" if gj_score > 60 else "#FF1744" if gj_score < 40 else "#FFCC00"
    g_bias = "BUY / LONG" if gj_score > 60 else "SELL / SHORT" if gj_score < 40 else "RANGING"

    st.markdown(f"""
    <div class="macro-card">
        <div class="card-header-box">
            <span style="font-size:1.5rem;">💱</span>
            <span class="card-title">GBPJPY</span>
        </div>
        <div class="card-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div>
                    <div style="font-size:2rem; font-weight:900; color:{g_color};">{g_bias}</div>
                    <div style="color:#666; font-size:0.8rem;">Macro Tendency</div>
                </div>
                <div class="progress-ring" style="--p: {gj_score}%; --color: {g_color};" data-score="{gj_score}%"></div>
            </div>
            <div>
                <div class="factor-item"><span class="factor-lbl">GBP ({gbp_c:+.2f}%):</span> <span style="color:{'#00E676' if gbp_c > 0 else '#FF1744'}">{'Strong' if gbp_c > 0 else 'Weak'}</span></div>
                <div class="factor-item"><span class="factor-lbl">Yen Weakness ({jpy_c:+.2f}%):</span> <span style="color:{'#00E676' if jpy_c > 0 else '#FF1744'}">{'Carry On' if jpy_c > 0 else 'Unwind Risk'}</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 3. NEWS & CALENDAR ---
c_news, c_cal = st.columns([1, 1])

with c_news:
    # Build HTML for news items
    news_html = ""
    if news_data:
        for item in news_data:
            try:
                dt = time.strftime("%A, %d %b • %H:%M", item.published_parsed)
            except: dt = item.published[:16]
            
            news_html += f"""
            <div class="news-item">
                <a href="{item.link}" target="_blank" class="news-link">{item.title}</a>
                <span class="news-date">🕒 {dt}</span>
            </div>
            """
    else:
        news_html = "<div style='color:#666'>No news available.</div>"

    st.markdown(f"""
    <div class="macro-card" style="min-height: 500px;">
        <div class="card-header-box">
            <span>📰</span>
            <span class="card-title">TOP MACRO HEADLINES</span>
        </div>
        <div class="card-content">
            {news_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c_cal:
    # Dynamic Day Display
    today_str = datetime.datetime.now().strftime("%A, %d %B")
    
    st.markdown(f"""
    <div class="macro-card" style="min-height: 500px;">
        <div class="card-header-box" style="justify-content: space-between;">
            <div style="display:flex; gap:10px; align-items:center;">
                <span>📅</span>
                <span class="card-title">FTMO RADAR</span>
            </div>
            <div style="font-size:0.9rem; color:#fff; background:#2962FF; padding:2px 8px; border-radius:4px;">
                TODAY: {today_str}
            </div>
        </div>
        <div style="height: 440px;"> 
    """, unsafe_allow_html=True)
    
    # Widget
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
    """, height=440)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
