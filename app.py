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

# ── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #080c14;
    color: #cdd5e0;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0c1220;
    border-right: 1px solid #1c2840;
}

[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}

.sb-brand {
    padding: 22px 20px 16px;
    border-bottom: 1px solid #1c2840;
    margin-bottom: 0;
}

.sb-logo-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}

.sb-logo-mark {
    width: 30px;
    height: 30px;
    background: linear-gradient(135deg, #1d4ed8, #3b82f6);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
}

.sb-app-name {
    font-family: 'Inter', sans-serif;
    font-size: 17px;
    font-weight: 600;
    color: #f0f4ff;
    letter-spacing: -0.3px;
}

.sb-tagline {
    font-size: 11px;
    color: #3d5580;
    letter-spacing: 0.02em;
    font-weight: 400;
}

.sb-section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    font-weight: 500;
    color: #2d4060;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 16px 20px 8px;
}

.sb-updated {
    padding: 0 20px 14px;
    font-size: 11px;
    color: #3d5580;
    font-family: 'IBM Plex Mono', monospace;
}

.sb-updated span {
    color: #5a7aaa;
}

.wl-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 20px;
    border-bottom: 1px solid #111c2e;
    transition: background 0.15s;
}

.wl-symbol {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #8aa0c0;
    letter-spacing: 0.04em;
    font-weight: 500;
}

.wl-change {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    font-weight: 500;
}

.sb-status-block {
    padding: 14px 20px;
    margin: 8px 12px;
    border-radius: 8px;
    background: #0e1928;
    border: 1px solid #1c2840;
}

.sb-status-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    color: #2d4060;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 4px;
}

/* ── Buttons ── */
.stButton > button {
    background: #0e1928;
    color: #7096c8;
    border: 1px solid #1c3050;
    border-radius: 7px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.06em;
    padding: 7px 16px;
    transition: all 0.18s;
    width: 100%;
}

.stButton > button:hover {
    background: #162238;
    color: #a0c0e8;
    border-color: #2a4a70;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    gap: 0;
    border-bottom: 1px solid #1c2840;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.08em;
    color: #3d5580;
    background: transparent;
    border: none;
    padding: 10px 20px;
    text-transform: uppercase;
}

.stTabs [aria-selected="true"] {
    color: #60a0f0 !important;
    border-bottom: 2px solid #3b82f6 !important;
    background: transparent !important;
}

/* ── Section headers ── */
.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    color: #2d4060;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    padding-bottom: 10px;
    margin: 1.5rem 0 1rem 0;
    border-bottom: 1px solid #1c2840;
}

/* ── Ticker cards ── */
.ticker-card {
    background: #0c1422;
    border: 1px solid #1a2840;
    border-radius: 10px;
    padding: 16px 14px;
    text-align: center;
    position: relative;
    transition: border-color 0.2s;
}

.ticker-card:hover {
    border-color: #2a4060;
}

.ticker-card-accent {
    position: absolute;
    top: 0; left: 16px; right: 16px;
    height: 1px;
    border-radius: 0 0 2px 2px;
}

.ticker-symbol {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #3d5a80;
    letter-spacing: 0.12em;
    margin-bottom: 8px;
    font-weight: 500;
}

.ticker-price {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px;
    font-weight: 500;
    color: #c8d8f0;
    margin-bottom: 6px;
    letter-spacing: -0.5px;
}

.ticker-change-up {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #34d399;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    background: #0a2018;
    border: 1px solid #0d3020;
    border-radius: 4px;
    padding: 2px 8px;
}

.ticker-change-down {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #f87171;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    background: #200a0a;
    border: 1px solid #300d0d;
    border-radius: 4px;
    padding: 2px 8px;
}

.ticker-alert-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    color: #fbbf24;
    letter-spacing: 0.08em;
    margin-top: 6px;
    background: #1a1200;
    border: 1px solid #2a1e00;
    border-radius: 4px;
    padding: 2px 6px;
    display: inline-block;
}

/* ── Alert cards ── */
.alert-card-up {
    background: #081a10;
    border: 1px solid #0d3020;
    border-left: 3px solid #34d399;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    color: #34d399;
}

.alert-card-down {
    background: #1a0808;
    border: 1px solid #300d0d;
    border-left: 3px solid #f87171;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    color: #f87171;
}

