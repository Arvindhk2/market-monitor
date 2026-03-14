import os
import yfinance as yf
import streamlit as st
from datetime import datetime
import anthropic

# ── Configuration ────────────────────────────────────────────────
WATCHLIST = ["NVDA", "AMD", "AAPL", "MSFT", "SPY"]
ALERT_THRESHOLD = 2.0

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

html, body, [class*="css"] {
    font-family: 'Geist', 'Inter', sans-serif;
}

/* ── Base ── */
.stApp {
    background: #f5f6f8;
    color: #1a1f2e;
}

header[data-testid="stHeader"] { background: transparent; height: 0; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e8eaee;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* Brand */
.sb-brand {
    padding: 24px 22px 18px;
    border-bottom: 1px solid #f0f1f4;
}
.sb-logo-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 3px;
}
.sb-icon {
    width: 32px; height: 32px;
    background: #1c3d8c;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; flex-shrink: 0;
}
.sb-name {
    font-size: 17px;
    font-weight: 600;
    color: #0f1624;
    letter-spacing: -0.3px;
}
.sb-tag {
    font-family: 'Geist Mono', monospace;
    font-size: 10px;
    color: #9ba3b2;
    letter-spacing: 0.06em;
    margin-left: 42px;
}

/* Sidebar meta */
.sb-meta {
    padding: 14px 22px 12px;
    font-family: 'Geist Mono', monospace;
    font-size: 10px;
    color: #b0b8c8;
    border-bottom: 1px solid #f0f1f4;
}
.sb-meta span { color: #6b7a94; display: block; margin-top: 1px; }

/* Section label */
.sb-lbl {
    font-family: 'Geist Mono', monospace;
    font-size: 9px;
    font-weight: 500;
    color: #c0c8d8;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    padding: 16px 22px 8px;
}

/* Watchlist rows */
.wl-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 22px;
    border-bottom: 1px solid #f5f6f8;
    transition: background 0.1s;
}
.wl-row:hover { background: #fafbfc; }
.wl-sym {
    font-family: 'Geist Mono', monospace;
    font-size: 12px;
    font-weight: 500;
    color: #4a5568;
    letter-spacing: 0.05em;
}
.wl-pct {
    font-family: 'Geist Mono', monospace;
    font-size: 12px;
    font-weight: 500;
}

/* Status block */
.sb-status {
    margin: 14px 14px 0;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #eef0f4;
    background: #f8f9fb;
}
.sb-status-lbl {
    font-family: 'Geist Mono', monospace;
    font-size: 9px;
    color: #b0b8c8;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 5px;
}

/* ── Buttons ── */
.stButton > button {
    background: #ffffff;
    color: #4a5568;
    border: 1px solid #e2e6ec;
    border-radius: 6px;
    font-family: 'Geist Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 8px 16px;
    transition: all 0.15s;
    width: 100%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.stButton > button:hover {
    background: #f0f4ff;
    color: #1c3d8c;
    border-color: #c0cfe8;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #e8eaee;
    gap: 0;
    padding: 0 4px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Geist', sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: #8a94a6;
    background: transparent;
    border: none;
    padding: 12px 22px;
    letter-spacing: 0.01em;
}
.stTabs [aria-selected="true"] {
    color: #1c3d8c !important;
    border-bottom: 2px solid #1c3d8c !important;
    background: transparent !important;
}

/* ── Section header ── */
.sec-hdr {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 1.8rem 0 1.1rem;
}
.sec-line { flex: 1; height: 1px; background: #e8eaee; }
.sec-txt {
    font-family: 'Geist Mono', monospace;
    font-size: 9px;
    font-weight: 500;
    color: #b0b8c8;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    white-space: nowrap;
}

/* ── Ticker cards ── */
.t-card {
    background: #ffffff;
    border: 1px solid #e8eaee;
    border-radius: 10px;
    padding: 18px 14px 15px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s, border-color 0.2s;
}
.t-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    border-color: #d0d6e0;
}
.t-bar { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.t-sym {
    font-family: 'Geist Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    color: #9ba3b2;
    letter-spacing: 0.18em;
    margin-bottom: 8px;
}
.t-price {
    font-family: 'Geist Mono', monospace;
    font-size: 22px;
    font-weight: 400;
    color: #0f1624;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}
.t-chg {
    font-family: 'Geist Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
}
.up   { color: #0a7c4e; background: #edf8f2; }
.dn   { color: #b91c3a; background: #fef1f3; }
.t-alert {
    font-family: 'Geist Mono', monospace;
    font-size: 9px;
    color: #b45309;
    letter-spacing: 0.08em;
    margin-top: 7px;
    background: #fffbeb;
    border-radius: 3px;
    padding: 2px 6px;
    display: inline-block;
}

/* ── Alert cards ── */
.a-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 18px;
    border-radius: 8px;
    margin-bottom: 8px;
    border: 1px solid;
}
.a-up  { background: #f0fdf7; border-color: #a7f0cc; }
.a-dn  { background: #fff1f3; border-color: #fca5b3; }

/* ── Chat ── */
.chat-wrap { display: flex; flex-direction: column; gap: 18px; margin-top: 8px; }
.chat-u { display: flex; justify-content: flex-end; }
.chat-b { display: flex; justify-content: flex-start; }
.chat-sender {
    font-family: 'Geist Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #b0b8c8;
    margin-bottom: 5px;
}
.chat-sender-r { text-align: right; }
.bubble-u {
    background: #1c3d8c;
    border-radius: 10px 10px 2px 10px;
    padding: 12px 16px;
    font-size: 13px;
    color: #dce8ff;
    max-width: 82%;
    line-height: 1.65;
}
.bubble-b {
    background: #ffffff;
    border: 1px solid #e8eaee;
    border-radius: 10px 10px 10px 2px;
    padding: 12px 16px;
    font-size: 13px;
    color: #2d3748;
    max-width: 88%;
    line-height: 1.75;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.chat-empty {
    text-align: center;
    padding: 60px 20px;
    font-family: 'Geist Mono', monospace;
    font-size: 10px;
    color: #c8d0dc;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    line-height: 2.8;
}

/* ── Form elements ── */
.stTextInput > div > div > input {
    background: #ffffff !important;
    border: 1px solid #e2e6ec !important;
    border-radius: 7px !important;
    color: #1a1f2e !important;
    font-family: 'Geist', sans-serif !important;
    font-size: 13px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}
.stTextInput > div > div > input:focus {
    border-color: #1c3d8c !important;
    box-shadow: 0 0 0 3px rgba(28,61,140,0.08) !important;
}
.stTextInput > label, .stSelectbox > label {
    font-family: 'Geist Mono', monospace !important;
    font-size: 9px !important;
    font-weight: 500 !important;
    color: #9ba3b2 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
}
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 1px solid #e2e6ec !important;
    border-radius: 7px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}
[data-baseweb="select"] span {
    color: #1a1f2e !important;
    font-family: 'Geist', sans-serif !important;
    font-size: 13px !important;
}

/* ── Slider ── */
[data-baseweb="slider"] [role="slider"] { background: #1c3d8c !important; }
[data-baseweb="slider"] div[data-testid="stSliderThumb"] { background: #1c3d8c !important; }

/* ── Misc ── */
hr { border-color: #e8eaee !important; }

.mp-footer {
    text-align: center;
    margin-top: 3rem;
    padding: 18px;
    font-family: 'Geist Mono', monospace;
    font-size: 9px;
    color: #c8d0dc;
    letter-spacing: 0.16em;
    border-top: 1px solid #e8eaee;
    text-transform: uppercase;
}
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


# ── Price fetching ────────────────────────────────────────────────
@st.cache_data(ttl=900)
def fetch_prices(tickers):
    results = []
    for symbol in tickers:
        try:
            info = yf.Ticker(symbol).fast_info
            current = info.last_price
            prev = info.previous_close
            pct = ((current - prev) / prev) * 100
            results.append({
                "symbol": symbol,
                "price": round(current, 2),
                "prev_close": round(prev, 2),
                "pct_change": round(pct, 2),
                "alert": abs(pct) >= ALERT_THRESHOLD,
            })
        except Exception as e:
            results.append({"symbol": symbol, "price": None,
                            "pct_change": None, "alert": False, "error": str(e)})
    return results


# ── Claude AI ────────────────────────────────────────────────────
def ask_claude(question: str, price_data: list) -> str:
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.Anthropic(api_key=api_key)

        price_lines = []
        for row in price_data:
            if not row.get("error"):
                arrow = "▲" if row["pct_change"] >= 0 else "▼"
                price_lines.append(f"  {row['symbol']}: ${row['price']} ({arrow}{abs(row['pct_change'])}%)")
        ctx = "\n".join(price_lines) or "  (unavailable)"

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            system=f"""You are a sharp, concise market analyst for MarketPlus, a professional investment research platform.

Live watchlist as of {datetime.now().strftime('%b %d, %Y %H:%M')}:
{ctx}

Be direct, precise, and professional. Reference live prices when relevant. Max 180 words. Plain text only.""",
            messages=[{"role": "user", "content": question}]
        )
        return response.content[0].text

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
price_data = fetch_prices(WATCHLIST)
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
    <div class="sb-meta">
        Last updated
        <span>{datetime.now().strftime('%b %d, %Y  ·  %H:%M')}</span>
    </div>""", unsafe_allow_html=True)

    if st.button("↻  Refresh Prices"):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="sb-lbl">Watchlist</div>', unsafe_allow_html=True)
    for row in price_data:
        if row.get("error"):
            continue
        pct = row["pct_change"]
        color = "#0a7c4e" if pct >= 0 else "#b91c3a"
        sign = "+" if pct >= 0 else ""
        st.markdown(f"""
        <div class="wl-row">
            <span class="wl-sym">{row['symbol']}</span>
            <span class="wl-pct" style="color:{color};">{sign}{pct}%</span>
        </div>""", unsafe_allow_html=True)

    # Status
    if alert_count:
        sc = "#b45309"; si = "◈"; st_text = f"{alert_count} alert{'s' if alert_count != 1 else ''} triggered"
    else:
        sc = "#0a7c4e"; si = "◉"; st_text = "All positions normal"
    st.markdown(f"""
    <div class="sb-status">
        <div class="sb-status-lbl">Market Status</div>
        <div style="font-family:'Geist Mono',monospace;font-size:12px;color:{sc};font-weight:500;">
            {si} {st_text}
        </div>
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["  Dashboard  ", "  AI Research  ", "  Alerts  "])


# ── TAB 1: DASHBOARD ─────────────────────────────────────────────
with tab1:
    sec_hdr("Live Prices")

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
                pct = row["pct_change"]
                is_up = pct >= 0
                bar = "#0a7c4e" if is_up else "#b91c3a"
                cls = "up" if is_up else "dn"
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

    sec_hdr("Price History — 30 Days")

    selected_ticker = st.selectbox("Ticker", WATCHLIST, label_visibility="collapsed")

    try:
        import plotly.graph_objects as go
        hist = yf.Ticker(selected_ticker).history(period="1mo")
        if not hist.empty:
            close = hist["Close"]
            is_up = close.iloc[-1] >= close.iloc[0]
            lc = "#0a7c4e" if is_up else "#b91c3a"
            fc = "rgba(10,124,78,0.06)" if is_up else "rgba(185,28,58,0.06)"
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, y=close, mode="lines",
                line=dict(color=lc, width=1.8),
                fill="tozeroy", fillcolor=fc,
                hovertemplate="<b>$%{y:.2f}</b><extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#ffffff",
                font=dict(family="Geist Mono, monospace", color="#9ba3b2", size=10),
                xaxis=dict(gridcolor="#f0f1f4", zeroline=False,
                           tickfont=dict(size=10, color="#9ba3b2"),
                           showline=False, linecolor="#e8eaee"),
                yaxis=dict(gridcolor="#f0f1f4", zeroline=False,
                           tickprefix="$", tickfont=dict(size=10, color="#9ba3b2"),
                           showline=False, side="right"),
                margin=dict(l=0, r=60, t=12, b=0),
                height=280, showlegend=False, hovermode="x unified",
                hoverlabel=dict(bgcolor="#1c3d8c", bordercolor="#1c3d8c",
                                font=dict(family="Geist Mono", size=11, color="#ffffff")),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
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
    question = st.text_input("Your question", value=selected_q,
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
            pct = a["pct_change"]
            css = "a-up" if pct > 0 else "a-dn"
            color = "#0a7c4e" if pct > 0 else "#b91c3a"
            sign = "+" if pct > 0 else ""
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
    new_threshold = st.slider(
        "threshold", min_value=0.5, max_value=10.0,
        value=float(ALERT_THRESHOLD), step=0.5, format="%.1f%%",
        label_visibility="collapsed",
    )
    st.markdown(f"""
    <div style="font-family:'Geist Mono',monospace;font-size:10px;
                color:#9ba3b2;margin-top:6px;letter-spacing:0.1em;">
        Alerts trigger on moves exceeding ±{new_threshold:.1f}%
    </div>""", unsafe_allow_html=True)

    sec_hdr("All Positions")
    for row in price_data:
        if row.get("error"):
            continue
        pct = row["pct_change"]
        color = "#0a7c4e" if pct >= 0 else "#b91c3a"
        bg    = "#edf8f2" if pct >= 0 else "#fef1f3"
        bar_w = min(abs(pct) / 5 * 100, 100)
        sign = "+" if pct >= 0 else ""
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
