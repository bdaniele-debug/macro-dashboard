import streamlit as st
import yfinance as yf
import streamlit.components.v1 as components

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Macro Sentinel", layout="wide", page_icon="⚡")

# --- CSS PERSONALIZZATO (Stile Dashboard Finanziaria) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .main-card {
        background-color: #1e1e24;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .factor-good { color: #00E676; font-weight: bold; }
    .factor-bad { color: #FF1744; font-weight: bold; }
    .factor-neu { color: #FFCC00; font-weight: bold; }
    h1, h2, h3 { color: #ffffff; }
    .big-verdict { font-size: 2rem; font-weight: 800; text-transform: uppercase; text-align: center; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# --- 1. RECUPERO DATI MACRO ---
@st.cache_data(ttl=300) # Aggiorna ogni 5 min
def get_data():
    # Tickers: US 10Y Yield, VIX, GBPUSD, USDJPY
    tickers = ["^TNX", "^VIX", "GBPUSD=X", "JPY=X"]
    data = yf.download(tickers, period="5d", interval="1d")
    
    # Prendi l'ultima chiusura e la variazione %
    latest = data['Close'].iloc[-1]
    prev = data['Close'].iloc[-2]
    changes = ((latest - prev) / prev) * 100
    
    return latest, changes

try:
    prices, changes = get_data()
except:
    st.error("Errore di connessione con Yahoo Finance. Riprova più tardi.")
    st.stop()

# --- 2. TITOLO E STATUS ---
st.title("⚡ MACRO SENTINEL | FTMO FOCUS")
st.markdown("Analisi dei Fattori Chiave e Calendario News Ristretto (Rosse).")

# --- 3. ANALISI US30 (DOW JONES) ---
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🇺🇸 US30 (DOW JONES)")
    
    # Logica US30
    us_score = 0
    reasons = []

    # Fattore 1: Rendimenti (Yields)
    tnx_val = prices['^TNX']
    tnx_chg = changes['^TNX']
    if tnx_chg < 0:
        us_score += 1
        reasons.append(f"<span class='factor-good'>✅ I rendimenti 10Y scendono ({tnx_chg:.2f}%):</span> Questo aiuta le azioni.")
    else:
        reasons.append(f"<span class='factor-bad'>❌ I rendimenti 10Y salgono (+{tnx_chg:.2f}%):</span> Pressione ribassista sull'US30.")

    # Fattore 2: Paura (VIX)
    vix_val = prices['^VIX']
    if vix_val < 20:
        us_score += 1
        reasons.append(f"<span class='factor-good'>✅ VIX sotto 20 ({vix_val:.2f}):</span> Ambiente 'Risk-On' tranquillo.")
    else:
        reasons.append(f"<span class='factor-bad'>❌ VIX alto ({vix_val:.2f}):</span> Troppa paura nel mercato.")

    # Verdetto Finale
    if us_score == 2:
        verdict = "BULLISH (RIALZISTA)"
        color = "#00E676"
    elif us_score == 0:
        verdict = "BEARISH (RIBASSISTA)"
        color = "#FF1744"
    else:
        verdict = "MIXED (INCERTO)"
        color = "#FFCC00"

    st.markdown(f"""
    <div class="main-card">
        <div class="big-verdict" style="color: {color}">{verdict}</div>
        <hr style="border-color: #333;">
        <p><strong>FATTORI CHIAVE OGGI:</strong></p>
        <ul>
            {''.join([f"<li>{r}</li>" for r in reasons])}
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- 4. ANALISI GBPJPY (GUPPY) ---
with col2:
    st.markdown("### 🇬🇧/🇯🇵 GBPJPY (GUPPY)")
    
    # Logica GJ
    gj_score = 0
    gj_reasons = []

    # Fattore 1: Forza Sterlina
    gbp_chg = changes['GBPUSD=X']
    if gbp_chg > 0:
        gj_score += 1
        gj_reasons.append(f"<span class='factor-good'>✅ La Sterlina è forte vs USD (+{gbp_chg:.2f}%).</span>")
    else:
        gj_reasons.append(f"<span class='factor-bad'>❌ La Sterlina è debole oggi ({gbp_chg:.2f}%).</span>")

    # Fattore 2: Debolezza Yen (USDJPY sale = Yen debole)
    jpy_chg = changes['JPY=X'] # Se positivo, USD sale su JPY, quindi JPY si indebolisce
    if jpy_chg > 0:
        gj_score += 1
        gj_reasons.append(f"<span class='factor-good'>✅ Lo Yen si sta indebolendo:</span> Ottimo per il Carry Trade.")
    else:
        gj_reasons.append(f"<span class='factor-bad'>❌ Lo Yen si sta rafforzando (Safe Haven):</span> Pericoloso per i long.")

    # Verdetto Finale
    if gj_score == 2:
        gj_verdict = "STRONG BUY"
        gj_color = "#00E676"
    elif gj_score == 0:
        gj_verdict = "STRONG SELL"
        gj_color = "#FF1744"
    else:
        gj_verdict = "RANGING (LATERALE)"
        gj_color = "#FFCC00"

    st.markdown(f"""
    <div class="main-card">
        <div class="big-verdict" style="color: {gj_color}">{gj_verdict}</div>
        <hr style="border-color: #333;">
        <p><strong>FATTORI CHIAVE OGGI:</strong></p>
        <ul>
            {''.join([f"<li>{r}</li>" for r in gj_reasons])}
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- 5. FTMO RADAR (NEWS ROSSE) ---
st.markdown("### ⚠️ FTMO RED FOLDER RADAR (UK TIME)")
st.info("Regola FTMO: Nessun trade 2 minuti prima/dopo queste notizie.")

components.html("""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
  {
  "width": "100%",
  "height": "600",
  "colorTheme": "dark",
  "isTransparent": false,
  "locale": "it",
  "importanceFilter": "1",
  "currencyFilter": "USD,GBP,JPY",
  "timeZone": "Europe/London"
}
  </script>
</div>
""", height=600)
