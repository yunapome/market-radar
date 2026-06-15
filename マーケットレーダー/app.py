import streamlit as st
import google.generativeai as genai
import pandas as pd
import yfinance as yf
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar Pro")

# --- 接続設定 ---
@st.cache_resource
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if 'gemini' in m), models[0])
        return genai.GenerativeModel(model_name)
    except Exception:
        return None

model = get_model()

# --- 状態管理 ---
if "input_key" not in st.session_state: st.session_state.input_key = 0

# --- UI構築 ---
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

# ボタンを横並びに配置
col1, col2 = st.columns(2)
with col1:
    start_btn = st.button("市場分析スタート")
with col2:
    clear_btn = st.button("入力欄をクリア")

if clear_btn:
    st.session_state.input_key += 1
    # データを消去
    if "data" in st.session_state: del st.session_state.data
    st.rerun()

if start_btn:
    if model and event_input:
        with st.spinner("Geminiが分析中..."):
            prompt = (f"「{event_input}」に関連する日本株を5社挙げてください。\n"
                      "形式：企業名,証券コード(4桁)\n"
                      "要約を最後に[COMMENT]タグで200文字以内で書いて。")
            
            res = model.generate_content(prompt).text
            
            # リスト抽出と株価取得
            data = []
            for line in res.split('\n'):
                if ',' in line and not line.startswith('['):
                    parts = line.split(',')
                    name, code = parts[0].strip(), parts[1].strip()
                    # 株価取得処理
                    ticker = yf.Ticker(f"{code}.T")
                    hist = ticker.history(period="2d")
                    if len(hist) >= 2:
                        curr = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2]
                        change_pct = ((curr - prev) / prev) * 100
                        trend = "↑" if curr >= prev else "↓"
                        data.append({"企業名": name, "証券コード": code, "株価": round(curr, 1), "前日比%": round(change_pct, 2), "トレンド": trend})
            
            st.session_state.data = pd.DataFrame(data)
            st.session_state.comment = re.split(r'\[COMMENT\]', res)[-1]
            st.rerun()

# --- 表示 ---
if "data" in st.session_state and not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True, hide_index=True)
    st.write("### 市場分析コメント")
    st.write(st.session_state.comment)
