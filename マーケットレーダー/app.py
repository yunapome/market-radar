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
    models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0].name)
except Exception as e:
    st.error("API設定エラー")
    st.stop()

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
            
            # プロンプトをより明確に：「名前,コード」の形式を徹底させる
            prompt = f"「{event_input}」に関連する日本企業を挙げ、必ず「企業名,証券コード(4桁)」の形式でリストアップして。余計な文章は不要。"
            response = model.generate_content(prompt)
            
            # 正規表現で「企業名,コード」のペアを抽出
            # 日本語（企業名）とカンマと4桁数字を探す
            matches = re.findall(r'([^,\n]+),(\d{4})', response.text)
            
            if matches:
                st.markdown("### 関連企業の現在株価")
                data = []
                for name, code in matches:
                    ticker = yf.Ticker(f"{code}.T")
                    info = ticker.history(period="1d")
                    if not info.empty:
                        price = info['Close'].iloc[-1]
                        data.append({"企業名": name, "証券コード": code, "現在株価": f"{price:.0f}円"})
                
                if data:
                    st.table(pd.DataFrame(data))
                else:
                    st.write("株価データが見つかりませんでした。")
            else:
                st.write("リスト形式が見つかりませんでした。")
            
            st.markdown("---")
            st.markdown("### 詳細分析")
            st.write(response.text)

with col2:
    if st.button("クリア", on_click=clear_input):
        st.rerun()
