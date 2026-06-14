import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar (Final Stable Version)")

# --- 安全な接続処理 ---
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # 使用可能なモデルを一覧から探し、フラッシュモデルがなければ最初に見つかったものを使う
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = "gemini-1.5-flash" if "models/gemini-1.5-flash" in models else models[0]
        return genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"API接続エラー: {e}")
        return None

model = get_model()

# --- 状態管理 ---
if "input_key" not in st.session_state: st.session_state.input_key = 0
if "last_result" not in st.session_state: st.session_state.last_result = None

# --- UI構築 ---
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("市場分析スタート"):
        if model and event_input:
            with st.spinner("Geminiが市場を分析中..."):
                try:
                    prompt = f"ニュース「{event_input}」について、[LIST]企業名,コード\n[COMMENT]分析 の形式で出力してください。"
                    response = model.generate_content(prompt)
                    st.session_state.last_result = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"分析失敗: {e}")
        elif not model:
            st.error("モデルが利用できません。APIキーを確認してください。")

with col2:
    if st.button("入力欄をクリア"):
        st.session_state.input_key += 1
        st.rerun()

# --- 結果表示 ---
if st.session_state.last_result:
    st.markdown("### 市場分析結果")
    st.write(st.session_state.last_result)
