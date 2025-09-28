# Python 3.10の公式イメージを使用（より新しいベースイメージ）
FROM python:3.10-slim-bullseye

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    mecab \
    mecab-ipadic \
    libmecab-dev \
    fonts-ipaexfont \
    fonts-noto-cjk \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# MeCabの設定ファイルを作成（複数の場所に作成）
RUN echo "dicdir = /var/lib/mecab/dic/debian" > /etc/mecabrc && \
    echo "dicdir = /var/lib/mecab/dic/debian" > /usr/local/etc/mecabrc && \
    mkdir -p /usr/local/etc

# MeCabの辞書が正しくインストールされているか確認
RUN mecab-config --dicdir && ls -la /var/lib/mecab/dic/

# フォントファイルの確認と正しいパスの設定
RUN find /usr/share/fonts -name "*ipaex*" -type f && \
    find /usr/share/fonts -name "*gothic*" -type f && \
    find /usr/share/fonts -name "*noto*" -type f

# 環境変数でMeCabの設定を指定
ENV MECAB_DICDIR=/var/lib/mecab/dic/debian

# pipをアップグレード
RUN pip install --upgrade pip

# 作業ディレクトリの設定
WORKDIR /app

# 出力ディレクトリを作成
RUN mkdir -p /app/output

# Pythonライブラリのインストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# スクリプトのコピー
COPY qiita_analysis.py .

# コンテナ実行時のコマンド設定
CMD ["python", "qiita_analysis.py"]
