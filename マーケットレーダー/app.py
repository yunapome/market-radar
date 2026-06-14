import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# ページ設定
st.set_page_config(layout="wide")
st.title("📡 Market Radar (Official API Version)")

# API設定（StreamlitのSecretsから読み込み）
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    st.error("APIキーの設定を確認してください。")

# 入力欄のキーを管理する変数
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

# 入力欄（キーに変数を使用）
event_input = st.text_input("分析したいニュースやキーワードを入力", key=f"input_{st.session_state.input_key}")

# 市場分析スタートボタン
if st.button("市場分析スタート"):
    if event_input:
        with st.spinner("Geminiが市場を分析中..."):
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
           # 【パース処理を安全な形式に修正】
            text = response.text
            
            # タグが見つからない場合に備えて、空文字ではなくデフォルト値を設定
            list_content = ""
            comment_content = "分析結果の形式が正しくありませんでした。"
            
            if "[LIST]" in text and "[COMMENT]" in text:
                list_match = re.search(r'\[LIST\](.*?)\[COMMENT\]', text, re.DOTALL)
                comment_match = re.search(r'\[COMMENT\](.*)', text, re.DOTALL)
                if list_match: list_content = list_match.group(1).strip()
                if comment_match: comment_content = comment_match.group(1).strip()
            else:
                # タグがない場合、全体をコメントとして扱うなどのフォールバック
                comment_content = text
            
            st.session_state.result = list_content
            st.session_state.comment = comment_content
            st.rerun()

# 入力欄クリアボタン
if st.button("入力欄をクリア"):
    st.session_state.input_key += 1
    st.rerun()

# 結果表示
if "result" in st.session_state:
    matches = re.findall(r'([^,\n]+),(\d{4})', st.session_state.result)
    if matches:
        st.markdown("### 関連企業の現在株価")
        data = []
        for name, code in matches:
            # 実際にはここでyfinanceなどから株価を取得すると完璧です
            data.append({"企業名": name.strip(), "証券コード": code, "詳細": "分析完了"})
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
    if "comment" in st.session_state:
        st.markdown("### 市場分析コメント")
        st.write(st.session_state.comment)
