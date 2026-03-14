import os
import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
import anthropic

# ── Configuration ────────────────────────────────────────────────
WATCHLIST       = ["NVDA", "AMD", "AAPL", "MSFT", "SPY"]
ALERT_THRESHOLD = 2.0

HEATMAP_SECTORS = {
    "Tech":     ["NVDA", "AAPL", "MSFT", "META", "GOOGL", "AMD"],
    "Finance":  ["JPM",  "BAC",  "GS",   "V",    "MA",    "WFC"],
    "Health":   ["UNH",  "JNJ",  "LLY",  "ABBV", "MRK",   "PFE"],
    "Energy":   ["XOM",  "CVX",  "COP",  "SLB",  "OXY",   "EOG"],
    "Consumer": ["AMZN", "TSLA", "HD",   "MCD",  "COST",  "NKE"],
}

MCAP = {
    "NVDA":2600,"AAPL":3000,"MSFT":2800,"META":1400,"GOOGL":2000,"AMD":250,
    "JPM":580,"BAC":330,"GS":160,"V":500,"MA":430,"WFC":320,
    "UNH":480,"JNJ":380,"LLY":700,"ABBV":300,"MRK":290,"PFE":160,
    "XOM":460,"CVX":290,"COP":180,"SLB":90,"OXY":70,"EOG":65,
    "AMZN":1900,"TSLA":600,"HD":340,"MCD":220,"COST":320,"NKE":120,
}

