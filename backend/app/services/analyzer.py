from typing import Dict, Iterable
import re
from janome.tokenizer import Tokenizer


_tokenizer = Tokenizer()
_allowed_word_re = re.compile(r"^[\u3040-\u30FF\u4E00-\u9FFFa-zA-Z]+$")


def _is_hiragana_only(s: str) -> bool:
    return all("\u3040" <= ch <= "\u309f" for ch in s)


def analyze_titles(titles: Iterable[str]) -> Dict[str, int]:
    """タイトル群から名詞のみを抽出し、基本形ごとに頻度集計する。

    汎用動詞・助詞・助動詞・記号は除外。かなのみの短語も除外し、固有名詞・技術用語を優先。
    """
    freq: Dict[str, int] = {}
    for title in titles:
        if not title:
            continue
        for token in _tokenizer.tokenize(title):
            pos_all = token.part_of_speech.split(",")  # 例: 名詞,一般,*,*
            pos = pos_all[0]
            base = token.base_form or token.surface

            # 名詞のみ採用（助詞・助動詞・記号などは除外）
            if pos != "名詞" or not base:
                continue

            # ノイズ軽減フィルタ
            if len(base) <= 1:
                continue
            if _is_hiragana_only(base) and len(base) <= 2:
                # ひらがな2文字以下は除外（例: こと, ため などは別途STOPWORDSでも除外）
                continue
            if base.isdigit():
                continue
            if not _allowed_word_re.match(base):
                # 記号やハイフン、スラッシュ等を含む語は除外
                continue

            freq[base] = freq.get(base, 0) + 1
    return freq
