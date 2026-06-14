import streamlit as st
import google.generativeai as genai
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# 1. API設定をシンプルにする
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# 2. 入力コンソール
if "event_input" not in st.session_state:
    st.session_state.event_input = ""

col1, col2 = st.columns([0.9, 0.1])
with col1:
    event_input = st.text_input("分析したいニュースや銘柄を入力してください", value=st.session_state.event_input)
with col2:
    if st.button("×"):
        st.session_state.event_input = ""
        st.rerun()

# 3. 分析ボタン（グラフ機能は一旦コメントアウトして、分析が動くか確認します）
if st.button("Analyze"):
    if not event_input:
        st.warning("内容を入力してください。")
    else:
        st.write(f"Analyzing: {event_input}...")
        try:
            response = model.generate_content(event_input)
            st.markdown("### Analysis Result")
            st.write(response.text)
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
