import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar (Auto-Model Detection)")

# --- 確実な接続処理 ---
@st.cache_resource
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # 利用可能なモデル一覧を取得
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not models:
            raise Exception("利用可能なモデルが見つかりません。")
        
        # モデル名に 'gemini-1.5' を含むものを優先、なければ最初に見つかったものを使用
        target_model = next((m for m in models if 'gemini-1.5' in m), models[0])
        st.sidebar.info(f"使用中モデル: {target_model}")
        return genai.GenerativeModel(target_model)
    except Exception as e:
        st.error(f"API接続エラー: {e}")
        return None

model = get_model()

# --- 状態管理 ---
if "input_key" not in st.session_state: st.session_state.input_key = 0
if "last_result" not in st.session_state: st.session_state.last_result = None

# --- UI構築 ---
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("市場分析スタート"):
        if model and event_input:
            with st.spinner("Geminiが分析中..."):
                try:
                    prompt = (
                        f"ニュース「{event_input}」について、以下の形式で出力してください。\n\n"
                        "[LIST]\n企業名,証券コード(4桁)\n\n"
                        "[COMMENT]\n市場への影響を200文字以内で客観的に分析してください。"
                    )
                    response = model.generate_content(prompt)
                    st.session_state.last_result = response.text
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
    list_match = re.search(r'\[LIST\](.*?)(?=\[COMMENT\]|$)', result_text, re.DOTALL)
    
    if list_match:
        lines = list_match.group(1).strip().split('\n')
        data = []
        for line in lines:
            parts = line.split(',')
            if len(parts) >= 2:
                name = re.sub(r'[\(\)0-9.T]', '', parts[0]).strip()
                code = re.sub(r'[^0-9]', '', parts[1]).strip()
                if name and code:
                    data.append({"企業名": name, "証券コード": code})
        if data:
            st.markdown("### 関連企業のリスト")
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    comment_match = re.search(r'\[COMMENT\](.*)', result_text, re.DOTALL)
    if comment_match:
        st.markdown("### 市場分析コメント")
        st.write(comment_match.group(1).strip())
