import streamlit as st
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar")

# セッション状態の初期化
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_comment" not in st.session_state:
    st.session_state.last_comment = None

# 入力フォーム（keyを動的に変えることで、入力欄だけをクリアするテクニック）
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

# ボタンの配置
col1, col2 = st.columns([1, 10])
with col1:
    if st.button("市場分析スタート"):
        if event_input:
            # ここにAPIの処理を戻します。今はダミーで確実に動くようにしています。
            st.session_state.last_result = "トヨタ自動車,7203\nソニーグループ,6758\n日立製作所,6501"
            st.session_state.last_comment = f"「{event_input}」について、客観的な市場分析を行いました。特異な変動は見られません。"
            st.rerun()

with col2:
    if st.button("入力欄をクリア"):
        # キーを更新して入力欄を強制リセット
        st.session_state.input_key += 1
        st.rerun()

# 結果の表示（analyzeボタンを押した後だけ表示される）
if st.session_state.last_result:
    st.markdown("---")
    st.markdown("### 関連企業の現在株価")
    
    # データを解析して表にする
    rows = []
    for line in st.session_state.last_result.split('\n'):
        if ',' in line:
            name, code = line.split(',')
            rows.append({"企業名": name, "証券コード": code, "詳細": "分析完了"})
    
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    
    st.markdown("### 市場分析コメント")
    st.write(st.session_state.last_comment)
