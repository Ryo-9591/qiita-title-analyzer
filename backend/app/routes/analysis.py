import json
import os
from flask import jsonify

from . import api
from ..services.analysis_cache import (
    ensure_data_dir,
    build_cache_if_needed,
    get_cache_path,
)


@api.get("/api/analysis")
def get_analysis():
    data_dir = ensure_data_dir(__file__)
    cache_path = get_cache_path(data_dir)
    if not os.path.exists(cache_path):
        return jsonify({"error": "analysis not ready"}), 503
    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)


@api.post("/api/rebuild")
def rebuild():
    data_dir = ensure_data_dir(__file__)
    build_cache_if_needed(data_dir, force=True)
    cache_path = get_cache_path(data_dir)
    if not os.path.exists(cache_path):
        return jsonify({"error": "failed to rebuild"}), 500
    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)
