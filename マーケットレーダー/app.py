import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")
st.title("📡 Market Radar (Robust Ver)")

# 入力欄のキーを管理する変数
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

# 入力欄（キーに変数を使用）
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

# 分析ボタン（ラベル変更）
if st.button("市場分析スタート"):
    if event_input:
        # ダミーデータのセット
        st.session_state.result = "トヨタ自動車,7203\nソニーグループ,6758\n日立製作所,6501"
        st.session_state.comment = f"ニュース「{event_input}」に対する客観的な分析です。市場への直接的な影響は限定的と推察されます。"

# 入力欄クリアボタン
if st.button("入力欄をクリア"):
    st.session_state.input_key += 1
    st.rerun()

# 結果表示（Analyzeを押すと表示され、入力欄をクリアしても消えない）
if "result" in st.session_state:
    matches = re.findall(r'([^,\n]+),(\d{4})', st.session_state.result)
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            data.append({
                "企業名": name.strip(), "証券コード": code, 
                "現在株価": "3000円", "前日比": "+1.20%",
                "トレンド": "↑"
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
    if "comment" in st.session_state:
        st.markdown("### 市場分析コメント")
        st.write(st.session_state.comment)
