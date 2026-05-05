from .base import BaseInputSource
from typing import List, Dict, Any
import os
import re

class RISInputSource(BaseInputSource):
    """Input source that parses RIS files."""
    name = "RIS"

    def get_articles(self) -> List[Dict[str, Any]]:
        filepath = self.config.get("filepath")
        if not filepath or not os.path.exists(filepath):
            return []
            
        articles = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            # Entries are separated by ER - (End of Record)
            entries = re.split(r'\nER\s*-\s*', content)
            
            for entry in entries:
                if not entry.strip(): continue
                
                doi = self._get_tag(entry, "DO") or self._get_tag(entry, "DI")
                if not doi:
                    # Fallback: look for DOI in UR or other tags using regex
                    doi_match = re.search(r'10\.\d{4,}/[^\s\,\;\]\)\"]+', entry)
                    if doi_match:
                        doi = doi_match.group(0).rstrip(".")
                
                if doi:
                    articles.append({
                        "article_doi": doi.strip(),
                        "title": self._get_tag(entry, "T1") or self._get_tag(entry, "TI") or "Unknown Title",
                        "authors": ", ".join(self._get_tags(entry, "AU")),
                        "year": self._get_tag(entry, "PY") or self._get_tag(entry, "Y1") or "Unknown Year",
                        "extra_data": {"ris_type": self._get_tag(entry, "TY")}
                    })
        except Exception as e:
            from ..utils import logger
            logger.error(f"[RIS] Error parsing {filepath}: {e}")
            
        return articles

    def _get_tag(self, entry: str, tag: str) -> str:
        """Extract a single tag value."""
        match = re.search(rf'^{tag}\s*-\s*(.*)$', entry, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _get_tags(self, entry: str, tag: str) -> List[str]:
        """Extract multiple occurrences of a tag (e.g. authors)."""
        return re.findall(rf'^{tag}\s*-\s*(.*)$', entry, re.MULTILINE)
