![Qiita WordCloud](docs/images/latest.png)

*最終更新: 2025-11-18*

# Qiita Title Analyzer

Qiita APIから記事データを取得し、バズった記事のタイトルを形態素解析してWordCloudで可視化するDockerアプリケーション。

## 主な機能

- Qiita APIからいいね数順で記事を取得
- バズ記事（いいね数上位10%）のタイトルを抽出
- MeCabによる形態素解析と単語頻度分析
- WordCloudによる日本語対応の可視化
- GitHub Actionsによる毎日の自動実行と画像更新

## 使用方法

### ローカル実行

```bash
docker-compose up --build
```

出力先: `docs/images/YYYY-MM-DD/`（日付別フォルダ）と `docs/images/latest.png`（最新画像）

### Qiita APIトークンの設定（推奨）

`docker-compose.yml` または環境変数で `QIITA_TOKEN` を設定すると、APIレート制限が緩和されます。

```bash
docker run -v $(pwd)/docs/images:/app/docs/images -e QIITA_TOKEN=your_token qiita-analyzer
```

## GitHub Actions での自動実行

毎日UTC 00:00（JST 09:00）に自動実行され、以下の処理が行われます：

- 分析の実行と画像生成
- `docs/images/` への保存（日付別フォルダ + `latest.png`）
- READMEの先頭画像を自動更新
- 変更をリポジトリに自動コミット

**設定**: GitHub Secretsに `QIITA_TOKEN` を登録（任意だが推奨）

手動実行も可能（Actions タブ → Generate Qiita WordCloud Daily → Run workflow）

## 出力ファイル

- `docs/images/latest.png`: 最新のWordCloud画像（README表示用）
- `docs/images/YYYY-MM-DD/wordcloud_qiita.png`: 日付別のWordCloud画像
- `docs/images/YYYY-MM-DD/analysis_results.csv`: 単語頻度分析結果

## ライセンス

MIT License
