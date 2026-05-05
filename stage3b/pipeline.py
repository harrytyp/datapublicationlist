from typing import List, Dict
import time
from .config import Stage3bConfig
from .models import AdapterResult, DatasetLink
from .adapters.doe_data_explorer import DOEDataExplorerAdapter
from .adapters.hepdata import HEPDataAdapter
from .adapters.nasa_ads import NASAADSAdapter
from .adapters.mdf import MDFAdapter
from .adapters.nomad_optimade import NOMADOptimadeAdapter

class Stage3bPipeline:
    """Orchestrator for Stage 3b dataset discovery adapters."""
    
    def __init__(self, config: Stage3bConfig):
        self.config = config
        self.adapters = [
            DOEDataExplorerAdapter(config.doe_data_explorer, config.http),
            HEPDataAdapter(config.hepdata, config.http),
            NASAADSAdapter(config.nasa_ads, config.http),
            MDFAdapter(config.mdf, config.http),
            NOMADOptimadeAdapter(config.nomad_optimade, config.http)
        ]

    def run(self, doi: str) -> List[AdapterResult]:
        """Call each adapter and collect results."""
        results = []
        for adapter in self.adapters:
            results.append(adapter.run(doi))
        return results

    def run_batch(self, dois: List[str]) -> Dict[str, List[AdapterResult]]:
        """Process a list of DOIs."""
        batch_results = {}
        for doi in dois:
            batch_results[doi] = self.run(doi)
            # Respect inter-request delay between articles if needed
            time.sleep(self.config.http.rate_limit_delay_seconds)
        return batch_results

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
