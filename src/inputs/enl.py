from .base import BaseInputSource
from ..enl_parser import extract_data_from_enl
from typing import List, Dict, Any
import os

class ENLInputSource(BaseInputSource):
    """Input source that extracts DOIs from EndNote library files."""
    name = "EndNote"

    def get_articles(self) -> List[Dict[str, Any]]:
        filepath = self.config.get("filepath")
        if not filepath or not os.path.exists(filepath):
            return []
            
        data = extract_data_from_enl(filepath)
        articles = []
        
        # Merge mappings and candidates
        all_dois = set(data.get("doi_to_url", {}).keys())
        all_dois.update(data.get("dataset_dois", []))
        
        for doi in all_dois:
            articles.append({
                "article_doi": doi,
                "title": f"EndNote Entry: {doi}",
                "authors": "Unknown",
                "year": "Unknown",
                "extra_data": {"enl_url": data.get("doi_to_url", {}).get(doi)}
            })
            
        return articles
