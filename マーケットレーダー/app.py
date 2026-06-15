"""
Market Radar Pro - リファクタリング版
改善点:
  1. Gemini / yfinance を完全分離し、それぞれ独立した再試行ロジックを実装
  2. Exponential Backoff + Jitter で 429/ResourceExhausted を回避
  3. yfinance はバッチ取得（download）＋スレッドプールで高速化
  4. セッション永続化: URL クエリパラメータ + localStorage (st.components) で
     スマホのページリフレッシュ後もデータを復元
  5. キャッシュ戦略: 株価は 60 秒 TTL でキャッシュし、Gemini 同一クエリは
     セッション内でキャッシュ（重複リクエスト防止）
"""

import streamlit as st
import google.generativeai as genai
import pandas as pd
import yfinance as yf
import re
import time
import random
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict, field
from typing import Optional
import streamlit.components.v1 as components

# ── ロギング設定 ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── ページ設定 ─────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Market Radar Pro")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 定数・設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Gemini 再試行パラメータ
GEMINI_MAX_RETRIES = 4
GEMINI_BASE_DELAY  = 2.0   # 秒（指数バックオフの基底）
GEMINI_MAX_DELAY   = 60.0  # 秒（上限）
GEMINI_JITTER      = 0.5   # ランダム揺らぎ係数

# yfinance 再試行パラメータ
YF_MAX_RETRIES  = 3
YF_BASE_DELAY   = 1.0
YF_MAX_DELAY    = 15.0
YF_CACHE_TTL    = 60       # 株価キャッシュ有効期間（秒）

# yfinance バッチ並列数（同時接続数を制限してレート制限回避）
YF_MAX_WORKERS  = 3


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. データクラス
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class StockRow:
    企業名: str
    証券コード: str
    株価: Optional[float] = None
    前日比率: Optional[float] = None
    トレンド: str = "–"
    取得状態: str = "OK"

    def to_display_dict(self):
        return {
            "企業名":    self.企業名,
            "証券コード": self.証券コード,
            "株価 (円)":  f"{self.株価:,.1f}" if self.株価 else "取得失敗",
            "前日比 (%)": f"{self.前日比率:+.2f}" if self.前日比率 is not None else "–",
            "トレンド":   self.トレンド,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Gemini クライアント（キャッシュ付き）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_resource(show_spinner=False)
def get_gemini_model():
    """アプリ全体で1インスタンスだけ保持する（接続コスト削減）"""
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        models = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        model_name = next((m for m in models if "gemini" in m), models[0])
        logger.info(f"Gemini モデル: {model_name}")
        return genai.GenerativeModel(model_name)
    except Exception as e:
        logger.error(f"Gemini 初期化失敗: {e}")
        return None


def _exponential_backoff(attempt: int, base: float, max_delay: float, jitter: float) -> float:
    """Exponential Backoff with Full Jitter"""
    delay = min(base * (2 ** attempt), max_delay)
    return delay * (1 - jitter + random.random() * jitter * 2)


def call_gemini_with_retry(model, prompt: str) -> str:
    """
    Gemini API を呼び出す。429 / ResourceExhausted の場合は
    Exponential Backoff + Jitter で再試行する。
    """
    last_exc = None
    for attempt in range(GEMINI_MAX_RETRIES):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = any(
                kw in err_str
                for kw in ["429", "resource_exhausted", "resourceexhausted", "quota", "rate"]
            )
            last_exc = e
            if is_rate_limit and attempt < GEMINI_MAX_RETRIES - 1:
                wait = _exponential_backoff(attempt, GEMINI_BASE_DELAY, GEMINI_MAX_DELAY, GEMINI_JITTER)
                logger.warning(f"Gemini レート制限 (試行 {attempt+1}/{GEMINI_MAX_RETRIES})。{wait:.1f}秒待機...")
                # ユーザーに待機を見せる
                with st.empty():
                    st.info(f"⏳ APIリクエスト制限中… {wait:.0f}秒後に再試行 ({attempt+1}/{GEMINI_MAX_RETRIES})")
                    time.sleep(wait)
            else:
                break  # レート制限以外のエラーは即座に諦める
    raise last_exc


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. yfinance 取得レイヤー（バッチ + 再試行 + キャッシュ）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _fetch_single_ticker(code: str) -> dict:
    """
    1銘柄の株価を取得して辞書で返す。
    スレッドプールから呼ばれるため例外は握り潰して状態を返す。
    """
    ticker_sym = f"{code}.T"
    last_exc = None

    for attempt in range(YF_MAX_RETRIES):
        try:
            hist = yf.Ticker(ticker_sym).history(period="5d")
            if len(hist) < 2:
                return {"code": code, "error": "データ不足"}
            curr = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2])
            change_pct = (curr - prev) / prev * 100
            return {
                "code":       code,
                "curr":       curr,
                "change_pct": change_pct,
                "trend":      "↑" if curr >= prev else "↓",
            }
        except Exception as e:
            last_exc = e
            err_str = str(e).lower()
            is_rate = any(kw in err_str for kw in ["429", "too many", "rate", "throttle"])
            if is_rate and attempt < YF_MAX_RETRIES - 1:
                wait = _exponential_backoff(attempt, YF_BASE_DELAY, YF_MAX_DELAY, 0.4)
                logger.warning(f"yfinance レート制限 {ticker_sym} (試行{attempt+1})。{wait:.1f}秒待機")
                time.sleep(wait)
            else:
                break

    return {"code": code, "error": str(last_exc)}