SECTOR_ETFS = {
    "Technology":"XLK","Financials":"XLF","Healthcare":"XLV",
    "Energy":"XLE","Consumer":"XLY","Industrials":"XLI",
    "Real Estate":"XLRE","Materials":"XLB","Utilities":"XLU",
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

html, body, [class*="css"] { font-family:'Geist','Inter',sans-serif; }
.stApp { background:#f5f6f8; color:#1a1f2e; }
header[data-testid="stHeader"] { background:transparent; height:0; }

[data-testid="stSidebar"] { background:#ffffff; border-right:1px solid #e8eaee; }
[data-testid="stSidebar"] > div { padding-top:0 !important; }

.sb-brand    { padding:24px 22px 18px; border-bottom:1px solid #f0f1f4; }
.sb-logo-row { display:flex;align-items:center;gap:10px;margin-bottom:3px; }
.sb-icon     { width:32px;height:32px;background:#1c3d8c;border-radius:8px;
               display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0; }
.sb-name     { font-size:17px;font-weight:600;color:#0f1624;letter-spacing:-0.3px; }
.sb-tag      { font-family:'Geist Mono',monospace;font-size:10px;color:#9ba3b2;letter-spacing:0.06em;margin-left:42px; }
.sb-meta     { padding:14px 22px 12px;font-family:'Geist Mono',monospace;font-size:10px;
               color:#b0b8c8;border-bottom:1px solid #f0f1f4; }
.sb-meta span { color:#6b7a94;display:block;margin-top:1px; }
.sb-lbl      { font-family:'Geist Mono',monospace;font-size:9px;font-weight:500;color:#c0c8d8;
               letter-spacing:0.16em;text-transform:uppercase;padding:16px 22px 8px; }
.wl-row      { display:flex;justify-content:space-between;align-items:center;
               padding:9px 22px;border-bottom:1px solid #f5f6f8; }
.wl-left     { display:flex;flex-direction:column; }
.wl-sym      { font-family:'Geist Mono',monospace;font-size:12px;font-weight:500;color:#4a5568;letter-spacing:0.05em; }
.wl-pr       { font-family:'Geist Mono',monospace;font-size:10px;color:#9ba3b2;margin-top:1px; }
.wl-pct      { font-family:'Geist Mono',monospace;font-size:12px;font-weight:500; }
.sb-status   { margin:14px 14px 0;padding:12px 16px;border-radius:8px;border:1px solid #eef0f4;background:#f8f9fb; }
.sb-status-lbl { font-family:'Geist Mono',monospace;font-size:9px;color:#b0b8c8;
                 letter-spacing:0.16em;text-transform:uppercase;margin-bottom:5px; }

.stButton > button { background:#ffffff;color:#4a5568;border:1px solid #e2e6ec;border-radius:6px;
    font-family:'Geist Mono',monospace;font-size:10px;letter-spacing:0.08em;text-transform:uppercase;
    padding:8px 16px;transition:all 0.15s;width:100%;box-shadow:0 1px 2px rgba(0,0,0,0.04); }
.stButton > button:hover { background:#f0f4ff;color:#1c3d8c;border-color:#c0cfe8; }

.stTabs [data-baseweb="tab-list"] { background:transparent;border-bottom:1px solid #e8eaee;gap:0;padding:0 4px; }
.stTabs [data-baseweb="tab"]      { font-family:'Geist',sans-serif;font-size:13px;font-weight:500;
    color:#8a94a6;background:transparent;border:none;padding:12px 22px;letter-spacing:0.01em; }
.stTabs [aria-selected="true"]    { color:#1c3d8c !important;border-bottom:2px solid #1c3d8c !important;background:transparent !important; }

.sec-hdr  { display:flex;align-items:center;gap:12px;margin:1.8rem 0 1.1rem; }
.sec-line { flex:1;height:1px;background:#e8eaee; }
.sec-txt  { font-family:'Geist Mono',monospace;font-size:9px;font-weight:500;color:#b0b8c8;
            letter-spacing:0.2em;text-transform:uppercase;white-space:nowrap; }

.stat-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:4px; }
.stat-card { background:#ffffff;border:1px solid #e8eaee;border-radius:10px;
             padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.stat-lbl  { font-family:'Geist Mono',monospace;font-size:9px;color:#9ba3b2;
             letter-spacing:0.14em;text-transform:uppercase;margin-bottom:6px; }
.stat-val  { font-family:'Geist Mono',monospace;font-size:22px;font-weight:400;
             color:#0f1624;letter-spacing:-0.5px;line-height:1; }
.stat-sub  { font-family:'Geist Mono',monospace;font-size:10px;color:#9ba3b2;margin-top:4px; }

.t-card  { background:#ffffff;border:1px solid #e8eaee;border-radius:10px;
           padding:18px 14px 15px;text-align:center;position:relative;overflow:hidden;
           box-shadow:0 1px 3px rgba(0,0,0,0.04);transition:box-shadow 0.2s; }
.t-card:hover { box-shadow:0 4px 12px rgba(0,0,0,0.08); }
.t-bar   { position:absolute;top:0;left:0;right:0;height:3px; }
.t-sym   { font-family:'Geist Mono',monospace;font-size:10px;font-weight:500;
           color:#9ba3b2;letter-spacing:0.18em;margin-bottom:8px; }
.t-price { font-family:'Geist Mono',monospace;font-size:22px;font-weight:400;
           color:#0f1624;margin-bottom:8px;letter-spacing:-0.5px; }
.t-chg   { font-family:'Geist Mono',monospace;font-size:11px;font-weight:500;
           display:inline-block;padding:3px 10px;border-radius:4px; }
.up  { color:#0a7c4e;background:#edf8f2; }
.dn  { color:#b91c3a;background:#fef1f3; }
.t-vol   { font-family:'Geist Mono',monospace;font-size:9px;color:#b0b8c8;margin-top:6px; }
.t-alert { font-family:'Geist Mono',monospace;font-size:9px;color:#b45309;
           letter-spacing:0.08em;margin-top:6px;background:#fffbeb;
           border-radius:3px;padding:2px 6px;display:inline-block; }

.hm-meta { display:flex;align-items:center;gap:8px;margin-top:8px;
           font-family:'Geist Mono',monospace;font-size:9px;color:#9ba3b2; }
.hm-bar  { width:90px;height:6px;border-radius:3px;
           background:linear-gradient(to right,#b91c3a,#fde8ec,#f5f6f8,#edf8f2,#0a7c4e);
           border:1px solid #e8eaee; }

.al-card  { background:#ffffff;border:1px solid #e8eaee;border-radius:10px;
            padding:0;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,0.04);
            display:flex;overflow:hidden; }
.al-stripe { width:4px;flex-shrink:0; }
.al-body   { flex:1;padding:16px 20px; }
.al-top    { display:flex;justify-content:space-between;align-items:center;margin-bottom:12px; }
.al-sym    { font-family:'Geist Mono',monospace;font-size:18px;font-weight:600;letter-spacing:0.04em; }
.al-right  { display:flex;align-items:center;gap:14px; }
.al-sig    { font-size:11px;font-weight:500;padding:4px 12px;border-radius:4px; }
.al-sig-dn { color:#b91c3a;background:#fef1f3; }
.al-sig-up { color:#0a7c4e;background:#edf8f2; }
.al-pct    { font-family:'Geist Mono',monospace;font-size:28px;font-weight:300;letter-spacing:-1px; }
.al-meta   { display:flex;gap:24px;flex-wrap:wrap; }
.al-m-item { display:flex;flex-direction:column;gap:3px; }
.al-m-lbl  { font-family:'Geist Mono',monospace;font-size:9px;color:#c0c8d8;
             letter-spacing:0.14em;text-transform:uppercase; }
.al-m-val  { font-family:'Geist Mono',monospace;font-size:12px;font-weight:500;color:#4a5568; }

.pos-card  { background:#ffffff;border:1px solid #e8eaee;border-radius:10px;
             padding:14px 16px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.pos-top   { display:flex;justify-content:space-between;align-items:center;margin-bottom:8px; }
.pos-sym   { font-family:'Geist Mono',monospace;font-size:13px;font-weight:600;color:#1a1f2e; }
.pos-alert { font-family:'Geist Mono',monospace;font-size:9px;color:#b45309;margin-left:8px; }
.pos-right { display:flex;align-items:center;gap:8px; }
.pos-price { font-family:'Geist Mono',monospace;font-size:15px;color:#1a1f2e;font-weight:400; }
.pos-chg   { font-family:'Geist Mono',monospace;font-size:11px;font-weight:500;
             padding:2px 8px;border-radius:4px; }
.pos-bar-bg{ background:#f0f1f4;border-radius:3px;height:3px;margin-bottom:8px; }
.pos-bar   { height:3px;border-radius:3px;opacity:0.6; }
.pos-range { margin-top:4px; }
.pos-range-labels { display:flex;justify-content:space-between;
    font-family:'Geist Mono',monospace;font-size:9px;color:#c0c8d8;margin-bottom:3px; }
.pos-range-track  { background:#f0f1f4;border-radius:3px;height:4px;position:relative; }
.pos-range-fill   { height:4px;border-radius:3px;opacity:0.25;position:absolute;left:0;top:0; }
.pos-range-dot    { width:8px;height:8px;border-radius:50%;position:absolute;
                    top:-2px;transform:translateX(-50%); }

.sector-row { display:flex;align-items:center;gap:12px;margin-bottom:10px; }
.sector-name { font-family:'Geist Mono',monospace;font-size:10px;font-weight:500;
               color:#4a5568;min-width:88px;letter-spacing:0.03em; }
.sector-track { flex:1;background:#f0f1f4;border-radius:3px;height:6px;position:relative; }
.sector-fill  { height:6px;border-radius:3px;position:absolute;top:0; }
.sector-mid   { position:absolute;left:50%;top:-2px;width:1px;height:10px;background:#e8eaee; }
.sector-pct   { font-family:'Geist Mono',monospace;font-size:10px;font-weight:500;min-width:50px;text-align:right; }

.chat-wrap { display:flex;flex-direction:column;gap:18px;margin-top:8px; }
.chat-u    { display:flex;justify-content:flex-end; }
.chat-b    { display:flex;justify-content:flex-start; }
.chat-sender { font-family:'Geist Mono',monospace;font-size:9px;letter-spacing:0.14em;
               text-transform:uppercase;color:#b0b8c8;margin-bottom:5px; }
.chat-sender-r { text-align:right; }
.bubble-u  { background:#1c3d8c;border-radius:10px 10px 2px 10px;padding:12px 16px;
             font-size:13px;color:#dce8ff;max-width:82%;line-height:1.65; }
.bubble-b  { background:#ffffff;border:1px solid #e8eaee;border-radius:10px 10px 10px 2px;
             padding:12px 16px;font-size:13px;color:#2d3748;max-width:88%;
             line-height:1.75;box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.chat-empty { text-align:center;padding:60px 20px;font-family:'Geist Mono',monospace;
              font-size:10px;color:#c8d0dc;letter-spacing:0.16em;text-transform:uppercase;line-height:2.8; }

.stTextInput > div > div > input { background:#ffffff !important;border:1px solid #e2e6ec !important;
    border-radius:7px !important;color:#1a1f2e !important;font-family:'Geist',sans-serif !important;
    font-size:13px !important;box-shadow:0 1px 2px rgba(0,0,0,0.03) !important; }
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
    st.markdown(f'<div class="sec-hdr"><div class="sec-line"></div>'
                f'<div class="sec-txt">{label}</div><div class="sec-line"></div></div>',
                unsafe_allow_html=True)

def pct_to_rgb(pct):
    c = max(-5.0, min(5.0, float(pct)))
    if c < 0:
        t = abs(c)/5.0
        return f"rgb({int(245+(185-245)*t)},{int(245+(28-245)*t)},{int(245+(58-245)*t)})"
    t = c/5.0
    return f"rgb({int(245+(10-245)*t)},{int(245+(124-245)*t)},{int(245+(78-245)*t)})"

def fmt_vol(v):
    if not v: return "—"
    if v >= 1e9: return f"{v/1e9:.1f}B"
    if v >= 1e6: return f"{v/1e6:.1f}M"
    return f"{v/1e3:.0f}K"

def color_for(pct):
    return "#0a7c4e" if pct >= 0 else "#b91c3a"

def bg_for(pct):
    return "#edf8f2" if pct >= 0 else "#fef1f3"


# ── Data fetching ─────────────────────────────────────────────────
@st.cache_data(ttl=900)
def fetch_prices(tickers):
    results = []
    for sym in tickers:
        try:
            fi   = yf.Ticker(sym).fast_info
            curr = float(fi.last_price)
            prev = float(fi.previous_close)
            pct  = round((curr - prev) / prev * 100, 2)
            results.append({
                "symbol":     sym,
                "price":      round(curr, 2),
                "prev_close": round(prev, 2),
                "pct_change": pct,
                "alert":      abs(pct) >= ALERT_THRESHOLD,
                "volume":     getattr(fi, "last_volume", None),
                "high":       round(float(getattr(fi, "year_high", curr)), 2),
                "low":        round(float(getattr(fi, "year_low",  curr)), 2),
            })
        except:
            results.append({"symbol": sym, "price": None, "pct_change": None,
                            "alert": False, "error": True})
    return results


@st.cache_data(ttl=300)
def fetch_heatmap(sectors):
    all_tickers = [t for tlist in sectors.values() for t in tlist]
    rows = []
    try:
        raw = yf.download(all_tickers, period="5d", interval="1d",
                          progress=False, auto_adjust=True, threads=True)
        close_df = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) \
                   else raw[["Close"]].rename(columns={"Close": all_tickers[0]})
        close_df = close_df.dropna(how="all")
        for sector, tickers in sectors.items():
            for sym in tickers:
                try:
                    col = close_df[sym].dropna()
                    if len(col) >= 2:
                        prev, curr = float(col.iloc[-2]), float(col.iloc[-1])
                        rows.append({"symbol": sym, "sector": sector,
                                     "price": round(curr,2),
                                     "pct_change": round((curr-prev)/prev*100, 2),
                                     "mcap": MCAP.get(sym, 50)})
                except: pass
    except: pass
    fetched = {r["symbol"] for r in rows}
    for sector, tickers in sectors.items():
        for sym in tickers:
            if sym not in fetched:
                try:
                    fi = yf.Ticker(sym).fast_info
                    curr, prev = float(fi.last_price), float(fi.previous_close)
                    rows.append({"symbol": sym, "sector": sector,
                                 "price": round(curr,2),
                                 "pct_change": round((curr-prev)/prev*100, 2),
                                 "mcap": MCAP.get(sym, 50)})
                except: pass
    return rows


@st.cache_data(ttl=600)
def fetch_sector_perf():
    out = {}
    for name, etf in SECTOR_ETFS.items():
        try:
            fi = yf.Ticker(etf).fast_info
            out[name] = round((float(fi.last_price)-float(fi.previous_close))/float(fi.previous_close)*100, 2)
        except:
            out[name] = None
    return out


@st.cache_data(ttl=1800)
def fetch_ticker_info(sym):
    try:
        info = yf.Ticker(sym).info
        return {
            "name":    info.get("longName", sym),
            "sector":  info.get("sector", "—"),
            "pe":      info.get("trailingPE"),
            "fwd_pe":  info.get("forwardPE"),
            "mktcap":  info.get("marketCap"),
            "w52_high":info.get("fiftyTwoWeekHigh"),
            "w52_low": info.get("fiftyTwoWeekLow"),
            "desc":    info.get("longBusinessSummary", ""),
        }
    except:
        return {}


# ── Claude AI ─────────────────────────────────────────────────────
def ask_claude(question, price_data):
    try:
        key    = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY","")
        client = anthropic.Anthropic(api_key=key)
        lines  = [f"  {r['symbol']}: ${r['price']} ({'▲' if r['pct_change']>=0 else '▼'}{abs(r['pct_change'])}%)"
                  for r in price_data if not r.get("error")]
        ctx    = "\n".join(lines) or "  (unavailable)"
        resp   = client.messages.create(
            model="claude-sonnet-4-5", max_tokens=512,
            system=f"""You are a sharp, concise market analyst for MarketPlus.
Live watchlist as of {datetime.now().strftime('%b %d, %Y %H:%M')}:
{ctx}
Be direct. Reference live prices when relevant. Max 180 words. Plain text only.""",
            messages=[{"role": "user", "content": question}])
        return resp.content[0].text
    except anthropic.AuthenticationError:
        return "API key not configured — add ANTHROPIC_API_KEY to Streamlit secrets."
    except Exception as e:
        err = str(e)
        if "credit" in err.lower():
            return "Insufficient API credits. Visit console.anthropic.com/settings/billing."
        return f"Unable to reach AI: {err}"


# ── HTML builders (avoids f-string nesting of raw HTML) ───────────
def render_position_card(row):
    """Build the full position card HTML as a plain string — no nested f-strings."""
    pct    = row["pct_change"]
    color  = color_for(pct)
    bg     = bg_for(pct)
    sign   = "+" if pct >= 0 else ""
    bar_w  = min(abs(pct) / 5 * 100, 100)

    alert_span = '<span class="pos-alert">◈ ALERT</span>' if row["alert"] else ""

    # 52-week range track
    high52 = row.get("high", 0) or 0
    low52  = row.get("low",  0) or 0
    curr   = row["price"]
    if high52 and low52 and high52 > low52:
        pos_pct = int((curr - low52) / (high52 - low52) * 100)
        pos_pct = max(0, min(100, pos_pct))
        range_block = (
            '<div class="pos-range">'
            '<div class="pos-range-labels">'
            f'<span>${low52}</span>'
            '<span style="color:#9ba3b2;font-size:9px;">52W Range</span>'
            f'<span>${high52}</span>'
            '</div>'
            '<div class="pos-range-track">'
            f'<div class="pos-range-fill" style="width:{pos_pct}%;background:{color};"></div>'
            f'<div class="pos-range-dot" style="left:{pos_pct}%;background:{color};"></div>'
            '</div>'
            '</div>'
        )
    else:
        range_block = ""

    html = (
        '<div class="pos-card">'
        '<div class="pos-top">'
        f'<div><span class="pos-sym">{row["symbol"]}</span>{alert_span}</div>'
        '<div class="pos-right">'
        f'<span class="pos-price">${row["price"]}</span>'
        f'<span class="pos-chg" style="color:{color};background:{bg};">{sign}{pct}%</span>'
        '</div>'
        '</div>'
        '<div class="pos-bar-bg">'
        f'<div class="pos-bar" style="width:{bar_w:.1f}%;background:{color};"></div>'
        '</div>'
        + range_block +
        '</div>'
    )
    return html


def render_alert_card(a):
    """Build alert card HTML as a plain string."""
    pct       = a["pct_change"]
    color     = color_for(pct)
    bg        = bg_for(pct)
    sign      = "+" if pct >= 0 else ""
    sig_cls   = "al-sig-up" if pct >= 0 else "al-sig-dn"
    signal    = "Bullish Move" if pct >= 0 else "Bearish Move"

    high52 = a.get("high", 0) or 0
    low52  = a.get("low",  0) or 0
    curr   = a["price"]
    if high52 and high52 > 0:
        from_high = f"{((curr-high52)/high52*100):+.1f}% from 52W high"
    else:
        from_high = "—"
    if low52 and low52 > 0 and curr > low52:
        from_low = f"+{((curr-low52)/low52*100):.1f}% from 52W low"
    else:
        from_low = "—"

    html = (
        '<div class="al-card">'
        f'<div class="al-stripe" style="background:{color};"></div>'
        '<div class="al-body">'
        '<div class="al-top">'
        f'<span class="al-sym" style="color:{color};">{a["symbol"]}</span>'
        '<div class="al-right">'
        f'<span class="al-sig {sig_cls}">{signal}</span>'
        f'<span class="al-pct" style="color:{color};">{sign}{pct}%</span>'
        '</div>'
        '</div>'
        '<div class="al-meta">'
        f'<div class="al-m-item"><span class="al-m-lbl">Current</span><span class="al-m-val">${a["price"]}</span></div>'
        f'<div class="al-m-item"><span class="al-m-lbl">Prev Close</span><span class="al-m-val">${a["prev_close"]}</span></div>'
        f'<div class="al-m-item"><span class="al-m-lbl">vs 52W High</span><span class="al-m-val" style="color:#b91c3a;">{from_high}</span></div>'
        f'<div class="al-m-item"><span class="al-m-lbl">vs 52W Low</span><span class="al-m-val" style="color:#0a7c4e;">{from_low}</span></div>'
        f'<div class="al-m-item"><span class="al-m-lbl">Volume</span><span class="al-m-val">{fmt_vol(a.get("volume"))}</span></div>'
        '</div>'
        '</div>'
        '</div>'
    )
    return html


# ════════════════════════════════════════════════════════════════
# DATA LOAD
# ════════════════════════════════════════════════════════════════
price_data  = fetch_prices(WATCHLIST)
alert_count = sum(1 for r in price_data if r.get("alert"))
alerts_list = [r for r in price_data if r.get("alert")]
valid       = [r for r in price_data if not r.get("error")]
avg_chg     = round(sum(r["pct_change"] for r in valid)/len(valid), 2) if valid else 0
best        = max(valid, key=lambda r: r["pct_change"], default=None)
worst       = min(valid, key=lambda r: r["pct_change"], default=None)
gainers_cnt = sum(1 for r in valid if r["pct_change"] > 0)
losers_cnt  = sum(1 for r in valid if r["pct_change"] < 0)


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

    st.markdown(f'<div class="sb-meta">Last updated<span>{datetime.now().strftime("%b %d, %Y  ·  %H:%M")}</span></div>',
                unsafe_allow_html=True)

    if st.button("↻  Refresh Prices"):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="sb-lbl">Watchlist</div>', unsafe_allow_html=True)
    for row in price_data:
        if row.get("error"): continue
        pct   = row["pct_change"]
        color = color_for(pct)
        sign  = "+" if pct >= 0 else ""
        st.markdown(
            f'<div class="wl-row">'
            f'<div class="wl-left"><span class="wl-sym">{row["symbol"]}</span>'
            f'<span class="wl-pr">${row["price"]}</span></div>'
            f'<span class="wl-pct" style="color:{color};">{sign}{pct}%</span>'
            f'</div>', unsafe_allow_html=True)

    sc  = "#b45309" if alert_count else "#0a7c4e"
    si  = "◈"      if alert_count else "◉"
    stx = f"{alert_count} alert{'s' if alert_count!=1 else ''} triggered" if alert_count else "All positions normal"
    st.markdown(
        f'<div class="sb-status"><div class="sb-status-lbl">Market Status</div>'
        f'<div style="font-family:\'Geist Mono\',monospace;font-size:12px;color:{sc};font-weight:500;">'
        f'{si} {stx}</div></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# MAIN TABS
# ════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["  Dashboard  ", "  AI Research  ", "  Alerts  "])


# ── TAB 1: DASHBOARD ─────────────────────────────────────────────
with tab1:
    # Portfolio summary
    sec_hdr("Portfolio Summary")
    avg_color = color_for(avg_chg)
    avg_sign  = "+" if avg_chg >= 0 else ""
    b_sign    = "+" if best  and best["pct_change"]  >= 0 else ""
    w_sign    = "+" if worst and worst["pct_change"] >= 0 else ""
    st.markdown(
        f'<div class="stat-grid">'
        f'<div class="stat-card"><div class="stat-lbl">Avg Daily Move</div>'
        f'<div class="stat-val" style="color:{avg_color};">{avg_sign}{avg_chg}%</div>'
        f'<div class="stat-sub">{gainers_cnt} up · {losers_cnt} down</div></div>'
        f'<div class="stat-card"><div class="stat-lbl">Best Performer</div>'
        f'<div class="stat-val" style="color:{color_for(best["pct_change"]) if best else "#9ba3b2"};">'
        f'{"" if not best else best["symbol"]}</div>'
        f'<div class="stat-sub" style="color:{color_for(best["pct_change"]) if best else "#9ba3b2"};">'
        f'{b_sign}{best["pct_change"] if best else "—"}%</div></div>'
        f'<div class="stat-card"><div class="stat-lbl">Worst Performer</div>'
        f'<div class="stat-val" style="color:{color_for(worst["pct_change"]) if worst else "#9ba3b2"};">'
        f'{"" if not worst else worst["symbol"]}</div>'
        f'<div class="stat-sub" style="color:{color_for(worst["pct_change"]) if worst else "#9ba3b2"};">'
        f'{w_sign}{worst["pct_change"] if worst else "—"}%</div></div>'
        f'<div class="stat-card"><div class="stat-lbl">Active Alerts</div>'
        f'<div class="stat-val" style="color:{"#b45309" if alert_count else "#0a7c4e"};">{alert_count}</div>'
        f'<div class="stat-sub">threshold ±{ALERT_THRESHOLD}%</div></div>'
        f'</div>', unsafe_allow_html=True)

    # Heatmap
    sec_hdr("Market Heatmap — Top Movers")
    all_sectors = list(HEATMAP_SECTORS.keys())
    if "hm_sector" not in st.session_state:
        st.session_state.hm_sector = "All"

    btn_cols = st.columns(len(all_sectors)+1, gap="small")
    with btn_cols[0]:
        if st.button("All", key="hm_all"): st.session_state.hm_sector = "All"
    for i, s in enumerate(all_sectors):
        with btn_cols[i+1]:
            if st.button(s, key=f"hm_{s}"): st.session_state.hm_sector = s

    with st.spinner("Fetching market data…"):
        hm_rows = fetch_heatmap(HEATMAP_SECTORS)

    sel = st.session_state.hm_sector
    if sel != "All":
        hm_rows = [r for r in hm_rows if r["sector"] == sel]

    if hm_rows:
        import plotly.graph_objects as go
        syms   = [r["symbol"] for r in hm_rows]
        secs   = [r["sector"] for r in hm_rows]
        pcts   = [r["pct_change"] for r in hm_rows]
        prices = [r["price"] for r in hm_rows]
        mcaps  = [r["mcap"] for r in hm_rows]
        colors = [pct_to_rgb(p) for p in pcts]
        signs  = ["+" if p >= 0 else "" for p in pcts]
        tile   = [f"<b>{s}</b><br>{sg}{p:.2f}%<br>${pr}"
                  for s,sg,p,pr in zip(syms,signs,pcts,prices)]
        fig = go.Figure(go.Treemap(
            labels=syms, parents=secs, values=mcaps,
            text=tile, textinfo="text",
            textfont=dict(family="Geist Mono, monospace", size=12),
            customdata=list(zip(pcts,prices,secs,signs)),
            hovertemplate="<b>%{label}</b><br>Change: %{customdata[3]}%{customdata[0]:.2f}%<br>Price: $%{customdata[1]}<br>Sector: %{customdata[2]}<extra></extra>",
            marker=dict(colors=colors, line=dict(width=2, color="#f5f6f8"), pad=dict(t=24,l=3,r=3,b=3)),
            tiling=dict(packing="squarify", pad=4), root_color="#f5f6f8",
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=0,b=0),
                          height=380, font=dict(family="Geist Mono, monospace", color="#1a1f2e", size=11))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        gainers = sum(1 for p in pcts if p > 0)
        losers  = sum(1 for p in pcts if p < 0)
        avg_hm  = round(sum(pcts)/len(pcts), 2)
        st.markdown(
            f'<div class="hm-meta"><span style="color:#b91c3a;">▼ -5%</span><div class="hm-bar"></div>'
            f'<span style="color:#0a7c4e;">▲ +5%</span> &nbsp;·&nbsp;'
            f'<span style="color:#0a7c4e;font-weight:500;">{gainers} up</span> &nbsp;·&nbsp;'
            f'<span style="color:#b91c3a;font-weight:500;">{losers} down</span> &nbsp;·&nbsp;'
            f'<span>Avg {"+" if avg_hm>=0 else ""}{avg_hm}%</span>'
            f'<span style="margin-left:auto;color:#c8d0dc;">{len(hm_rows)} stocks · 5-min refresh</span></div>',
            unsafe_allow_html=True)
    else:
        st.warning("Heatmap unavailable — click ↻ Refresh Prices to retry.")

    # Watchlist cards
    sec_hdr("Watchlist — Live Prices")
    cols = st.columns(len(WATCHLIST), gap="small")
    for col, row in zip(cols, price_data):
        with col:
            if row.get("error"):
                st.markdown(
                    f'<div class="t-card"><div class="t-sym">{row["symbol"]}</div>'
                    f'<div class="t-price" style="font-size:14px;color:#b91c3a;">ERR</div></div>',
                    unsafe_allow_html=True)
            else:
                pct  = row["pct_change"]
                bar  = color_for(pct)
                cls  = "up" if pct >= 0 else "dn"
                sign = "+" if pct >= 0 else ""
                al   = '<div class="t-alert">◈ ALERT</div>' if row["alert"] else ""
                st.markdown(
                    f'<div class="t-card">'
                    f'<div class="t-bar" style="background:{bar};"></div>'
                    f'<div class="t-sym">{row["symbol"]}</div>'
                    f'<div class="t-price">${row["price"]}</div>'
                    f'<div class="t-chg {cls}">{sign}{pct}%</div>'
                    f'<div class="t-vol">Vol {fmt_vol(row.get("volume"))}</div>'
                    f'{al}</div>', unsafe_allow_html=True)

    # Sector performance
    sec_hdr("Sector Performance — Today")
    with st.spinner("Loading sectors…"):
        sector_data = fetch_sector_perf()
    sorted_sectors = sorted([(k,v) for k,v in sector_data.items() if v is not None],
                            key=lambda x: x[1], reverse=True)
    max_abs = max(abs(v) for _,v in sorted_sectors) if sorted_sectors else 1
    for name, pct in sorted_sectors:
        color  = color_for(pct)
        sign   = "+" if pct >= 0 else ""
        half_w = abs(pct) / max_abs * 50  # percent of half-track
        if pct >= 0:
            fill_style = f"left:50%;width:{half_w:.1f}%;background:{color};opacity:0.65;"
        else:
            fill_style = f"left:{50-half_w:.1f}%;width:{half_w:.1f}%;background:{color};opacity:0.65;"
        st.markdown(
            f'<div class="sector-row">'
            f'<div class="sector-name">{name}</div>'
            f'<div class="sector-track">'
            f'<div class="sector-mid"></div>'
            f'<div class="sector-fill" style="{fill_style}border-radius:2px;height:6px;top:0;"></div>'
            f'</div>'
            f'<div class="sector-pct" style="color:{color};">{sign}{pct}%</div>'
            f'</div>', unsafe_allow_html=True)

    # Price chart
    sec_hdr("Price History — 30 Days")
    sel_ticker = st.selectbox("Ticker", WATCHLIST, label_visibility="collapsed")
    try:
        hist = yf.Ticker(sel_ticker).history(period="1mo")
        if not hist.empty:
            close = hist["Close"]
            is_up = close.iloc[-1] >= close.iloc[0]
            lc    = "#0a7c4e" if is_up else "#b91c3a"
            fc    = "rgba(10,124,78,0.06)" if is_up else "rgba(185,28,58,0.06)"
            fig_c = go.Figure()
            fig_c.add_trace(go.Scatter(x=hist.index, y=close, mode="lines",
                line=dict(color=lc, width=1.8), fill="tozeroy", fillcolor=fc,
                hovertemplate="<b>$%{y:.2f}</b><extra></extra>"))
            fig_c.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                font=dict(family="Geist Mono, monospace", color="#9ba3b2", size=10),
                xaxis=dict(gridcolor="#f0f1f4", zeroline=False, tickfont=dict(size=10,color="#9ba3b2"), showline=False),
                yaxis=dict(gridcolor="#f0f1f4", zeroline=False, tickprefix="$",
                           tickfont=dict(size=10,color="#9ba3b2"), showline=False, side="right"),
                margin=dict(l=0,r=60,t=12,b=0), height=260, showlegend=False, hovermode="x unified",
                hoverlabel=dict(bgcolor="#1c3d8c", bordercolor="#1c3d8c",
                                font=dict(family="Geist Mono", size=11, color="#ffffff")))
            st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False})
    except Exception as e:
        st.caption(f"Chart unavailable: {e}")


# ── TAB 2: AI RESEARCH ───────────────────────────────────────────
with tab2:
    sec_hdr("AI Research Assistant")
    st.markdown(
        '<div style="font-size:13px;color:#6b7a94;margin-bottom:24px;line-height:1.7;max-width:600px;">'
        'Ask anything about your watchlist. Powered by Claude with live price context injected automatically.'
        '</div>', unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    examples = ["",
        "What drove NVDA's revenue growth?",
        "What are AAPL's main business segments?",
        "How is AMD positioned in the AI chip market?",
        "What risks could affect MSFT this year?",
        "Compare NVDA and AMD on gross margins",
        "Why is SPY moving today?",
        "What is the outlook for semiconductor stocks?",
    ]

    col_q, col_i = st.columns([2,3])
    with col_q:
        selected_q = st.selectbox("Quick prompts", examples, label_visibility="visible")
    with col_i:
        question = st.text_input("Your question", value=selected_q,
                                 placeholder="Ask about earnings, valuation, risks, strategy…")

    c1, c2, _ = st.columns([1,1,6])
    with c1:
        ask_btn = st.button("Ask →", disabled=not question)
    with c2:
        if st.button("Clear"):
            st.session_state.chat_history = []
            st.rerun()

    if ask_btn and question:
        with st.spinner("Analyzing…"):
            answer = ask_claude(question, price_data)
        st.session_state.chat_history.append({"question": question, "answer": answer})

    if st.session_state.chat_history:
        st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)
        for entry in reversed(st.session_state.chat_history):
            st.markdown(
                '<div>'
                '<div class="chat-u"><div>'
                '<div class="chat-sender chat-sender-r">You</div>'
                f'<div class="bubble-u">{entry["question"]}</div>'
                '</div></div>'
                '<div class="chat-b" style="margin-top:10px;"><div>'
                '<div class="chat-sender">MarketPlus AI</div>'
                f'<div class="bubble-b">{entry["answer"]}</div>'
                '</div></div>'
                '</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="chat-empty">No messages yet<br>'
            '<span style="font-size:9px;color:#d8dde8;">Select a prompt or type a question</span></div>',
            unsafe_allow_html=True)

    # Company snapshot
    sec_hdr("Company Snapshot")
    snap_ticker = st.selectbox("Company", WATCHLIST, key="snap_sel", label_visibility="collapsed")
    snap = fetch_ticker_info(snap_ticker)
    if snap:
        mktcap_s = f"${snap['mktcap']/1e9:.0f}B" if snap.get("mktcap") else "—"
        pe_s     = f"{snap['pe']:.1f}x"       if snap.get("pe")      else "—"
        fpe_s    = f"{snap['fwd_pe']:.1f}x"   if snap.get("fwd_pe")  else "—"
        h52_s    = f"${snap['w52_high']}"      if snap.get("w52_high") else "—"
        l52_s    = f"${snap['w52_low']}"       if snap.get("w52_low")  else "—"
        sc1,sc2,sc3,sc4 = st.columns(4)
        def snap_card(lbl, val, sub=""):
            sub_html = f'<div class="stat-sub">{sub}</div>' if sub else ""
            return (f'<div class="stat-card"><div class="stat-lbl">{lbl}</div>'
                    f'<div class="stat-val" style="font-size:16px;">{val}</div>{sub_html}</div>')
        with sc1: st.markdown(snap_card("Market Cap", mktcap_s), unsafe_allow_html=True)
        with sc2: st.markdown(snap_card("P/E Ratio", pe_s, f"Fwd {fpe_s}"), unsafe_allow_html=True)
        with sc3: st.markdown(snap_card("52W High", h52_s), unsafe_allow_html=True)
        with sc4: st.markdown(snap_card("52W Low",  l52_s), unsafe_allow_html=True)
        if snap.get("desc"):
            desc = snap["desc"][:420] + ("…" if len(snap["desc"]) > 420 else "")
            st.markdown(
                f'<div style="background:#ffffff;border:1px solid #e8eaee;border-radius:10px;'
                f'padding:16px 20px;margin-top:10px;font-size:12px;color:#6b7a94;line-height:1.7;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
                f'<div style="font-family:\'Geist Mono\',monospace;font-size:9px;color:#b0b8c8;'
                f'letter-spacing:0.16em;text-transform:uppercase;margin-bottom:8px;">About {snap_ticker}</div>'
                f'{desc}</div>', unsafe_allow_html=True)


# ── TAB 3: ALERTS ────────────────────────────────────────────────
with tab3:

    # Status banner
    if alert_count:
        b_color  = "#b45309"; b_bg = "#fffbeb"; b_border = "#fde68a"
        b_icon   = "◈"
        b_msg    = f"{alert_count} position{'s' if alert_count>1 else ''} exceeded the ±{ALERT_THRESHOLD}% threshold today"
    else:
        b_color  = "#0a7c4e"; b_bg = "#f0fdf7"; b_border = "#a7f0cc"
        b_icon   = "◉"
        b_msg    = f"All positions within normal range · threshold ±{ALERT_THRESHOLD}%"

    st.markdown(
        f'<div style="background:{b_bg};border:1px solid {b_border};border-radius:10px;'
        f'padding:16px 20px;margin-bottom:8px;display:flex;align-items:center;gap:12px;">'
        f'<span style="font-family:\'Geist Mono\',monospace;font-size:18px;color:{b_color};">{b_icon}</span>'
        f'<div><div style="font-family:\'Geist Mono\',monospace;font-size:12px;color:{b_color};font-weight:500;">{b_msg}</div>'
        f'<div style="font-family:\'Geist Mono\',monospace;font-size:10px;color:{b_color};opacity:0.6;margin-top:2px;">'
        f'{datetime.now().strftime("%b %d, %Y  ·  %H:%M")}</div></div></div>',
        unsafe_allow_html=True)

    # Triggered alert cards
    if alerts_list:
        sec_hdr("Triggered Alerts")
        for a in alerts_list:
            st.markdown(render_alert_card(a), unsafe_allow_html=True)

    # All positions — 2-column grid
    sec_hdr("All Positions")
    col_l, col_r = st.columns(2, gap="large")
    mid = (len(valid) + 1) // 2
    for i, row in enumerate(valid):
        target = col_l if i < mid else col_r
        with target:
            st.markdown(render_position_card(row), unsafe_allow_html=True)

    # Threshold settings
    sec_hdr("Alert Settings")
    c_thr, c_info = st.columns([2,3])
    with c_thr:
        new_threshold = st.slider("Threshold", min_value=0.5, max_value=10.0,
                                  value=float(ALERT_THRESHOLD), step=0.5, format="%.1f%%",
                                  label_visibility="collapsed")
    with c_info:
        triggered = sum(1 for r in valid if abs(r["pct_change"]) >= new_threshold)
        tc = "#b45309" if triggered else "#0a7c4e"
        st.markdown(
            f'<div style="padding:12px 0;font-family:\'Geist Mono\',monospace;font-size:11px;color:#6b7a94;">'
            f'At ±{new_threshold:.1f}% threshold: '
            f'<span style="color:{tc};font-weight:500;margin-left:6px;">'
            f'{triggered} of {len(valid)} positions would trigger</span></div>',
            unsafe_allow_html=True)


st.markdown(
    '<div class="mp-footer">MarketPlus &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; Claude AI &nbsp;·&nbsp; yfinance</div>',
    unsafe_allow_html=True)
