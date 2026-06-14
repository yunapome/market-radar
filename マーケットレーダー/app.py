import streamlit as st
import pandas as pd
import re

# ページ設定
st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Robust Ver - Debug Mode)")

# --- セッションステートの初期化 ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "market_comment" not in st.session_state:
    st.session_state.market_comment = None

# --- 入力フォーム ---
# keyを明示して定義
event_input = st.text_input("分析したいニュースやキーワードを入力", key="input_text")

# --- アクションボタン ---
col1, col2 = st.columns([1, 5])
with col1:
    analyze_btn = st.button("Analyze")
    clear_btn = st.button("クリア")

# --- Analyzeの処理 ---
if analyze_btn:
    if event_input:
        with st.spinner("分析中..."):
            # 【API制限解除後、ここに元の genai 処理を戻します】
            st.session_state.analysis_result = "トヨタ自動車,7203\nソニーグループ,6758\n日立製作所,6501"
            st.session_state.market_comment = f"ニュース「{event_input}」に対する客観的な分析です。市場への直接的な影響は限定的と推察されます。"
            st.rerun()

# --- クリアの処理（エラー回避） ---
if clear_btn:
    # 保持データをすべてリセット
    st.session_state.analysis_result = None
    st.session_state.market_comment = None
    # ここが重要：input_text の値を空にする代わりに、ウィジェットをリセットさせる
    st.session_state.input_text = "" 
    st.rerun()

# --- 結果の表示 ---
if st.session_state.analysis_result:
    matches = re.findall(r'([^,\n]+),(\d{4})', st.session_state.analysis_result)
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            data.append({"企業名": name, "証券コード": code, "現在株価": "3000円", "前日比": "+1.20%", "トレンド": "↑"})
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
    if st.session_state.market_comment:
        st.markdown("### 市場分析コメント")
        st.write(st.session_state.market_comment)
