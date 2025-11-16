import requests
import pandas as pd
import MeCab
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from collections import Counter
import os
import time
import re
import glob
from typing import List, Dict, Optional
from datetime import datetime

# 定数設定
TOP_PERCENT = 0.1  # バズの定義：いいね数上位10%の記事
PER_PAGE = 100  # 1ページあたりの記事数
PAGE_COUNT = 5  # 取得するページ数
MAX_WORDS = 100  # WordCloudの最大単語数
REQUEST_TIMEOUT = 10  # APIリクエストのタイムアウト
SLEEP_TIME_AUTH = 0.5  # 認証済みリクエストの待機時間
SLEEP_TIME_ANON = 2.0  # 匿名リクエストの待機時間

# フォント候補パス
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/ipaexgothic/ipaexgothic.ttf",
    "/usr/share/fonts/truetype/ipaexgothic/ipaexgothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
]

# Qiita APIトークン
QIITA_TOKEN = os.environ.get("QIITA_TOKEN", "")

# ストップワードリスト
STOP_WORDS = {
    "する",
    "できる",
    "この",
    "その",
    "ます",
    "です",
    "について",
    "Qiita",
    "記事",
    "〜",
    "【",
    "】",
    "!",
    "?",
    "(",
    ")",
    "こと",
    "ため",
    "よう",
    "とき",
    "もの",
    "など",
    "から",
    "まで",
    "である",
    "だ",
    "の",
    "に",
    "を",
    "は",
    "が",
    "で",
    "と",
    "も",
    "へ",
    "や",
    "て",
    "で",
    "に",
    "を",
    "は",
    "が",
    "と",
    "も",
}

# 除外記号
EXCLUDE_SYMBOLS = {"【", "】", "(", ")", "「", "」", ":", ";", ".", ",", "!", "?"}


def fetch_qiita_articles() -> List[Dict]:
    """
    Qiita APIから記事データを取得する

    Returns:
        List[Dict]: 記事データのリスト
    """
    current_token = QIITA_TOKEN
    all_articles = []
    base_url = "https://qiita.com/api/v2/items"

    # ヘッダーを設定
    headers = {"User-Agent": "Qiita-Analyzer/1.0"}
    if current_token:
        headers["Authorization"] = f"Bearer {current_token}"

    for page in range(1, PAGE_COUNT + 1):
        params = {"page": page, "per_page": PER_PAGE, "sort": "like"}

        try:
            response = requests.get(
                base_url, params=params, headers=headers, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            articles = response.json()
            all_articles.extend(articles)

            # APIレート制限を回避するため、リクエスト間隔を追加
            if page < PAGE_COUNT:
                sleep_time = SLEEP_TIME_AUTH if current_token else SLEEP_TIME_ANON
                time.sleep(sleep_time)

        except requests.exceptions.RequestException as e:
            # 401エラーの場合は認証に問題がある可能性
            if "401" in str(e) and current_token:
                # ヘッダーから認証情報を削除
                headers = {"User-Agent": "Qiita-Analyzer/1.0"}
                current_token = ""
                continue
            continue

    return all_articles


def extract_buzz_titles(articles: List[Dict]) -> List[str]:
    """
    取得したデータからバズった記事のタイトルを抽出する

    Args:
        articles (List[Dict]): 記事データのリスト

    Returns:
        List[str]: バズった記事のタイトルリスト
    """
    # DataFrameに変換
    df = pd.DataFrame(articles)

    if df.empty:
        return []

    # 上位10%の記事を抽出
    threshold = df["likes_count"].quantile(1 - TOP_PERCENT)
    buzz_articles = df[df["likes_count"] >= threshold]

    # タイトルを抽出
    buzz_titles = buzz_articles["title"].tolist()

    return buzz_titles


def analyze_titles(titles: List[str]) -> pd.DataFrame:
    """
    タイトルを形態素解析して単語を集計する

    Args:
        titles (List[str]): タイトルのリスト

    Returns:
        pd.DataFrame: 単語と頻度のDataFrame
    """
    if not titles:
        return pd.DataFrame(columns=["word", "frequency"])

    # MeCabオブジェクトを初期化
    dicdir = os.environ.get("MECAB_DICDIR", "/var/lib/mecab/dic/debian")
    mecab = MeCab.Tagger(f"-Owakati -d {dicdir}")

    all_words = []

    # 単語フィルタリング関数を事前定義
    def is_valid_word(word: str) -> bool:
        clean_word = re.sub(r"[\ud800-\udfff]", "", word)
        return (
            len(clean_word) > 1
            and clean_word not in STOP_WORDS
            and not clean_word.isdigit()
            and clean_word not in EXCLUDE_SYMBOLS
            and clean_word.isprintable()
        )

    # バッチ処理で効率化
    for title in titles:
        parsed = mecab.parse(title)
        words = parsed.strip().split()

        # リスト内包表記で高速化
        valid_words = [
            re.sub(r"[\ud800-\udfff]", "", word)
            for word in words
            if is_valid_word(word)
        ]
        all_words.extend(valid_words)

    # 単語の出現頻度を集計
    word_counts = Counter(all_words)

    # DataFrameに変換（上位単語のみ）
    top_words = word_counts.most_common(MAX_WORDS)
    word_df = pd.DataFrame(
        [{"word": word, "frequency": count} for word, count in top_words]
    )

    return word_df


def find_font_path() -> Optional[str]:
    """
    利用可能なフォントファイルのパスを検索する

    Returns:
        Optional[str]: フォントファイルのパス、見つからない場合はNone
    """
    # フォント候補を順番に確認
    for candidate in FONT_CANDIDATES:
        if os.path.exists(candidate):
            return candidate

    # システムフォントを検索
    try:
        system_fonts = glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)
        system_fonts.extend(glob.glob("/usr/share/fonts/**/*.ttc", recursive=True))
        if system_fonts:
            return system_fonts[0]
    except:
        pass

    return None


