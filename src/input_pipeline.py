import logging
from typing import List, Dict, Any
from .inputs.website import WebsiteInputSource
from .inputs.json import JSONInputSource
from .inputs.enl import ENLInputSource
from .inputs.ris import RISInputSource

logger = logging.getLogger(__name__)

class InputPipeline:
    """Unified orchestrator for all article input sources."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        input_configs = config.get("input_sources", {})
        
        self.sources = []
        
        # Initialize sources based on config
        if "website" in input_configs:
            self.sources.append(WebsiteInputSource(input_configs["website"]))
        if "json" in input_configs:
            self.sources.append(JSONInputSource(input_configs["json"]))
        if "enl" in input_configs:
            self.sources.append(ENLInputSource(input_configs["enl"]))
        if "ris" in input_configs:
            self.sources.append(RISInputSource(input_configs["ris"]))

    def collect_articles(self) -> List[Dict[str, Any]]:
        """Run all enabled sources and deduplicate DOIs."""
        all_articles = []
        seen_dois = set()
        
        for source in self.sources:
            articles = source.run()
            for art in articles:
                doi = art.get("article_doi")
                if not doi: continue
                
                normalized_doi = doi.strip().lower()
                if normalized_doi not in seen_dois:
                    all_articles.append(art)
                    seen_dois.add(normalized_doi)
                else:
                    # Optional: Merge metadata if duplicate found
                    pass
                    
        logger.info(f"Collected total of {len(all_articles)} unique articles from all sources.")
        return all_articles
