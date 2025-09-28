from flask import Blueprint

api = Blueprint("api", __name__)

# 重要: この行でエンドポイント定義を読み込み、Blueprintに登録させる
from . import analysis  # noqa: E402,F401
