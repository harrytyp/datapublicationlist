import logging
import os
from typing import List, Dict, Any
from .inputs.website import WebsiteInputSource
from .inputs.json import JSONInputSource
from .inputs.enl import ENLInputSource
from .inputs.ris import RISInputSource

logger = logging.getLogger(__name__)

class InputPipeline:
    """Orchestrator that automatically discovers and processes input files."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.input_dir = config.get("input_dir", "inputs")
        input_configs = config.get("input_sources", {})
        
        self.sources = []
        
        # 1. Initialize permanent sources (like website)
        if input_configs.get("website", {}).get("enabled", True):
            self.sources.append(WebsiteInputSource(input_configs.get("website", {})))
        
        # 2. Automatically discover files in the inputs directory
        if os.path.exists(self.input_dir):
            for filename in os.listdir(self.input_dir):
                filepath = os.path.join(self.input_dir, filename)
                if not os.path.isfile(filepath):
                    continue
                    
                ext = filename.lower().split('.')[-1]
                
                if ext == "enl":
                    logger.info(f"Auto-discovered EndNote file: {filename}")
                    self.sources.append(ENLInputSource({"filepath": filepath}))
                elif ext == "ris":
                    logger.info(f"Auto-discovered RIS file: {filename}")
                    self.sources.append(RISInputSource({"filepath": filepath}))
                elif ext == "json":
                    # Skip config.json if it was somehow put there
                    if filename == "config.json": continue
                    logger.info(f"Auto-discovered JSON file: {filename}")
                    self.sources.append(JSONInputSource({"filepath": filepath}))

    def collect_articles(self) -> List[Dict[str, Any]]:
        """Run all discovered sources and deduplicate DOIs."""
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
                    # If we find a duplicate, we might want to merge extra_data (e.g. enl_url)
                    for existing in all_articles:
                        if existing["article_doi"].strip().lower() == normalized_doi:
                            if "extra_data" not in existing: existing["extra_data"] = {}
                            if "extra_data" in art:
                                existing["extra_data"].update(art["extra_data"])
                            break
                    
        logger.info(f"Collected total of {len(all_articles)} unique articles from all sources.")
        return all_articles
