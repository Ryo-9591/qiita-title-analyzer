from flask import Flask
from flask_cors import CORS

from .routes import api
from .services.analysis_cache import ensure_data_dir, build_cache_if_needed


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    # 起動時にキャッシュを準備
    data_dir = ensure_data_dir(__file__)
    build_cache_if_needed(data_dir)

    # ルート登録
    app.register_blueprint(api)
    return app


# gunicornエントリポイント
app = create_app()
