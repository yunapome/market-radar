import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar")

# --- 接続処理 ---
@st.cache_resource
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception:
        return None

model = get_model()

# --- 状態管理 ---
if "input_key" not in st.session_state: st.session_state.input_key = 0
if "last_result" not in st.session_state: st.session_state.last_result = None

# --- UI構築 ---
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

col1, col2 = st.columns([1, 10])
with col1:
    if st.button("市場分析スタート"):
        if model and event_input:
            with st.spinner("Geminiが分析中..."):
                try:
                    # 形式を指定して出力させる
                    prompt = (
                        f"ニュース「{event_input}」について、以下の形式で出力してください。\n\n"
                        "[LIST]\n企業名,証券コード(4桁),現在株価,前日比,トレンド(↑or↓)\n\n"
                        "[COMMENT]\n市場への影響を200文字以内で要約してください。"
                    )
                    st.session_state.last_result = model.generate_content(prompt).text
                    st.rerun()
                except Exception as e:
                    st.error(f"分析失敗: {e}")

with col2:
    if st.button("入力欄をクリア"):
        st.session_state.input_key += 1
        st.rerun()

# --- 結果表示とパース処理 ---
if st.session_state.last_result:
    result_text = st.session_state.last_result
    
    # [LIST]と[COMMENT]で分割
    list_match = re.search(r'\[LIST\](.*?)(?=\[COMMENT\]|$)', result_text, re.DOTALL)
    comment_match = re.search(r'\[COMMENT\](.*)', result_text, re.DOTALL)
    
    if list_match:
        # 表の作成
        lines = list_match.group(1).strip().split('\n')
        data = []
        for line in lines:
            parts = line.split(',')
            if len(parts) >= 5:
                data.append({
                    "企業名": parts[0].strip(), "証券コード": parts[1].strip(),
                    "株価": parts[2].strip(), "前日比": parts[3].strip(), "トレンド": parts[4].strip()
                })
        st.markdown("### 関連企業の現在株価")
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
    if comment_match:
        st.markdown("### 市場分析コメント")
        st.write(comment_match.group(1).strip())
