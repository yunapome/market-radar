import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar")

# --- 接続設定 ---
@st.cache_resource
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # Gemini 1.5 Flash を使用
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception:
        return None

model = get_model()

# --- UIと状態管理 ---
if "input_key" not in st.session_state: st.session_state.input_key = 0
if "last_result" not in st.session_state: st.session_state.last_result = None

event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

if st.button("市場分析スタート"):
    if model and event_input:
        with st.spinner("Geminiが分析中..."):
            # 重要なポイント：Geminiに「リストで返せ」と強く指示します
            prompt = f"ニュース「{event_input}」について、関連銘柄をリストアップしてください。必ず以下の形式で返してください。\n\n企業名,証券コード\n(例: トヨタ自動車,7203)"
            st.session_state.last_result = model.generate_content(prompt).text
            st.rerun()

if st.button("入力欄をクリア"):
    st.session_state.input_key += 1
    st.rerun()

# --- 結果表示とパース（解析）処理 ---
if st.session_state.last_result:
    st.markdown("### 市場分析結果")
    
    # ここが「リスト」を抽出する魔法の命令です
    lines = st.session_state.last_result.strip().split('\n')
    data = []
    for line in lines:
        if ',' in line:
            name, code = line.split(',', 1)
            data.append({"企業名": name.strip(), "証券コード": code.strip()})
    
    # データがあれば表にする
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.write(st.session_state.last_result)
