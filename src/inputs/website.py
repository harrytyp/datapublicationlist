from .base import BaseInputSource
from ..scraper import scrape_dois, PUBLICATIONS_URL
from typing import List, Dict, Any

class WebsiteInputSource(BaseInputSource):
    """Input source that scrapes the WordPress publication list."""
    name = "Website"

    def get_articles(self) -> List[Dict[str, Any]]:
        url = self.config.get("url", PUBLICATIONS_URL)
        use_cache = self.config.get("use_cache", True)
        return scrape_dois(url, use_cache=use_cache)
