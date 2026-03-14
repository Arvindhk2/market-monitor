import os
import yfinance as yf
import streamlit as st
from datetime import datetime
import anthropic

# ── Configuration ────────────────────────────────────────────────
WATCHLIST = ["NVDA", "AMD", "AAPL", "MSFT", "SPY"]
ALERT_THRESHOLD = 2.0

# Heatmap universe — major stocks by sector
HEATMAP_SECTORS = {
    "Technology":  ["NVDA", "AAPL", "MSFT", "META", "GOOGL", "AMZN", "AMD", "AVGO", "ORCL", "CRM"],
    "Finance":     ["JPM", "BAC", "GS", "MS", "V", "MA", "BRK-B", "WFC", "AXP", "BLK"],
    "Healthcare":  ["UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "DHR", "AMGN", "PFE"],
    "Energy":      ["XOM", "CVX", "COP", "SLB", "OXY", "PSX", "MPC", "VLO", "EOG", "HES"],
    "Consumer":    ["TSLA", "HD", "MCD", "NKE", "SBUX", "TGT", "COST", "LOW", "CMG", "AZO"],
}

# Approximate market cap weights for treemap sizing (billions)
MCAP = {
    "AAPL":3000,"MSFT":2800,"NVDA":2600,"GOOGL":2000,"AMZN":1900,"META":1400,
    "BRK-B":800,"AVGO":700,"LLY":700,"TSLA":600,"JPM":580,"V":500,"UNH":480,
    "XOM":460,"WFC":320,"MA":430,"BAC":330,"COST":320,"HD":340,"ORCL":380,
    "AMD":250,"CRM":280,"ABBV":300,"MRK":290,"JNJ":380,"TMO":220,"ABT":190,
    "DHR":160,"AMGN":160,"PFE":160,"CVX":290,"COP":180,"SLB":90,"OXY":70,
    "PSX":60,"MPC":65,"VLO":55,"EOG":65,"HES":45,"GS":160,"MS":150,
    "AXP":190,"BLK":120,"MCD":220,"NKE":120,"SBUX":90,"TGT":70,
    "LOW":150,"CMG":80,"AZO":50,
}

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="MarketPlus",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Geist', 'Inter', sans-serif; }

.stApp { background: #f5f6f8; color: #1a1f2e; }
header[data-testid="stHeader"] { background: transparent; height: 0; }

[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e8eaee; }
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

.sb-brand { padding: 24px 22px 18px; border-bottom: 1px solid #f0f1f4; }
.sb-logo-row { display: flex; align-items: center; gap: 10px; margin-bottom: 3px; }
.sb-icon { width:32px;height:32px;background:#1c3d8c;border-radius:8px;
           display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0; }
.sb-name { font-size:17px;font-weight:600;color:#0f1624;letter-spacing:-0.3px; }
.sb-tag  { font-family:'Geist Mono',monospace;font-size:10px;color:#9ba3b2;
           letter-spacing:0.06em;margin-left:42px; }
.sb-meta { padding:14px 22px 12px;font-family:'Geist Mono',monospace;
           font-size:10px;color:#b0b8c8;border-bottom:1px solid #f0f1f4; }
.sb-meta span { color:#6b7a94;display:block;margin-top:1px; }
.sb-lbl  { font-family:'Geist Mono',monospace;font-size:9px;font-weight:500;
           color:#c0c8d8;letter-spacing:0.16em;text-transform:uppercase;padding:16px 22px 8px; }
.wl-row  { display:flex;justify-content:space-between;align-items:center;
           padding:9px 22px;border-bottom:1px solid #f5f6f8;transition:background 0.1s; }
.wl-row:hover { background:#fafbfc; }
.wl-sym  { font-family:'Geist Mono',monospace;font-size:12px;font-weight:500;
           color:#4a5568;letter-spacing:0.05em; }
.wl-pct  { font-family:'Geist Mono',monospace;font-size:12px;font-weight:500; }
.sb-status { margin:14px 14px 0;padding:12px 16px;border-radius:8px;
             border:1px solid #eef0f4;background:#f8f9fb; }
.sb-status-lbl { font-family:'Geist Mono',monospace;font-size:9px;color:#b0b8c8;
                 letter-spacing:0.16em;text-transform:uppercase;margin-bottom:5px; }

/* Buttons */
.stButton > button { background:#ffffff;color:#4a5568;border:1px solid #e2e6ec;
    border-radius:6px;font-family:'Geist Mono',monospace;font-size:10px;
    letter-spacing:0.08em;text-transform:uppercase;padding:8px 16px;
    transition:all 0.15s;width:100%;box-shadow:0 1px 2px rgba(0,0,0,0.04); }
.stButton > button:hover { background:#f0f4ff;color:#1c3d8c;border-color:#c0cfe8; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background:transparent;border-bottom:1px solid #e8eaee;gap:0;padding:0 4px; }
.stTabs [data-baseweb="tab"] { font-family:'Geist',sans-serif;font-size:13px;font-weight:500;
    color:#8a94a6;background:transparent;border:none;padding:12px 22px;letter-spacing:0.01em; }
.stTabs [aria-selected="true"] { color:#1c3d8c !important;border-bottom:2px solid #1c3d8c !important;background:transparent !important; }

/* Section headers */
.sec-hdr { display:flex;align-items:center;gap:12px;margin:1.8rem 0 1.1rem; }
.sec-line { flex:1;height:1px;background:#e8eaee; }
.sec-txt  { font-family:'Geist Mono',monospace;font-size:9px;font-weight:500;
            color:#b0b8c8;letter-spacing:0.2em;text-transform:uppercase;white-space:nowrap; }

/* Heatmap loading */
.hm-loading { text-align:center;padding:80px 20px;font-family:'Geist Mono',monospace;
              font-size:10px;color:#b0b8c8;letter-spacing:0.16em;text-transform:uppercase; }
.hm-meta { display:flex;align-items:center;gap:8px;margin-top:8px;font-family:'Geist Mono',monospace;
           font-size:9px;color:#9ba3b2;letter-spacing:0.04em; }
.hm-legend-bar { width:100px;height:6px;border-radius:3px;
    background:linear-gradient(to right,#b91c3a,#fde8ec,#f5f6f8,#edf8f2,#0a7c4e);
    border:1px solid #e8eaee; }

/* Ticker cards */
.t-card { background:#ffffff;border:1px solid #e8eaee;border-radius:10px;
          padding:18px 14px 15px;text-align:center;position:relative;overflow:hidden;
          box-shadow:0 1px 3px rgba(0,0,0,0.04);transition:box-shadow 0.2s,border-color 0.2s; }
.t-card:hover { box-shadow:0 4px 12px rgba(0,0,0,0.08);border-color:#d0d6e0; }
.t-bar  { position:absolute;top:0;left:0;right:0;height:3px; }
.t-sym  { font-family:'Geist Mono',monospace;font-size:10px;font-weight:500;
          color:#9ba3b2;letter-spacing:0.18em;margin-bottom:8px; }
.t-price { font-family:'Geist Mono',monospace;font-size:22px;font-weight:400;
           color:#0f1624;margin-bottom:8px;letter-spacing:-0.5px; }
.t-chg  { font-family:'Geist Mono',monospace;font-size:11px;font-weight:500;
          display:inline-block;padding:3px 10px;border-radius:4px; }
.up { color:#0a7c4e;background:#edf8f2; }
.dn { color:#b91c3a;background:#fef1f3; }
.t-alert { font-family:'Geist Mono',monospace;font-size:9px;color:#b45309;
           letter-spacing:0.08em;margin-top:7px;background:#fffbeb;
           border-radius:3px;padding:2px 6px;display:inline-block; }

/* Alert cards */
.a-card { display:flex;align-items:center;justify-content:space-between;
          padding:14px 20px;border-radius:8px;margin-bottom:8px;border:1px solid; }
.a-up { background:#f0fdf7;border-color:#a7f0cc; }
.a-dn { background:#fff1f3;border-color:#fca5b3; }

/* Chat */
.chat-wrap { display:flex;flex-direction:column;gap:18px;margin-top:8px; }
.chat-u    { display:flex;justify-content:flex-end; }
.chat-b    { display:flex;justify-content:flex-start; }
.chat-sender { font-family:'Geist Mono',monospace;font-size:9px;letter-spacing:0.14em;
               text-transform:uppercase;color:#b0b8c8;margin-bottom:5px; }
.chat-sender-r { text-align:right; }
.bubble-u { background:#1c3d8c;border-radius:10px 10px 2px 10px;padding:12px 16px;
            font-size:13px;color:#dce8ff;max-width:82%;line-height:1.65; }
.bubble-b { background:#ffffff;border:1px solid #e8eaee;border-radius:10px 10px 10px 2px;
            padding:12px 16px;font-size:13px;color:#2d3748;max-width:88%;
            line-height:1.75;box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.chat-empty { text-align:center;padding:60px 20px;font-family:'Geist Mono',monospace;
              font-size:10px;color:#c8d0dc;letter-spacing:0.16em;text-transform:uppercase;line-height:2.8; }

/* Form elements */
.stTextInput > div > div > input { background:#ffffff !important;border:1px solid #e2e6ec !important;
    border-radius:7px !important;color:#1a1f2e !important;
    font-family:'Geist',sans-serif !important;font-size:13px !important;
    box-shadow:0 1px 2px rgba(0,0,0,0.03) !important; }
.stTextInput > div > div > input:focus { border-color:#1c3d8c !important;
    box-shadow:0 0 0 3px rgba(28,61,140,0.08) !important; }
.stTextInput > label, .stSelectbox > label { font-family:'Geist Mono',monospace !important;
    font-size:9px !important;font-weight:500 !important;color:#9ba3b2 !important;
    letter-spacing:0.18em !important;text-transform:uppercase !important; }
.stSelectbox > div > div { background:#ffffff !important;border:1px solid #e2e6ec !important;
    border-radius:7px !important;box-shadow:0 1px 2px rgba(0,0,0,0.03) !important; }
[data-baseweb="select"] span { color:#1a1f2e !important;font-family:'Geist',sans-serif !important;font-size:13px !important; }

hr { border-color:#e8eaee !important; }
.mp-footer { text-align:center;margin-top:3rem;padding:18px;font-family:'Geist Mono',monospace;
             font-size:9px;color:#c8d0dc;letter-spacing:0.16em;border-top:1px solid #e8eaee;text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────
def sec_hdr(label):
    st.markdown(f"""
    <div class="sec-hdr">
        <div class="sec-line"></div>
        <div class="sec-txt">{label}</div>
        <div class="sec-line"></div>
    </div>""", unsafe_allow_html=True)


def pct_to_rgb(pct):
    """Map % change → RGB color. Red ≤ -5%, white = 0, green ≥ +5%."""
    clamped = max(-5.0, min(5.0, pct))
    if clamped < 0:
        t = abs(clamped) / 5.0
        r = int(245 + (185 - 245) * t)
        g = int(245 + (28  - 245) * t)
        b = int(245 + (58  - 245) * t)
    else:
        t = clamped / 5.0
        r = int(245 + (10  - 245) * t)
        g = int(245 + (124 - 245) * t)
        b = int(245 + (78  - 245) * t)
    return f"rgb({r},{g},{b})"


def text_on_bg(pct):
    return "#ffffff" if abs(pct) >= 2.8 else "#1a1f2e"


# ── Price fetching ────────────────────────────────────────────────
@st.cache_data(ttl=900)
def fetch_prices(tickers):
    results = []
    for symbol in tickers:
        try:
            fi = yf.Ticker(symbol).fast_info
            curr = fi.last_price
            prev = fi.previous_close
            pct  = round((curr - prev) / prev * 100, 2)
            results.append({"symbol": symbol, "price": round(curr, 2),
                            "prev_close": round(prev, 2), "pct_change": pct,
                            "alert": abs(pct) >= ALERT_THRESHOLD})
        except Exception as e:
            results.append({"symbol": symbol, "price": None,
                            "pct_change": None, "alert": False, "error": str(e)})
    return results


@st.cache_data(ttl=300)
def fetch_heatmap(sectors: dict) -> list:
    """
    Fetch per-ticker via fast_info — reliable on Streamlit Cloud.
    Returns flat list: {symbol, sector, price, pct_change, mcap}.
    """
    rows = []
    for sector, tickers in sectors.items():
        for sym in tickers:
            try:
                fi   = yf.Ticker(sym).fast_info
                curr = float(fi.last_price)
                prev = float(fi.previous_close)
                if prev and prev > 0:
                    pct = round((curr - prev) / prev * 100, 2)
                    rows.append({
                        "symbol":     sym,
                        "sector":     sector,
                        "price":      round(curr, 2),
                        "pct_change": pct,
                        "mcap":       MCAP.get(sym, 50),
                    })
            except Exception:
                pass
    return rows


# ── Claude AI ────────────────────────────────────────────────────
def ask_claude(question: str, price_data: list) -> str:
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
        client  = anthropic.Anthropic(api_key=api_key)
        lines   = [f"  {r['symbol']}: ${r['price']} ({'▲' if r['pct_change']>=0 else '▼'}{abs(r['pct_change'])}%)"
                   for r in price_data if not r.get("error")]
        ctx     = "\n".join(lines) or "  (unavailable)"
        resp    = client.messages.create(
            model="claude-sonnet-4-5", max_tokens=512,
            system=f"""You are a sharp, concise market analyst for MarketPlus.
Live watchlist as of {datetime.now().strftime('%b %d, %Y %H:%M')}:
{ctx}
Be direct. Reference prices when relevant. Max 180 words. Plain text only.""",
            messages=[{"role": "user", "content": question}]
        )
        return resp.content[0].text
    except anthropic.AuthenticationError:
        return "API key not configured — add ANTHROPIC_API_KEY to Streamlit secrets."
    except Exception as e:
        err = str(e)
        if "credit" in err.lower():
            return "Insufficient API credits. Visit console.anthropic.com/settings/billing."
        return f"Unable to reach AI service: {err}"


# ════════════════════════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════════════════════════
price_data  = fetch_prices(WATCHLIST)
alert_count = sum(1 for r in price_data if r.get("alert"))


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-logo-row">
            <div class="sb-icon">📈</div>
            <div class="sb-name">MarketPlus</div>
        </div>
        <div class="sb-tag">AI Research Terminal</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sb-meta">Last updated<span>{datetime.now().strftime('%b %d, %Y  ·  %H:%M')}</span></div>
    """, unsafe_allow_html=True)

    if st.button("↻  Refresh Prices"):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="sb-lbl">Watchlist</div>', unsafe_allow_html=True)
    for row in price_data:
        if row.get("error"):
            continue
        pct   = row["pct_change"]
        color = "#0a7c4e" if pct >= 0 else "#b91c3a"
        sign  = "+" if pct >= 0 else ""
        st.markdown(f"""
        <div class="wl-row">
            <span class="wl-sym">{row['symbol']}</span>
            <span class="wl-pct" style="color:{color};">{sign}{pct}%</span>
        </div>""", unsafe_allow_html=True)

    if alert_count:
        sc, si, st_txt = "#b45309", "◈", f"{alert_count} alert{'s' if alert_count!=1 else ''} triggered"
    else:
        sc, si, st_txt = "#0a7c4e", "◉", "All positions normal"
    st.markdown(f"""
    <div class="sb-status">
        <div class="sb-status-lbl">Market Status</div>
        <div style="font-family:'Geist Mono',monospace;font-size:12px;color:{sc};font-weight:500;">
            {si} {st_txt}
        </div>
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["  Dashboard  ", "  AI Research  ", "  Alerts  "])


# ── TAB 1: DASHBOARD ─────────────────────────────────────────────
with tab1:

    # ────────────────────────────────────────────────────────────
    # HEATMAP
    # ────────────────────────────────────────────────────────────
    sec_hdr("Market Heatmap — Top Movers")

    all_sectors = list(HEATMAP_SECTORS.keys())
    if "hm_sector" not in st.session_state:
        st.session_state.hm_sector = "All"

    # Sector filter pills
    pill_cols = st.columns(len(all_sectors) + 1, gap="small")
    with pill_cols[0]:
        if st.button("All", key="hm_all"):
            st.session_state.hm_sector = "All"
            st.cache_data.clear()
            st.rerun()
    for i, s in enumerate(all_sectors):
        with pill_cols[i + 1]:
            if st.button(s, key=f"hm_{s}"):
                st.session_state.hm_sector = s
                st.rerun()

    selected_sector = st.session_state.hm_sector

    # Load heatmap data
    with st.spinner("Loading market data…"):
        hm_rows = fetch_heatmap(HEATMAP_SECTORS)

    # Filter by sector
    if selected_sector != "All":
        hm_rows = [r for r in hm_rows if r["sector"] == selected_sector]

    if hm_rows:
        import plotly.graph_objects as go

        # Build treemap — parent = sector label
        symbols = [r["symbol"]     for r in hm_rows]
        sectors = [r["sector"]     for r in hm_rows]
        pcts    = [r["pct_change"] for r in hm_rows]
        prices  = [r["price"]      for r in hm_rows]
        mcaps   = [r["mcap"]       for r in hm_rows]

        colors     = [pct_to_rgb(p)    for p in pcts]
        txt_colors = [text_on_bg(p)    for p in pcts]
        signs      = ["+" if p >= 0 else "" for p in pcts]

        # Tile text — symbol + change % + price
        tile_text = [
            f"<b>{sym}</b><br>{s}{p:+.2f}%<br><span style='font-size:10px'>${pr}</span>"
            for sym, s, p, pr in zip(symbols, signs, pcts, prices)
        ]

        fig_hm = go.Figure(go.Treemap(
            labels   = symbols,
            parents  = sectors,
            values   = mcaps,
            text     = tile_text,
            textinfo = "text",
            textfont = dict(family="Geist Mono, monospace", size=11),
            customdata = list(zip(pcts, prices, sectors, signs)),
            hovertemplate = (
                "<b>%{label}</b><br>"
                "Change: %{customdata[3]}%{customdata[0]:.2f}%<br>"
                "Price: $%{customdata[1]}<br>"
                "Sector: %{customdata[2]}"
                "<extra></extra>"
            ),
            marker = dict(
                colors = colors,
                line   = dict(width=2, color="#f5f6f8"),
                pad    = dict(t=22, l=3, r=3, b=3),
            ),
            tiling     = dict(packing="squarify", pad=4),
            root_color = "#f5f6f8",
        ))

        fig_hm.update_layout(
            paper_bgcolor = "rgba(0,0,0,0)",
            margin        = dict(l=0, r=0, t=0, b=0),
            height        = 440,
            font          = dict(family="Geist Mono, monospace", color="#1a1f2e", size=11),
        )

        st.plotly_chart(fig_hm, use_container_width=True,
                        config={"displayModeBar": False, "responsive": True})

        # Legend row
        gainers = sum(1 for p in pcts if p > 0)
        losers  = sum(1 for p in pcts if p < 0)
        avg_pct = round(sum(pcts) / len(pcts), 2) if pcts else 0
        sign_avg = "+" if avg_pct >= 0 else ""

        st.markdown(f"""
        <div class="hm-meta">
            <span style="color:#b91c3a;">▼ Bearish</span>
            <div class="hm-legend-bar"></div>
            <span style="color:#0a7c4e;">▲ Bullish</span>
            &nbsp;·&nbsp;
            <span style="color:#0a7c4e;">{gainers} up</span>
            &nbsp;·&nbsp;
            <span style="color:#b91c3a;">{losers} down</span>
            &nbsp;·&nbsp;
            <span>Avg {sign_avg}{avg_pct}%</span>
            <span style="margin-left:auto;color:#c8d0dc;">
                {len(hm_rows)} stocks · tile size = mkt cap · refreshes every 5 min
            </span>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="hm-loading">
            Unable to load heatmap data<br>
            <span style="font-size:9px;color:#d0d8e4;">
                Try clicking Refresh Prices in the sidebar
            </span>
        </div>""", unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # WATCHLIST CARDS
    # ────────────────────────────────────────────────────────────
    sec_hdr("Watchlist — Live Prices")

    cols = st.columns(len(WATCHLIST), gap="small")
    for col, row in zip(cols, price_data):
        with col:
            if row.get("error"):
                st.markdown(f"""
                <div class="t-card">
                    <div class="t-sym">{row['symbol']}</div>
                    <div class="t-price" style="font-size:14px;color:#b91c3a;">ERR</div>
                </div>""", unsafe_allow_html=True)
            else:
                pct  = row["pct_change"]
                is_up = pct >= 0
                bar  = "#0a7c4e" if is_up else "#b91c3a"
                cls  = "up" if is_up else "dn"
                sign = "+" if is_up else ""
                alert_html = '<div class="t-alert">◈ ALERT</div>' if row["alert"] else ""
                st.markdown(f"""
                <div class="t-card">
                    <div class="t-bar" style="background:{bar};"></div>
                    <div class="t-sym">{row['symbol']}</div>
                    <div class="t-price">${row['price']}</div>
                    <div class="t-chg {cls}">{sign}{pct}%</div>
                    {alert_html}
                </div>""", unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # PRICE CHART
    # ────────────────────────────────────────────────────────────
    sec_hdr("Price History — 30 Days")

    selected_ticker = st.selectbox("Ticker", WATCHLIST, label_visibility="collapsed")

    try:
        hist = yf.Ticker(selected_ticker).history(period="1mo")
        if not hist.empty:
            close  = hist["Close"]
            is_up  = close.iloc[-1] >= close.iloc[0]
            lc     = "#0a7c4e" if is_up else "#b91c3a"
            fc     = "rgba(10,124,78,0.06)" if is_up else "rgba(185,28,58,0.06)"
            fig_ch = go.Figure()
            fig_ch.add_trace(go.Scatter(
                x=hist.index, y=close, mode="lines",
                line=dict(color=lc, width=1.8), fill="tozeroy", fillcolor=fc,
                hovertemplate="<b>$%{y:.2f}</b><extra></extra>",
            ))
            fig_ch.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                font=dict(family="Geist Mono, monospace", color="#9ba3b2", size=10),
                xaxis=dict(gridcolor="#f0f1f4", zeroline=False,
                           tickfont=dict(size=10, color="#9ba3b2"), showline=False),
                yaxis=dict(gridcolor="#f0f1f4", zeroline=False, tickprefix="$",
                           tickfont=dict(size=10, color="#9ba3b2"), showline=False, side="right"),
                margin=dict(l=0, r=60, t=12, b=0), height=260,
                showlegend=False, hovermode="x unified",
                hoverlabel=dict(bgcolor="#1c3d8c", bordercolor="#1c3d8c",
                                font=dict(family="Geist Mono", size=11, color="#ffffff")),
            )
            st.plotly_chart(fig_ch, use_container_width=True, config={"displayModeBar": False})
    except Exception as e:
        st.caption(f"Chart unavailable: {e}")


# ── TAB 2: AI RESEARCH ───────────────────────────────────────────
with tab2:
    sec_hdr("AI Research Assistant")

    st.markdown("""
    <div style="font-size:13px;color:#6b7a94;margin-bottom:24px;line-height:1.7;max-width:600px;">
        Ask anything about your watchlist. Powered by Claude with live price context injected automatically.
    </div>""", unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    examples = [
        "",
        "What drove NVDA's revenue growth?",
        "What are AAPL's main business segments?",
        "How is AMD positioned in the AI chip market?",
        "What risks could affect MSFT this year?",
        "Compare NVDA and AMD on gross margins",
        "Why is SPY moving today?",
    ]

    selected_q = st.selectbox("Quick prompts", examples, label_visibility="visible")
    question   = st.text_input("Your question", value=selected_q,
                               placeholder="Ask about earnings, valuation, risks, strategy...")

    col_ask, col_clear, _ = st.columns([1, 1, 5])
    with col_ask:
        ask_btn = st.button("Ask →", disabled=not question)
    with col_clear:
        if st.button("Clear"):
            st.session_state.chat_history = []
            st.rerun()

    if ask_btn and question:
        with st.spinner("Analyzing..."):
            answer = ask_claude(question, price_data)
        st.session_state.chat_history.append({"question": question, "answer": answer})

    if st.session_state.chat_history:
        st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)
        for entry in reversed(st.session_state.chat_history):
            st.markdown(f"""
            <div>
                <div class="chat-u">
                    <div>
                        <div class="chat-sender chat-sender-r">You</div>
                        <div class="bubble-u">{entry['question']}</div>
                    </div>
                </div>
                <div class="chat-b" style="margin-top:10px;">
                    <div>
                        <div class="chat-sender">MarketPlus AI</div>
                        <div class="bubble-b">{entry['answer']}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="chat-empty">
            No messages yet<br>
            <span style="font-size:9px;color:#d8dde8;">Select a prompt or type a question</span>
        </div>""", unsafe_allow_html=True)


# ── TAB 3: ALERTS ────────────────────────────────────────────────
with tab3:
    sec_hdr("Active Alerts")

    alerts = [r for r in price_data if r.get("alert")]
    if not alerts:
        st.markdown(f"""
        <div style="text-align:center;padding:48px 20px;font-family:'Geist Mono',monospace;
                    font-size:10px;color:#c8d0dc;letter-spacing:0.16em;text-transform:uppercase;line-height:3;">
            ◉ No alerts triggered<br>
            <span style="font-size:9px;color:#d8dde8;">Threshold · ±{ALERT_THRESHOLD}%</span>
        </div>""", unsafe_allow_html=True)
    else:
        for a in alerts:
            pct   = a["pct_change"]
            css   = "a-up" if pct > 0 else "a-dn"
            color = "#0a7c4e" if pct > 0 else "#b91c3a"
            sign  = "+" if pct > 0 else ""
            direction = "Bullish signal" if pct > 0 else "Bearish signal"
            st.markdown(f"""
            <div class="a-card {css}">
                <div>
                    <span style="font-family:'Geist Mono',monospace;font-size:14px;
                                 color:{color};font-weight:600;">{a['symbol']}</span>
                    <span style="font-family:'Geist Mono',monospace;font-size:10px;
                                 color:{color};opacity:0.6;margin-left:12px;">{direction}</span>
                </div>
                <div style="text-align:right;">
                    <div style="font-family:'Geist Mono',monospace;font-size:16px;
                                color:{color};font-weight:500;">{sign}{pct}%</div>
                    <div style="font-family:'Geist Mono',monospace;font-size:10px;
                                color:{color};opacity:0.5;">${a['prev_close']} → ${a['price']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    sec_hdr("Alert Threshold")
    new_threshold = st.slider("threshold", min_value=0.5, max_value=10.0,
                              value=float(ALERT_THRESHOLD), step=0.5, format="%.1f%%",
                              label_visibility="collapsed")
    st.markdown(f"""
    <div style="font-family:'Geist Mono',monospace;font-size:10px;color:#9ba3b2;
                margin-top:6px;letter-spacing:0.1em;">
        Alerts trigger on moves exceeding ±{new_threshold:.1f}%
    </div>""", unsafe_allow_html=True)

    sec_hdr("All Positions")
    for row in price_data:
        if row.get("error"):
            continue
        pct   = row["pct_change"]
        color = "#0a7c4e" if pct >= 0 else "#b91c3a"
        bar_w = min(abs(pct) / 5 * 100, 100)
        sign  = "+" if pct >= 0 else ""
        st.markdown(f"""
        <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;
                        font-family:'Geist Mono',monospace;font-size:11px;margin-bottom:6px;">
                <span style="color:#4a5568;font-weight:500;">{row['symbol']}</span>
                <span style="color:{color};font-weight:500;">{sign}{pct}%</span>
            </div>
            <div style="background:#f0f1f4;border-radius:3px;height:3px;">
                <div style="background:{color};width:{bar_w}%;height:3px;
                            border-radius:3px;opacity:0.7;"></div>
            </div>
        </div>""", unsafe_allow_html=True)


# ── Footer ───────────────────────────────────────────────────────
st.markdown("""
<div class="mp-footer">
    MarketPlus &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; Claude AI &nbsp;·&nbsp; yfinance
</div>""", unsafe_allow_html=True)
