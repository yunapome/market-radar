import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar (Robust Connection)")

# --- 安全な接続処理（モデル自動探索） ---
@st.cache_resource
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # 利用可能なモデルをAPIから自動取得
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 'gemini' を含むモデルを探し、なければ最初に見つかったものを使う
        target_model = next((m for m in models if 'gemini' in m), models[0])
        return genai.GenerativeModel(target_model)
    except Exception as e:
        return None

model = get_model()

# --- 状態管理 ---
if "input_key" not in st.session_state: st.session_state.input_key = 0
if "last_result" not in st.session_state: st.session_state.last_result = None

# --- UI構築 ---
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

if st.button("市場分析スタート"):
    if model and event_input:
        with st.spinner("Geminiが分析中..."):
            try:
                # 分析リクエスト
                response = model.generate_content(f"「{event_input}」について、関連銘柄をリストアップし、客観的に分析して")
                st.session_state.last_result = response.text
                st.rerun()
            except Exception as e:
                st.error(f"分析失敗: {e}")
    elif not model:
        st.error("API接続に失敗しました。キー設定を確認してください。")

if st.button("入力欄をクリア"):
    st.session_state.input_key += 1
    st.rerun()

# --- 結果表示 ---
if st.session_state.last_result:
    st.markdown("### 分析結果")
    st.write(st.session_state.last_result)
