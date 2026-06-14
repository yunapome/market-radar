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
    st.error("API設定が読み込めません。")
    st.stop()

# セッションステートの初期化
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "market_comment" not in st.session_state:
    st.session_state.market_comment = None
if "cache_results" not in st.session_state:
    st.session_state.cache_results = {}

def clear_data():
    st.session_state.analysis_result = None
    st.session_state.market_comment = None
    st.session_state.input_text = ""

# 入力フォーム
event_input = st.text_input("分析したいニュースやキーワードを入力", key="input_text")

# 分析ボタン
if st.button("Analyze"):
    if event_input:
        if event_input in st.session_state.cache_results:
            result = st.session_state.cache_results[event_input]
            st.session_state.analysis_result = result['list']
            st.session_state.market_comment = result['comment']
            st.info("キャッシュから結果を表示しました。")
        else:
            with st.spinner("分析中..."):
                try:
                    # プロンプトを安全な形式で定義
                    prompt = (
                        f"ニュース「{event_input}」について、以下の形式で出力してください。"
                        "余計な前置きは不要です。\n\n"
                        "[LIST]\n"
                        "企業名,証券コード(4桁)\n"
                        "(複数あれば改行)\n\n"
                        "[COMMENT]\n"
                        "市場への影響を客観的かつ論理的に分析し、200文字以内で要約してください。"
                        "感情的・扇動的な表現は排除してください。"
                    )
                    response = model.generate_content(prompt)
                    text = response.text
                    
                    # 出力をパース
                    list_match = re.search(r'\[LIST\](.*?)\[COMMENT\]', text, re.DOTALL)
                    comment_match = re.search(r'\[COMMENT\](.*)', text, re.DOTALL)
                    
                    analysis_list = list_match.group(1).strip() if list_match else ""
                    market_comment = comment_match.group(1).strip() if comment_match else "分析コメントを取得できませんでした。"
                    
                    st.session_state.analysis_result = analysis_list
                    st.session_state.market_comment = market_comment
                    st.session_state.cache_results[event_input] = {'list': analysis_list, 'comment': market_comment}
                except Exception as e:
                    st.error("API制限かエラーです。少し時間を置いてください。")

# 結果の表示
if st.session_state.analysis_result:
    matches = re.findall(r'([^,\n]+),(\d{4})', st.session_state.analysis_result)
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            try:
                ticker = yf.Ticker(f"{code}.T")
                info = ticker.history(period="2d")
                if len(info) >= 2:
                    curr, prev = info['Close'].iloc[-1], info['Close'].iloc[-2]
                    change_pct = ((curr - prev) / prev) * 100
                    data.append({
                        "企業名": name.strip(), "証券コード": code, 
                        "現在株価": f"{curr:.0f}円", "前日比": f"{change_pct:+.2f}%",
                        "トレンド": "↑" if change_pct > 0 else "↓" if change_pct < 0 else "-"
                    })
            except: continue
        
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
    # 考察表示
    st.markdown("---")
    st.markdown("### 市場分析コメント")
    st.write(st.session_state.market_comment)

if st.button("クリア"):
    clear_data()
    st.rerun()
