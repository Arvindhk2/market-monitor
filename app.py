import os
import glob
import yfinance as yf
import streamlit as st
from datetime import datetime
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────
WATCHLIST = ["NVDA", "AMD", "AAPL", "MSFT", "SPY"]
ALERT_THRESHOLD = 2.0
PDF_DIR = str(Path.home() / "Downloads" / "earnings_pdfs")
FAISS_INDEX = str(Path.home() / "Downloads" / "earnings_faiss_index")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #0a0a0f;
    color: #e8e8f0;
}

/* Hide default streamlit header */
header[data-testid="stHeader"] {
    background: transparent;
}

/* Top banner */
.top-banner {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%);
    border-bottom: 1px solid #2a2a4a;
    padding: 18px 24px;
    margin: -1rem -1rem 2rem -1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.banner-title {
    font-family: 'Space Mono', monospace;
    font-size: 22px;
    font-weight: 700;
    color: #00ff9f;
    letter-spacing: -0.5px;
}

.banner-time {
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    color: #555577;
}

/* Ticker cards */
.ticker-card {
    background: #0f0f1a;
    border: 1px solid #1e1e3a;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}

.ticker-card:hover {
    border-color: #00ff9f44;
    transform: translateY(-2px);
}

.ticker-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00ff9f44, transparent);
}

.ticker-symbol {
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    color: #555577;
    letter-spacing: 2px;
    margin-bottom: 6px;
}

.ticker-price {
    font-family: 'Space Mono', monospace;
    font-size: 24px;
    font-weight: 700;
    color: #e8e8f0;
    margin-bottom: 4px;
}

.ticker-change-up {
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    color: #00ff9f;
    font-weight: 700;
}

.ticker-change-down {
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    color: #ff4d6d;
    font-weight: 700;
}

.ticker-alert {
    font-size: 10px;
    color: #ffaa00;
    margin-top: 4px;
    letter-spacing: 1px;
}

/* Section headers */
.section-header {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #555577;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin: 2rem 0 1rem 0;
    border-bottom: 1px solid #1e1e3a;
    padding-bottom: 8px;
}

/* Alert cards */
.alert-up {
    background: #001a0d;
    border: 1px solid #00ff9f33;
    border-left: 3px solid #00ff9f;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    color: #00ff9f;
}

.alert-down {
    background: #1a000a;
    border: 1px solid #ff4d6d33;
    border-left: 3px solid #ff4d6d;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    color: #ff4d6d;
}

/* Chat messages */
.chat-user {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 12px 12px 4px 12px;
    padding: 12px 16px;
    margin: 8px 0 8px 40px;
    font-size: 14px;
    color: #c8c8e0;
}

.chat-bot {
    background: #001a0d;
    border: 1px solid #00ff9f22;
    border-radius: 12px 12px 12px 4px;
    padding: 12px 16px;
    margin: 8px 40px 8px 0;
    font-size: 14px;
    color: #00cc7a;
    font-family: 'DM Sans', sans-serif;
}

.chat-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    margin-bottom: 4px;
}

/* News items */
.news-item {
    border-bottom: 1px solid #1e1e3a;
    padding: 12px 0;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}

.news-ticker-badge {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 1px;
    padding: 3px 8px;
    border-radius: 4px;
    white-space: nowrap;
    min-width: 48px;
    text-align: center;
}

.news-title {
    font-size: 13px;
    color: #c8c8e0;
    line-height: 1.5;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f0f1a;
    border-right: 1px solid #1e1e3a;
}

/* Streamlit metric override */
[data-testid="stMetric"] {
    background: transparent;
}

/* Buttons */
.stButton > button {
    background: #001a0d;
    color: #00ff9f;
    border: 1px solid #00ff9f44;
    border-radius: 8px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    letter-spacing: 1px;
    padding: 8px 20px;
    transition: all 0.2s;
}

.stButton > button:hover {
    background: #00ff9f;
    color: #0a0a0f;
    border-color: #00ff9f;
}

/* Text input */
.stTextInput > div > div > input {
    background: #0f0f1a;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    color: #e8e8f0;
    font-family: 'DM Sans', sans-serif;
}

.stTextInput > div > div > input:focus {
    border-color: #00ff9f44;
    box-shadow: 0 0 0 1px #00ff9f22;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    gap: 8px;
    border-bottom: 1px solid #1e1e3a;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 2px;
    color: #555577;
    background: transparent;
    border: none;
    padding: 8px 16px;
}