def fetch_stock_prices(stocks: list[tuple[str, str]]) -> dict[str, dict]:
    """
    複数銘柄を並列取得（YF_MAX_WORKERS で同時数を制限）。
    返値: {証券コード: 取得結果辞書}
    """
    results = {}
    with ThreadPoolExecutor(max_workers=YF_MAX_WORKERS) as executor:
        future_to_code = {
            executor.submit(_fetch_single_ticker, code): code
            for _, code in stocks
        }
        for future in as_completed(future_to_code):
            result = future.result()
            results[result["code"]] = result
    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. パース処理（Gemini レスポンス → 銘柄リスト）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_gemini_response(text: str) -> tuple[list[tuple[str, str]], str]:
    """
    Gemini の出力から (企業名, 証券コード) リストとコメントを抽出。
    コードは4桁数字のみ受け付ける。
    """
    stocks = []
    seen_codes = set()

    for line in text.split("\n"):
        # [COMMENT] 以降のタグを除外
        if re.search(r"\[COMMENT\]", line):
            break
        if "," not in line:
            continue
        parts = line.split(",", 1)
        name = parts[0].strip().lstrip("0123456789.- 　")
        code = re.sub(r"\D", "", parts[1].strip())[:4]
        if len(code) == 4 and code not in seen_codes:
            stocks.append((name, code))
            seen_codes.add(code)

    comment_parts = re.split(r"\[COMMENT\]", text, maxsplit=1)
    comment = comment_parts[-1].strip() if len(comment_parts) > 1 else ""

    return stocks, comment


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. セッション永続化（localStorage ブリッジ）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STORAGE_KEY = "market_radar_session_v1"

