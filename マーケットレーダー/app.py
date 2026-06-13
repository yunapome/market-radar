import streamlit as st
import anthropic
import yfinance as yf
import json
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="マーケット・レーダー",
    page_icon="📡",
    layout="wide"
)

st.title("📡 マーケット・レーダー")
st.caption("ニュースイベント → 関連銘柄 → 当日の市場反応を確認")

# --- AIで関連銘柄を抽出 ---
def analyze_with_claude(event: str, api_key: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": f"""あなたはマーケットアナリストです。
次のイベントについてウェブ検索し、関連する上場企業5社を抽出してください。

イベント: 「{event}」

以下のJSON形式のみで返答してください（説明文不要）:
{{
  "event_summary": "イベントの1〜2文の要約（日本語）",
  "companies": [
    {{
      "ticker": "Yahoo Finance形式のティッカー（日本株は7203.Tのように.T付き）",
      "name": "会社名（日本語）",
      "reason": "このイベントとの関連理由（30〜50字）"
    }}
  ]
}}"""
        }]
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    text = text[text.index("{"):text.rindex("}") + 1]
    return json.loads(text)

# --- 株価データを取得 ---
def fetch_stock(ticker: str) -> dict | None:
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        # 直近2営業日分を使う（週末・祝日対応）
        hist = hist[hist["Close"].notna()].tail(2)
        if len(hist) < 2:
            return None
        prev = hist["Close"].iloc[-2]
        curr = hist["Close"].iloc[-1]
        change = (curr - prev) / prev * 100
        return {
            "current": round(float(curr), 2),
            "previous": round(float(prev), 2),
            "change": round(float(change), 2)
        }
    except Exception:
        return None

# --- UIレイアウト ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.secrets["ANTHROPIC_API_KEY"]
        "Anthropic APIキー",
        type="password",
        help="anthropic.comで取得したAPIキーを入力"
    )
    st.divider()
    st.markdown("**イベント例**")
    presets = [
        "スペースX ロケット打ち上げ",
        "Apple 決算発表",
        "半導体輸出規制",
        "日銀 金利政策決定",
        "EV補助金 政策変更",
    ]
    for p in presets:
        if st.button(p, use_container_width=True):
            st.session_state["event_input"] = p

event = st.text_input(
    "分析したいニュースイベントを入力",
    placeholder="例：ロケット打ち上げ、決算発表、半導体規制...",
    key="event_input"
)

if st.button("🔍 分析する", type="primary", disabled=not (event and api_key)):

    # Step 1: AI分析
    with st.spinner("ニュースを検索・分析中..."):
        try:
            result = analyze_with_claude(event, api_key)
        except Exception as e:
            st.error(f"AI分析エラー: {e}")
            st.stop()

    st.subheader("📰 イベント概要")
    st.info(result.get("event_summary", event))

    # Step 2: 株価取得
    companies = result.get("companies", [])
    with st.spinner("株価データを取得中..."):
        stocks = [fetch_stock(c["ticker"]) for c in companies]

    # Step 3: 銘柄カード表示
    st.subheader("🏢 関連銘柄 5社")
    cols = st.columns(len(companies))
    for i, (col, company, stock) in enumerate(zip(cols, companies, stocks)):
        with col:
            change = stock["change"] if stock else None
            delta_str = f"{change:+.2f}%" if change is not None else "データなし"
            # st.metricはdeltaの符号で自動的に色が変わる
            st.metric(
                label=f"{company['ticker']}　{company['name']}",
                value=f"${stock['current']:.2f}" if stock else "---",
                delta=delta_str if change is not None else None
            )
            st.caption(company["reason"])

    # Step 4: グラフ表示
    valid = [(c, s) for c, s in zip(companies, stocks) if s]
    if valid:
        st.subheader("📊 当日騰落率")
        tickers = [c["ticker"] for c, _ in valid]
        changes = [s["change"] for _, s in valid]
        colors = ["#1D9E75" if v >= 0 else "#E24B4A" for v in changes]

        fig = go.Figure(go.Bar(
            x=tickers,
            y=changes,
            marker_color=colors,
            text=[f"{v:+.2f}%" for v in changes],
            textposition="outside"
        ))
        fig.update_layout(
            yaxis_title="騰落率 (%)",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(zeroline=True, zerolinecolor="#ccc"),
            showlegend=False,
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Step 5: 一覧テーブル
        st.subheader("📋 まとめ一覧")
        df = pd.DataFrame([{
            "ティッカー": c["ticker"],
            "会社名": c["name"],
            "現値": f"${s['current']:.2f}",
            "前日比": f"{s['change']:+.2f}%",
            "関連理由": c["reason"]
        } for c, s in valid])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("株価データを取得できませんでした。ティッカーを確認してください。")