.stTabs [aria-selected="true"] {
    color: #00ff9f !important;
    border-bottom: 2px solid #00ff9f !important;
}

/* Divider */
hr {
    border-color: #1e1e3a;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #0f0f1a;
    border: 1px solid #2a2a4a;
    color: #e8e8f0;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


# ── Price fetching ───────────────────────────────────────────────
@st.cache_data(ttl=900)
def fetch_prices(tickers):
    results = []
    for symbol in tickers:
        try:
            # Use download() — most reliable on Streamlit Cloud
            hist = yf.download(
                symbol,
                period="5d",
                progress=False,
                auto_adjust=True,
            )

            if hist.empty:
                raise ValueError("No data returned")

            # Get last two valid closing prices
            closes = hist["Close"].dropna()
            if len(closes) < 2:
                raise ValueError("Not enough data points")

            current = float(closes.iloc[-1])
            prev    = float(closes.iloc[-2])

            if current == 0 or prev == 0:
                raise ValueError("Zero price returned")

            pct = ((current - prev) / prev) * 100
            results.append({
                "symbol":     symbol,
                "price":      round(current, 2),
                "prev_close": round(prev, 2),
                "pct_change": round(pct, 2),
                "alert":      abs(pct) >= ALERT_THRESHOLD,
            })
        except Exception as e:
            results.append({
                "symbol":     symbol,
                "price":      None,
                "pct_change": None,
                "alert":      False,
                "error":      str(e),
            })
    return results


# ── RAG setup ────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Initializing knowledge base...")
def load_rag():
    try:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS

        embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

        if os.path.exists(FAISS_INDEX):
            return FAISS.load_local(FAISS_INDEX, embeddings, allow_dangerous_deserialization=True)

        pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
        if not pdf_files:
            return None

        all_docs = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        for pdf_path in pdf_files:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            for page in pages:
                page.metadata["source_ticker"] = Path(pdf_path).stem.split("_")[0]
            all_docs.extend(splitter.split_documents(pages))

        if not all_docs:
            return None

        vs = FAISS.from_documents(all_docs, embeddings)
        vs.save_local(FAISS_INDEX)
        return vs
    except Exception:
        return None


@st.cache_resource(show_spinner="Loading AI model...")
def load_llm():
    try:
        from transformers import pipeline as hf_pipeline
        from langchain_community.llms import HuggingFacePipeline
        pipe = hf_pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            max_new_tokens=256,
            do_sample=False,
        )
        return HuggingFacePipeline(pipeline=pipe)
    except Exception:
        return None


