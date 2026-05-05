import time
import logging
from typing import List, Dict, Any
from .discovery_models import AdapterResult, DatasetLink

from .adapters.openaire import OpenAIREAdapter
from .adapters.crossref import CrossrefAdapter
from .adapters.datacite import DataCiteAdapter
from .adapters.doe_dde import DOEDataExplorerAdapter
from .adapters.hepdata import HEPDataAdapter
from .adapters.nasa_ads import NASAADSAdapter
from .adapters.mdf import MDFAdapter
from .adapters.nomad import NOMADAdapter

logger = logging.getLogger(__name__)

class DiscoveryPipeline:
    """Unified orchestrator for all dataset discovery adapters."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        http_config = config.get("http_settings", {})
        
        # Create a helper for http settings
        class HttpSettings:
            def __init__(self, settings):
                self.user_agent = settings.get("user_agent", "publication-finder/1.0")
                self.retry_attempts = settings.get("retry_attempts", 3)
                self.retry_backoff_seconds = settings.get("retry_backoff_seconds", 2.0)
                self.rate_limit_delay_seconds = settings.get("rate_limit_delay_seconds", 1.0)
        
        self.http_settings = HttpSettings(http_config)
        
        # Initialize all adapters
        adapter_configs = config.get("adapters", {})
        self.adapters = [
            OpenAIREAdapter(adapter_configs.get("openaire", {}), self.http_settings),
            CrossrefAdapter(adapter_configs.get("crossref", {}), self.http_settings),
            DataCiteAdapter(adapter_configs.get("datacite", {}), self.http_settings),
            DOEDataExplorerAdapter(adapter_configs.get("doe_dde", {}), self.http_settings),
            HEPDataAdapter(adapter_configs.get("hepdata", {}), self.http_settings),
            NASAADSAdapter(adapter_configs.get("nasa_ads", {"enabled": False}), self.http_settings),
            MDFAdapter(adapter_configs.get("mdf", {"enabled": False}), self.http_settings),
            NOMADAdapter(adapter_configs.get("nomad", {"enabled": False}), self.http_settings),
        ]

    def run(self, doi: str) -> List[AdapterResult]:
        """Call each adapter and collect results."""
        results = []
        for adapter in self.adapters:
            results.append(adapter.run(doi))
        return results

    def get_all_links(self, doi: str) -> List[DatasetLink]:
        """Convenience method to get a flattened, deduplicated list of links."""
        all_results = self.run(doi)
        links_map = {} # (dataset_doi or dataset_url, repository) -> link
        
        for res in all_results:
            for link in res.links:
                # Use DOI if available, else URL as key
                key = (link.dataset_doi or link.dataset_url, link.repository)
                
                if key not in links_map:
                    links_map[key] = link
                else:
                    # Keep "confirmed" over "inferred"
                    existing = links_map[key]
                    if link.confidence == "confirmed" and existing.confidence == "inferred":
                        links_map[key] = link
        
        return list(links_map.values())