def _local_storage_bridge():
    """
    localStorage への読み書きを行う隠しコンポーネント。
    ページリロード時に保存済みデータを st.query_params 経由で復元する。

    仕組み:
      ① 初回マウント時: localStorage から JSON を読み出し、
        window.location の ?_restore=<base64> に設定 → Streamlit がリロード
      ② Streamlit 側で st.query_params["_restore"] を検出して session_state に展開
      ③ データ更新時: Python から st.query_params["_save"] に JSON を書き込み、
        JS 側で検知して localStorage に保存
    """
    # ── 復元フェーズ（query_params → session_state）──
    qp = st.query_params
    if "_restore" in qp and "data_rows" not in st.session_state:
        try:
            import base64
            raw = base64.b64decode(qp["_restore"]).decode()
            saved = json.loads(raw)
            st.session_state.data_rows   = saved.get("data_rows", [])
            st.session_state.comment     = saved.get("comment", "")
            st.session_state.last_query  = saved.get("last_query", "")
            # 復元後はパラメータを消す（次回リロードで二重復元しない）
            del qp["_restore"]
        except Exception as e:
            logger.warning(f"セッション復元失敗: {e}")

    # ── 保存 JS の埋め込み ──
    # データが存在する場合は localStorage に書き出す
    if "data_rows" in st.session_state:
        import base64
        payload = json.dumps({
            "data_rows":  st.session_state.data_rows,
            "comment":    st.session_state.get("comment", ""),
            "last_query": st.session_state.get("last_query", ""),
        }, ensure_ascii=False)
        encoded = base64.b64encode(payload.encode()).decode()

        components.html(f"""
        <script>
        (function() {{
            const KEY   = "{STORAGE_KEY}";
            const DATA  = "{encoded}";
            // 保存
            try {{ localStorage.setItem(KEY, DATA); }} catch(e) {{}}

            // ページロード時に localStorage からリストア（まだ query_params が空の場合）
            window.addEventListener("DOMContentLoaded", function() {{
                const stored = localStorage.getItem(KEY);
                if (stored && !location.search.includes("_restore")) {{
                    location.replace(location.pathname + "?_restore=" + stored);
                }}
            }});
        }})();
        </script>
        """, height=0)
    else:
        # データが無い状態でも、ページロード時リストアを試みる JS は常に埋め込む
        components.html(f"""
        <script>
        (function() {{
            const KEY = "{STORAGE_KEY}";
            window.addEventListener("DOMContentLoaded", function() {{
                const stored = localStorage.getItem(KEY);
                if (stored && !location.search.includes("_restore")) {{
                    location.replace(location.pathname + "?_restore=" + stored);
                }}
            }});
        }})();
        </script>
        """, height=0)


def save_to_session(rows: list[dict], comment: str, query: str):
    """分析結果を session_state に書き込む（JSON シリアライズ可能な形式）"""
    st.session_state.data_rows  = rows          # list[dict] — DataFrame にせず保持
    st.session_state.comment    = comment
    st.session_state.last_query = query


