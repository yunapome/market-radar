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

# --- セッションステートの初期化 ---
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
    # 実際にはAPIを叩かず、テスト用の固定値を設定する
    st.session_state.analysis_result = "トヨタ自動車,7203\nソニーグループ,6758\n日立製作所,6501"
    st.rerun() # 強制的に再読み込みして結果を表示させる
    if event_input:
        # キャッシュ確認
        if event_input in st.session_state.cache_results:
            st.session_state.analysis_result = st.session_state.cache_results[event_input]
            st.info("キャッシュから結果を表示しました。")
        else:
            with st.spinner("Analyzing..."):
                try:
                    prompt = f"「{event_input}」に関連する日本企業を挙げ、必ず「企業名,証券コード(4桁)」の形式でリストアップして。余計な文章は不要。"
                    response = model.generate_content(prompt)
                    
                    # 結果を保存
                    st.session_state.analysis_result = response.text
                    st.session_state.cache_results[event_input] = response.text
                except Exception as e:
                    st.error("APIの通信制限かエラーが発生しました。少し時間を置いて再試行してください。")

# 結果の表示（ボタンの外側で制御）
if st.session_state.analysis_result:
    result_text = st.session_state.analysis_result
    # CSV形式の抽出（カンマ区切りで企業名と4桁コードを取得）
    matches = re.findall(r'([^,\n]+),(\d{4})', result_text)
    
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            try:
                # 堅牢な株価取得処理
                ticker = yf.Ticker(f"{code}.T")
                info = ticker.history(period="1d")
                if not info.empty:
                    price = info['Close'].iloc[-1]
                    data.append({"企業名": name.strip(), "証券コード": code, "現在株価": f"{price:.0f}円"})
            except Exception:
                continue # 1社失敗しても全体は止まらない
        
        if data:
            st.table(pd.DataFrame(data))
    
    st.markdown("---")
    st.markdown("### 詳細分析結果")
    st.write(result_text)

# クリアボタン
if st.button("クリア"):
    clear_data()
    st.rerun()
