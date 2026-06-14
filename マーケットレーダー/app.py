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

# 入力フォーム（keyを指定して管理）
event_input = st.text_input("分析したいニュースやキーワードを入力", key="input_text")

# 分析ボタン
if st.button("Analyze"):
    if event_input:
        with st.spinner("分析中..."):
            # 【ここをAPI復活時にgenaiの呼び出しに戻します】
            # 現在はダミーデータでUIを確定させます
            st.session_state.analysis_result = "トヨタ自動車,7203\nソニーグループ,6758\n日立製作所,6501"
            st.session_state.market_comment = f"ニュース「{event_input}」に対する客観的な分析です。市場は冷静に反応しており、各企業の株価推移には大きな変動は見られません。"
            st.rerun()

# 結果の表示
if st.session_state.analysis_result:
    matches = re.findall(r'([^,\n]+),(\d{4})', st.session_state.analysis_result)
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            # ダミー株価データ
            data.append({
                "企業名": name.strip(), "証券コード": code, 
                "現在株価": "3000円", "前日比": "+1.20%",
                "トレンド": "↑"
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 市場分析コメント")
    st.write(st.session_state.market_comment)

# クリアボタンの安全な処理
if st.button("クリア"):
    # session_stateを個別にクリアする安全な手法
    if "input_text" in st.session_state:
        st.session_state.input_text = ""
    st.session_state.analysis_result = None
    st.session_state.market_comment = None
    st.rerun()
