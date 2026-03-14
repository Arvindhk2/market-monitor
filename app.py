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
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

.stApp {
    background: #06080f;
    color: #b8c4d4;
}

header[data-testid="stHeader"] { background: transparent; height: 0; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #080b14;
    border-right: 1px solid rgba(255,255,255,0.04);
    box-shadow: 4px 0 24px rgba(0,0,0,0.4);
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

.sb-brand {
    padding: 28px 24px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.sb-wordmark {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}
.sb-dot {
    width: 8px; height: 8px;
    background: #4f8ef7;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}
.sb-tagline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #1e2d45;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-left: 18px;
}
.sb-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #1e2d45;
    padding: 16px 24px 14px;
}
.sb-time span { color: #2a3a54; display: block; margin-top: 2px; }

.sb-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #161e2e;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    padding: 16px 24px 8px;
}

.wl-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 24px;
    border-bottom: 1px solid rgba(255,255,255,0.02);
}
.wl-sym {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 500;
    color: #2a3a54;
    letter-spacing: 0.08em;
}
.wl-pct { font-family: 'JetBrains Mono', monospace; font-size: 12px; }

.sb-status {
    margin: 16px 14px 0;
    padding: 12px 16px;
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.03);
    background: rgba(255,255,255,0.015);
}
.sb-status-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #161e2e;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 6px;
}

/* ── Buttons ── */
.stButton > button {
    background: transparent;
    color: #2a3a54;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 5px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 8px 16px;
    transition: all 0.15s;
    width: 100%;
}
.stButton > button:hover {
    background: rgba(79,142,247,0.06);
    color: #4f6e98;
    border-color: rgba(79,142,247,0.12);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    gap: 0;
    padding: 0 8px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.06em;
    color: #1e2d45;
    background: transparent;
    border: none;
    padding: 14px 24px;
    text-transform: uppercase;
}
.stTabs [aria-selected="true"] {
    color: #d8e8ff !important;
    border-bottom: 1px solid #4f8ef7 !important;
    background: transparent !important;
}

/* ── Section headers ── */
.sec-hdr {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 2rem 0 1.2rem;
}
.sec-line { flex: 1; height: 1px; background: rgba(255,255,255,0.03); }
.sec-txt {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #161e2e;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    white-space: nowrap;
}

