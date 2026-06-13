import streamlit as st
import anthropic

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar")

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("API Key not found in Secrets.")
    st.stop()

event_input = st.text_input("Enter a news event")

if st.button("Analyze"):
    if not event_input:
        st.warning("Please enter an event.")
    else:
        st.write("Analyzing...")
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                messages=[{"role": "user", "content": f"Analyze: {event_input}"}]
            )
            st.write(response.content[0].text)
        except Exception as e:
            st.error(f"Error: {e}")
