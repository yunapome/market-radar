import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# APIの設定（環境変数が正しく読み込まれているかを確認）
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"APIキーの設定エラー: {e}")
    st.stop()

# 入力欄の管理（最もシンプルな形）
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

user_input = st.text_input("分析したいニュースや銘柄を入力してください", key="input_field")

# クリアと分析のボタン（ボタンのクリックイベントを個別に管理）
col1, col2 = st.columns(2)
with col1:
    if st.button("クリア"):
        st.session_state.input_field = ""
        st.rerun()

with col2:
    if st.button("Analyze"):
        if not user_input:
            st.warning("内容を入力してください。")
        else:
            try:
                response = model.generate_content(user_input)
                st.markdown("### Analysis Result")
                st.write(response.text)
            except Exception as e:
                st.error("分析エラー：モデルへの接続に失敗しました。少し時間を置いて再試行してください。")