def ask_rag(question, vector_store, llm):
    from langchain.chains import RetrievalQA
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    qa = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    result = qa({"query": question})
    return result["result"], result["source_documents"]


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style='font-family: Space Mono, monospace; font-size: 18px;
                color: #00ff9f; font-weight: 700; margin-bottom: 4px;'>
        📈 MARKET<br>MONITOR
    </div>
    <div style='font-family: Space Mono, monospace; font-size: 10px;
                color: #333355; letter-spacing: 2px; margin-bottom: 24px;'>
        AI-POWERED RESEARCH
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-family: Space Mono, monospace; font-size: 10px;
                color: #333355; margin-bottom: 16px;'>
        LAST UPDATED<br>
        <span style='color: #555577;'>
            {datetime.now().strftime('%b %d, %Y %H:%M')}
        </span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⟳  REFRESH PRICES"):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.markdown("""
    <div style='font-family: Space Mono, monospace; font-size: 10px;
                color: #333355; letter-spacing: 2px; margin-bottom: 12px;'>
        WATCHLIST
    </div>
    """, unsafe_allow_html=True)

    price_data = fetch_prices(WATCHLIST)
    for row in price_data:
        if row.get("error"):
            continue
        pct = row["pct_change"]
        color = "#00ff9f" if pct >= 0 else "#ff4d6d"
        arrow = "▲" if pct >= 0 else "▼"
        st.markdown(f"""
        <div style='display: flex; justify-content: space-between;
                    padding: 6px 0; border-bottom: 1px solid #1e1e3a;'>
            <span style='font-family: Space Mono, monospace; font-size: 12px;
                         color: #888899;'>{row['symbol']}</span>
            <span style='font-family: Space Mono, monospace; font-size: 12px;
                         color: {color};'>{arrow} {abs(pct)}%</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    alert_count = sum(1 for r in price_data if r.get("alert"))
    st.markdown(f"""
    <div style='font-family: Space Mono, monospace; font-size: 10px;
                color: #333355; letter-spacing: 2px; margin-bottom: 8px;'>
        STATUS
    </div>
    <div style='font-size: 13px; color: #{"ffaa00" if alert_count else "00ff9f"};
                font-family: Space Mono, monospace;'>
        {"⚠ " + str(alert_count) + " ALERT" + ("S" if alert_count > 1 else "") if alert_count else "● ALL CLEAR"}
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# MAIN CONTENT — TABS
# ════════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs(["DASHBOARD", "AI CHAT", "ALERTS"])


# ── TAB 1: DASHBOARD ─────────────────────────────────────────────
with tab1:
    st.markdown("<div class='section-header'>LIVE PRICES</div>", unsafe_allow_html=True)

    cols = st.columns(len(WATCHLIST))
    for col, row in zip(cols, price_data):
        with col:
            if row.get("error"):
                st.markdown(f"""
                <div class='ticker-card'>
                    <div class='ticker-symbol'>{row['symbol']}</div>
                    <div class='ticker-price' style='font-size:14px; color:#ff4d6d;'>ERROR</div>
                </div>""", unsafe_allow_html=True)
            else:
                pct = row["pct_change"]
                change_class = "ticker-change-up" if pct >= 0 else "ticker-change-down"
                arrow = "▲" if pct >= 0 else "▼"
                alert_html = "<div class='ticker-alert'>⚠ ALERT TRIGGERED</div>" if row["alert"] else ""
                st.markdown(f"""
                <div class='ticker-card'>
                    <div class='ticker-symbol'>{row['symbol']}</div>
                    <div class='ticker-price'>${row['price']}</div>
                    <div class='{change_class}'>{arrow} {abs(pct)}%</div>
                    {alert_html}
                </div>""", unsafe_allow_html=True)

    # Price chart
    st.markdown("<div class='section-header'>PRICE CHART</div>", unsafe_allow_html=True)

    selected_ticker = st.selectbox(
        "Select ticker",
        WATCHLIST,
        label_visibility="collapsed"
    )

    try:
        import plotly.graph_objects as go
        hist = yf.Ticker(selected_ticker).history(period="1mo")

        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist["Close"],
                mode="lines",
                line=dict(color="#00ff9f", width=2),
                fill="tozeroy",
                fillcolor="rgba(0, 255, 159, 0.05)",
                name=selected_ticker,
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,15,26,0.8)",
                font=dict(family="Space Mono", color="#555577", size=11),
                xaxis=dict(
                    gridcolor="#1e1e3a",
                    showgrid=True,
                    zeroline=False,
                ),
                yaxis=dict(
                    gridcolor="#1e1e3a",
                    showgrid=True,
                    zeroline=False,
                    tickprefix="$",
                ),
                margin=dict(l=0, r=0, t=20, b=0),
                height=280,
                showlegend=False,
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception as e:
        st.caption(f"Chart unavailable: {e}")


# ── TAB 2: AI CHAT ───────────────────────────────────────────────
with tab2:
    st.markdown("<div class='section-header'>AI RESEARCH ASSISTANT</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size: 13px; color: #555577; margin-bottom: 20px;
                font-family: DM Sans, sans-serif; line-height: 1.6;'>
        Ask anything about your watchlist. Answers are grounded in earnings
        reports when PDFs are loaded — or powered by general market knowledge.
    </div>
    """, unsafe_allow_html=True)

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Example questions
    examples = [
        "",
        "What drove NVDA's revenue growth?",
        "What are AAPL's main business segments?",
        "How did AMD describe AI chip competition?",
        "What risks did MSFT flag in their 10-K?",
        "Compare NVDA and AMD gross margins",
    ]

    selected_q = st.selectbox("Quick questions:", examples, label_visibility="visible")
    question = st.text_input(
        "Your question:",
        value=selected_q,
        placeholder="Ask about earnings, strategy, risks, performance...",
    )

    col_ask, col_clear = st.columns([1, 4])
    with col_ask:
        ask_btn = st.button("ASK →", disabled=not question)
    with col_clear:
        if st.button("CLEAR CHAT"):
            st.session_state.chat_history = []
            st.rerun()

    if ask_btn and question:
        vs = load_rag()
        llm = load_llm()

        if vs and llm:
            with st.spinner("Searching earnings documents..."):
                try:
                    answer, sources = ask_rag(question, vs, llm)
                    source_tickers = list(set(
                        d.metadata.get("source_ticker", "?") for d in sources
                    ))
                    answer_with_src = f"{answer}\n\n*Sources: {', '.join(source_tickers)}*"
                except Exception as e:
                    answer_with_src = f"Error retrieving answer: {e}"
        else:
            # Fallback: general context answer without RAG
            answer_with_src = (
                "No earnings PDFs loaded. Add PDFs to `~/Downloads/earnings_pdfs/` "
                "to enable grounded answers from filings."
            )

        st.session_state.chat_history.append({
            "question": question,
            "answer": answer_with_src,
        })

    # Render chat history
    if st.session_state.chat_history:
        st.markdown("<br>", unsafe_allow_html=True)
        for entry in reversed(st.session_state.chat_history):
            st.markdown(f"""
            <div>
                <div class='chat-label' style='color:#333355; text-align:right;'>YOU</div>
                <div class='chat-user'>{entry['question']}</div>
                <div class='chat-label' style='color:#00ff9f22;'>AI</div>
                <div class='chat-bot'>{entry['answer']}</div>
            </div>
            <br>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align: center; padding: 40px; color: #333355;
                    font-family: Space Mono, monospace; font-size: 12px;'>
            NO CONVERSATION YET<br>
            <span style='font-size: 10px; letter-spacing: 2px;'>
                ASK A QUESTION ABOVE TO BEGIN
            </span>
        </div>
        """, unsafe_allow_html=True)