/* ── Chat UI ── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 8px;
}

.chat-user-wrap {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

.chat-bot-wrap {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

.chat-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.1em;
    color: #2d4060;
    margin-bottom: 5px;
    text-transform: uppercase;
}

.chat-user {
    background: #111e35;
    border: 1px solid #1c3050;
    border-radius: 10px 10px 3px 10px;
    padding: 11px 15px;
    font-size: 14px;
    color: #a8c0e0;
    max-width: 85%;
    line-height: 1.55;
}

.chat-bot {
    background: #0a1820;
    border: 1px solid #1a3040;
    border-radius: 10px 10px 10px 3px;
    padding: 11px 15px;
    font-size: 14px;
    color: #90c0d8;
    max-width: 90%;
    line-height: 1.65;
    font-family: 'Inter', sans-serif;
}

.chat-sources {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #2d5070;
    margin-top: 6px;
}

.chat-empty {
    text-align: center;
    padding: 50px 20px;
    color: #2d4060;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.08em;
    line-height: 2;
}

/* ── News items ── */
.news-item {
    border-bottom: 1px solid #111c2e;
    padding: 12px 0;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}

.news-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.06em;
    padding: 3px 8px;
    border-radius: 5px;
    white-space: nowrap;
    min-width: 50px;
    text-align: center;
    flex-shrink: 0;
    margin-top: 1px;
    font-weight: 500;
}

.news-title {
    font-size: 13px;
    color: #8aa0c0;
    line-height: 1.5;
}

.news-time {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #2d4060;
    margin-top: 3px;
}

/* ── Form elements ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #0c1422 !important;
    border: 1px solid #1a2840 !important;
    border-radius: 8px !important;
    color: #c8d8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextInput > div > div > input:focus {
    border-color: #2a4a70 !important;
    box-shadow: 0 0 0 2px #1a3050 !important;
}

.stTextInput > label,
.stSelectbox > label {
    font-size: 11px !important;
    color: #3d5580 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

/* ── Slider ── */
.stSlider > div {
    color: #3d5580;
}

/* ── Selectbox dropdown text ── */
[data-baseweb="select"] span {
    color: #c8d8f0 !important;
    font-size: 13px;
}

/* ── Plotly chart bg ── */
.js-plotly-plot .plotly {
    background: transparent !important;
}

/* ── Divider ── */
hr {
    border-color: #1c2840 !important;
}

/* ── Footer ── */
.mp-footer {
    text-align: center;
    margin-top: 3rem;
    padding: 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    color: #1c2840;
    letter-spacing: 0.12em;
    border-top: 1px solid #111c2e;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)


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
            results.append({
                "symbol": symbol, "price": None,
                "pct_change": None, "alert": False, "error": str(e)
            })
    return results


# ── AI Chat via Claude API ────────────────────────────────────────
def ask_claude(question: str, price_data: list) -> str:
    """Send question to Claude with live market context."""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

        # Build market context from live data
        price_lines = []
        for row in price_data:
            if not row.get("error"):
                arrow = "▲" if row["pct_change"] >= 0 else "▼"
                price_lines.append(
                    f"  {row['symbol']}: ${row['price']} ({arrow}{abs(row['pct_change'])}% today)"
                )
        market_ctx = "\n".join(price_lines) if price_lines else "  (prices unavailable)"

        system_prompt = f"""You are a concise, knowledgeable market research assistant for a professional trading dashboard called MarketPlus.

Current watchlist prices as of {datetime.now().strftime('%b %d, %Y %H:%M')}:
{market_ctx}

Guidelines:
- Be direct and analytical — no fluff or filler
- Reference the live price data above when relevant
- For earnings/fundamental questions, draw on your training knowledge about these companies
- Keep responses under 200 words unless the question clearly warrants more detail
- Use plain text only — no markdown headers or bullet symbols
- If you don't have specific earnings data, say so clearly and give useful general context"""

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": question}]
        )
        return response.content[0].text

    except anthropic.AuthenticationError:
        return "Authentication error: please set your ANTHROPIC_API_KEY environment variable to enable AI responses."
    except Exception as e:
        return f"Unable to reach AI service: {e}"


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════

price_data = fetch_prices(WATCHLIST)
alert_count = sum(1 for r in price_data if r.get("alert"))

