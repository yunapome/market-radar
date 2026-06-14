import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# Configure Gemini
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # モデル名を指定せず、代わりに利用可能なモデル一覧から自動で探す
    models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0].name) # 使えるモデルの最初のものを自動選択
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
