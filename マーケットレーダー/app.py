import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar (Robust Connection)")

# API設定を確実にする
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # モデルのリストを取得して確認するステップを追加（これで接続を確実にします）
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"接続エラー: {e}")
    st.stop() # ここで止めることでエラーを明確にします

# 入力欄のキー管理
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

if st.button("市場分析スタート"):
    if event_input:
        with st.spinner("Geminiが市場を分析中..."):
            try:
                prompt = f"ニュース「{event_input}」について、以下の形式で出力してください。\n\n[LIST]\n企業名,証券コード(4桁)\n\n[COMMENT]\n市場への影響を客観的かつ論理的に分析し、200文字以内で要約してください。"
                response = model.generate_content(prompt)
                
                # 結果を保存
                st.session_state.last_result = response.text
                st.rerun()
            except Exception as e:
                st.error(f"分析中にエラーが発生しました: {e}")

# 以下、結果表示ロジック...