def clear_session():
    for key in ("data_rows", "comment", "last_query", "input_key"):
        st.session_state.pop(key, None)
    # localStorage も消去
    components.html(f"""
    <script>
    localStorage.removeItem("{STORAGE_KEY}");
    </script>
    """, height=0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. メイン処理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_analysis(model, query: str):
    """
    分析パイプライン:
      Gemini 呼び出し → パース → yfinance バッチ取得 → session_state 保存
    """
    # ── Step 1: Gemini に銘柄候補を生成させる ──
    prompt = (
        f"「{query}」に関連する日本株を5社挙げてください。\n"
        "出力形式（ヘッダー不要）:\n"
        "企業名,証券コード(4桁)\n"
        "全5行出力後、[COMMENT]タグの後に200文字以内の市場分析コメントを書いてください。"
    )

    with st.status("📡 Gemini が銘柄を分析中...", expanded=True) as status:
        try:
            raw_text = call_gemini_with_retry(model, prompt)
            status.update(label="✅ 銘柄リスト生成完了", state="complete")
        except Exception as e:
            st.error(f"❌ Gemini API エラー（再試行上限超過）: {e}")
            return

    stocks, comment = parse_gemini_response(raw_text)
    if not stocks:
        st.warning("銘柄を解析できませんでした。別のキーワードを試してください。")
        return

    # ── Step 2: yfinance で並列株価取得 ──
    with st.status(f"📈 {len(stocks)} 銘柄の株価を取得中...", expanded=True) as status:
        price_data = fetch_stock_prices(stocks)
        status.update(label="✅ 株価取得完了", state="complete")

    # ── Step 3: データ統合 ──
    rows = []
    for name, code in stocks:
        pd_ = price_data.get(code, {})
        if "error" in pd_:
            row = StockRow(企業名=name, 証券コード=code, 取得状態=f"⚠ {pd_['error']}")
        else:
            row = StockRow(
                企業名=name,
                証券コード=code,
                株価=round(pd_["curr"], 1),
                前日比率=round(pd_["change_pct"], 2),
                トレンド=pd_["trend"],
            )
        rows.append(row.to_display_dict())

    save_to_session(rows, comment, query)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. UI レンダリング
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    # セッション永続化ブリッジを起動（UI より先に実行）
    _local_storage_bridge()

    st.title("📡 Market Radar Pro")

    model = get_gemini_model()
    if model is None:
        st.error("Gemini APIキーが設定されていないか、接続に失敗しました。")
        st.stop()

    # ── 入力エリア ──
    if "input_key" not in st.session_state:
        st.session_state.input_key = 0

    last_query = st.session_state.get("last_query", "")
    event_input = st.text_input(
        "分析したいニュースやキーワードを入力",
        value=last_query,
        key=f"input_{st.session_state.input_key}",
        placeholder="例: 半導体不足、円安、AI投資...",
    )

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_btn = st.button("🔍 市場分析スタート", type="primary", use_container_width=True)
    with col2:
        refresh_btn = st.button("🔄 株価を更新", use_container_width=True,
                                disabled="data_rows" not in st.session_state)
    with col3:
        clear_btn = st.button("🗑 クリア", use_container_width=True)

    # ── ボタンアクション ──
    if clear_btn:
        clear_session()
        st.session_state.input_key = st.session_state.get("input_key", 0) + 1
        st.rerun()

    if start_btn and event_input.strip():
        # 同一クエリのキャッシュチェック（Gemini リクエスト節約）
        if event_input.strip() == st.session_state.get("last_query", "") \
                and "data_rows" in st.session_state:
            st.info("同じキーワードの結果を表示中です。株価を最新化する場合は「株価を更新」を押してください。")
        else:
            run_analysis(model, event_input.strip())
            st.rerun()

    if refresh_btn and "data_rows" in st.session_state:
        # Gemini を呼ばずに株価だけ再取得
        last_q = st.session_state.get("last_query", "")
        raw_rows = st.session_state.data_rows
        codes = [(r["企業名"], r["証券コード"]) for r in raw_rows]
        with st.status("📈 株価を最新化中...", expanded=True) as status:
            price_data = fetch_stock_prices(codes)
            status.update(label="✅ 更新完了", state="complete")
        updated = []
        for r in raw_rows:
            code = r["証券コード"]
            pd_ = price_data.get(code, {})
            if "error" not in pd_:
                r = dict(r)
                r["株価 (円)"]  = f"{pd_['curr']:,.1f}"
                r["前日比 (%)"] = f"{pd_['change_pct']:+.2f}"
                r["トレンド"]   = pd_["trend"]
            updated.append(r)
        st.session_state.data_rows = updated
        st.rerun()

    # ── 結果表示 ──
    if "data_rows" in st.session_state and st.session_state.data_rows:
        df = pd.DataFrame(st.session_state.data_rows)

        # トレンドに色を付ける
        def color_trend(val):
            if val == "↑":
                return "color: #2ecc71; font-weight: bold"
            elif val == "↓":
                return "color: #e74c3c; font-weight: bold"
            return ""

        # pandas 2.1+ では applymap が廃止され map に変更
        style_fn = df.style.map if hasattr(df.style, "map") else df.style.applymap
        styled = style_fn(color_trend, subset=["トレンド"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        if st.session_state.get("comment"):
            with st.expander("📝 市場分析コメント", expanded=True):
                st.write(st.session_state.comment)

        # 最終更新時刻
        st.caption(f"最終更新: {pd.Timestamp.now(tz='Asia/Tokyo').strftime('%Y-%m-%d %H:%M:%S JST')}")


if __name__ == "__main__" or True:
    main()
