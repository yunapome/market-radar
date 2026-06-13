import streamlit as st
import os

st.title("マーケット・レーダー")
st.write("ニュースイベント → 関連銘柄 → 当日の市場反応を確認")

# SecretsからAPIキーを取得
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("APIキーが設定されていません。Settings > Secrets を確認してください。")
    st.stop()

# 以下、なつさんのメイン機能のコードが続きます
# （もしClaudeが作った元のコードが手元になければ、続けて出しますので教えてください！）
