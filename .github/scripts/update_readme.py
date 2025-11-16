#!/usr/bin/env python3
"""
READMEの先頭画像を更新するスクリプト
"""
import os
import re
from pathlib import Path
from datetime import datetime


def update_readme_image():
    """READMEの先頭画像を更新"""
    readme_path = Path("README.md")
    
    if not readme_path.exists():
        print("README.md not found")
        return False
    
    # 最新の日付フォルダを取得
    images_dir = Path("docs/images")
    if not images_dir.exists():
        print("docs/images directory not found")
        return False
    
    date_dirs = [
        d for d in images_dir.iterdir()
        if d.is_dir() and re.match(r'^\d{4}-\d{2}-\d{2}$', d.name)
    ]
    
    if not date_dirs:
        print("No date directories found")
        return False
    
    latest_date = sorted([d.name for d in date_dirs])[-1]
    
    # READMEを読み込む
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 既存の画像と日付行を削除（存在する場合）
    pattern = r'^!\[.*?\]\(docs/images/latest\.png\)\n\n\*最終更新:.*?\*\n\n'
    content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    # 先頭に画像と日付を追加
    header = f"![Qiita WordCloud](docs/images/latest.png)\n\n*最終更新: {latest_date}*\n\n"
    content = header + content
    
    # READMEを書き込む
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"README updated with latest date: {latest_date}")
    return True


if __name__ == "__main__":
    update_readme_image()