with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-logo-row">
            <div class="sb-logo-mark">📈</div>
            <div class="sb-app-name">MarketPlus</div>
        </div>
        <div class="sb-tagline">AI-Powered Market Research</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sb-updated">
        Last updated<br>
        <span>{datetime.now().strftime('%b %d, %Y  %H:%M')}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⟳  Refresh Prices"):
        st.cache_data.clear()
        st.rerun()

    # Watchlist
    st.markdown('<div class="sb-section-label">Watchlist</div>', unsafe_allow_html=True)
    for row in price_data:
        if row.get("error"):
            continue
        pct = row["pct_change"]
        color = "#34d399" if pct >= 0 else "#f87171"
        arrow = "▲" if pct >= 0 else "▼"
        st.markdown(f"""
        <div class="wl-row">
            <span class="wl-symbol">{row['symbol']}</span>
            <span class="wl-change" style="color:{color};">{arrow} {abs(pct)}%</span>
        </div>
        """, unsafe_allow_html=True)

    # Status
    status_color = "#fbbf24" if alert_count else "#34d399"
    status_text = f"⚠ {alert_count} Alert{'s' if alert_count != 1 else ''}" if alert_count else "● All Clear"
    st.markdown(f"""
    <div class="sb-status-block" style="margin-top: 16px;">
        <div class="sb-status-label">Status</div>
        <div style="font-family:'IBM Plex Mono',monospace; font-size:13px;
                    color:{status_color}; font-weight:500;">{status_text}</div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ════════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs(["  Dashboard  ", "  AI Chat  ", "  Alerts  "])


# ── TAB 1: DASHBOARD ─────────────────────────────────────────────
with tab1:
    st.markdown("<div class='section-header'>Live Prices</div>", unsafe_allow_html=True)

    cols = st.columns(len(WATCHLIST))
    for col, row in zip(cols, price_data):
        with col:
            if row.get("error"):
                st.markdown(f"""
                <div class='ticker-card'>
                    <div class='ticker-symbol'>{row['symbol']}</div>
                    <div class='ticker-price' style='font-size:14px;color:#f87171;'>ERROR</div>
                </div>""", unsafe_allow_html=True)
            else:
                pct = row["pct_change"]
                is_up = pct >= 0
                change_class = "ticker-change-up" if is_up else "ticker-change-down"
                arrow = "▲" if is_up else "▼"
                accent_color = "#34d399" if is_up else "#f87171"
                alert_html = "<div class='ticker-alert-badge'>⚠ ALERT</div>" if row["alert"] else ""
                st.markdown(f"""
                <div class='ticker-card'>
                    <div class='ticker-card-accent' style='background:{accent_color}22;'></div>
                    <div class='ticker-symbol'>{row['symbol']}</div>
                    <div class='ticker-price'>${row['price']}</div>
                    <div class='{change_class}'>{arrow} {abs(pct)}%</div>
                    {alert_html}
                </div>""", unsafe_allow_html=True)

    # Price chart
    st.markdown("<div class='section-header'>Price Chart</div>", unsafe_allow_html=True)

    selected_ticker = st.selectbox(
        "Select ticker",
        WATCHLIST,
        label_visibility="collapsed"
    )

    try:
        import plotly.graph_objects as go
        hist = yf.Ticker(selected_ticker).history(period="1mo")

        if not hist.empty:
            close = hist["Close"]
            is_up = close.iloc[-1] >= close.iloc[0]
            line_color = "#34d399" if is_up else "#f87171"
            fill_color = "rgba(52,211,153,0.06)" if is_up else "rgba(248,113,113,0.06)"

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=close,
                mode="lines",
                line=dict(color=line_color, width=1.8),
                fill="tozeroy",
                fillcolor=fill_color,
                name=selected_ticker,
                hovertemplate="$%{y:.2f}<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(12,20,34,0.6)",
                font=dict(family="IBM Plex Mono", color="#3d5580", size=10),
                xaxis=dict(
                    gridcolor="#111c2e",
                    showgrid=True,
                    zeroline=False,
                    tickfont=dict(size=10),
                    showline=False,
                ),
                yaxis=dict(
                    gridcolor="#111c2e",
                    showgrid=True,
                    zeroline=False,
                    tickprefix="$",
                    tickfont=dict(size=10),
                    showline=False,
                    side="right",
                ),
                margin=dict(l=0, r=50, t=16, b=0),
                height=260,
                showlegend=False,
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception as e:
        st.caption(f"Chart unavailable: {e}")


# ── TAB 2: AI CHAT ───────────────────────────────────────────────
with tab2:
    st.markdown("<div class='section-header'>AI Research Assistant</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size: 13px; color: #3d5580; margin-bottom: 20px; line-height: 1.6;'>
        Ask anything about your watchlist — powered by Claude with live market context.
    </div>
    """, unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    examples = [
        "",
        "What drove NVDA's revenue growth?",
        "What are AAPL's main business segments?",
        "How is AMD positioned in the AI chip market?",
        "What risks could affect MSFT this year?",
        "Compare NVDA and AMD on gross margins",
        "Why is SPY up or down today?",
    ]

    selected_q = st.selectbox("Quick questions", examples, label_visibility="visible")
    question = st.text_input(
        "Your question",
        value=selected_q,
        placeholder="Ask about earnings, strategy, risks, performance...",
    )

    col_ask, col_clear = st.columns([1, 4])
    with col_ask:
        ask_btn = st.button("Ask →", disabled=not question)
    with col_clear:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    if ask_btn and question:
        with st.spinner("Thinking..."):
            answer = ask_claude(question, price_data)
        st.session_state.chat_history.append({
            "question": question,
            "answer": answer,
        })

    if st.session_state.chat_history:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for entry in reversed(st.session_state.chat_history):
            st.markdown(f"""
            <div class="chat-user-wrap">
                <div class="chat-meta">You</div>
                <div class="chat-user">{entry['question']}</div>
            </div>
            <div class="chat-bot-wrap">
                <div class="chat-meta">MarketPlus AI</div>
                <div class="chat-bot">{entry['answer']}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="chat-empty">
            No conversation yet<br>
            <span style="font-size:9px; letter-spacing:0.12em;">
                Ask a question above to begin
            </span>
        </div>
        """, unsafe_allow_html=True)


# ── TAB 3: ALERTS ────────────────────────────────────────────────
with tab3:
    st.markdown("<div class='section-header'>Active Alerts</div>", unsafe_allow_html=True)

    alerts = [r for r in price_data if r.get("alert")]

    if not alerts:
        st.markdown("""
        <div style='text-align:center; padding:40px; color:#2d4060;
                    font-family:IBM Plex Mono,monospace; font-size:11px; letter-spacing:0.1em;'>
            ● No alerts triggered<br>
            <span style='font-size:10px;'>Threshold: ±2.0%</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        for a in alerts:
            pct = a["pct_change"]
            direction = "UP" if pct > 0 else "DOWN"
            css_class = "alert-card-up" if pct > 0 else "alert-card-down"
            arrow = "▲" if pct > 0 else "▼"
            st.markdown(f"""
            <div class='{css_class}'>
                {arrow} {a['symbol']} — {direction} {abs(pct)}%
                &nbsp;&nbsp;
                <span style='opacity:0.5; font-size:11px;'>${a['prev_close']} → ${a['price']}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='section-header' style='margin-top:2rem;'>Threshold Settings</div>", unsafe_allow_html=True)

    new_threshold = st.slider(
        "Alert on price moves greater than:",
        min_value=0.5,
        max_value=10.0,
        value=ALERT_THRESHOLD,
        step=0.5,
        format="%.1f%%",
    )
    st.markdown(f"""
    <div style='font-family:IBM Plex Mono,monospace; font-size:11px;
                color:#3d5580; margin-top:8px;'>
        Current threshold: ±{new_threshold:.1f}%
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header' style='margin-top:2rem;'>All Positions</div>", unsafe_allow_html=True)

    for row in price_data:
        if row.get("error"):
            continue
        pct = row["pct_change"]
        bar_color = "#34d399" if pct >= 0 else "#f87171"
        bar_width = min(abs(pct) / 5 * 100, 100)
        sign = "+" if pct >= 0 else ""
        st.markdown(f"""
        <div style='margin-bottom:14px;'>
            <div style='display:flex; justify-content:space-between;
                        font-family:IBM Plex Mono,monospace; font-size:12px; margin-bottom:5px;'>
                <span style='color:#5a7aaa;'>{row['symbol']}</span>
                <span style='color:{bar_color};'>{sign}{pct}%</span>
            </div>
            <div style='background:#111c2e; border-radius:3px; height:3px;'>
                <div style='background:{bar_color}; width:{bar_width}%;
                            height:3px; border-radius:3px; opacity:0.6;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Footer ───────────────────────────────────────────────────────
st.markdown("""
<div class="mp-footer">
    MarketPlus · Built with Streamlit · Powered by Claude AI · Data via yfinance
</div>
""", unsafe_allow_html=True)
