import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Macro Command Center",
    layout="wide",
    page_icon="🦅",
    initial_sidebar_state="collapsed"
)

# --- PROFESSIONAL STYLING (CSS) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #0E1117; }
    
    /* Cards */
    .macro-card {
        background-color: #1E1E24;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Text Typography */
    h1, h2, h3 { color: #FFFFFF; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    p, li, span { color: #E0E0E0; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Highlight Colors */
    .bull-text { color: #00E676; font-weight: bold; }
    .bear-text { color: #FF1744; font-weight: bold; }
    .neutral-text { color: #FFCC00; font-weight: bold; }
    
    /* News Feed styling */
    .news-item {
        border-bottom: 1px solid #333;
        padding: 10px 0;
    }
    .news-title { color: #4da6ff; font-weight: bold; text-decoration: none; font-size: 1.1rem; }
    .news-meta { color: #888; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=120) # Cache for 2 mins
def get_market_data():
    # Tickers: US10Y, US02Y, VIX, DXY, GBPUSD, USDJPY, Dow Jones
    tickers = ["^TNX", "^IRX", "^VIX", "DX-Y.NYB", "GBPUSD=X", "JPY=X", "^DJI"]
    
    # Download data
    data = yf.download(tickers, period="5d", interval="1d", progress=False)
    
    # Handle MultiIndex if necessary (Yfinance update fix)
    try:
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs('Close', axis=1, level=0)
    except:
        pass

    results = {}
    
    for ticker in tickers:
        try:
            # Get series for specific ticker
            series = data[ticker].dropna()
            latest = series.iloc[-1]
            prev = series.iloc[-2]
            change_pct = ((latest - prev) / prev) * 100
            
            results[ticker] = {
                "price": latest,
                "change": change_pct
            }
        except Exception as e:
            results[ticker] = {"price": 0.0, "change": 0.0}
            
    return results

@st.cache_data(ttl=600) # Cache news for 10 mins
def get_macro_news():
    # RSS Feeds for reliable Macro News
    feeds = [
        "https://www.investing.com/rss/news_25.rss", # Forex News
        "https://www.cnbc.com/id/10000664/device/rss/rss.html" # CNBC Economy/Fed
    ]
    
    news_items = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Top 5 from each
                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published
                })
        except:
            continue
    return news_items

# Load Data
market = get_market_data()
news = get_macro_news()

# --- HELPER: GAUGE CHART ---
def create_gauge(value, title, min_val, max_val, thresholds):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title, 'font': {'size': 24, 'color': "white"}},
        number = {'font': {'color': "white"}},
        gauge = {
            'axis': {'range': [min_val, max_val], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "white"},
            'bgcolor': "black",
            'steps': [
                {'range': [min_val, thresholds[0]], 'color': "#FF1744"}, # Red
                {'range': [thresholds[0], thresholds[1]], 'color': "#FFCC00"}, # Yellow
                {'range': [thresholds[1], max_val], 'color': "#00E676"} # Green
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(paper_bgcolor="#1E1E24", font={'color': "white", 'family': "Arial"}, height=250, margin=dict(l=20,r=20,t=50,b=20))
    return fig

# --- HEADER ---
c_head_1, c_head_2 = st.columns([3, 1])
with c_head_1:
    st.markdown("# 🦅 MACRO COMMAND CENTER")
    st.markdown(f"**Live Intelligence for US30 & GBPJPY** | Updated: {datetime.datetime.now().strftime('%H:%M UTC')}")
with c_head_2:
    # Quick Status
    if market['^VIX']['price'] < 15:
        st.success("✅ MARKET CALM")
    elif market['^VIX']['price'] < 22:
        st.warning("⚠️ CAUTION")
    else:
        st.error("🚨 HIGH VOLATILITY")

# --- ROW 1: KEY MACRO METRICS ---
st.markdown("### 🔑 THE MACRO MATRIX (The raw data driving price)")
m1, m2, m3, m4 = st.columns(4)

def metric_card(col, label, ticker_key, inverse=False, suffix=""):
    data = market[ticker_key]
    val = data['price']
    chg = data['change']
    
    # Color Logic
    if inverse:
        color = "normal" if chg < 0 else "off" # Red if up (bad)
    else:
        color = "normal" if chg > 0 else "off" # Green if up (good)
        
    col.metric(label, f"{val:.2f}{suffix}", f"{chg:.2f}%", delta_color="inverse" if inverse else "normal")

metric_card(m1, "US 10Y YIELD", "^TNX", inverse=True, suffix="%")
metric_card(m2, "US DOLLAR (DXY)", "DX-Y.NYB", inverse=True)
metric_card(m3, "FEAR INDEX (VIX)", "^VIX", inverse=True)
metric_card(m4, "GBP STRENGTH (Cable)", "GBPUSD=X", inverse=False)

st.markdown("---")

# --- ROW 2: ASSET ANALYSIS ---
col_us, col_gj = st.columns(2)

# === US30 LOGIC ===
with col_us:
    st.markdown('<div class="macro-card">', unsafe_allow_html=True)
    st.markdown("## 🇺🇸 US30 (DOW JONES)")
    
    # Calculate Score
    us_score = 50
    reasons = []
    
    # 1. Yields
    if market['^TNX']['change'] < -0.5:
        us_score += 20
        reasons.append("Yields are dropping significantly. <b>Bullish for Tech/Industry.</b>")
    elif market['^TNX']['change'] > 0.5:
        us_score -= 20
        reasons.append("Yields are surging. <b>Pressure on valuations.</b>")
        
    # 2. VIX
    if market['^VIX']['price'] < 16:
        us_score += 15
        reasons.append("VIX is low. Risk-on sentiment is active.")
    elif market['^VIX']['price'] > 22:
        us_score -= 20
        reasons.append("VIX is spiking. Investors are fleeing equities.")
        
    # 3. DXY
    if market['DX-Y.NYB']['change'] > 0.3:
        us_score -= 10
        reasons.append("Strong Dollar is hurting US exports.")
        
    # Chart
    fig_us = create_gauge(us_score, "Macro Sentiment", 0, 100, [40, 60])
    st.plotly_chart(fig_us, use_container_width=True)
    
    # Text Analysis
    st.markdown("#### 📝 MACRO CONTEXT")
    for r in reasons:
        st.markdown(f"- {r}", unsafe_allow_html=True)
        
    if not reasons:
        st.markdown("- No major macro divergences. Market is likely technical today.")
        
    st.markdown('</div>', unsafe_allow_html=True)

# === GBPJPY LOGIC ===
with col_gj:
    st.markdown('<div class="macro-card">', unsafe_allow_html=True)
    st.markdown("## 🇬🇧/🇯🇵 GBPJPY (THE BEAST)")
    
    # Calculate Score
    gj_score = 50
    gj_reasons = []
    
    # 1. GBP Strength
    gbp_chg = market['GBPUSD=X']['change']
    if gbp_chg > 0.2:
        gj_score += 15
        gj_reasons.append("Pound Sterling is showing strength across the board.")
    elif gbp_chg < -0.2:
        gj_score -= 15
        gj_reasons.append("Pound is weak today.")

    # 2. JPY Weakness (USDJPY)
    # Note: If JPY=X (USD/JPY) goes UP, Yen is WEAK.
    jpy_chg = market['JPY=X']['change'] 
    
    if jpy_chg > 0.2:
        gj_score += 20
        gj_reasons.append("Yen is weakening (USDJPY Up). <b>Carry trade is ON.</b>")
    elif jpy_chg < -0.2:
        gj_score -= 20
        gj_reasons.append("Yen is strengthening (Intervention risk or Safe Haven flow).")
        
    # 3. Risk Sentiment linkage
    if market['^DJI']['change'] < -0.5:
        gj_score -= 10
        gj_reasons.append("Stock market sell-off is dragging GJ down (Correlation).")

    # Chart
    fig_gj = create_gauge(gj_score, "Macro Sentiment", 0, 100, [40, 60])
    st.plotly_chart(fig_gj, use_container_width=True)
    
    # Text Analysis
    st.markdown("#### 📝 MACRO CONTEXT")
    for r in gj_reasons:
        st.markdown(f"- {r}", unsafe_allow_html=True)
        
    if gj_score > 60:
        st.success("BIAS: LOOK FOR BUYS (Carry Trade Active)")
    elif gj_score < 40:
        st.error("BIAS: LOOK FOR SELLS (Risk Off / Yen Strength)")
    else:
        st.warning("BIAS: MIXED / RANGING")

    st.markdown('</div>', unsafe_allow_html=True)


# --- ROW 3: NEWS & CALENDAR ---
c_news, c_cal = st.columns([1, 1])

with c_news:
    st.markdown("### 📰 LATEST MACRO HEADLINES (Fed/Global)")
    st.markdown('<div class="macro-card">', unsafe_allow_html=True)
    
    if news:
        for item in news:
            st.markdown(f"""
            <div class="news-item">
                <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a><br>
                <span class="news-meta">{item['published']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("No news fetched. Check connection.")
    st.markdown('</div>', unsafe_allow_html=True)

with c_cal:
    st.markdown("### 📅 FTMO RED FOLDER RADAR (High Impact)")
    # Calendar Widget
    components.html("""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "width": "100%",
      "height": "400",
      "colorTheme": "dark",
      "isTransparent": false,
      "locale": "en",
      "importanceFilter": "1",
      "currencyFilter": "USD,GBP,JPY"
    }
      </script>
    </div>
    """, height=400)
