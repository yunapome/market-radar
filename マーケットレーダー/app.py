import streamlit as st
import anthropic
import os

# Page Config
st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar")

# Load API Key safely
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("API Key not set in Secrets.")
    st.stop()

# Input
event_input = st.text_input("Enter a news event to analyze")

if st.button("Analyze"):
    if not event_input:
        st.warning("Please enter an event.")
    else:
        st.write(f"Analyzing: {event_input}...")
        
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                messages=[{"role": "user", "content": f"Analyze the market reaction to: {event_input}"}]
            )
            st.markdown("### Analysis Result")
            st.write(response.content[0].text)
        except Exception as e:
            st.error(f"Error: {e}")
