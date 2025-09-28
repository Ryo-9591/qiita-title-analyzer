import requests
import pandas as pd
import MeCab
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import os
import time

# 定数設定
TOP_PERCENT = 0.2  # バズの定義：いいね数上位20%の記事
PER_PAGE = 100  # 1ページあたりの記事数
PAGE_COUNT = 5  # 取得するページ数
FONT_PATH = (
    "/usr/share/fonts/opentype/ipaexgothic/ipaexgothic.ttf"  # IPAexGothicフォントパス
)

# Qiita APIトークン（環境変数から取得）
QIITA_TOKEN = os.environ.get("QIITA_TOKEN", "")

# ストップワードリスト
STOP_WORDS = [
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
    "です",
    "である",
    "です",
    "だ",
    "である",
    "です",
    "ます",
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
]


def fetch_qiita_articles():
    """
    Qiita APIから記事データを取得する

    Returns:
        list: 記事データのリスト
    """
    # ローカル変数としてトークンを管理
    current_token = QIITA_TOKEN

    all_articles = []
    base_url = "https://qiita.com/api/v2/items"

    # ヘッダーを設定
    headers = {}
    if current_token:
        headers["Authorization"] = f"Bearer {current_token}"

    for page in range(1, PAGE_COUNT + 1):
        params = {"page": page, "per_page": PER_PAGE, "sort": "like"}

        try:
            response = requests.get(
                base_url, params=params, headers=headers, timeout=10
            )
            response.raise_for_status()
            articles = response.json()
            all_articles.extend(articles)

            # APIレート制限を回避するため、リクエスト間隔を追加
            if page < PAGE_COUNT:
                sleep_time = 0.5 if current_token else 2.0  # トークンがある場合は短縮
                time.sleep(sleep_time)

        except requests.exceptions.RequestException as e:
            # 401エラーの場合は認証に問題がある可能性
            if "401" in str(e) and current_token:
                # ヘッダーから認証情報を削除
                headers = {}
                current_token = ""  # ローカル変数を更新
                continue

            continue

    return all_articles


def extract_buzz_titles(articles):
    """
    取得したデータからバズった記事のタイトルを抽出する

    Args:
        articles (list): 記事データのリスト

    Returns:
        list: バズった記事のタイトルリスト
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


def analyze_titles(titles):
    """
    タイトルを形態素解析して単語を集計する

    Args:
        titles (list): タイトルのリスト

    Returns:
        pd.DataFrame: 単語と頻度のDataFrame
    """
    # MeCabオブジェクトを初期化（辞書パスを明示的に指定）
    import os

    dicdir = os.environ.get("MECAB_DICDIR", "/var/lib/mecab/dic/debian")

    # 分かち書き結果から直接単語を抽出
    mecab = MeCab.Tagger(f"-Owakati -d {dicdir}")
    all_words = []

    for title in titles:
        parsed = mecab.parse(title)
        words = parsed.strip().split()

        for word in words:
            # 文字化けチェックとフィルタリング
            import re

            # サロゲート文字や制御文字を除去
            clean_word = re.sub(r"[\ud800-\udfff]", "", word)

            # 基本的なフィルタリング
            if (
                len(clean_word) > 1
                and clean_word not in STOP_WORDS
                and not clean_word.isdigit()  # 数字を除外
                and clean_word
                not in ["【", "】", "(", ")", "「", "」", ":", ";", ".", ","]
                and clean_word.isprintable()  # 表示可能文字のみ
            ):  # 記号を除外
                all_words.append(clean_word)

    # 単語の出現頻度を集計
    word_counts = Counter(all_words)

    # DataFrameに変換
    word_df = pd.DataFrame(
        [
            {"word": word, "frequency": count}
            for word, count in word_counts.most_common()
        ]
    )

    return word_df


def create_wordcloud(word_df):
    """
    WordCloud画像を生成する

    Args:
        word_df (pd.DataFrame): 単語と頻度のDataFrame
    """
    if word_df.empty:
        return

    # 単語と頻度の辞書を作成
    word_freq = dict(zip(word_df["word"], word_df["frequency"]))

    # フォントファイルの存在確認
    import os
    import glob

    # 複数のフォントパスを試す
    font_candidates = [
        "/usr/share/fonts/opentype/ipaexgothic/ipaexgothic.ttf",
        "/usr/share/fonts/truetype/ipaexgothic/ipaexgothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    ]

    # フォントファイルを検索
    font_path = None
    for candidate in font_candidates:
        if os.path.exists(candidate):
            font_path = candidate
            break

    # 見つからない場合は、システムフォントを検索
    if not font_path:
        # システムフォントを検索
        system_fonts = glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)
        system_fonts.extend(glob.glob("/usr/share/fonts/**/*.ttc", recursive=True))

        if system_fonts:
            font_path = system_fonts[0]
        else:
            font_path = None

    # WordCloudの設定
    wordcloud_config = {
        "width": 800,
        "height": 400,
        "background_color": "white",
        "max_words": 100,
        "colormap": "viridis",
    }

    # フォントパスが存在する場合のみ設定
    if font_path:
        wordcloud_config["font_path"] = font_path

    wordcloud = WordCloud(**wordcloud_config).generate_from_frequencies(word_freq)

    # matplotlibの日本語フォント設定
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    # 日本語フォントを設定
    if font_path:
        try:
            font_prop = fm.FontProperties(fname=font_path)
            plt.rcParams["font.family"] = font_prop.get_name()
        except:
            plt.rcParams["font.family"] = "DejaVu Sans"
    else:
        # フォールバック: システムの日本語フォントを検索
        try:
            japanese_fonts = [
                f.name
                for f in fm.fontManager.ttflist
                if "Noto" in f.name or "IPA" in f.name
            ]
            if japanese_fonts:
                plt.rcParams["font.family"] = japanese_fonts[0]
            else:
                plt.rcParams["font.family"] = "DejaVu Sans"
        except:
            plt.rcParams["font.family"] = "DejaVu Sans"

    # フォントサイズとスタイルを設定
    plt.rcParams["font.size"] = 12
    plt.rcParams["axes.unicode_minus"] = False

    # 画像を保存
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")

    # タイトルを設定（フォントプロパティを直接指定）
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
    plt.savefig("/app/output/wordcloud_qiita.png", dpi=300, bbox_inches="tight")
    plt.close()


def export_results(word_df):
    """
    分析結果をCSVファイルに出力する

    Args:
        word_df (pd.DataFrame): 単語と頻度のDataFrame
    """
    if word_df.empty:
        return

    # 文字化けした文字を除去
    import re

    def clean_text(text):
        # サロゲート文字や制御文字を除去
        return re.sub(r"[\ud800-\udfff]", "", str(text))

    # DataFrameの単語列をクリーニング
    word_df_clean = word_df.copy()
    word_df_clean["word"] = word_df_clean["word"].apply(clean_text)

    # 空の単語を除去
    word_df_clean = word_df_clean[word_df_clean["word"].str.len() > 0]

    # CSVファイルに保存（エラー処理付き）
    try:
        word_df_clean.to_csv(
            "/app/output/analysis_results.csv",
            index=False,
            encoding="utf-8-sig",
            errors="replace",  # エンコードできない文字を置換
        )
    except Exception as e:
        # フォールバック: ASCIIエンコーディングで保存
        word_df_clean.to_csv(
            "/app/output/analysis_results.csv",
            index=False,
            encoding="ascii",
            errors="replace",
        )


def main():
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
        pass


if __name__ == "__main__":
    main()
