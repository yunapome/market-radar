import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# Configure Gemini (成功している設定をそのまま利用)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0].name)
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# --- クリアボタンのための処理 ---
# 1. 入力欄に "my_input" という名前（key）を付けます
# 2. ページが読み込まれるたびに、セッション内のこの名前の値を表示します
event_input = st.text_input("Enter a news event to analyze", key="my_input")

# ボタンを横並びに配置
col1, col2 = st.columns([0.2, 0.8])

with col1:
    # 「クリア」ボタンが押されたら、セッション内の値を空にして再読み込み
    if st.button("クリア"):
        st.session_state.my_input = ""
        st.rerun()

with col2:
    if st.button("Analyze"):
        if not event_input:
            st.warning("Please enter an event.")
        else:
            st.write(f"Analyzing: {event_input}...")
            try:
                response = model.generate_content(event_input)
                st.markdown("### Analysis Result")
                st.write(response.text)
            except Exception as e:
                st.error(f"Analysis Error: {e}")
