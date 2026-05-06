from .base import BaseAdapter
from ..discovery_models import AdapterResult, DatasetLink
from ..utils import normalize_doi, HTTPSession
import logging
import requests

logger = logging.getLogger(__name__)

class NOMADAdapter(BaseAdapter):
    """
    NOMAD Adapter — EXPERIMENTAL AND CURRENTLY NON-FUNCTIONAL.
    
    As of May 2026, the NOMAD API v1 does not provide a documented or working
    method to search entries by publication DOI. The metadata.references field
    is not indexed for search queries, and no alternative publication-to-dataset
    linkage mechanism exists in the public API.
    
    This adapter is disabled by default and should not be expected to return results.
    """
    name = "NOMAD"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        # Override enabled to False since this adapter doesn't work
        self.enabled = False
        self.base_url = config.get("base_url", "https://nomad-lab.eu/prod/v1/api/v1")
        self.timeout = config.get("timeout_seconds", 20)
        self.user_agent = http_config.user_agent

    def _query_entries(self, doi_variant: str) -> list:
        """Query NOMAD entries using POST /entries/query with JSON body."""
        entries = []
        json_body = {
            "query": {
                "metadata.references": doi_variant
            },
            "pagination": {"page_size": 50},
            "required": {"include": ["entry_id", "upload_id", "metadata"]}
        }
        
        while True:
            try:
                response = requests.post(
                    f"{self.base_url}/entries/query",
                    json=json_body,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    logger.warning(f"NOMAD query failed: {response.status_code} - {response.text[:200]}")
                    break
                    
                data = response.json()
                batch = data.get("data", [])
                entries.extend(batch)
                
                # Cursor-based pagination
                next_value = data.get("pagination", {}).get("next_page_after_value")
                if not next_value:
                    break
                    
                json_body["pagination"]["page_after_value"] = next_value
                
            except Exception as e:
                logger.error(f"NOMAD query error: {e}")
                break
                
        return entries

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        
        try:
            # Try both bare DOI and prefixed form
            doi_variants = [
                normalized_input,
                f"https://doi.org/{normalized_input}"
            ]
            
            seen_entry_ids = set()
            
            for doi_variant in doi_variants:
                entries = self._query_entries(doi_variant)
                
                for entry in entries:
                    entry_id = entry.get("entry_id")
                    if not entry_id or entry_id in seen_entry_ids:
                        continue
                    seen_entry_ids.add(entry_id)
                    
                    # Extract dataset DOI if available
                    metadata = entry.get("metadata", {})
                    dataset_doi = metadata.get("doi")
                    
                    # NOMAD entry URL as fallback
                    dataset_url = f"https://nomad-lab.eu/prod/v1/gui/entry/{entry_id}"
                    
                    # Only create link if we have some identifier
                    if dataset_doi or dataset_url:
                        links.append(DatasetLink(
                            source_doi=doi,
                            dataset_doi=dataset_doi,
                            dataset_url=dataset_url,
                            relation_type="IsRelatedTo",
                            repository=self.name,
                            confidence="inferred",
                            raw=entry
                        ))
                        
        except Exception as e:
            return AdapterResult(adapter_name=self.name, input_doi=doi, errors=[str(e)])
            
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links)
