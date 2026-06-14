import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar")

# API設定
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0].name)
except Exception as e:
    st.error(f"接続エラー: {e}")
    st.stop()

# --- 入力状態の管理 ---
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

def clear_input():
    st.session_state.input_text = ""

# 入力欄
event_input = st.text_input(
    "分析したいニュースや銘柄を入力してください", 
    value=st.session_state.input_text,
    key="input_text"
)

# ボタンの配置
col1, col2 = st.columns([0.2, 0.8])

with col1:
    if st.button("市場分析スタート"):
        if not event_input:
            st.warning("内容を入力してください。")
        else:
            st.write(f"Analyzing: {event_input}...")
            try:
                # --- ここを強化しました ---
                # 「銘柄名と証券コードを必ず出す」という強いルールを追加
                prompt = (
                    f"あなたはプロの投資家です。{event_input}について、市場への影響やリスク・チャンスを分析してください。"
                    "もし分析に日本の企業が関わる場合、必ずその『銘柄名』と『証券コード』をリスト形式で明記してください。"
                )
                response = model.generate_content(prompt)
                st.markdown("### Analysis Result")
                st.write(response.text)
            except Exception as e:
                st.error(f"分析中にエラーが発生しました: {e}")

with col2:
    if st.button("クリア", on_click=clear_input):
        st.rerun()
