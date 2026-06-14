import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar")

# --- 接続処理（モデル名を 'gemini-1.5-flash' に統一） ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # 接続モデルを安定版に指定
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"接続エラー: {e}")

# --- UIとクリア処理 ---
if "input_key" not in st.session_state: st.session_state.input_key = 0
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

if st.button("市場分析スタート"):
    if event_input:
        # ここでAPIを呼び出しますが、失敗してもアプリが落ちないようにガードします
        try:
            # 分析プロンプト（必要に応じて調整してください）
            response = model.generate_content(f"「{event_input}」に関連する日本株をリストアップし、市場への影響を分析して")
            st.session_state.last_result = response.text
        except Exception as e:
            st.error(f"分析失敗: {e}")
            st.session_state.last_result = None

if st.button("入力欄をクリア"):
    st.session_state.input_key += 1
    st.rerun()

# --- 結果表示 ---
if "last_result" in st.session_state and st.session_state.last_result:
    st.markdown("### 分析結果")
    st.write(st.session_state.last_result)
    
    # 【次にやること】ここにパース処理（リスト抽出）を入れれば、株価表に戻ります
