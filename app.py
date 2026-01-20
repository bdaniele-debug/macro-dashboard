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

# --- HEADER & MANUAL REFRESH ---
c_head_1, c_head_2 = st.columns([3, 1])
with c_head_1:
    st.markdown("## 🦅 MACRO ALPHA TERMINAL")
with c_head_2:
    if st.button("🔄 FORCE REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

# --- AUTO-REFRESH (Now every 60 Seconds for News/Price agility) ---
st.markdown("""<meta http-equiv="refresh" content="60">""", unsafe_allow_html=True)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E0E0E0; font-family: 'Helvetica Neue', sans-serif; }
    .block-container { padding-top: 1rem; padding-bottom: 3rem; }
    
    /* CARDS */
    .metric-box { background: #0F0F0F; border: 1px solid #333; border-radius: 12px; padding: 15px; text-align: center; height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .metric-lbl { font-size: 0.8rem; color: #888; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .metric-val { font-size: 1.6rem; font-weight: 800; color: #fff; }
    
    .html-card { border: 2px solid #2962FF; border-radius: 15px; background-color: #0a0a0a; margin-bottom: 20px; overflow: hidden; box-shadow: 0 0 15px rgba(41, 98, 255, 0.1); }
    .card-header { background: rgba(41, 98, 255, 0.15); padding: 12px 20px; border-bottom: 1px solid #2962FF; font-weight: 900; font-size: 1rem; color: #fff; text-transform: uppercase; display: flex; justify-content: space-between; align-items: center; }
    .card-body { padding: 20px; }

    /* NEWS & TAGS */
    .news-item { padding: 10px 0; border-bottom: 1px solid #222; display: flex; flex-direction: column; gap: 4px; }
    .news-link { color: #fff; text-decoration: none; font-weight: 600; font-size: 0.95rem; }
    .news-link:hover { color: #2962FF; }
    .news-meta-row { display: flex; justify-content: space-between; align-items: center; }
    .news-date { font-size: 0.75rem; color: #666; }
    .sentiment-badge { font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: 800; text-transform: uppercase; }

    /* FACTORS TABLE */
    .factor-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #333; font-size: 0.85rem; }
    .factor-row:last-child { border-bottom: none; }
    .score-pill { padding: 2px 8px; border-radius: 10px; font-weight: bold; font-size: 0.8rem; }

    /* RING CHART */
    .ring-container { position: relative; width: 90px; height: 90px; border-radius: 50%; background: conic-gradient(var(--ring-color) var(--ring-pct), #222 0); display: flex; align-items: center; justify-content: center; }
    .ring-inner { width: 74px; height: 74px; background: #0a0a0a; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; color: white; font-size: 1.1rem; }

    /* IFRAME FIX */
    iframe[title="streamlit_components_v1.components.html"] { border: 2px solid #2962FF !important; border-top: none !important; border-bottom-left-radius: 15px !important; border-bottom-right-radius: 15px !important; background-color: #0a0a0a; margin-top: -5px; }
    
    /* Button Style */
    div.stButton > button { width: 100%; background-color: #2962FF; color: white; border: none; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- DATA ENGINE (TTL REDUCED TO 60 SECONDS) ---
@st.cache_data(ttl=60) 
def get_data():
    tickers = ["^TNX", "^IRX", "^T5YIE", "^VIX", "DX-Y.NYB", "GBPUSD=X", "JPY=X", "^DJI", "XLK", "XLU", "CL=F"]
    try:
        data = yf.download(tickers, period="5d", interval="1d", progress=False)
        if isinstance(data.columns, pd.MultiIndex): data = data.xs('Close', axis=1, level=0)
    except: return {}

    res = {}
    for t in tickers:
        try:
            s = data[t].dropna()
            if len(s) >= 2:
                res[t] = {"price": s.iloc[-1], "change": ((s.iloc[-1] - s.iloc[-2]) / s.iloc[-2]) * 100}
            else: res[t] = {"price": 0.0, "change": 0.0}
        except: res[t] = {"price": 0.0, "change": 0.0}

    if res.get("^T5YIE", {}).get("price", 0) < 0.1:
        res["^T5YIE"] = res.get("^TNX", {"price": 0.0, "change": 0.0})
    return res

# --- NEWS ENGINE (TTL REDUCED TO 60 SECONDS) ---
@st.cache_data(ttl=60)
def get_news_analysis():
    feed_urls = [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", 
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362"
    ]
    try:
        analyzer = SentimentIntensityAnalyzer()
        us_news, gj_news = [], []
        seen_titles = set()

        macro_high = ["fed", "powell", "inflation", "cpi", "ppi", "treasury", "yield", "fomc", "gdp", "recession", "payrolls", "jobs", "unemployment", "rates", "boe", "bailey", "bank of england", "boj", "ueda", "bank of japan"]
        macro_mid = ["housing", "retail sales", "pmi", "manufacturing", "services", "confidence", "oil", "energy", "ecb", "lagarde", "china", "stimulus", "tax", "budget", "deficit", "liquidity", "credit", "banks"]
        us_assets = ["stocks", "dow", "s&p", "nasdaq", "wall street", "dollar", "usd", "fed"]
        gj_assets = ["uk", "britain", "pound", "sterling", "gilt", "japan", "yen", "jgb", "forex", "carry trade", "boe", "boj"]
        noise = ["bitcoin", "crypto", "nft", "disney", "movie", "sport", "star wars", "marvel", "celebrity"]

        for url in feed_urls:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.title in seen_titles: continue
                seen_titles.add(entry.title)
                text = (entry.title + " " + entry.get('summary', '')).lower()
                
                relevance = 0
                for w in macro_high: 
                    if w in text: relevance += 3
                for w in macro_mid: 
                    if w in text: relevance += 2
                for w in noise: 
                    if w in text: relevance -= 10
                for w in gj_assets:
                    if w in text: relevance += 1 # Boost GJ visibility

                if relevance < 2: continue

                vs = analyzer.polarity_scores(entry.title)
                compound = vs['compound']
                item = {
                    "title": entry.title, "link": entry.link, "published": entry.published,
                    "sentiment": "POS" if compound>=0.05 else "NEG" if compound<=-0.05 else "NEU",
                    "color": "#00E676" if compound>=0.05 else "#FF1744" if compound<=-0.05 else "#888",
                    "score": compound
                }
                
                is_us = any(w in text for w in us_assets)
                is_gj = any(w in text for w in gj_assets)
                if not is_us and not is_gj and relevance >= 3: is_us = True 

                if is_us: us_news.append(item)
                if is_gj: gj_news.append(item)
        
        us_s = sum(n['score'] for n in us_news)/len(us_news) if us_news else 0
        gj_s = sum(n['score'] for n in gj_news)/len(gj_news) if gj_news else 0
        
        return us_news, gj_news, us_s, gj_s
    except: return [], [], 0, 0

market = get_data()
us_news, gj_news, us_sentiment, gj_sentiment = get_news_analysis()

# --- METRICS ROW ---
c1, c2, c3, c4 = st.columns(4)
def render_metric(col, title, key, invert=False, is_pct=False):
    d = market.get(key, {'price':0.0, 'change':0.0})
    val = f"{d['price']:.2f}%" if is_pct else f"{d['price']:.2f}"
    color = "#00E676"
    if invert: color = "#FF1744" if d['change'] > 0 else "#00E676"
    else: color = "#FF1744" if d['change'] < 0 else "#00E676"
    arrow = "▲" if d['change'] > 0 else "▼"
    col.markdown(f"""<div class="metric-box"><div class="metric-lbl">{title}</div><div class="metric-val">{val}</div><div style="color:{color}; font-weight:bold; font-size:0.8rem; margin-top:5px;">{arrow} {abs(d['change']):.2f}%</div></div>""", unsafe_allow_html=True)

render_metric(c1, "MKT INFLATION (5Y)", "^T5YIE", invert=True, is_pct=True)
render_metric(c2, "FED PROXY (13W)", "^IRX", invert=True, is_pct=True)
render_metric(c3, "RISK (VIX)", "^VIX", invert=True)
render_metric(c4, "DOLLAR (DXY)", "DX-Y.NYB", invert=True)

st.markdown("<div style='margin-bottom: 25px'></div>", unsafe_allow_html=True)

# --- ASSET CARDS ---
col_us, col_gj = st.columns(2)

# === US30 LOGIC ===
with col_us:
    us_base = 50
    inf_c = market.get('^T5YIE', {'change':0})['change']
    rate_c = market.get('^IRX', {'change':0})['change']
    tech_c = market.get('XLK', {'change':0})['change']
    util_c = market.get('XLU', {'change':0})['change']
    vix_p = market.get('^VIX', {'price':0})['price']
    
    macro_score = 0
    if inf_c > 0.5: macro_score -= 10
    elif inf_c < -0.5: macro_score += 10
    if rate_c > 1.0: macro_score -= 10
    elif rate_c < -1.0: macro_score += 10
    
    risk_on = tech_c > util_c
    flow_score = 25 if risk_on else -25
    flow_txt = "Tech > Utils (Risk On)" if risk_on else "Utils > Tech (Defensive)"
    
    sent_score = 0
    if vix_p > 20: sent_score -= 15
    elif vix_p < 16: sent_score += 10
    if us_sentiment > 0.05: sent_score += 5
    elif us_sentiment < -0.05: sent_score -= 5
    
    us_final = max(0, min(100, us_base + macro_score + flow_score + sent_score))
    u_col = "#00E676" if us_final > 60 else "#FF1744" if us_final < 40 else "#FFCC00"
    u_txt = "BULLISH" if us_final > 60 else "BEARISH" if us_final < 40 else "NEUTRAL"

    html_us = f"""<div class="html-card"><div class="card-header"><span>🇺🇸 US30 (Dow Jones)</span><span style="font-size:0.8rem; opacity:0.7">SMART MONEY MODEL</span></div><div class="card-body"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;"><div><div style="font-size:2rem; font-weight:900; color:{u_col};">{u_txt}</div><div style="color:#666; font-size:0.8rem;">Algo Score: {us_final}/100</div></div><div class="ring-container" style="--ring-color:{u_col}; --ring-pct:{us_final}%;"><div class="ring-inner">{us_final}%</div></div></div><div style="background:#111; padding:15px; border-radius:8px;">
    <div class="factor-row"><span style="color:#aaa;">Sector Flow (Smart Money)</span><span class="score-pill" style="background:{'rgba(0,230,118,0.2)' if risk_on else 'rgba(255,23,68,0.2)'}; color:{'#00E676' if risk_on else '#FF1744'}">{flow_txt}</span></div>
    <div class="factor-row"><span style="color:#aaa;">Macro Drag (Yields/Fed)</span><span style="font-weight:bold; color:{'#FF1744' if macro_score < 0 else '#00E676'}">{macro_score:+d} pts</span></div>
    <div class="factor-row"><span style="color:#aaa;">Sentiment Impact</span><span style="font-weight:bold; color:{'#FF1744' if sent_score < 0 else '#00E676'}">{sent_score:+d} pts</span></div>
    </div></div></div>"""
    st.markdown(html_us, unsafe_allow_html=True)

# === GBPJPY LOGIC ===
with col_gj:
    gj_base = 50
    gbp_c = market.get('GBPUSD=X', {'change':0})['change']
    jpy_c = market.get('JPY=X', {'change':0})['change']
    oil_c = market.get('CL=F', {'change':0})['change']
    
    fx_score = 0
    if gbp_c > 0.1: fx_score += 15
    elif gbp_c < -0.1: fx_score -= 15
    if jpy_c > 0.1: fx_score += 20 
    elif jpy_c < -0.1: fx_score -= 20
    
    oil_score = 0
    if oil_c > 0.5: oil_score += 15
    elif oil_c < -0.5: oil_score -= 15
    
    gj_sent_score = 0
    if gj_sentiment > 0.05: gj_sent_score += 10
    elif gj_sentiment < -0.05: gj_sent_score -= 10
    
    gj_final = max(0, min(100, gj_base + fx_score + oil_score + gj_sent_score))
    g_col = "#00E676" if gj_final > 60 else "#FF1744" if gj_final < 40 else "#FFCC00"
    g_txt = "LONG (BUY)" if gj_final > 60 else "SHORT (SELL)" if gj_final < 40 else "RANGING"

    html_gj = f"""<div class="html-card"><div class="card-header"><span>💱 GBPJPY (The Beast)</span><span style="font-size:0.8rem; opacity:0.7">YIELD & OIL MODEL</span></div><div class="card-body"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;"><div><div style="font-size:2rem; font-weight:900; color:{g_col};">{g_txt}</div><div style="color:#666; font-size:0.8rem;">Algo Score: {gj_final}/100</div></div><div class="ring-container" style="--ring-color:{g_col}; --ring-pct:{gj_final}%;"><div class="ring-inner">{gj_final}%</div></div></div><div style="background:#111; padding:15px; border-radius:8px;">
    <div class="factor-row"><span style="color:#aaa;">Yen Strength (Carry)</span><span style="font-weight:bold; color:{'#00E676' if jpy_c > 0 else '#FF1744'}">{'Weak (Bullish)' if jpy_c > 0 else 'Strong (Bearish)'}</span></div>
    <div class="factor-row"><span style="color:#aaa;">Oil Correlation (JP Imp)</span><span style="font-weight:bold; color:{'#00E676' if oil_score > 0 else '#FF1744'}">{oil_score:+d} pts</span></div>
    <div class="factor-row"><span style="color:#aaa;">UK/JP Sentiment</span><span style="font-weight:bold; color:{'#00E676' if gj_sent_score > 0 else '#FF1744'}">{gj_sent_score:+d} pts</span></div>
    </div></div></div>"""
    st.markdown(html_gj, unsafe_allow_html=True)

# --- NEWS FEEDS ---
c_news, c_cal = st.columns(2)

with c_news:
    all_news = us_news + gj_news
    all_news.sort(key=lambda x: x['published'], reverse=True)

    news_html = ""
    if all_news:
        for item in all_news[:8]:
            try: dt = time.strftime("%d %b %H:%M", datetime.datetime.strptime(item['published'][:25], "%a, %d %b %Y %H:%M:%S").timetuple())
            except: dt = "Recent"
            if item in us_news and item in gj_news: tag, tag_col, tag_txt = "GLOBAL", "#9C27B0", "#FFF"
            elif item in gj_news: tag, tag_col, tag_txt = "FX/WRLD", "#FFD700", "#000"
            else: tag, tag_col, tag_txt = "US", "#2962FF", "#FFF"
            
            news_html += f"""<div class="news-item"><a href="{item['link']}" target="_blank" class="news-link">{item['title']}</a><div class="news-meta-row"><span class="news-date">🕒 {dt}</span><div style="display:flex; gap:5px;"><span class="sentiment-badge" style="background:{tag_col}; color:{tag_txt};">{tag}</span><span class="sentiment-badge" style="background:{item['color']}; color:#000;">AI: {item['sentiment']}</span></div></div></div>"""
    else: news_html = "<div style='color:#666; padding:10px;'>No relevant macro news found. (Filters are active)</div>"

    st.markdown(f"""<div class="html-card" style="height: 600px;"><div class="card-header"><span>📰 Smart Macro Wire</span><span style="font-size:0.8rem; opacity:0.7">US + WORLD AGGREGATOR</span></div><div class="card-body" style="overflow-y:auto; height:540px;">{news_html}</div></div>""", unsafe_allow_html=True)

with c_cal:
    today_str = datetime.datetime.now().strftime("%A, %d %B")
    st.markdown(f"""<div style="border: 2px solid #2962FF; border-bottom: none; border-top-left-radius: 15px; border-top-right-radius: 15px; background-color: #0a0a0a; margin-bottom: 0px;"><div class="card-header" style="border-bottom: 1px solid #2962FF;"><span>📅 FTMO Radar</span><span style="font-size:0.8rem; background:#2962FF; padding:2px 8px; border-radius:4px;">{today_str}</span></div></div>""", unsafe_allow_html=True)
    components.html("""<div class="tradingview-widget-container" style="background-color: #0a0a0a;"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"width": "100%","height": "535","colorTheme": "dark","isTransparent": true,"locale": "en","importanceFilter": "1","currencyFilter": "USD,GBP,JPY","timeZone": "Europe/London"}</script></div>""", height=535)
