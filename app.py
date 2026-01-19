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

# --- CSS STYLING ---
st.markdown("""
<style>
    /* 1. RESET & BACKGROUND */
    .stApp { 
        background-color: #050505; 
        color: #E0E0E0; 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* FIX: Add padding to top so metrics aren't cut off */
    .block-container { 
        padding-top: 3rem; 
        padding-bottom: 3rem; 
    }

    /* 2. MACRO CARD (Blue Box) */
    .macro-card {
        background: #0a0a0a; 
        border: 2px solid #2962FF; 
        border-radius: 15px; 
        margin-bottom: 20px;
        overflow: hidden; 
        box-shadow: 0 4px 20px rgba(41, 98, 255, 0.1);
    }

    /* 3. CARD HEADER */
    .card-header-box {
        background: rgba(41, 98, 255, 0.15); 
        border-bottom: 1px solid #2962FF;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .card-title {
        color: #fff;
        font-weight: 800;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .card-content { padding: 20px; }

    /* 4. METRIC BOXES */
    .metric-box {
        background: #0F0F0F;
        border: 1px solid #333; 
        border-radius: 12px; 
        padding: 15px;
        text-align: center;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-lbl { 
        font-size: 0.8rem; 
        color: #888; 
        font-weight: 700; 
        text-transform: uppercase; 
        margin-bottom: 8px;
    }
    .metric-val { font-size: 1.6rem; font-weight: 800; color: #fff; }

    /* 5. RING CHART */
    .progress-ring {
        position: relative;
        width: 110px; 
        height: 110px;
        border-radius: 50%;
        background: conic-gradient(var(--color) var(--p), #222 0);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .progress-ring::after {
        content: attr(data-score);
        position: absolute;
        width: 90px; 
        height: 90px;
        background: #0a0a0a;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.4rem; 
        color: #fff;
    }

    /* 6. NEWS ITEMS */
    .news-item {
        padding: 10px 0;
        border-bottom: 1px solid #222;
    }
    .news-link { 
        font-size: 1rem; 
        color: #E0E0E0; 
        text-decoration: none; 
        font-weight: 600; 
        line-height: 1.4;
    }
    .news-link:hover { color: #2962FF; }
    .news-meta { font-size: 0.75rem; color: #666; margin-top: 4px; }

    /* Key Factors */
    .factor-row { 
        display: flex; 
        justify-content: space-between; 
        margin-bottom: 8px; 
        border-bottom: 1px solid #222; 
        padding-bottom: 4px;
    }
    .factor-name { color: #aaa; font-size: 0.9rem; }
    .factor-val { font-weight: bold; font-size: 0.9rem; }

</style>
""", unsafe_allow_html=True)

# --- HEDGE FUND DATA ENGINE ---
@st.cache_data(ttl=120) 
def get_data():
    # ^TNX = 10Y Yield (Growth/Long Term Inflation)
    # ^IRX = 13 Week Bill (Fed Rate Proxy)
    # ^T5YIE = 5-Year Breakeven Inflation Rate (The Market's CPI Expectation)
    # ^VIX = Fear
    tickers = ["^TNX", "^IRX", "^T5YIE", "^VIX", "DX-Y.NYB", "GBPUSD=X", "JPY=X", "^DJI"]
    
    data = yf.download(tickers, period="5d", interval="1d", progress=False)
    
    # Cleaning MultiIndex
    try:
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs('Close', axis=1, level=0)
    except: pass

    res = {}
    for t in tickers:
        try:
            s = data[t].dropna()
            if len(s) > 1:
                latest = s.iloc[-1]
                prev = s.iloc[-2]
                change = ((latest - prev) / prev) * 100
                res[t] = {"price": latest, "change": change}
            else:
                res[t] = {"price": 0.0, "change": 0.0}
        except:
            res[t] = {"price": 0.0, "change": 0.0}
    return res

@st.cache_data(ttl=600)
def get_news():
    feed_url = "https://www.cnbc.com/id/10000664/device/rss/rss.html"
    feed = feedparser.parse(feed_url)
    return feed.entries[:5]

market = get_data()
news_data = get_news()

