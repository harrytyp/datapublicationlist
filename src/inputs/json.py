from .base import BaseInputSource
from typing import List, Dict, Any
import json
import os

class JSONInputSource(BaseInputSource):
    """Input source that loads articles from a JSON file."""
    name = "JSON"

    def get_articles(self) -> List[Dict[str, Any]]:
        filepath = self.config.get("filepath")
        if not filepath or not os.path.exists(filepath):
            return []
            
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "articles" in data:
            return data["articles"]
        return []
