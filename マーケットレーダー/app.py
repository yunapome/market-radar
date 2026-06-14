import streamlit as st
import google.generativeai as genai
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# API設定
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 1. 入力コンソールとクリア機能
if "event_input" not in st.session_state:
    st.session_state.event_input = ""

col1, col2 = st.columns([0.9, 0.1])
with col1:
    event_input = st.text_input("分析したいニュースや銘柄を入力してください", value=st.session_state.event_input)
with col2:
    if st.button("×"):
        st.session_state.event_input = ""
        st.rerun()

# 分析とグラフ表示のボタン
if st.button("Analyze"):
    if not event_input:
        st.warning("内容を入力してください。")
    else:
        # 左右に画面を分割
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.write(f"Analyzing: {event_input}...")
            response = model.generate_content(event_input)
            st.markdown("### Analysis Result")
            st.write(response.text)
            
        with right_col:
            # 2. 株価グラフ機能 (銘柄コードが含まれている場合)
            if "7011" in event_input or "7203" in event_input: # 例として特定のコードを判定
                st.markdown("### Stock Price Graph")
                ticker = yf.Ticker("7203.T") # 例：トヨタのデータ
                df = ticker.history(period="1mo")
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                st.plotly_chart(fig, use_container_width=True)
