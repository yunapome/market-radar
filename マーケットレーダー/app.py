import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar")

# --- 接続設定 ---
@st.cache_resource
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # 自動モデル選択のロジック
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if 'gemini-1.5' in m), models[0])
        return genai.GenerativeModel(model_name)
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
                    # 指示を明確に修正
                    prompt = (
                        f"「{event_input}」について、関連銘柄をリストアップしてください。\n"
                        "出力は以下の形式で「見出し行を含めず」データのみを返してください。\n"
                        "形式：企業名,証券コード,株価,前日比,トレンド(↑/↓)\n\n"
                        "また、最後に[COMMENT]というタグを付けて、市場への影響を200文字以内で要約してください。"
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
    # 1. リスト部分（[COMMENT]タグの前まで）を抽出
    list_part = re.split(r'\[COMMENT\]', st.session_state.last_result)[0]
    
    # 2. 表の作成
    data = []
    for line in list_part.strip().split('\n'):
        parts = line.split(',')
        if len(parts) >= 5:
            data.append({
                "企業名": parts[0].strip(), "証券コード": parts[1].strip(),
                "株価": parts[2].strip(), "前日比": parts[3].strip(), "トレンド": parts[4].strip()
            })
    
    if data:
        st.markdown("### 関連企業の現在株価")
        df = pd.DataFrame(data)
        # カラム名を明示的に設定して重複を防ぐ
        df.columns = ["企業名", "証券コード", "株価", "前日比", "トレンド"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 3. コメント表示
    comment_part = re.split(r'\[COMMENT\]', st.session_state.last_result)
    if len(comment_part) > 1:
        st.markdown("### 市場分析コメント")
        st.write(comment_part[1].strip())
