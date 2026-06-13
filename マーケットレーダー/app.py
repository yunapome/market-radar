import streamlit as st
import anthropic
import yfinance as yf
import json
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="マーケット・レーダー",
    page_icon="📡",
    layout="wide"
)

st.title("📡 マーケット・レーダー")
st.caption("ニュースイベント → 関連銘柄 → 当日の市場反応を確認")

# SecretsからAPIキーを読み込む
api_key = st.secrets["ANTHROPIC_API_KEY"]

# サイドバー設定
st.sidebar.header("⚙️ Settings")

# イベント入力
event_input = st.text_input("分析したいニュースイベントを入力", placeholder="例：スペースX ロケット打ち上げ、決算発表、半導体規制...")

if st.button("分析する"):
    if event_input:
        st.write(f"「{event_input}」を分析しています...")
    else:
        st.warning("イベントを入力してください。")
