from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseInputSource(ABC):
    """Abstract base class for all publication input sources."""
    
    name: str = "Base"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def get_articles(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from the source.
        Returns a list of dicts with at least:
        {
            "article_doi": "...",
            "title": "...",
            "authors": "...",
            "year": "...",
            "extra_data": {} # Optional metadata specific to the source
        }
        """
        pass

    def run(self) -> List[Dict[str, Any]]:
        """Calls get_articles() if enabled."""
        if not self.enabled:
            return []
        
        try:
            logger.info(f"[{self.name}] Fetching articles...")
            return self.get_articles()
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching articles: {e}")
            return []
