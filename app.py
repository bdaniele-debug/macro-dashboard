import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import datetime
import streamlit.components.v1 as components

# --- CONFIGURAZIONE PAGINA (Compact Mode) ---
st.set_page_config(
    page_title="Macro Dashboard",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# --- CSS MODERNO E COMPATTO ---
st.markdown("""
<style>
    /* Riduciamo i margini generali per vedere tutto in una schermata */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    /* Sfondo scuro e pulito */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Card Stile Glass */
    .macro-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        height: 100%;
    }
    
    /* Titoli */
    h3 { font-size: 1rem !important; margin-bottom: 5px !important; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    h2 { font-size: 1.2rem !important; font-weight: 700; color: #fff; margin: 0; }
    
    /* Metriche Piccole */
    .metric-box {
        text-align: center;
        background: #0d1117;
        border-radius: 6px;
        padding: 8px;
        border: 1px solid #21262d;
    }
    .metric-val { font-size: 1.1rem; font-weight: bold; color: #fff; }
    .metric-lbl { font-size: 0.7rem; color: #8b949e; }
    
    /* INDICATORE PERCENTUALE A CERCHIO (CSS PURO) */
    .progress-ring {
        position: relative;
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: conic-gradient(var(--color) var(--p), #21262d 0);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }
    .progress-ring::after {
        content: attr(data-score);
        position: absolute;
        width: 86px;
        height: 86px;
        background: #161b22;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.2rem;
        color: #fff;
    }

    /* News Compatte */
    .news-row {
        padding: 8px 0;
        border-bottom: 1px solid #21262d;
        font-size: 0.85rem;
    }
    .news-row:last-child { border-bottom: none; }
    .news-link { color: #58a6ff; text-decoration: none; font-weight: 500; }
    .news-link:hover { text-decoration: underline; }
    .news-time { font-size: 0.7rem; color: #8b949e; display: block; margin-top: 2px; }
    
</style>
""", unsafe_allow_html=True)

# --- MOTORE DATI ---
@st.cache_data(ttl=120) 
def get_data():
    tickers = ["^TNX", "^VIX", "DX-Y.NYB", "GBPUSD=X", "JPY=X", "^DJI"]
    data = yf.download(tickers, period="5d", interval="1d", progress=False)
    
    # Fix per MultiIndex di yfinance
    try:
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs('Close', axis=1, level=0)
    except: pass

    res = {}
    for t in tickers:
        try:
            s = data[t].dropna()
            res[t] = {"price": s.iloc[-1], "change": ((s.iloc[-1] - s.iloc[-2])/s.iloc[-2])*100}
        except:
            res[t] = {"price": 0.0, "change": 0.0}
    return res

@st.cache_data(ttl=600)
def get_news():
    # Prendo solo le top 3 notizie da CNBC Economy
    feed = feedparser.parse("https://www.cnbc.com/id/10000664/device/rss/rss.html")
    return feed.entries[:3]

market = get_data()
news_data = get_news()

# --- HEADER COMPATTO ---
c1, c2, c3, c4 = st.columns(4)
def mini_metric(col, label, key, inv=False, is_pct=False):
    d = market[key]
    val = f"{d['price']:.2f}%" if is_pct else f"{d['price']:.2f}"
    chg = d['change']
    color = "#3fb950" if (chg < 0 and inv) or (chg > 0 and not inv) else "#f85149"
    icon = "▼" if chg < 0 else "▲"
    
    col.markdown(f"""
    <div class="metric-box">
        <div class="metric-lbl">{label}</div>
        <div class="metric-val">{val}</div>
        <div style="color: {color}; font-size: 0.8rem; font-weight: bold;">{icon} {abs(chg):.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

mini_metric(c1, "US 10Y YIELD", "^TNX", inv=True, is_pct=True)
mini_metric(c2, "VIX (FEAR)", "^VIX", inv=True)
mini_metric(c3, "DOLLAR DXY", "DX-Y.NYB", inv=True)
mini_metric(c4, "GBP STRENGTH", "GBPUSD=X", inv=False)

st.markdown("<div style='margin-bottom: 10px'></div>", unsafe_allow_html=True)

# --- BLOCCO CENTRALE: ANALISI ASSET ---
col_main_1, col_main_2 = st.columns(2)

# === US30 ===
with col_main_1:
    # Calcolo Score US30
    us_score = 50
    tnx_c = market['^TNX']['change']
    vix_p = market['^VIX']['price']
    
    if tnx_c < -0.5: us_score += 25 # Yields giù = Bene
    elif tnx_c > 0.5: us_score -= 25 # Yields su = Male
    
    if vix_p < 16: us_score += 25 # Calma = Bene
    elif vix_p > 22: us_score -= 25 # Paura = Male
    
    us_score = max(0, min(100, us_score))
    
    # Colore Cerchio
    u_color = "#3fb950" if us_score > 60 else "#f85149" if us_score < 40 else "#e3b341"
    u_bias = "BULLISH" if us_score > 60 else "BEARISH" if us_score < 40 else "NEUTRAL"
    
    st.markdown(f"""
    <div class="macro-card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:15px;">
            <div>
                <h2>US30 (DOW)</h2>
                <div style="color:{u_color}; font-weight:bold; letter-spacing:1px;">{u_bias}</div>
            </div>
            <div class="progress-ring" style="--p: {us_score}%; --color: {u_color};" data-score="{us_score}%"></div>
        </div>
        <div style="font-size: 0.85rem; color: #8b949e; line-height: 1.4;">
            <b>Fattori Chiave:</b><br>
            • Yields: <span style="color:{'#3fb950' if tnx_c < 0 else '#f85149'}">{tnx_c:+.2f}%</span> (Correlazione Inversa)<br>
            • VIX: {vix_p:.2f} (Soglia rischio: 20.00)
        </div>
    </div>
    """, unsafe_allow_html=True)

# === GBPJPY ===
with col_main_2:
    # Calcolo Score GJ
    gj_score = 50
    gbp_c = market['GBPUSD=X']['change']
    jpy_c = market['JPY=X']['change'] # JPY=X UP significa Yen debole (Buono per GJ)
    
    if gbp_c > 0.1: gj_score += 20
    elif gbp_c < -0.1: gj_score -= 20
    
    if jpy_c > 0.1: gj_score += 30 # Carry Trade ON
    elif jpy_c < -0.1: gj_score -= 30 # Yen Safety ON
    
    gj_score = max(0, min(100, gj_score))
    
    g_color = "#3fb950" if gj_score > 60 else "#f85149" if gj_score < 40 else "#e3b341"
    g_bias = "BUY / LONG" if gj_score > 60 else "SELL / SHORT" if gj_score < 40 else "RANGING"

    st.markdown(f"""
    <div class="macro-card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:15px;">
            <div>
                <h2>GBPJPY</h2>
                <div style="color:{g_color}; font-weight:bold; letter-spacing:1px;">{g_bias}</div>
            </div>
            <div class="progress-ring" style="--p: {gj_score}%; --color: {g_color};" data-score="{gj_score}%"></div>
        </div>
        <div style="font-size: 0.85rem; color: #8b949e; line-height: 1.4;">
            <b>Fattori Chiave:</b><br>
            • GBP Strength: <span style="color:{'#3fb950' if gbp_c > 0 else '#f85149'}">{gbp_c:+.2f}%</span><br>
            • Carry Trade (Yen Debole): <span style="color:{'#3fb950' if jpy_c > 0 else '#f85149'}">{jpy_c:+.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- COLONNE INFERIORI: NEWS & CALENDARIO ---
c_news, c_cal = st.columns([1, 1])

with c_news:
    st.markdown("### 📰 TOP MACRO NEWS")
    content = ""
    for item in news_data:
        published = item.published if 'published' in item else "Just now"
        # Accorcia la data
        published = published[:16] 
        content += f"""
        <div class="news-row">
            <a href="{item.link}" target="_blank" class="news-link">{item.title}</a>
            <span class="news-time">{published}</span>
        </div>
        """
    st.markdown(f'<div class="macro-card">{content}</div>', unsafe_allow_html=True)

with c_cal:
    st.markdown("### 📅 FTMO RED FOLDER (UK TIME)")
    # Calendar Widget Ridimensionato
    components.html("""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "width": "100%",
      "height": "180",
      "colorTheme": "dark",
      "isTransparent": true,
      "locale": "en",
      "importanceFilter": "1",
      "currencyFilter": "USD,GBP,JPY",
      "timeZone": "Europe/London"
    }
      </script>
    </div>
    """, height=200)
