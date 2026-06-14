import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# API設定
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 成功していた時のシンプルな入力欄
event_input = st.text_input("分析したいニュースや銘柄を入力してください")

# 成功していた時のシンプルな分析ボタン
if st.button("Analyze"):
    if not event_input:
        st.warning("内容を入力してください。")
    else:
        st.write(f"Analyzing: {event_input}...")
        response = model.generate_content(event_input)
        st.markdown("### Analysis Result")
        st.write(response.text)
