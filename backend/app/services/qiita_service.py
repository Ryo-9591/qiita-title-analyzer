import time
import os
from typing import List, Dict, Any

import requests


BASE_URL = "https://qiita.com/api/v2"


def fetch_tag_items(
    tag_name: str, max_pages: int = 1, per_page: int = 100
) -> List[Dict[str, Any]]:
    """指定タグのアイテム一覧を複数ページに渡って取得する。

    注意: Qiita APIはレート制限があるため、ページ間で短いスリープを挟む。
    認証トークンが環境変数 QIITA_TOKEN にある場合は、それも利用する。
    """
    headers = {"Accept": "application/json"}
    token = os.getenv("QIITA_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    items: List[Dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/tags/{tag_name}/items"
        params = {"page": page, "per_page": per_page}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                break
            items.extend(data)
            # これ以上無い場合は早期終了
            if len(data) < per_page:
                break
        except requests.RequestException:
            # 通信失敗時は中断して手元の分だけ返す
            break
        time.sleep(0.4)
    return items


def fetch_search_items(
    query: str, max_pages: int = 1, per_page: int = 100
) -> List[Dict[str, Any]]:
    """検索クエリでアイテムを複数ページ取得する。

    例: "tag:Python stocks:>20 created:>=2024-01-01"
    """
    headers = {"Accept": "application/json"}
    token = os.getenv("QIITA_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    items: List[Dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/items"
        params = {"page": page, "per_page": per_page, "query": query}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                break
            items.extend(data)
            if len(data) < per_page:
                break
        except requests.RequestException:
            break
        time.sleep(0.4)
    return items
