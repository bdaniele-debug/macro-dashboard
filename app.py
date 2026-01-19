import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import datetime
import time
import streamlit.components.v1 as components
import textwrap
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Macro Alpha Terminal",
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="collapsed"
)

# --- AUTO-REFRESH (5 Minutes) ---
st.markdown("""<meta http-equiv="refresh" content="300">""", unsafe_allow_html=True)

# --- CSS STYLING ---
st.markdown("""
<style>
    /* 1. BACKGROUND */
    .stApp { 
        background-color: #050505; 
        color: #E0E0E0; 
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }

    /* 2. METRIC CARDS */
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

    /* 3. HTML CARDS */
    .html-card {
        border: 2px solid #2962FF;
        border-radius: 15px;
        background-color: #0a0a0a;
        margin-bottom: 20px;
        overflow: hidden;
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
        display: flex; justify-content: space-between; align-items: center;
    }
    .card-body { padding: 20px; }

    /* 4. NEWS & SENTIMENT STYLES */
    .news-item { padding: 12px 0; border-bottom: 1px solid #222; }
    .news-link { color: #fff; text-decoration: none; font-weight: 600; font-size: 1.05rem; display: block; margin-bottom: 4px; }
    .news-link:hover { color: #2962FF; }
    .news-meta { font-size: 0.8rem; color: #666; display: flex; justify-content: space-between; }
    .sentiment-badge { font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; }

    /* 5. FACTORS */
    .factor-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; font-size: 0.9rem; }
    .factor-row:last-child { border-bottom: none; }
    
    /* 6. RING CHART */
    .ring-container {
        position: relative; width: 100px; height: 100px;
        border-radius: 50%;
        background: conic-gradient(var(--ring-color) var(--ring-pct), #222 0);
        display: flex; align-items: center; justify-content: center;
    }
    .ring-inner {
        width: 84px; height: 84px; background: #0a0a0a; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; color: white; font-size: 1.2rem;
    }

    /* 7. CUSTOM IFRAME BORDER */
    iframe[title="streamlit_components_v1.components.html"] {
        border: 2px solid #2962FF !important;
        border-top: none !important;
        border-bottom-left-radius: 15px !important;
        border-bottom-right-radius: 15px !important;
        background-color: #0a0a0a;
        margin-top: -5px; 
    }
</style>
""", unsafe_allow_html=True)

# --- DATA ENGINE (ENHANCED) ---
@st.cache_data(ttl=300) 
def get_data():
    # NEW TICKERS ADDED:
    # XLK = Tech (Risk On)
    # XLU = Utilities (Defense)
    # CL=F = Crude Oil (Yen Killer)
    tickers = ["^TNX", "^IRX", "^T5YIE", "^VIX", "DX-Y.NYB", "GBPUSD=X", "JPY=X", "^DJI", "XLK", "XLU", "CL=F"]
    
    try:
        data = yf.download(tickers, period="5d", interval="1d", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs('Close', axis=1, level=0)
    except:
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
                res[t] = {"price": 0.0, "change": 0.0}
        except:
            res[t] = {"price": 0.0, "change": 0.0}

    # FAILSAFE
    if res.get("^T5YIE", {}).get("price", 0) < 0.1:
        res["^T5YIE"] = res.get("^TNX", {"price": 0.0, "change": 0.0})

    return res

# --- AI SENTIMENT ENGINE ---
@st.cache_data(ttl=600)
def get_news_analysis():
    try:
        feed = feedparser.parse("https://www.cnbc.com/id/10000664/device/rss/rss.html")
        analyzer = SentimentIntensityAnalyzer()
        
        news_items = []
        total_score = 0
        count = 0
        
        for entry in feed.entries[:6]:
            # VADER Analysis
            vs = analyzer.polarity_scores(entry.title)
            compound = vs['compound']
            total_score += compound
            count += 1
            
            # Determine color/label
            if compound >= 0.05: s_label, s_color = "POS", "#00E676"
            elif compound <= -0.05: s_label, s_color = "NEG", "#FF1744"
            else: s_label, s_color = "NEU", "#888"
            
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "sentiment": s_label,
                "color": s_color
            })
            
        avg_sentiment = total_score / count if count > 0 else 0
        return news_items, avg_sentiment
    except:
        return [], 0

market = get_data()
news_data, sentiment_score = get_news_analysis()

# --- TOP METRICS ---
c1, c2, c3, c4 = st.columns(4)