def create_wordcloud(word_df: pd.DataFrame) -> None:
    """
    WordCloud画像を生成する

    Args:
        word_df (pd.DataFrame): 単語と頻度のDataFrame
    """
    if word_df.empty:
        return

    # 単語と頻度の辞書を作成
    word_freq = dict(zip(word_df["word"], word_df["frequency"]))

    # フォントファイルを検索
    font_path = find_font_path()

    # WordCloudの設定
    wordcloud_config = {
        "width": 800,
        "height": 400,
        "background_color": "white",
        "max_words": MAX_WORDS,
        "colormap": "viridis",
    }

    # フォントパスが存在する場合のみ設定
    if font_path:
        wordcloud_config["font_path"] = font_path

    # WordCloud生成
    wordcloud = WordCloud(**wordcloud_config).generate_from_frequencies(word_freq)

    # matplotlibの日本語フォント設定
    try:
        if font_path:
            font_prop = fm.FontProperties(fname=font_path)
            plt.rcParams["font.family"] = font_prop.get_name()
        else:
            japanese_fonts = [
                f.name
                for f in fm.fontManager.ttflist
                if "Noto" in f.name or "IPA" in f.name
            ]
            plt.rcParams["font.family"] = (
                japanese_fonts[0] if japanese_fonts else "DejaVu Sans"
            )
    except:
        plt.rcParams["font.family"] = "DejaVu Sans"

    # フォント設定
    plt.rcParams["font.size"] = 12
    plt.rcParams["axes.unicode_minus"] = False

    # 画像を保存
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")

    # タイトルを設定
    if font_path:
        title_font = fm.FontProperties(fname=font_path, size=16, weight="bold")
        plt.title(
            "Qiitaバズタイトル分析 - WordCloud", fontproperties=title_font, pad=20
        )
    else:
        plt.title(
            "Qiitaバズタイトル分析 - WordCloud", fontsize=16, pad=20, fontweight="bold"
        )

    plt.tight_layout()

    # 日付別の出力ディレクトリを作成
    base_output_dir = "/app/output"
    date_dir = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(base_output_dir, date_dir)
    os.makedirs(output_dir, exist_ok=True)

    # 画像を保存
    plt.savefig(os.path.join(output_dir, "wordcloud_qiita.png"), dpi=300, bbox_inches="tight")
    plt.close()


def export_results(word_df: pd.DataFrame) -> None:
    """
    分析結果をCSVファイルに出力する

    Args:
        word_df (pd.DataFrame): 単語と頻度のDataFrame
    """
    if word_df.empty:
        return

    # 文字化けした文字を除去
    def clean_text(text: str) -> str:
        return re.sub(r"[\ud800-\udfff]", "", str(text))

    # DataFrameの単語列をクリーニング
    word_df_clean = word_df.copy()
    word_df_clean["word"] = word_df_clean["word"].apply(clean_text)

    # 空の単語を除去
    word_df_clean = word_df_clean[word_df_clean["word"].str.len() > 0]

    # 日付別の出力ディレクトリを作成
    base_output_dir = "/app/output"
    date_dir = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(base_output_dir, date_dir)
    os.makedirs(output_dir, exist_ok=True)

    # CSVファイルに保存（エラー処理付き）
    try:
        word_df_clean.to_csv(
            os.path.join(output_dir, "analysis_results.csv"),
            index=False,
            encoding="utf-8-sig",
            errors="replace",
        )
    except Exception:
        # フォールバック: ASCIIエンコーディングで保存
        word_df_clean.to_csv(
            os.path.join(output_dir, "analysis_results.csv"),
            index=False,
            encoding="ascii",
            errors="replace",
        )


def main() -> None:
    """
    メイン処理
    """
    try:
        # ステップ1: データ取得
        articles = fetch_qiita_articles()
        if not articles:
            return

        # ステップ2: バズ記事の抽出
        buzz_titles = extract_buzz_titles(articles)
        if not buzz_titles:
            return

        # ステップ3: 形態素解析と単語集計
        word_df = analyze_titles(buzz_titles)
        if word_df.empty:
            return

        # ステップ4: WordCloud生成と結果エクスポート
        create_wordcloud(word_df)
        export_results(word_df)

    except Exception as e:
        # エラーログを出力（本番環境では適切なログシステムを使用）
        print(f"エラーが発生しました: {e}")
        raise


if __name__ == "__main__":
    main()
