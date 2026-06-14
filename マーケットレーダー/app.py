import streamlit as st
import pandas as pd
import re

# ページ設定
st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Robust Ver - Debug Mode)")

# セッションステートの初期化
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "market_comment" not in st.session_state:
    st.session_state.market_comment = None
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# 入力フォーム
event_input = st.text_input("分析したいニュースやキーワードを入力", key="input_text")

# --- ダミーデータを返す分析ボタン ---
if st.button("Analyze"):
    if event_input:
        with st.spinner("分析中（現在はダミーデータを使用中）..."):
            # APIを叩かず、即座にダミーデータをセット
            st.session_state.analysis_result = "トヨタ自動車,7203\nソニーグループ,6758\n日立製作所,6501"
            st.session_state.market_comment = "ニュース「" + event_input + "」に対し、対象企業は堅調な推移を見せています。市場への直接的な影響は限定的であり、長期的には安定した成長が見込まれると推察されます。"
            st.rerun()

# 結果の表示
if st.session_state.analysis_result:
    matches = re.findall(r'([^,\n]+),(\d{4})', st.session_state.analysis_result)
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            # ダミーの株価計算（APIを使わずランダム値などでシミュレーション）
            data.append({
                "企業名": name.strip(), "証券コード": code, 
                "現在株価": "3000円", "前日比": "+1.20%",
                "トレンド": "↑"
            })
        
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 市場分析コメント")
    st.write(st.session_state.market_comment)

# クリアボタン（入力のみ消去）
if st.button("クリア"):
    st.session_state.input_text = ""
    st.session_state.analysis_result = None
    st.session_state.market_comment = None
    st.rerun()
