import streamlit as st
import anthropic
import yfinance as yf
import json
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="マーケット・レーダー", layout="wide")

st.title("📡 マーケット・レーダー")

# SecretsからAPIキーを読み込む（ブラウザ翻訳で壊れないようシンプルにしています）
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    st.error("API Key not found in secrets.")
    st.stop()

event_input = st.text_input("分析したいニュースイベントを入力")

if st.button("分析する"):
    st.write(f"「{event_input}」を分析しています...")
