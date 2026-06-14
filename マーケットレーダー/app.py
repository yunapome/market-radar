import streamlit as st
import google.generativeai as genai

# Page Configuration
st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Gemini Ver)")

# Configure Gemini
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # 利用可能なモデルから 1.5-flash を探す
    model_name = "gemini-1.5-flash"
    model = genai.GenerativeModel(model_name)
except KeyError:
    st.error("API Key not found in Secrets.")
    st.stop()

# User Input
event_input = st.text_input("Enter a news event to analyze")

if st.button("Analyze"):
    if not event_input:
        st.warning("Please enter an event.")
    else:
        st.write(f"Analyzing: {event_input}...")
        try:
            # Generate content
            response = model.generate_content(f"Analyze the market reaction to: {event_input}")
            st.markdown("### Analysis Result")
            st.write(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
