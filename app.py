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
    page_icon="🦅",
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

    /* 4. NEWS STYLES */
    .news-item { 
        padding: 12px 0; 
        border-bottom: 1px solid #222; 
        display: flex; 
        flex-direction: column; 
        gap: 5px; 
    }
    .news-link { 
        color: #fff; 
        text-decoration: none; 
        font-weight: 600; 
        font-size: 1rem; 
        line-height: 1.4;
    }
    .news-link:hover { color: #2962FF; }
    
    .news-meta-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .news-date { font-size: 0.8rem; color: #666; }
    .sentiment-badge { 
        font-size: 0.75rem; 
        padding: 3px 8px; 
        border-radius: 4px; 
        font-weight: 800; 
        text-transform: uppercase;
    }

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

    /* 7. IFRAME BORDER */
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

# --- DATA ENGINE ---
@st.cache_data(ttl=300) 
def get_data():
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

    if res.get("^T5YIE", {}).get("price", 0) < 0.1:
        res["^T5YIE"] = res.get("^TNX", {"price": 0.0, "change": 0.0})

    return res

# --- DUAL-CORE AI SENTIMENT ENGINE (SEPARATED) ---
@st.cache_data(ttl=600)
def get_news_analysis():
    feed_url = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664" 
    
    try:
        feed = feedparser.parse(feed_url)
        analyzer = SentimentIntensityAnalyzer()
        
        us_news = []
        gj_news = []
        
        # KEYWORDS SEPARATION
        us_keywords = ["fed", "powell", "inflation", "cpi", "treasury", "yield", "recession", "stocks", "dow", "s&p", "nasdaq", "gdp", "fomc"]
        gj_keywords = ["boe", "bailey", "bank of england", "uk", "britain", "pound", "gilt", "boj", "ueda", "bank of japan", "yen", "japan", "jgb", "forex"]
        
        block_words = ["bitcoin", "crypto", "nft", "disney", "movie", "sport"]

        for entry in feed.entries:
            text = (entry.title + " " + entry.get('summary', '')).lower()
            
            if any(bad in text for bad in block_words): continue
            
            vs = analyzer.polarity_scores(entry.title)
            compound = vs['compound']
            
            if compound >= 0.05: s_label, s_color = "POS", "#00E676"
            elif compound <= -0.05: s_label, s_color = "NEG", "#FF1744"
            else: s_label, s_color = "NEU", "#888"
            
            news_obj = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "sentiment": s_label,
                "color": s_color,
                "score": compound
            }
            
            # Bucket the news
            is_us = any(k in text for k in us_keywords)
            is_gj = any(k in text for k in gj_keywords)
            
            if is_us: us_news.append(news_obj)
            if is_gj: gj_news.append(news_obj)
        
        # Calculate Scores
        us_score = sum(n['score'] for n in us_news)/len(us_news) if us_news else 0
        gj_score = sum(n['score'] for n in gj_news)/len(gj_news) if gj_news else 0
            
        return us_news, gj_news, us_score, gj_score
    except:
        return [], [], 0, 0

market = get_data()
us_news, gj_news, us_sentiment, gj_sentiment = get_news_analysis()

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
    
    html = f"""<div class="metric-box"><div class="metric-lbl">{title}</div><div class="metric-val">{val}</div><div style="color:{color}; font-weight:bold; font-size:0.9rem; margin-top:5px;">{arrow} {abs(chg):.2f}%</div></div>"""
    col.markdown(html, unsafe_allow_html=True)

render_metric(c1, "MKT INFLATION (5Y)", "^T5YIE", invert=True, is_pct=True)
render_metric(c2, "FED PROXY (13W)", "^IRX", invert=True, is_pct=True)
render_metric(c3, "RISK (VIX)", "^VIX", invert=True)
render_metric(c4, "DOLLAR (DXY)", "DX-Y.NYB", invert=True)

st.markdown("<div style='margin-bottom: 25px'></div>", unsafe_allow_html=True)

# --- ASSET CARDS ---
col_us, col_gj = st.columns(2)

# === US30 (DOW) ===
with col_us:
    us_score = 50
    inf = market.get('^T5YIE', {'change':0})['change']
    rates = market.get('^IRX', {'change':0})['change']
    tech_chg = market.get('XLK', {'change':0})['change']
    util_chg = market.get('XLU', {'change':0})['change']
    risk_on = tech_chg > util_chg
    
    # 1. Yield Logic
    if inf > 0.5: us_score -= 15
    elif inf < -0.5: us_score += 15
    if rates > 1.0: us_score -= 15
    elif rates < -1.0: us_score += 15
    # 2. Flow Logic
    if risk_on: us_score += 20
    else: us_score -= 20
    # 3. US Specific Sentiment
    if us_sentiment > 0.05: us_score += 10
    elif us_sentiment < -0.05: us_score -= 10

    us_score = max(0, min(100, us_score))
    u_color = "#00E676" if us_score > 60 else "#FF1744" if us_score < 40 else "#FFCC00"
    u_txt = "BULLISH" if us_score > 60 else "BEARISH" if us_score < 40 else "NEUTRAL"
    rot_txt = "Risk On (Tech > Utils)" if risk_on else "Defensive (Utils > Tech)"
    rot_col = "#00E676" if risk_on else "#FF1744"

    html_us = f"""<div class="html-card"><div class="card-header"><span>🇺🇸 US30 (Dow Jones)</span><span style="font-size:0.8rem; opacity:0.7">US MACRO ONLY</span></div><div class="card-body"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;"><div><div style="font-size:2rem; font-weight:900; color:{u_color};">{u_txt}</div><div style="color:#666; font-size:0.8rem;">Independent Score</div></div><div class="ring-container" style="--ring-color:{u_color}; --ring-pct:{us_score}%;"><div class="ring-inner">{us_score}%</div></div></div><div style="background:#111; padding:15px; border-radius:8px;"><div class="factor-row"><span style="color:#aaa;">Sector Flow</span><span style="font-weight:bold; color:{rot_col}">{rot_txt}</span></div><div class="factor-row"><span style="color:#aaa;">Fed Rates (13W Bill)</span><span style="font-weight:bold; color:{'#FF1744' if rates > 0 else '#00E676'}">{rates:+.2f}%</span></div><div class="factor-row"><span style="color:#aaa;">US News Sentiment</span><span style="font-weight:bold; color:{'#00E676' if us_sentiment > 0 else '#FF1744'}">{us_sentiment:.2f} Score</span></div></div></div></div>"""
    st.markdown(html_us, unsafe_allow_html=True)

# === GBPJPY ===
with col_gj:
    gj_score = 50
    gbp = market.get('GBPUSD=X', {'change':0})['change']
    jpy = market.get('JPY=X', {'change':0})['change']
    oil = market.get('CL=F', {'change':0})['change']
    
    # 1. FX Logic
    if gbp > 0.1: gj_score += 20
    elif gbp < -0.1: gj_score -= 20
    if jpy > 0.1: gj_score += 25
    elif jpy < -0.1: gj_score -= 25
    # 2. Oil Logic
    if oil > 0.5: gj_score += 15
    elif oil < -0.5: gj_score -= 15
    # 3. UK/JP Specific Sentiment
    if gj_sentiment > 0.05: gj_score += 10
    elif gj_sentiment < -0.05: gj_score -= 10
    
    gj_score = max(0, min(100, gj_score))
    g_color = "#00E676" if gj_score > 60 else "#FF1744" if gj_score < 40 else "#FFCC00"
    g_txt = "LONG (BUY)" if gj_score > 60 else "SHORT (SELL)" if gj_score < 40 else "RANGING"

    html_gj = f"""<div class="html-card"><div class="card-header"><span>💱 GBPJPY (The Beast)</span><span style="font-size:0.8rem; opacity:0.7">YIELD & OIL MODEL</span></div><div class="card-body"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;"><div><div style="font-size:2rem; font-weight:900; color:{g_color};">{g_txt}</div><div style="color:#666; font-size:0.8rem;">Independent Score</div></div><div class="ring-container" style="--ring-color:{g_color}; --ring-pct:{gj_score}%;"><div class="ring-inner">{gj_score}%</div></div></div><div style="background:#111; padding:15px; border-radius:8px;"><div class="factor-row"><span style="color:#aaa;">Yen Weakness (Carry)</span><span style="font-weight:bold; color:{'#00E676' if jpy > 0 else '#FF1744'}">{jpy:+.2f}%</span></div><div class="factor-row"><span style="color:#aaa;">Oil Impact (Japan Imp.)</span><span style="font-weight:bold; color:{'#00E676' if oil > 0 else '#FF1744'}">{oil:+.2f}%</span></div><div class="factor-row"><span style="color:#aaa;">UK/JP News Sentiment</span><span style="font-weight:bold; color:{'#00E676' if gj_sentiment > 0 else '#FF1744'}">{gj_sentiment:.2f} Score</span></div></div></div></div>"""
    st.markdown(html_gj, unsafe_allow_html=True)

# --- SEPARATED NEWS ---
c_news, c_cal = st.columns(2)

with c_news:
    # We combine both lists for the feed, but label them
    news_feed_html = ""
    combined_news = us_news + gj_news
    # Sort by date (newest first) could be done here, but feed is usually sorted.
    
    if combined_news:
        for item in combined_news[:6]: # Show top 6 combined
            try: dt = time.strftime("%d %b %H:%M", item['published_parsed'])
            except: dt = "Recent"
            
            # Badge logic to show if it impacted US or GJ
            # (Simplified check for display)
            tag = "US" if item in us_news else "FX"
            tag_color = "#2962FF" if tag == "US" else "#FFCC00"
            tag_text_col = "#FFF" if tag == "US" else "#000"

            news_feed_html += f"<div class='news-item'><a href='{item['link']}' target='_blank' class='news-link'>{item['title']}</a><div class='news-meta-row'><span class='news-date'>🕒 {dt}</span><div style='display:flex; gap:5px;'><span class='sentiment-badge' style='background:{tag_color}; color:{tag_text_col};'>{tag}</span><span class='sentiment-badge' style='background:{item['color']}; color:#000;'>AI: {item['sentiment']}</span></div></div></div>"
    else:
        news_feed_html = "<div style='color:#666; padding:10px;'>No relevant news found.</div>"

    st.markdown(f"""<div class="html-card" style="height: 600px;"><div class="card-header"><span>📰 Smart Macro Wire</span><span style="font-size:0.8rem; opacity:0.7">SEPARATED STREAMS</span></div><div class="card-body" style="overflow-y:auto; height:540px;">{news_feed_html}</div></div>""", unsafe_allow_html=True)

with c_cal:
    today_str = datetime.datetime.now().strftime("%A, %d %B")
    
    st.markdown(f"""<div style="border: 2px solid #2962FF; border-bottom: none; border-top-left-radius: 15px; border-top-right-radius: 15px; background-color: #0a0a0a; margin-bottom: 0px;"><div class="card-header" style="border-bottom: 1px solid #2962FF;"><span>📅 FTMO Radar</span><span style="font-size:0.8rem; background:#2962FF; padding:2px 8px; border-radius:4px;">{today_str}</span></div></div>""", unsafe_allow_html=True)
    
    components.html("""<div class="tradingview-widget-container" style="background-color: #0a0a0a;"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"width": "100%","height": "535","colorTheme": "dark","isTransparent": true,"locale": "en","importanceFilter": "1","currencyFilter": "USD,GBP,JPY","timeZone": "Europe/London"}</script></div>""", height=535)
