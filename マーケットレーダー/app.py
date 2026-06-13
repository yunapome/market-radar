import streamlit as st
import anthropic
import yfinance as yf
import json
import plotly.graph_objects as go
import pandas as pd

# ページ設定
st.set_page_config(page_title="マーケット・レーダー", layout="wide")
st.title("📡 マーケット・レーダー")

# Secretsから安全にAPIキーを取得
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("API Key が設定されていません。Settings > Secrets を確認してください。")
    st.stop()

# ユーザー入力
event_input = st.text_input("分析したいニュースイベントを入力")

if st.button("分析する"):
    if not event_input:
        st.warning("イベントを入力してください。")
    else:
        st.write(f"📡 「{event_input}」について市場反応を分析中...")
        
        # Claude API呼び出しの準備
        client = anthropic.Anthropic(api_key=api_key)
        
        try:
            # 分析のリクエスト
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                messages=[{"role": "user", "content": f"{event_input} に関連する上場企業を3つ挙げ、それぞれの市場への影響を簡潔に分析してください。"}]
            )
            # 結果を表示
            st.markdown("### 分析結果")
            st.write(response.content[0].text)
        except Exception as e:
            st.error(f"分析中にエラーが発生しました: {e}")
