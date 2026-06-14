import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import re

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Robust Ver)")

# API設定（変更なし）
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # モデル指定を明示すると安定します
except Exception as e:
    st.error("API設定エラー")
    st.stop()

# --- 変更点：セッションステートに「結果」を保存する場所を作る ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

def clear_data():
    st.session_state.analysis_result = None
    st.session_state.input_text = ""

event_input = st.text_input("分析したいニュースやキーワードを入力", key="input_text")

if st.button("Analyze"):
    if event_input:
        with st.spinner("Analyzing..."):
            try:
                prompt = f"「{event_input}」に関連する日本企業を挙げ、必ず「企業名,証券コード(4桁)」の形式でリストアップして。余計な文章は不要。"
                response = model.generate_content(prompt)
                st.session_state.analysis_result = response.text # 結果を保存
            except Exception as e:
                st.error("API制限かエラーです。少し時間を置いてください。")

# --- 結果の表示（ボタンの中ではなく、外側に書く） ---
if st.session_state.analysis_result:
    result_text = st.session_state.analysis_result
    matches = re.findall(r'([^,\n]+),(\d{4})', result_text)
    
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            ticker = yf.Ticker(f"{code}.T")
            info = ticker.history(period="1d")
            if not info.empty:
                price = info['Close'].iloc[-1]
                data.append({"企業名": name.strip(), "証券コード": code, "現在株価": f"{price:.0f}円"})
        
        if data:
            st.table(pd.DataFrame(data))
    
    st.markdown("---")
    st.markdown("### 詳細分析")
    st.write(result_text)

if st.button("クリア"):
    clear_data()
    st.rerun()
