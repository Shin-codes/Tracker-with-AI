import json
import os
from typing import List, Dict, Optional

from .models import Shirt


def _default_data_path() -> str:
    # data directory is sibling to src
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(src_dir)
    data_dir = os.path.join(root_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "shirts.json")


def load_shirts(path_override: Optional[str] = None) -> List[Shirt]:
    path = path_override or _default_data_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [Shirt.from_dict(item) for item in data]
    except (OSError, json.JSONDecodeError):
        return []


def save_shirts(shirts: List[Shirt], path_override: Optional[str] = None) -> None:
    path = path_override or _default_data_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in shirts], f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Error saving data: {e}")


