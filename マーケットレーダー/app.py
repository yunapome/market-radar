import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")
st.title("📡 Market Radar (Robust Ver)")

# 入力欄のキーを管理する変数
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

# 【重要】入力欄のキーに変数を使うことで、キーが変わると入力欄が自動でリセットされる
event_input = st.text_input("分析したいニュースを入力", key=f"input_{st.session_state.input_key}")

# 分析処理（結果はsession_stateに保持され続ける）
if st.button("Analyze"):
    if event_input:
        st.session_state.result = "トヨタ自動車,7203\nソニーグループ,6758"
        st.session_state.comment = f"ニュース「{event_input}」の分析結果です。"

# 【重要】クリア処理：入力欄のキーだけを更新する
if st.button("入力欄をクリア"):
    st.session_state.input_key += 1 # キーを変えることで、text_inputを強制的に初期化
    st.rerun()

# 結果表示（ボタンを押しても消えない）
if "result" in st.session_state:
    st.markdown("### 分析結果")
    st.write(st.session_state.comment)
    # 表の表示処理...
