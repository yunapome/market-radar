import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import re
import time

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Efficient Ver)")

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
            
            # --- 効率化のキモ：プロンプトを統合 ---
            # 「[DATA]」と「[ANALYSIS]」というラベルを付けてAIに区別させる
            prompt = f"""
            「{event_input}」について分析してください。以下の形式を厳守して回答してください。
            
            [DATA]
            企業名,証券コード(4桁)
            (この形式でリストアップして。データ以外の解説は不要)
            
            [ANALYSIS]
            市場や経済への影響をプロの投資家視点で解説してください。
            """
            
            try:
                response = model.generate_content(prompt)
                full_text = response.text
                
                # [DATA]と[ANALYSIS]で分割
                data_part = ""
                analysis_part = ""
                if "[DATA]" in full_text and "[ANALYSIS]" in full_text:
                    parts = re.split(r'\[DATA\]|\[ANALYSIS\]', full_text)
                    data_part = parts[1]
                    analysis_part = parts[2]
                
                # --- 表の表示 ---
                st.markdown("### 関連企業の現在株価")
                matches = re.findall(r'([^,\n]+),(\d{4})', data_part)
                
                if matches:
                    data = []
                    for name, code in matches:
                        # yfinance通信の負荷も考慮しつつ取得
                        ticker = yf.Ticker(f"{code}.T")
                        info = ticker.history(period="1d")
                        if not info.empty:
                            price = info['Close'].iloc[-1]
                            data.append({"企業名": name.strip(), "証券コード": code, "現在株価": f"{price:.0f}円"})
                    st.table(pd.DataFrame(data))
                
                # --- 分析の表示 ---
                st.markdown("---")
                st.markdown("### 市場ニュース分析")
                st.write(analysis_part.strip())
                
            except Exception as e:
                st.error("分析に失敗しました。少し時間を置いて再試行してください。")

with col2:
    if st.button("クリア", on_click=clear_input):
        st.rerun()
