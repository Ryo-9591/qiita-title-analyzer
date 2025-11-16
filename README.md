# Qiita Title Analyzer

Docker環境で動作するQiitaバズタイトル分析アプリケーションです。Qiita APIから記事データを取得し、形態素解析とWordCloudで可視化します。

## 機能

- Qiita APIを使用した記事データの取得（いいね数順）
- バズった記事（いいね数上位10%）の抽出
- MeCabによる形態素解析と単語頻度分析
- WordCloudによる日本語対応の可視化
- 分析結果のCSV出力
- Docker環境での簡単実行

## 技術スタック

- **コンテナ**: Docker
- **言語**: Python 3.10
- **データ取得**: requests (Qiita API)
- **データ処理**: pandas
- **形態素解析**: mecab-python3
- **可視化**: wordcloud
- **フォント**: IPAexGothic (日本語表示用)

## ファイル構成

```
├── Dockerfile              # Dockerイメージ定義
├── docker-compose.yml      # Docker Compose設定
├── requirements.txt        # Python依存関係
├── qiita_analysis.py      # メイン分析スクリプト
├── output/                # 出力ファイル格納ディレクトリ
│   └── YYYY-MM-DD/           # 生成日のサブフォルダ
│       ├── wordcloud_qiita.png    # WordCloud画像
│       └── analysis_results.csv   # 分析結果CSV
└── README.md              # このファイル
```

## 使用方法

### 1. Dockerイメージのビルドと実行

```bash
# Docker Composeでビルド・実行
docker-compose up --build

# または、Dockerコマンドで直接実行
docker build -t qiita-analyzer .
docker run -v $(pwd)/output:/app/output qiita-analyzer
```

### 1.1. Qiita APIトークンの設定（推奨）

APIレート制限を回避するために、Qiita APIトークンを設定することをお勧めします：

1. [Qiitaの設定ページ](https://qiita.com/settings/tokens)でアクセストークンを生成
2. `docker-compose.yml`の環境変数セクションを編集：

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - QIITA_TOKEN=your_qiita_token_here  # コメントアウトを外して設定
```

3. または、Dockerコマンドで直接指定：

```bash
docker run -v $(pwd)/output:/app/output -e QIITA_TOKEN=your_token qiita-analyzer
```

**トークン設定の効果：**
- レート制限が緩和される（1時間あたり1000リクエスト）
- リクエスト間隔が短縮される（0.5秒）
- より安定したAPIアクセス

### 2. 出力ファイルの確認

実行後、`output/YYYY-MM-DD` ディレクトリ（生成日ごと）に以下のファイルが生成されます：

- `wordcloud_qiita.png`: WordCloud画像
- `analysis_results.csv`: 単語頻度分析結果

例:

```
output/
  2025-11-16/
    wordcloud_qiita.png
    analysis_results.csv
```

### 3. 設定の変更

`qiita_analysis.py`の定数で以下の設定を変更できます：

```python
TOP_PERCENT = 0.1    # バズの定義（上位10%）
PER_PAGE = 100       # 1ページあたりの記事数
PAGE_COUNT = 5       # 取得するページ数
```

## 分析の流れ

1. **データ取得**: Qiita APIからいいね数順で記事を取得
2. **バズ記事抽出**: いいね数上位10%の記事をフィルタリング
3. **形態素解析**: MeCabでタイトルを解析し、名詞・形容詞・動詞を抽出
4. **単語集計**: ストップワードを除去し、頻度を集計
5. **可視化**: WordCloud画像を生成
6. **結果出力**: CSVファイルに分析結果を保存

## ライセンス

MIT License

## GitHub Actions での自動実行

このリポジトリには、毎日1回（UTC 00:00）自動で分析を実行するワークフローが含まれています（`.github/workflows/generate-wordcloud.yml`）。

設定手順:

1. GitHub リポジトリの Settings → Secrets and variables → Actions → New repository secret から以下を登録
   - `QIITA_TOKEN`: Qiita API トークン（任意だが推奨）
2. ワークフローは既定で毎日実行され、生成物は Actions の Artifacts に `qiita-wordcloud-output` としてアップロードされます。

手動実行も可能です（Actions タブ → Generate Qiita WordCloud Daily → Run workflow）。

