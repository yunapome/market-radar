import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# API設定
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("API設定でエラーが発生しました")
    st.stop()

# --- 入力管理の仕組み ---
# 「現在の入力内容」をセッションで保持する
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

def clear_text():
    st.session_state.user_input = ""

# 入力欄（値が変わったらセッションに書き込む）
user_input = st.text_input(
    "分析したいニュースや銘柄を入力してください", 
    value=st.session_state.user_input,
    key="input_field"
)

# ボタンの配置
col1, col2 = st.columns([0.1, 0.9])
with col1:
    if st.button("クリア"):
        # セッションを空にして、入力欄を更新する
        st.session_state.user_input = ""
        st.rerun()

# 分析処理
if st.button("Analyze"):
    if not user_input:
        st.warning("内容を入力してください。")
    else:
        st.write(f"Analyzing: {user_input}...")
        try:
            response = model.generate_content(user_input)
            st.markdown("### Analysis Result")
            st.write(response.text)
        except Exception as e:
            st.error("分析中にエラーが発生しました。時間を置いて試してください。")
