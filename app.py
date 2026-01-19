import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import datetime
import streamlit.components.v1 as components

# --- CONFIGURAZIONE PAGINA (Layout Wide) ---
st.set_page_config(
    page_title="Macro Dashboard",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# --- CSS AGGIORNATO (TESTI GRANDI & VISIBILI) ---
st.markdown("""
<style>
    /* Sfondo generale */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Riduzione spazi inutili in alto */
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    
    /* Card Stile "Glass" */
    .macro-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
    }
    
    /* TITOLI PIÙ GRANDI */
    h3 { font-size: 1.1rem !important; margin-bottom: 8px !important; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    h2 { font-size: 1.6rem !important; font-weight: 800; color: #fff; margin: 0; }
    
    /* Metriche in alto (Molto più grandi) */
    .metric-box {
        text-align: center;
        background: #0d1117;
        border-radius: 8px;
        padding: 15px 10px; /* Più spazio interno */
        border: 1px solid #21262d;
    }
    .metric-lbl { font-size: 0.9rem; color: #8b949e; margin-bottom: 5px; text-transform: uppercase; }
    .metric-val { font-size: 1.8rem; font-weight: 800; color: #fff; } /* Valore gigante */
    
    /* INDICATORE A CERCHIO */
    .progress-ring {
        position: relative;
        width: 120px; /* Più grande */
        height: 120px; /* Più grande */
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
        width: 104px; /* Adattato al nuovo cerchio */
        height: 104px;
        background: #161b22;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.6rem; /* Testo % più grande */
        color: #fff;
    }

    /* News Link */
    .news-link { 
        font-size: 1.1rem !important; /* Testo notizie più grande */
        color: #58a6ff !important; 
        text-decoration: none; 
        font-weight: 600; 
        display: block;
        margin-bottom: 4px;
    }
    .news-link:hover { text-decoration: underline; }
    .news-time { font-size: 0.85rem; color: #8b949e; }
    
</style>
""", unsafe_allow_html=True)

# --- MOTORE DATI ---
@st.cache_data(ttl=120) 
def get_data():
    tickers = ["^TNX", "^VIX", "DX-Y.NYB", "GBPUSD=X", "JPY=X", "^DJI"]
    data = yf.download(tickers, period="5d", interval="1d", progress=False)
    
    # Fix per MultiIndex
    try:
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs('Close', axis=1, level=0)
    except: pass

    res = {}
    for t in tickers:
        try:
            s = data[t].dropna()
            # Calcolo variazione %
            change = ((s.iloc[-1] - s.iloc[-2])/s.iloc[-2])*100
            res[t] = {"price": s.iloc[-1], "change": change}
        except:
            res[t] = {"price": 0.0, "change": 0.0}
    return res

@st.cache_data(ttl=600)
def get_news():
    # Top 4 notizie Macro/Forex
    feed_url = "https://www.cnbc.com/id/10000664/device/rss/rss.html"
    feed = feedparser.parse(feed_url)
    return feed.entries[:4]

market = get_data()
news_data = get_news()

# --- 1. HEADER METRICHE (Top Row) ---
c1, c2, c3, c4 = st.columns(4)

def mini_metric(col, label, key, inv=False, is_pct=False):
    d = market[key]
    val_fmt = f"{d['price']:.2f}%" if is_pct else f"{d['price']:.2f}"
    chg = d['change']
    
    # Logica Colore: Se inv=True, rosso è positivo (es. Yields salgono = rosso)
    if inv:
        color = "#3fb950" if chg < 0 else "#f85149" # Verde se scende, Rosso se sale
    else:
        color = "#3fb950" if chg > 0 else "#f85149" # Verde se sale
        
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

mini_metric(c1, "US 10Y YIELD", "^TNX", inv=True, is_pct=True)
mini_metric(c2, "VIX (FEAR)", "^VIX", inv=True)
mini_metric(c3, "DOLLAR DXY", "DX-Y.NYB", inv=True)
mini_metric(c4, "GBP STRENGTH", "GBPUSD=X", inv=False)

st.markdown("<div style='margin-bottom: 20px'></div>", unsafe_allow_html=True)

# --- 2. ANALISI ASSET (Middle Row) ---
col_us, col_gj = st.columns(2)

# === US30 LOGIC ===
with col_us:
    us_score = 50
    tnx_c = market['^TNX']['change']
    vix_p = market['^VIX']['price']
    
    # Logica Punteggio
    if tnx_c < -0.5: us_score += 25
    elif tnx_c > 0.5: us_score -= 25
    
    if vix_p < 16: us_score += 25
    elif vix_p > 22: us_score -= 25
    
    us_score = max(0, min(100, us_score))
    
    # Colori e Testi
    u_color = "#3fb950" if us_score > 60 else "#f85149" if us_score < 40 else "#e3b341"
    u_bias = "BULLISH" if us_score > 60 else "BEARISH" if us_score < 40 else "NEUTRAL"
    
    # Card HTML
    st.markdown(f"""
    <div class="macro-card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
            <div>
                <h2>US30 (DOW)</h2>
                <div style="color:{u_color}; font-weight:800; font-size:1.2rem; letter-spacing:1px; margin-top:5px;">{u_bias}</div>
            </div>
            <div class="progress-ring" style="--p: {us_score}%; --color: {u_color};" data-score="{us_score}%"></div>
        </div>
        <div style="font-size: 1rem; color: #c9d1d9; line-height: 1.6;">
            <b>Fattori Chiave:</b><br>
            • Yields: <span style="color:{'#3fb950' if tnx_c < 0 else '#f85149'}; font-weight:bold;">{tnx_c:+.2f}%</span> (Se scende è Bullish)<br>
            • VIX: <span style="font-weight:bold;">{vix_p:.2f}</span> (Soglia Rischio: 20.00)
        </div>
    </div>
    """, unsafe_allow_html=True)

# === GBPJPY LOGIC ===
with col_gj:
    gj_score = 50
    gbp_c = market['GBPUSD=X']['change']
    jpy_c = market['JPY=X']['change']
    
    if gbp_c > 0.1: gj_score += 20
    elif gbp_c < -0.1: gj_score -= 20
    
    if jpy_c > 0.1: gj_score += 30 # Yen debole = Bullish GJ
    elif jpy_c < -0.1: gj_score -= 30
    
    gj_score = max(0, min(100, gj_score))
    
    g_color = "#3fb950" if gj_score > 60 else "#f85149" if gj_score < 40 else "#e3b341"
    g_bias = "BUY / LONG" if gj_score > 60 else "SELL / SHORT" if gj_score < 40 else "RANGING"

    st.markdown(f"""
    <div class="macro-card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
            <div>
                <h2>GBPJPY</h2>
                <div style="color:{g_color}; font-weight:800; font-size:1.2rem; letter-spacing:1px; margin-top:5px;">{g_bias}</div>
            </div>
            <div class="progress-ring" style="--p: {gj_score}%; --color: {g_color};" data-score="{gj_score}%"></div>
        </div>
        <div style="font-size: 1rem; color: #c9d1d9; line-height: 1.6;">
            <b>Fattori Chiave:</b><br>
            • GBP Strength: <span style="color:{'#3fb950' if gbp_c > 0 else '#f85149'}; font-weight:bold;">{gbp_c:+.2f}%</span><br>
            • Yen Weakness: <span style="color:{'#3fb950' if jpy_c > 0 else '#f85149'}; font-weight:bold;">{jpy_c:+.2f}%</span> (Carry Trade)
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 3. NEWS & CALENDARIO (Bottom Row) ---
c_news, c_cal = st.columns([1, 1])

with c_news:
    st.markdown("### 📰 TOP MACRO NEWS")
    # Uso un container con bordo
    with st.container(border=True):
        if news_data:
            for item in news_data:
                # Renderizzo ogni notizia singolarmente (Fix problema HTML grezzo)
                st.markdown(f"""
                <a href="{item.link}" target="_blank" class="news-link">{item.title}</a>
                <div class="news-time">Pubblicato: {item.published[:16]}</div>
                <hr style="margin: 10px 0; border-color: #30363d;">
                """, unsafe_allow_html=True)
        else:
            st.write("Nessuna notizia recente trovata.")

with c_cal:
    st.markdown("### 📅 FTMO RED FOLDER (UK TIME)")
    # Widget Calendario
    components.html("""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
      {
      "width": "100%",
      "height": "300",
      "colorTheme": "dark",
      "isTransparent": true,
      "locale": "en",
      "importanceFilter": "1",
      "currencyFilter": "USD,GBP,JPY",
      "timeZone": "Europe/London"
    }
      </script>
    </div>
    """, height=300)
