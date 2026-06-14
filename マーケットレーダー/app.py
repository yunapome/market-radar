import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import re

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (with Stock Data)")

# API設定
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("API設定エラー")
    st.stop()

# 状態管理
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

def clear_input():
    st.session_state.input_text = ""

event_input = st.text_input("分析したいニュースやキーワードを入力", value=st.session_state.input_text, key="input_text")

col1, col2 = st.columns([0.2, 0.8])

with col1:
    if st.button("Analyze"):
        if event_input:
            st.write(f"Analyzing: {event_input}...")
            
            # Geminiに証券コード(4桁)を出させる
            prompt = f"「{event_input}」に関連する日本企業を挙げ、銘柄名と証券コード(4桁)のみを抽出して。形式: 銘柄名,コード"
            response = model.generate_content(prompt)
            
            # テキストから4桁の数字を抽出
            codes = re.findall(r'\d{4}', response.text)
            unique_codes = list(set(codes)) # 重複削除
            
            if unique_codes:
                st.markdown("### 関連企業の現在株価")
                data = []
                for code in unique_codes:
                    ticker = yf.Ticker(f"{code}.T")
                    info = ticker.history(period="1d")
                    if not info.empty:
                        price = info['Close'].iloc[-1]
                        data.append({"証券コード": code, "現在株価": f"{price:.0f}円"})
                
                if data:
                    st.table(pd.DataFrame(data))
                else:
                    st.write("株価データが見つかりませんでした。")
            else:
                st.write("銘柄コードが見つかりませんでした。")
            
            st.markdown("---")
            st.markdown("### 詳細分析")
            st.write(response.text)

with col2:
    if st.button("クリア", on_click=clear_input):
        st.rerun()
