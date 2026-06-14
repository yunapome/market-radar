import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import re

# ページ設定
st.set_page_config(page_title="Market Radar", layout="wide")
st.title("📡 Market Radar (Robust Ver)")

# API設定
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("API設定が読み込めません。secretsを確認してください。")
    st.stop()

# セッションステートの初期化
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "cache_results" not in st.session_state:
    st.session_state.cache_results = {}

def clear_data():
    st.session_state.analysis_result = None
    st.session_state.input_text = ""

# 入力フォーム
event_input = st.text_input("分析したいニュースやキーワードを入力", key="input_text")

# 分析ボタン
if st.button("Analyze"):
    if event_input:
        if event_input in st.session_state.cache_results:
            st.session_state.analysis_result = st.session_state.cache_results[event_input]
            st.info("キャッシュから結果を表示しました。")
        else:
            with st.spinner("Analyzing..."):
                try:
                    # ニュースから企業を抽出
                    prompt = f"「{event_input}」に関連する日本企業を挙げ、必ず「企業名,証券コード(4桁)」の形式でリストアップして。余計な文章は不要。"
                    response = model.generate_content(prompt)
                    st.session_state.analysis_result = response.text
                    st.session_state.cache_results[event_input] = response.text
                except Exception as e:
                    st.error("APIの通信制限かエラーが発生しました。少し時間を置いて再試行してください。")

# 結果の表示
if st.session_state.analysis_result:
    result_text = st.session_state.analysis_result
    matches = re.findall(r'([^,\n]+),(\d{4})', result_text)
    
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            try:
                ticker = yf.Ticker(f"{code}.T")
                # 比較のために2日分取得
                info = ticker.history(period="2d")
                if len(info) >= 2:
                    current_price = info['Close'].iloc[-1]
                    prev_close = info['Close'].iloc[-2]
                    
                    # 前日比の計算
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                    
                    # トレンド判定
                    if change_pct > 0:
                        mark = "↑"
                    elif change_pct < 0:
                        mark = "↓"
                    else:
                        mark = "-"
                    
                    data.append({
                        "企業名": name.strip(), 
                        "証券コード": code, 
                        "現在株価": f"{current_price:.0f}円",
                        "前日比": f"{change_pct:+.2f}%",
                        "トレンド": mark
                    })
            except Exception:
                continue
        
        if data:
            # データの表示（st.dataframeでより見やすく）
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 詳細分析結果")
    st.write(result_text)

# クリアボタン
if st.button("クリア"):
    clear_data()
    st.rerun()
