
import os
import glob
import yfinance as yf
import streamlit as st
from datetime import datetime
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline as hf_pipeline

WATCHLIST = ["NVDA", "AMD", "AAPL", "MSFT", "SPY"]
ALERT_THRESHOLD = 2.0
PDF_DIR = str(Path.home() / "Downloads" / "earnings_pdfs")
FAISS_INDEX = str(Path.home() / "Downloads" / "earnings_faiss_index")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

st.set_page_config(page_title="Market Monitor", page_icon="📈", layout="wide")

@st.cache_data(ttl=900)
def fetch_prices(tickers):
    results = []
    for symbol in tickers:
        try:
            info = yf.Ticker(symbol).fast_info
            current = info.last_price
            prev = info.previous_close
            pct = ((current - prev) / prev) * 100
            results.append({"symbol": symbol, "price": round(current, 2), "prev_close": round(prev, 2), "pct_change": round(pct, 2), "alert": abs(pct) >= ALERT_THRESHOLD})
        except Exception as e:
            results.append({"symbol": symbol, "price": None, "pct_change": None, "alert": False, "error": str(e)})
    return results

@st.cache_resource(show_spinner="Loading FAISS index...")
def load_vector_store():
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

@st.cache_resource(show_spinner="Loading LLM...")
def load_llm():
    pipe = hf_pipeline("text2text-generation", model="google/flan-t5-base", max_new_tokens=256, do_sample=False)
    return HuggingFacePipeline(pipeline=pipe)

def ask_earnings(question, vector_store, llm):
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)
    result = qa({"query": question})
    return result["result"], result["source_documents"]

st.title("📈 Market Monitor")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
st.divider()

st.subheader("Live Prices")
price_data = fetch_prices(WATCHLIST)
for col, row in zip(st.columns(len(WATCHLIST)), price_data):
    with col:
        if row.get("error"):
            st.error(f"{row['symbol']} Error")
        else:
            pct = row["pct_change"]
            st.metric(row["symbol"], f"${row['price']}", f"{'+' if pct >= 0 else ''}{pct}%", delta_color="normal" if pct >= 0 else "inverse")
            if row["alert"]:
                st.warning("⚠ Alert")
st.divider()

alerts = [r for r in price_data if r.get("alert")]
if alerts:
    st.subheader("🚨 Alerts")
    for a in alerts:
        d = "UP" if a["pct_change"] > 0 else "DOWN"
        st.markdown(f"{'🟢' if d == 'UP' else '🔴'} **{a['symbol']}** {d} {abs(a['pct_change'])}% — \${a['prev_close']} → \${a['price']}")
    st.divider()

st.subheader("📄 Ask the Earnings Reports")
vs = load_vector_store()
if vs is None:
    st.warning(f"No PDFs in {PDF_DIR}. Add earnings PDFs to enable Q&A.")
else:
    llm = load_llm()
    q = st.text_input("Ask anything:", placeholder="What did NVDA say about data center revenue?")
    if st.button("Ask", disabled=not q):
        with st.spinner("Searching..."):
            answer, sources = ask_earnings(q, vs, llm)
        st.success(answer)
        with st.expander("Source passages"):
            for i, doc in enumerate(sources, 1):
                st.markdown(f"**{i}. {doc.metadata.get('source_ticker','?')} p.{doc.metadata.get('page','?')}**")
                st.caption(doc.page_content[:400] + "...")