# --- 1. TOP METRICS (THE DASHBOARD) ---
# We display 4 Key "Hedge Fund" Metrics
c1, c2, c3, c4 = st.columns(4)

def metric_card(col, title, key, invert_color=False, is_pct=False):
    d = market.get(key, {'price':0, 'change':0})
    val = f"{d['price']:.2f}%" if is_pct else f"{d['price']:.2f}"
    chg = d['change']
    
    # Logic: If 'invert_color' is True, RISING is RED (Bad). e.g. Inflation/VIX.
    if invert_color:
        color = "#00E676" if chg < 0 else "#FF1744"
    else:
        color = "#00E676" if chg > 0 else "#FF1744"
        
    icon = "▼" if chg < 0 else "▲"
    
    col.markdown(f"""
    <div class="metric-box">
        <div class="metric-lbl">{title}</div>
        <div class="metric-val">{val}</div>
        <div style="color:{color}; font-weight:bold; font-size:0.9rem; margin-top:5px;">{icon} {abs(chg):.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

# 1. Inflation Expectations (The "Real" CPI)
metric_card(c1, "MARKET INFLATION (5Y)", "^T5YIE", invert_color=True, is_pct=True)
# 2. Cost of Money (Fed Proxy)
metric_card(c2, "FED RATE PROXY (13W)", "^IRX", invert_color=True, is_pct=True)
# 3. Fear
metric_card(c3, "RISK SENTIMENT (VIX)", "^VIX", invert_color=True)
# 4. Dollar
metric_card(c4, "DOLLAR INDEX (DXY)", "DX-Y.NYB", invert_color=True)

st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

# --- 2. ASSET ANALYSIS ---
col_us, col_gj = st.columns(2)

# === US30 (DOW) LOGIC ===
with col_us:
    us_score = 50
    
    # Data Points
    inf_exp = market['^T5YIE']['change'] # Inflation Expectations
    fed_proxy = market['^IRX']['change'] # Short Term Rates
    vix = market['^VIX']['price']
    
    # Logic: 
    # If Market expects MORE inflation -> Bad for stocks (Rates stay high)
    if inf_exp > 0.5: us_score -= 20
    elif inf_exp < -0.5: us_score += 20
    
    # If Short term rates rising -> Bad for liquidity
    if fed_proxy > 1.0: us_score -= 20
    elif fed_proxy < -1.0: us_score += 20
    
    # VIX Filter
    if vix < 16: us_score += 10
    elif vix > 20: us_score -= 20
    
    us_score = max(0, min(100, us_score))
    
    u_color = "#00E676" if us_score > 60 else "#FF1744" if us_score < 40 else "#FFCC00"
    u_bias = "BULLISH" if us_score > 60 else "BEARISH" if us_score < 40 else "NEUTRAL"

    st.markdown(f"""
    <div class="macro-card">
        <div class="card-header-box">
            <div class="card-title">🇺🇸 US30 (DOW JONES)</div>
            <div style="font-size:0.8rem; color:#888;">EQUITY MACRO</div>
        </div>
        <div class="card-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div>
                    <div style="font-size:2rem; font-weight:900; color:{u_color};">{u_bias}</div>
                    <div style="color:#666; font-size:0.8rem;">Algorithmic Verdict</div>
                </div>
                <div class="progress-ring" style="--p: {us_score}%; --color: {u_color};" data-score="{us_score}%"></div>
            </div>
            
            <div style="background:#111; padding:15px; border-radius:10px;">
                <div class="factor-row">
                    <span class="factor-name">Inflation Exp (Breakevens)</span>
                    <span class="factor-val" style="color:{'#FF1744' if inf_exp > 0 else '#00E676'}">{inf_exp:+.2f}%</span>
                </div>
                <div class="factor-row">
                    <span class="factor-name">Fed Rate Proxy (13W Bill)</span>
                    <span class="factor-val" style="color:{'#FF1744' if fed_proxy > 0 else '#00E676'}">{fed_proxy:+.2f}%</span>
                </div>
                 <div class="factor-row" style="border-bottom:none;">
                    <span class="factor-name">Risk Premium (VIX)</span>
                    <span class="factor-val" style="color:{'#FF1744' if vix > 20 else '#00E676'}">{vix:.2f}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# === GBPJPY LOGIC ===
with col_gj:
    gj_score = 50
    
    # Data Points
    # Since we lack live CB rate feeds, we use the Market's pricing of them:
    # 1. Yield Spread Proxy: GBPUSD Strength vs JPY Strength
    gbp_strength = market['GBPUSD=X']['change']
    yen_weakness = market['JPY=X']['change'] # If Positive, USD>JPY (Yen Weak)
    
    # Logic:
    # GBP Strength = Yields in UK likely holding/rising vs US
    if gbp_strength > 0.1: gj_score += 20
    elif gbp_strength < -0.1: gj_score -= 20
    
    # Yen Weakness = BOJ Dovish / Carry Trade ON
    if yen_weakness > 0.1: gj_score += 30
    elif yen_weakness < -0.1: gj_score -= 30
    
    gj_score = max(0, min(100, gj_score))
    
    g_color = "#00E676" if gj_score > 60 else "#FF1744" if gj_score < 40 else "#FFCC00"
    g_bias = "LONG (BUY)" if gj_score > 60 else "SHORT (SELL)" if gj_score < 40 else "RANGING"

    st.markdown(f"""
    <div class="macro-card">
        <div class="card-header-box">
            <div class="card-title">💱 GBPJPY (THE BEAST)</div>
            <div style="font-size:0.8rem; color:#888;">YIELD SPREAD MODEL</div>
        </div>
        <div class="card-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div>
                    <div style="font-size:2rem; font-weight:900; color:{g_color};">{g_bias}</div>
                    <div style="color:#666; font-size:0.8rem;">Algorithmic Verdict</div>
                </div>
                <div class="progress-ring" style="--p: {gj_score}%; --color: {g_color};" data-score="{gj_score}%"></div>
            </div>
            
            <div style="background:#111; padding:15px; border-radius:10px;">
                <div class="factor-row">
                    <span class="factor-name">GBP Strength (Rate Proxy)</span>
                    <span class="factor-val" style="color:{'#00E676' if gbp_strength > 0 else '#FF1744'}">{gbp_strength:+.2f}%</span>
                </div>
                <div class="factor-row">
                    <span class="factor-name">Yen Weakness (Carry Flow)</span>
                    <span class="factor-val" style="color:{'#00E676' if yen_weakness > 0 else '#FF1744'}">{yen_weakness:+.2f}%</span>
                </div>
                 <div class="factor-row" style="border-bottom:none;">
                    <span class="factor-name">Global Risk (Correlation)</span>
                    <span class="factor-val" style="color:{'#FF1744' if vix > 20 else '#00E676'}">{'Risk Off' if vix > 20 else 'Risk On'}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 3. NEWS & CALENDAR ---
c_news, c_cal = st.columns([1, 1])

with c_news:
    st.markdown("""
    <div class="macro-card" style="height: 520px; overflow-y: auto;">
        <div class="card-header-box">
            <div class="card-title">📰 MACRO WIRE</div>
        </div>
        <div class="card-content">
    """, unsafe_allow_html=True)
    
    if news_data:
        for item in news_data:
            try:
                dt_obj = item.published_parsed
                date_str = time.strftime("%d %b %H:%M", dt_obj)
            except:
                date_str = "Latest"
                
            st.markdown(f"""
            <div class="news-item">
                <a href="{item.link}" target="_blank" class="news-link">{item.title}</a>
                <div class="news-meta">🕒 {date_str} • Source: CNBC</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("No news feeds available.")

    st.markdown("</div></div>", unsafe_allow_html=True)

with c_cal:
    # Dynamic Day Date
    today_date = datetime.datetime.now().strftime("%A, %d %B")
    
    st.markdown(f"""
    <div class="macro-card" style="height: 520px; display: flex; flex-direction: column;">
        <div class="card-header-box">
            <div class="card-title">📅 FTMO RADAR</div>
            <div style="background:#2962FF; color:white; padding:2px 8px; border-radius:4px; font-size:0.8rem;">{today_date}</div>
        </div>
        <div style="flex-grow: 1; padding: 0;">
    """, unsafe_allow_html=True)
    
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
