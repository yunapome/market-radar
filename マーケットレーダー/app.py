import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar")

# 成功している設定
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0].name)
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# --- ここが修正ポイント ---
# 1. session_stateに値を保存する箱を作ります
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# 2. 関数を作って、クリアボタンで「箱」を空にします
def clear_input():
    st.session_state.input_text = ""

# 3. text_input の value に session_state を指定して同期させます
# on_changeを使うことで、ユーザーが入力するたびに値が保存されます
event_input = st.text_input(
    "Enter a news event to analyze", 
    value=st.session_state.input_text,
    key="input_text",
    on_change=lambda: st.session_state.update({"input_text": st.session_state.input_text})
)

# ボタン配置
col1, col2 = st.columns([0.2, 0.8])
with col1:
    if st.button("クリア", on_click=clear_input):
        st.rerun()

with col2:
    if st.button("関連銘柄分析"):
        if not event_input:
            st.warning("Please enter an event.")
        else:
            st.write(f"Analyzing: {event_input}...")
            try:
                prompt = f"あなたはプロの投資家です。以下のニュースやキーワードが、市場や関連企業の株価にどう影響するかを分析し、リスクとチャンスの観点で短くまとめてください：{event_input}"
response = model.generate_content(prompt)
                st.markdown("### Analysis Result")
                st.write(response.text)
            except Exception as e:
                st.error(f"Analysis Error: {e}")