def render_metric(col, title, key, invert=False, is_pct=False):
    d = market.get(key, {'price':0.0, 'change':0.0})
    val = f"{d['price']:.2f}%" if is_pct else f"{d['price']:.2f}"
    chg = d['change']
    color = "#00E676"
    if invert:
        if chg > 0: color = "#FF1744"
    else:
        if chg < 0: color = "#FF1744"
    arrow = "▲" if chg > 0 else "▼"
    
    html = textwrap.dedent(f"""
    <div class="metric-box">
        <div class="metric-lbl">{title}</div>
        <div class="metric-val">{val}</div>
        <div style="color:{color}; font-weight:bold; font-size:0.9rem; margin-top:5px;">{arrow} {abs(chg):.2f}%</div>
    </div>
    """)
    col.markdown(html, unsafe_allow_html=True)

render_metric(c1, "MKT INFLATION (5Y)", "^T5YIE", invert=True, is_pct=True)
render_metric(c2, "FED PROXY (13W)", "^IRX", invert=True, is_pct=True)
render_metric(c3, "RISK (VIX)", "^VIX", invert=True)
render_metric(c4, "DOLLAR (DXY)", "DX-Y.NYB", invert=True)

st.markdown("<div style='margin-bottom: 25px'></div>", unsafe_allow_html=True)

# --- ASSET CARDS ---
col_us, col_gj = st.columns(2)

# === US30 (SMART MONEY LOGIC) ===
with col_us:
    us_score = 50
    
    # 1. Base Macro
    inf = market.get('^T5YIE', {'change':0})['change']
    rates = market.get('^IRX', {'change':0})['change']
    vix_p = market.get('^VIX', {'price':0})['price']
    
    if inf > 0.5: us_score -= 15
    elif inf < -0.5: us_score += 15
    if rates > 1.0: us_score -= 15
    elif rates < -1.0: us_score += 15
    
    # 2. SECTOR ROTATION (The Hedge Fund Upgrade)
    # Compare Tech (Risk) vs Utilities (Safety)
    tech_chg = market.get('XLK', {'change':0})['change']
    util_chg = market.get('XLU', {'change':0})['change']
    risk_on = tech_chg > util_chg
    
    if risk_on: us_score += 20 # Money flowing into Risk
    else: us_score -= 20 # Money flowing into Safety
    
    # 3. AI Sentiment Impact
    if sentiment_score > 0.1: us_score += 10
    elif sentiment_score < -0.1: us_score -= 10

    us_score = max(0, min(100, us_score))
    u_color = "#00E676" if us_score > 60 else "#FF1744" if us_score < 40 else "#FFCC00"
    u_txt = "BULLISH" if us_score > 60 else "BEARISH" if us_score < 40 else "NEUTRAL"
    
    rot_txt = "Risk On (Tech > Utils)" if risk_on else "Defensive (Utils > Tech)"
    rot_col = "#00E676" if risk_on else "#FF1744"

    html_us = textwrap.dedent(f"""
    <div class="html-card">
        <div class="card-header">
            <span>🇺🇸 US30 (Dow Jones)</span>
            <span style="font-size:0.8rem; opacity:0.7">SMART MONEY MODEL</span>
        </div>
        <div class="card-body">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div>
                    <div style="font-size:2rem; font-weight:900; color:{u_color};">{u_txt}</div>
                    <div style="color:#666; font-size:0.8rem;">Algo Verdict</div>
                </div>
                <div class="ring-container" style="--ring-color:{u_color}; --ring-pct:{us_score}%;">
                    <div class="ring-inner">{us_score}%</div>
                </div>
            </div>
            <div style="background:#111; padding:15px; border-radius:8px;">
                <div class="factor-row">
                    <span style="color:#aaa;">Sector Rotation (Flow)</span>
                    <span style="font-weight:bold; color:{rot_col}">{rot_txt}</span>
                </div>
                <div class="factor-row">
                    <span style="color:#aaa;">Fed Rates (13W Bill)</span>
                    <span style="font-weight:bold; color:{'#FF1744' if rates > 0 else '#00E676'}">{rates:+.2f}%</span>
                </div>
                <div class="factor-row">
                    <span style="color:#aaa;">AI News Sentiment</span>
                    <span style="font-weight:bold; color:{'#00E676' if sentiment_score > 0 else '#FF1744'}">{sentiment_score:.2f} Score</span>
                </div>
            </div>
        </div>
    </div>
    """)
    st.markdown(html_us, unsafe_allow_html=True)

