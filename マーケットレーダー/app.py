import streamlit as st
import google.generativeai as genai
import yfinance as yf

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Data Integrated)")

# API設定
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.stop()

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

def clear_input():
    st.session_state.input_text = ""

event_input = st.text_input("分析したいニュースや銘柄を入力", value=st.session_state.input_text, key="input_text")

col1, col2 = st.columns([0.2, 0.8])

with col1:
    if st.button("Analyze"):
        if event_input:
            st.write(f"Analyzing: {event_input}...")
            # プロンプトで「株価取得のために証券コードを正確に出せ」と指示
            prompt = f"「{event_input}」に関連する日本企業を挙げ、銘柄名と証券コード(4桁)のみをリスト形式で抽出して。余計な解説は不要。"
            response = model.generate_content(prompt)
            st.markdown("### 関連銘柄と現在の株価")
            
            # 結果からコードを抜き出して株価を取得（簡易実装）
            text = response.text
            st.write(text) # AIの回答を表示
            
            st.info("※銘柄コードを抽出して株価を取得中...")
            # ここにコードを解析して yf.Ticker(f"{code}.T").history(period="1d") を実行する処理を追加していきます
        
with col2:
    if st.button("クリア", on_click=clear_input):
        st.rerun()
