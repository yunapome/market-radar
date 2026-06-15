import streamlit as st
import google.generativeai as genai
import pandas as pd
import yfinance as yf
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar Pro")

# --- 接続設定 ---
@st.cache_resource
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if 'gemini' in m), models[0])
        return genai.GenerativeModel(model_name)
    except Exception:
        return None

model = get_model()

# --- リアルタイム株価取得関数 ---
def get_stock_data(code):
    try:
        ticker = yf.Ticker(f"{code}.T")
        hist = ticker.history(period="2d") # 前日比計算のために2日分取得
        if len(hist) < 2: return None, None, "N/A"
        
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        change_pct = ((curr - prev) / prev) * 100
        trend = "↑" if curr >= prev else "↓"
        return round(curr, 1), round(change_pct, 2), trend
    except:
        return None, None, "N/A"

# --- UIと状態管理 ---
event_input = st.text_input("分析したいニュースやキーワードを入力")

if st.button("市場分析スタート"):
    if model and event_input:
        with st.spinner("Geminiが分析中..."):
            prompt = (f"「{event_input}」に関連する日本株を5社挙げてください。\n"
                      "形式：企業名,証券コード(4桁)\n"
                      "要約を最後に[COMMENT]タグで200文字以内で書いて。")
            
            res = model.generate_content(prompt).text
            
            # リスト抽出と株価取得
            data = []
            for line in res.split('\n'):
                if ',' in line and not line.startswith('['):
                    parts = line.split(',')
                    name, code = parts[0].strip(), parts[1].strip()
                    price, change, trend = get_stock_data(code)
                    if price:
                        data.append({"企業名": name, "証券コード": code, "株価": price, "前日比%": change, "トレンド": trend})
            
            st.session_state.data = pd.DataFrame(data)
            st.session_state.comment = re.split(r'\[COMMENT\]', res)[-1]
            st.rerun()

# --- 表示 ---
if "data" in st.session_state:
    st.dataframe(st.session_state.data, use_container_width=True, hide_index=True)
    st.write("### 市場分析コメント")
    st.write(st.session_state.comment)