# === GBPJPY (OIL & YIELD LOGIC) ===
with col_gj:
    gj_score = 50
    gbp = market.get('GBPUSD=X', {'change':0})['change']
    jpy = market.get('JPY=X', {'change':0})['change']
    
    # 1. Base Yield Logic
    if gbp > 0.1: gj_score += 20
    elif gbp < -0.1: gj_score -= 20
    if jpy > 0.1: gj_score += 25
    elif jpy < -0.1: gj_score -= 25
    
    # 2. OIL CORRELATION (The Hedge Fund Upgrade)
    # Japan imports 99% of Oil. High Oil = Weak Yen = High GJ.
    oil = market.get('CL=F', {'change':0})['change']
    
    if oil > 0.5: gj_score += 15 # Oil Up -> Yen Dead -> GJ Up
    elif oil < -0.5: gj_score -= 15 # Oil Down -> Yen Safe
    
    gj_score = max(0, min(100, gj_score))
    g_color = "#00E676" if gj_score > 60 else "#FF1744" if gj_score < 40 else "#FFCC00"
    g_txt = "LONG (BUY)" if gj_score > 60 else "SHORT (SELL)" if gj_score < 40 else "RANGING"

    html_gj = textwrap.dedent(f"""
    <div class="html-card">
        <div class="card-header">
            <span>💱 GBPJPY (The Beast)</span>
            <span style="font-size:0.8rem; opacity:0.7">OIL & YIELD MODEL</span>
        </div>
        <div class="card-body">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div>
                    <div style="font-size:2rem; font-weight:900; color:{g_color};">{g_txt}</div>
                    <div style="color:#666; font-size:0.8rem;">Algo Verdict</div>
                </div>
                <div class="ring-container" style="--ring-color:{g_color}; --ring-pct:{gj_score}%;">
                    <div class="ring-inner">{gj_score}%</div>
                </div>
            </div>
            <div style="background:#111; padding:15px; border-radius:8px;">
                <div class="factor-row">
                    <span style="color:#aaa;">Yen Weakness (Carry)</span>
                    <span style="font-weight:bold; color:{'#00E676' if jpy > 0 else '#FF1744'}">{jpy:+.2f}%</span>
                </div>
                <div class="factor-row">
                    <span style="color:#aaa;">Oil Impact (Japan Imp.)</span>
                    <span style="font-weight:bold; color:{'#00E676' if oil > 0 else '#FF1744'}">{oil:+.2f}%</span>
                </div>
                <div class="factor-row">
                    <span style="color:#aaa;">GBP Strength</span>
                    <span style="font-weight:bold; color:{'#00E676' if gbp > 0 else '#FF1744'}">{gbp:+.2f}%</span>
                </div>
            </div>
        </div>
    </div>
    """)
    st.markdown(html_gj, unsafe_allow_html=True)

# --- NEWS & CALENDAR ---
c_news, c_cal = st.columns(2)

with c_news:
    items_html = ""
    if news_data:
        for item in news_data:
            try: dt = time.strftime("%d %b %H:%M", item['published_parsed'])
            except: dt = "Recent"
            
            items_html += f"""
            <div class="news-item">
                <a href="{item['link']}" target="_blank" class="news-link">{item['title']}</a>
                <div class="news-meta">
                    <span>🕒 {dt}</span>
                    <span class="sentiment-badge" style="background:{item['color']}; color:#000;">AI: {item['sentiment']}</span>
                </div>
            </div>
            """
    else:
        items_html = "<div style='color:#666'>No news available right now.</div>"

    html_news = textwrap.dedent(f"""
    <div class="html-card" style="height: 600px;">
        <div class="card-header">
            <span>📰 AI Sentiment Wire</span>
            <span style="font-size:0.8rem; opacity:0.7">VADER ANALYTICS</span>
        </div>
        <div class="card-body" style="overflow-y:auto; height:540px;">
            {items_html}
        </div>
    </div>
    """)
    st.markdown(html_news, unsafe_allow_html=True)

with c_cal:
    today_str = datetime.datetime.now().strftime("%A, %d %B")
    
    st.markdown(textwrap.dedent(f"""
    <div style="border: 2px solid #2962FF; border-bottom: none; border-top-left-radius: 15px; border-top-right-radius: 15px; background-color: #0a0a0a; margin-bottom: 0px;">
        <div class="card-header" style="border-bottom: 1px solid #2962FF;">
            <span>📅 FTMO Radar</span>
            <span style="font-size:0.8rem; background:#2962FF; padding:2px 8px; border-radius:4px;">{today_str}</span>
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    components.html("""
    <div class="tradingview-widget-container" style="background-color: #0a0a0a;">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "width": "100%",
      "height": "535",
      "colorTheme": "dark",
      "isTransparent": true,
      "locale": "en",
      "importanceFilter": "1",
      "currencyFilter": "USD,GBP,JPY",
      "timeZone": "Europe/London"
    }
      </script>
    </div>
    """, height=535)
