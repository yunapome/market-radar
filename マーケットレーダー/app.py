import streamlit as st
import google.generativeai as genai
import pandas as pd
import yfinance as yf
import re
import time
import random
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional
import streamlit.components.v1 as components

# ── 1. CSSによるボタン色カスタマイズ ──
st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #b0e0e6 !important;
    color: black !important;
    border: 1px solid #99caca !important;
}
</style>
""", unsafe_allow_html=True)

# ── 2. ロギングとページ設定 ──
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
st.set_page_config(layout="wide", page_title="Market Radar Pro")

# ── 3. 定数・設定 ──
GEMINI_MAX_RETRIES = 4
GEMINI_BASE_DELAY  = 2.0
GEMINI_MAX_DELAY   = 60.0
GEMINI_JITTER      = 0.5
YF_MAX_RETRIES     = 3
YF_BASE_DELAY      = 1.0
YF_MAX_DELAY       = 15.0
YF_MAX_WORKERS     = 3
STORAGE_KEY        = "market_radar_session_v1"

@dataclass
class StockRow:
    企業名: str
    証券コード: str
    株価: Optional[float] = None
    前日比率: Optional[float] = None
    トレンド: str = "–"
    取得状態: str = "OK"
    def to_display_dict(self):
        return {
            "企業名": self.企業名, "証券コード": self.証券コード,
            "株価 (円)": f"{self.株価:,.1f}" if self.株価 else "取得失敗",
            "前日比 (%)": f"{self.前日比率:+.2f}" if self.前日比率 is not None else "–",
            "トレンド": self.トレンド,
        }

# ── 4. 関数定義 ──
@st.cache_resource(show_spinner=False)
def get_gemini_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        return genai.GenerativeModel(next((m for m in models if "gemini" in m), models[0]))
    except: return None

def _exponential_backoff(attempt, base, max_delay, jitter):
    delay = min(base * (2 ** attempt), max_delay)
    return delay * (1 - jitter + random.random() * jitter * 2)

def call_gemini_with_retry(model, prompt):
    for attempt in range(GEMINI_MAX_RETRIES):
        try: return model.generate_content(prompt).text
        except Exception as e:
            if any(kw in str(e).lower() for kw in ["429", "resource_exhausted", "quota"]):
                wait = _exponential_backoff(attempt, GEMINI_BASE_DELAY, GEMINI_MAX_DELAY, GEMINI_JITTER)
                time.sleep(wait)
            else: raise e

def fetch_stock_prices(stocks):
    def _fetch(code):
        try:
            hist = yf.Ticker(f"{code}.T").history(period="5d")
            curr, prev = float(hist["Close"].iloc[-1]), float(hist["Close"].iloc[-2])
            return {"code": code, "curr": curr, "change_pct": (curr - prev) / prev * 100, "trend": "↑" if curr >= prev else "↓"}
        except: return {"code": code, "error": "失敗"}
    
    with ThreadPoolExecutor(max_workers=YF_MAX_WORKERS) as executor:
        results = {res["code"]: res for res in [f.result() for f in as_completed([executor.submit(_fetch, c) for _, c in stocks])]}
    return results

def parse_gemini_response(text):
    stocks, seen = [], set()
    for line in text.split("\n"):
        if re.search(r"\[COMMENT\]", line): break
        if "," in line:
            parts = line.split(",", 1)
            code = re.sub(r"\D", "", parts[1].strip())[:4]
            if len(code) == 4 and code not in seen:
                stocks.append((parts[0].strip().lstrip("0123456789.- "), code))
                seen.add(code)
    return stocks, re.split(r"\[COMMENT\]", text, maxsplit=1)[-1].strip()

def _local_storage_bridge():
    qp = st.query_params
    if "_restore" in qp and "data_rows" not in st.session_state:
        import base64
        saved = json.loads(base64.b64decode(qp["_restore"]).decode())
        st.session_state.data_rows, st.session_state.comment, st.session_state.last_query = saved["data_rows"], saved["comment"], saved["last_query"]
        del qp["_restore"]
    
    if "data_rows" in st.session_state:
        import base64
        payload = base64.b64encode(json.dumps({"data_rows": st.session_state.data_rows, "comment": st.session_state.get("comment", ""), "last_query": st.session_state.get("last_query", "")}, ensure_ascii=False).encode()).decode()
        components.html(f"<script>localStorage.setItem('{STORAGE_KEY}', '{payload}'); window.addEventListener('DOMContentLoaded', ()=>{{if(!location.search.includes('_restore')) location.replace(location.pathname + '?_restore=' + localStorage.getItem('{STORAGE_KEY}'));}});</script>", height=0)

def clear_session():
    for key in ("data_rows", "comment", "last_query", "input_key"): st.session_state.pop(key, None)
    components.html(f"<script>localStorage.removeItem('{STORAGE_KEY}');</script>", height=0)

# ── 5. メイン処理 ──
def main():
    _local_storage_bridge()
    st.title("📡 Market Radar Pro")
    model = get_gemini_model()
    if not model: st.error("APIエラー"); st.stop()
    
    if "input_key" not in st.session_state: st.session_state.input_key = 0
    event_input = st.text_input("分析キーワードを入力", value=st.session_state.get("last_query", ""), key=f"input_{st.session_state.input_key}")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1: start_btn = st.button("🔍 市場分析スタート", use_container_width=True)
    with col2: refresh_btn = st.button("🔄 株価を更新", use_container_width=True, disabled="data_rows" not in st.session_state)
    with col3: clear_btn = st.button("🗑 クリア", use_container_width=True)

    if clear_btn: clear_session(); st.session_state.input_key += 1; st.rerun()
    if start_btn and event_input.strip():
        stocks, comment = parse_gemini_response(call_gemini_with_retry(model, f"「{event_input}」関連の日本株5社を「企業名,証券コード(4桁)」形式で挙げ、[COMMENT]タグ後に分析を書く"))
        price_data = fetch_stock_prices(stocks)
        st.session_state.data_rows = [StockRow(name, code, **({} if "error" in price_data.get(code, {}) else {"株価": round(price_data[code]["curr"], 1), "前日比率": round(price_data[code]["change_pct"], 2), "トレンド": price_data[code]["trend"]})).to_display_dict() for name, code in stocks]
        st.session_state.comment, st.session_state.last_query = comment, event_input.strip()
        st.rerun()
        
    if "data_rows" in st.session_state and st.session_state.data_rows:
        st.dataframe(pd.DataFrame(st.session_state.data_rows), use_container_width=True, hide_index=True)
        if st.session_state.get("comment"): st.expander("📝 市場分析コメント", expanded=True).write(st.session_state.comment)
        st.caption(f"最終更新: {pd.Timestamp.now(tz='Asia/Tokyo').strftime('%Y-%m-%d %H:%M:%S JST')}")

if __name__ == "__main__": main()
