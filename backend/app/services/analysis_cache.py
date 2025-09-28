import os
import json
from typing import List, Dict, Any

# 日本語コメント: キャッシュ生成と保存の責務を分離
from .qiita_service import fetch_tag_items, fetch_search_items
from .analyzer import analyze_titles


def ensure_data_dir(base_file: str) -> str:
    """与えられたファイルパスからアプリ直下の data ディレクトリを見つける/作成する。

    app 配下の任意のモジュール（routes/services/mainなど）から呼ばれても
    app/data を指すように、'app' ディレクトリを上方向に探索する。
    """
    current = os.path.dirname(os.path.abspath(base_file))
    while True:
        if os.path.basename(current) == "app":
            break
        parent = os.path.dirname(current)
        if parent == current:
            # ルートまで来た場合はフォールバックとして現在ディレクトリを使用
            break
        current = parent
    data_dir = os.path.join(current, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_cache_path(data_dir: str) -> str:
    return os.path.join(data_dir, "analysis.json")


def _load_envs() -> Dict[str, Any]:
    return {
        "tag": os.getenv("QIITA_TAG", "Python"),
        "min_likes": int(os.getenv("MIN_LIKES", "50")),
        "max_pages": int(os.getenv("QIITA_MAX_PAGES", "10")),
        "per_page": int(os.getenv("QIITA_PER_PAGE", "100")),
        "min_count": int(os.getenv("MIN_COUNT", "2")),
        "query": os.getenv("QIITA_SEARCH_QUERY", ""),
        "min_stocks": int(os.getenv("MIN_STOCKS", "0")),
        "ttl": int(os.getenv("CACHE_TTL_SECONDS", "0")),
        "stopwords": os.getenv("STOPWORDS", ""),
    }


def build_cache_if_needed(data_dir: str, force: bool = False) -> None:
    env = _load_envs()
    cache_path = get_cache_path(data_dir)

    # TTL判定
    if not force and os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        if env["ttl"] > 0:
            import time as _t

            if (_t.time() - os.path.getmtime(cache_path)) < env["ttl"]:
                return
        else:
            return

    # ストップワード
    stopwords = set(filter(None, [w.strip() for w in env["stopwords"].split(",")]))
    default_stop = {
        "する",
        "できる",
        "なる",
        "ある",
        "いる",
        "こと",
        "よう",
        "ため",
        "紹介",
        "解説",
        "入門",
        "まとめ",
        "完全",
        "徹底",
        "超",
        "便利",
        "記事",
        "方法",
        "対応",
        "環境",
        "設定",
        "解決",
        "問題",
        "対応",
        "みる",
        "られる",
        "れる",
        "せる",
        "てる",
        "でき",
        "され",
        env["tag"],
    }
    stopwords |= default_stop

    # データ取得
    if env["query"]:
        items = fetch_search_items(
            env["query"], max_pages=env["max_pages"], per_page=env["per_page"]
        )
    else:
        items = fetch_tag_items(
            env["tag"], max_pages=env["max_pages"], per_page=env["per_page"]
        )

    # フィルタ
    filtered = [
        it
        for it in items
        if (it.get("likes_count") or 0) >= env["min_likes"]
        and (it.get("stocks_count") or 0) >= env["min_stocks"]
    ]

    titles = [it.get("title", "") for it in filtered]
    words = analyze_titles(titles)

    # ストップワードと最小出現回数
    filtered_words = {
        k: v for k, v in words.items() if (k not in stopwords and v >= env["min_count"])
    }

    payload = [
        {"text": k, "value": v}
        for k, v in sorted(filtered_words.items(), key=lambda kv: kv[1], reverse=True)
    ]
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