# ── TAB 3: ALERTS ────────────────────────────────────────────────
with tab3:
    st.markdown("<div class='section-header'>ACTIVE ALERTS</div>", unsafe_allow_html=True)

    alerts = [r for r in price_data if r.get("alert")]

    if not alerts:
        st.markdown("""
        <div style='text-align: center; padding: 40px; color: #333355;
                    font-family: Space Mono, monospace; font-size: 12px;'>
            ● NO ALERTS TRIGGERED<br>
            <span style='font-size: 10px; letter-spacing: 2px;'>
                THRESHOLD: ±2.0%
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        for a in alerts:
            pct = a["pct_change"]
            direction = "UP" if pct > 0 else "DOWN"
            css_class = "alert-up" if pct > 0 else "alert-down"
            arrow = "▲" if pct > 0 else "▼"
            st.markdown(f"""
            <div class='{css_class}'>
                {arrow} {a['symbol']} — {direction} {abs(pct)}%
                &nbsp;&nbsp;
                <span style='opacity: 0.6; font-size: 11px;'>
                    ${a['prev_close']} → ${a['price']}
                </span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='section-header' style='margin-top:2rem;'>THRESHOLD SETTINGS</div>", unsafe_allow_html=True)

    new_threshold = st.slider(
        "Alert on price moves greater than:",
        min_value=0.5,
        max_value=10.0,
        value=ALERT_THRESHOLD,
        step=0.5,
        format="%.1f%%",
    )

    st.markdown(f"""
    <div style='font-family: Space Mono, monospace; font-size: 11px;
                color: #555577; margin-top: 8px;'>
        CURRENT THRESHOLD: ±{new_threshold}%
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header' style='margin-top:2rem;'>ALL POSITIONS</div>", unsafe_allow_html=True)

    for row in price_data:
        if row.get("error"):
            continue
        pct = row["pct_change"]
        bar_color = "#00ff9f" if pct >= 0 else "#ff4d6d"
        bar_width = min(abs(pct) / 5 * 100, 100)
        st.markdown(f"""
        <div style='margin-bottom: 12px;'>
            <div style='display: flex; justify-content: space-between;
                        font-family: Space Mono, monospace; font-size: 12px;
                        margin-bottom: 4px;'>
                <span style='color: #888899;'>{row['symbol']}</span>
                <span style='color: {bar_color};'>
                    {"+" if pct >= 0 else ""}{pct}%
                </span>
            </div>
            <div style='background: #1e1e3a; border-radius: 4px; height: 4px;'>
                <div style='background: {bar_color}; width: {bar_width}%;
                            height: 4px; border-radius: 4px; opacity: 0.7;'>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; margin-top: 3rem; padding: 16px;
            font-family: Space Mono, monospace; font-size: 10px;
            color: #222233; letter-spacing: 2px; border-top: 1px solid #1e1e3a;'>
    MARKET MONITOR AGENT — BUILT WITH STREAMLIT + LANGCHAIN + FAISS
</div>
""", unsafe_allow_html=True)
