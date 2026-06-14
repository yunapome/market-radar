import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar (Official API Version)")

# --- 安全な接続処理 ---
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # gemini-1.5-flash があれば優先、なければ最初に見つかったものを使用
        model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in models else models[0]
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
                    # パースしやすくするため、出力形式を厳密に指定
                    prompt = (
                        f"ニュース「{event_input}」について、以下の形式で出力してください。\n\n"
                        "[LIST]\n企業名,証券コード(4桁)\n(複数あれば改行)\n\n"
                        "[COMMENT]\n市場への影響を客観的に分析し、200文字以内で要約してください。"
                    )
                    response = model.generate_content(prompt)
                    st.session_state.last_result = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"分析失敗: {e}")

with col2:
    if st.button("入力欄をクリア"):
        st.session_state.input_key += 1
        st.rerun()

# --- 結果表示とパース処理 ---
if st
