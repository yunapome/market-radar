import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import re

# ページ設定
st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Robust Ver)")

# API設定
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("API設定が読み込めません。")
    st.stop()

# セッションステートの初期化
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "market_comment" not in st.session_state:
    st.session_state.market_comment = None
if "cache_results" not in st.session_state:
    st.session_state.cache_results = {}

def clear_data():
    st.session_state.analysis_result = None
    st.session_state.market_comment = None
    st.session_state.input_text = ""

# 入力フォーム
event_input = st.text_input("分析したいニュースやキーワードを入力", key="input_text")

# 分析ボタン
if st.button("Analyze"):
    if event_input:
        if event_input in st.session_state.cache_results:
            result = st.session_state.cache_results[event_input]
            st.session_state.analysis_result = result['list']
            st.session_state.market_comment = result['comment']
            st.info("キャッシュから結果を表示しました。")
        else:
            with st.spinner("分析中..."):
                try:
                    # フラットな視点を求めるプロンプト
                    prompt = f"""
                    ニュース「{event_input}」について、以下の形式で出力してください。
                    余計な前置きは不要です。

                    [LIST]
                    企業名,証券コード(4桁)
                    (複数あれば改行)

                    [COMMENT]
                    市場への影響を客観的かつ論理的に分析し、200文字以内で要約してください。感情的・扇動的な表現は排除してください
