import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar")

# API設定
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # モデル名を指定せず、使えるものを自動で見つける仕組み
    models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(models[0].name)
except Exception as e:
    st.error(f"接続エラー: {e}")
    st.stop()

# 入力欄
event_input = st.text_input("分析したいニュースや銘柄を入力してください")

# 分析ボタン
if st.button("市場分析"):
    if not event_input:
        st.warning("内容を入力してください。")
    else:
        st.write(f"Analyzing: {event_input}...")
        try:
            # プロンプトに役割を与える
            prompt = f"あなたはプロの投資家です。以下のキーワードについて、市場への影響やリスク・チャンスを分析して教えてください：{event_input}"
            response = model.generate_content(prompt)
            
            st.markdown("### Analysis Result")
            st.write(response.text)
        except Exception as e:
            st.error(f"分析中にエラーが発生しました: {e}")
