import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# 1. APIキーの設定を確実に行う
api_key = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)

# 2. モデル名を「最新の安定版」に指定して直接呼び出す
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. 入力欄の管理（session_stateをシンプルに）
if "text_input" not in st.session_state:
    st.session_state.text_input = ""

# 入力フィールド
user_input = st.text_input("分析したいニュースや銘柄を入力してください", key="input_text")

# ボタン配置
col1, col2 = st.columns(2)
with col1:
    if st.button("クリア"):
        st.session_state.input_text = ""
        st.rerun()

with col2:
    if st.button("Analyze"):
        if not user_input:
            st.warning("内容を入力してください。")
        else:
            with st.spinner("分析中..."):
                try:
                    response = model.generate_content(user_input)
                    st.markdown("### Analysis Result")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"接続エラー: {e}")
