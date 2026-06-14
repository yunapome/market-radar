import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# API Key load
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # モデル名を指定せず、genaiのデフォルト設定を利用する書き方に変更
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

event_input = st.text_input("Enter a news event to analyze")

if st.button("Analyze"):
    if not event_input:
        st.warning("Please enter an event.")
    else:
        st.write(f"Analyzing: {event_input}...")
        try:
            # プロンプトの投げ方を少しだけシンプルに
            response = model.generate_content(event_input)
            st.markdown("### Analysis Result")
            st.write(response.text)
        except Exception as e:
            st.error(f"Analysis Error: {e}")
