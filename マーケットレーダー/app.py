import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Simple Robust)")

# フォーム形式にすると、送信ボタンで画面全体が綺麗に再実行されます
with st.form("input_form"):
    event_input = st.text_input("分析したいニュースやキーワードを入力")
    submitted = st.form_submit_button("Analyze")

# Analyzeが押された時
if submitted and event_input:
    with st.spinner("分析中..."):
        # 【ダミーデータ】
        st.session_state.result = "トヨタ自動車,7203\nソニーグループ,6758\n日立製作所,6501"
        st.session_state.comment = f"ニュース「{event_input}」に対する客観的な分析です。"
        st.rerun()

# 結果表示（データがある場合のみ）
if "result" in st.session_state:
    matches = re.findall(r'([^,\n]+),(\d{4})', st.session_state.result)
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            data.append({"企業名": name, "証券コード": code, "現在株価": "3000円", "前日比": "+1.20%", "トレンド": "↑"})
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        st.write(st.session_state.comment)

# クリアボタン（シンプルに全データを破棄してリロード）
if st.button("クリア"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
