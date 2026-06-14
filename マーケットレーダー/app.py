import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar")

# --- 接続設定（モデル名を柔軟に探索） ---
@st.cache_resource
def get_model():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # 利用可能なモデルを一覧から探し、自動で最適化する
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if 'gemini-1.5' in m), models[0])
        return genai.GenerativeModel(model_name)
    except Exception:
        return None

model = get_model()

# --- 状態管理 ---
if "input_key" not in st.session_state: st.session_state.input_key = 0
if "last_result" not in st.session_state: st.session_state.last_result = None

# --- UIとクリア処理 ---
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

if st.button("市場分析スタート"):
    if model and event_input:
        with st.spinner("Geminiが市場分析中..."):
            try:
                # 必須項目をGeminiに強く指示するプロンプト
                prompt = (
                    f"ニュース「{event_input}」について、関連銘柄のリストを作成してください。\n"
                    "必ず以下のCSV形式で出力してください：\n"
                    "企業名,証券コード,株価,前日比,トレンド\n"
                    "(トレンドは上昇なら↑、下落なら↓と記載)"
                )
                st.session_state.last_result = model.generate_content(prompt).text
                st.rerun()
            except Exception as e:
                st.error(f"分析失敗: {e}")

if st.button("入力欄をクリア"):
    st.session_state.input_key += 1
    st.rerun()

# --- 結果表示とパース処理 ---
if st.session_state.last_result:
    st.markdown("### 市場分析結果")
    
    # 複数行の回答からCSV形式の部分だけを抽出して表にする
    lines = st.session_state.last_result.strip().split('\n')
    data = []
    for line in lines:
        # カンマで区切られたデータを探す
        parts = line.split(',')
        if len(parts) >= 5: # 企業名,コード,株価,前日比,トレンド の5項目あるか確認
            data.append({
                "企業名": parts[0].strip(),
                "証券コード": parts[1].strip(),
                "株価": parts[2].strip(),
                "前日比": parts[3].strip(),
                "トレンド": parts[4].strip()
            })
    
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.write(st.session_state.last_result)