/* ── Ticker cards ── */
.t-card {
    background: #080c16;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 20px 14px 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: background 0.2s, border-color 0.2s;
}
.t-card:hover { background: #0a0f1c; border-color: rgba(255,255,255,0.07); }
.t-bar { position: absolute; top: 0; left: 0; right: 0; height: 2px; }
.t-sym {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #1e2d45;
    letter-spacing: 0.22em;
    margin-bottom: 10px;
}
.t-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    font-weight: 300;
    color: #c0d0e8;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}
.t-chg {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    display: inline-block;
    padding: 3px 10px;
    border-radius: 3px;
}
.up   { color: #3dcf8e; background: rgba(61,207,142,0.07); }
.dn   { color: #e05c6a; background: rgba(224,92,106,0.07); }
.t-alert {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #b87820;
    letter-spacing: 0.1em;
    margin-top: 8px;
}

/* ── Alert cards ── */
.a-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    border-radius: 6px;
    margin-bottom: 8px;
    border-left: 2px solid;
}
.a-up   { background: rgba(61,207,142,0.04);  border-color: #3dcf8e; }
.a-dn   { background: rgba(224,92,106,0.04); border-color: #e05c6a; }

/* ── Chat ── */
.chat-wrap { display: flex; flex-direction: column; gap: 20px; margin-top: 8px; }
.chat-u { display: flex; justify-content: flex-end; }
.chat-b { display: flex; justify-content: flex-start; }
.chat-sender {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #161e2e;
    margin-bottom: 6px;
}
.chat-sender-r { text-align: right; }
.bubble-u {
    background: #0d1525;
    border: 1px solid rgba(79,142,247,0.1);
    border-radius: 10px 10px 2px 10px;
    padding: 13px 16px;
    font-size: 13px;
    color: #6888a8;
    max-width: 82%;
    line-height: 1.65;
}
.bubble-b {
    background: #070b14;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 10px 10px 10px 2px;
    padding: 13px 16px;
    font-size: 13px;
    color: #6888a8;
    max-width: 88%;
    line-height: 1.75;
}
.chat-empty {
    text-align: center;
    padding: 60px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #111824;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    line-height: 3;
}

/* ── Form elements ── */
.stTextInput > div > div > input {
    background: #080c16 !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 6px !important;
    color: #8aa0c0 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 13px !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(79,142,247,0.18) !important;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.04) !important;
}
.stTextInput > label, .stSelectbox > label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 9px !important;
    color: #161e2e !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
}
.stSelectbox > div > div {
    background: #080c16 !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 6px !important;
}
[data-baseweb="select"] span {
    color: #8aa0c0 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 13px !important;
}

/* ── Misc ── */
hr { border-color: rgba(255,255,255,0.03) !important; }

.mp-footer {
    text-align: center;
    margin-top: 4rem;
    padding: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #0e1624;
    letter-spacing: 0.18em;
    border-top: 1px solid rgba(255,255,255,0.02);
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
            system=f"""You are a sharp, concise market analyst for MarketPlus.

Live prices as of {datetime.now().strftime('%b %d, %Y %H:%M')}:
{ctx}

Be direct and analytical. Reference prices when relevant. Max 180 words. Plain text only.""",
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
        <div class="sb-wordmark"><span class="sb-dot"></span>MarketPlus</div>
        <div class="sb-tagline">AI Research Terminal</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sb-time">Last updated<span>{datetime.now().strftime('%b %d, %Y  ·  %H:%M')}</span></div>
    """, unsafe_allow_html=True)

    if st.button("↻  Refresh"):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="sb-lbl">Watchlist</div>', unsafe_allow_html=True)
    for row in price_data:
        if row.get("error"):
            continue
        pct = row["pct_change"]
        color = "#3dcf8e" if pct >= 0 else "#e05c6a"
        sign = "+" if pct >= 0 else ""
        st.markdown(f"""
        <div class="wl-item">
            <span class="wl-sym">{row['symbol']}</span>
            <span class="wl-pct" style="color:{color};">{sign}{pct}%</span>
        </div>""", unsafe_allow_html=True)

    status_color = "#b87820" if alert_count else "#3dcf8e"
    status_icon = "◈" if alert_count else "◉"
    status_text = f"{alert_count} alert{'s' if alert_count != 1 else ''} triggered" if alert_count else "All positions normal"
    st.markdown(f"""
    <div class="sb-status">
        <div class="sb-status-lbl">Market Status</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:12px;color:{status_color};letter-spacing:0.02em;">
            {status_icon} {status_text}
        </div>
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["Dashboard", "AI Research", "Alerts"])


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
                    <div class="t-price" style="font-size:14px;color:#e05c6a;">ERR</div>
                </div>""", unsafe_allow_html=True)
            else:
                pct = row["pct_change"]
                is_up = pct >= 0
                bar = "#3dcf8e" if is_up else "#e05c6a"
                cls = "up" if is_up else "dn"
                sign = "+" if is_up else ""
                alert_html = '<div class="t-alert">◈ ALERT</div>' if row["alert"] else ""
                st.markdown(f"""
                <div class="t-card">
                    <div class="t-bar" style="background:{bar};opacity:0.5;"></div>
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
            lc = "#3dcf8e" if is_up else "#e05c6a"
            fc = "rgba(61,207,142,0.05)" if is_up else "rgba(224,92,106,0.05)"
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, y=close, mode="lines",
                line=dict(color=lc, width=1.5),
                fill="tozeroy", fillcolor=fc,
                hovertemplate="<b>$%{y:.2f}</b><extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(8,12,22,0.9)",
                font=dict(family="JetBrains Mono", color="#1e2d45", size=9),
                xaxis=dict(gridcolor="rgba(255,255,255,0.02)", zeroline=False,
                           tickfont=dict(size=9, color="#1e2d45"), showline=False),
                yaxis=dict(gridcolor="rgba(255,255,255,0.02)", zeroline=False,
                           tickprefix="$", tickfont=dict(size=9, color="#1e2d45"),
                           showline=False, side="right"),
                margin=dict(l=0, r=56, t=12, b=0),
                height=280, showlegend=False, hovermode="x unified",
                hoverlabel=dict(bgcolor="#0d1525", bordercolor="rgba(79,142,247,0.2)",
                                font=dict(family="JetBrains Mono", size=11, color="#8aa8d0")),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception as e:
        st.caption(f"Chart unavailable: {e}")


# ── TAB 2: AI RESEARCH ───────────────────────────────────────────
with tab2:
    sec_hdr("AI Research Assistant")

    st.markdown("""
    <div style="font-size:13px;color:#1e2d45;margin-bottom:24px;line-height:1.7;max-width:600px;font-family:'Syne',sans-serif;">
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
        with st.spinner(""):
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
                <div class="chat-b" style="margin-top:12px;">
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
            <span style="font-size:9px;color:#0e1624;">Select a prompt or type a question</span>
        </div>""", unsafe_allow_html=True)


# ── TAB 3: ALERTS ────────────────────────────────────────────────
with tab3:
    sec_hdr("Active Alerts")

    alerts = [r for r in price_data if r.get("alert")]
    if not alerts:
        st.markdown(f"""
        <div style="text-align:center;padding:48px 20px;font-family:'JetBrains Mono',monospace;
                    font-size:9px;color:#111824;letter-spacing:0.18em;text-transform:uppercase;line-height:3;">
            ◉ No alerts triggered<br>
            <span style="font-size:9px;color:#0a1018;">Threshold · ±{ALERT_THRESHOLD}%</span>
        </div>""", unsafe_allow_html=True)
    else:
        for a in alerts:
            pct = a["pct_change"]
            css = "a-up" if pct > 0 else "a-dn"
            color = "#3dcf8e" if pct > 0 else "#e05c6a"
            sign = "+" if pct > 0 else ""
            direction = "Bullish signal" if pct > 0 else "Bearish signal"
            st.markdown(f"""
            <div class="a-card {css}">
                <div>
                    <span style="font-family:'JetBrains Mono',monospace;font-size:14px;
                                 color:{color};font-weight:500;">{a['symbol']}</span>
                    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;
                                 color:{color};opacity:0.4;margin-left:12px;">{direction}</span>
                </div>
                <div style="text-align:right;">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:15px;color:{color};">{sign}{pct}%</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{color};opacity:0.4;">${a['prev_close']} → ${a['price']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    sec_hdr("Threshold")
    new_threshold = st.slider(
        "threshold", min_value=0.5, max_value=10.0,
        value=float(ALERT_THRESHOLD), step=0.5, format="%.1f%%",
        label_visibility="collapsed",
    )
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                color:#161e2e;margin-top:6px;letter-spacing:0.12em;">
        Alert threshold · ±{new_threshold:.1f}%
    </div>""", unsafe_allow_html=True)

    sec_hdr("All Positions")
    for row in price_data:
        if row.get("error"):
            continue
        pct = row["pct_change"]
        color = "#3dcf8e" if pct >= 0 else "#e05c6a"
        bar_w = min(abs(pct) / 5 * 100, 100)
        sign = "+" if pct >= 0 else ""
        st.markdown(f"""
        <div style="margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;
                        font-family:'JetBrains Mono',monospace;font-size:11px;margin-bottom:5px;">
                <span style="color:#1e2d45;">{row['symbol']}</span>
                <span style="color:{color};">{sign}{pct}%</span>
            </div>
            <div style="background:rgba(255,255,255,0.03);border-radius:2px;height:2px;">
                <div style="background:{color};width:{bar_w}%;height:2px;border-radius:2px;opacity:0.5;"></div>
            </div>
        </div>""", unsafe_allow_html=True)


# ── Footer ───────────────────────────────────────────────────────
st.markdown("""
<div class="mp-footer">
    MarketPlus &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; Claude AI &nbsp;·&nbsp; yfinance
</div>""", unsafe_allow_html=True)
