# --- セッションステートの初期化 ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
# 過去の検索結果を保存する辞書（キャッシュ）を追加
if "cache_results" not in st.session_state:
    st.session_state.cache_results = {}

# --- 入力処理 ---
event_input = st.text_input("分析したいニュースやキーワードを入力", key="input_text")

if st.button("Analyze"):
    if event_input:
        # キャッシュにあるか確認
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
                    # キャッシュ辞書にも追加
                    st.session_state.cache_results[event_input] = response.text
                except Exception as e:
                    st.error("API制限かエラーです。少し時間を置いてください。")
