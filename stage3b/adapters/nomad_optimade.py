from .base import BaseAdapter
from ..models import AdapterResult, DatasetLink
from ..utils.doi import normalize_doi
from ..utils.http import HTTPSession
import logging

logger = logging.getLogger(__name__)

class NOMADOptimadeAdapter(BaseAdapter):
    """
    Adapter for the NOMAD / OPTIMADE API.
    
    Caveat: NOMAD's OPTIMADE implementation does not publicly document support 
    for filtering by references.doi. This adapter's coverage is uncertain.
    """
    name = "NOMAD_OPTIMADE"

    def __init__(self, config, http_config):
        super().__init__(config)
        self.session = HTTPSession(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            user_agent=http_config.user_agent
        )
        self.http_config = http_config

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        errors = []
        
        try:
            # 1. OPTIMADE references query
            params = {
                "filter": f'doi="{normalized_input}"',
                "page_limit": 25
            }
            
            try:
                response = self.session.get("optimade/references", params=params)
                if response and response.status_code == 200:
                    data = response.json()
                    refs = data.get("data", [])
                    for ref in refs:
                        # Extract relationship to structures
                        structs = ref.get("relationships", {}).get("structures", {}).get("data", [])
                        for struct in structs:
                            struct_id = struct.get("id")
                            links.append(DatasetLink(
                                source_doi=doi,
                                dataset_doi=None,
                                dataset_url=f"{self.config.base_url}/optimade/structures/{struct_id}",
                                relation_type="IsRelatedTo",
                                repository="NOMAD_OPTIMADE",
                                confidence="inferred",
                                raw=ref
                            ))
            except Exception as e:
                logger.info(f"[NOMAD_OPTIMADE] OPTIMADE references query failed or unsupported: {e}")

            # 2. NOMAD native API fallback
            if not links:
                params = {
                    "q": f"references.doi:{normalized_input}",
                    "pagination[page_size]": 25
                }
                response = self.session.get("api/v1/entries", params=params)
                if response and response.status_code == 200:
                    data = response.json()
                    entries = data.get("data", [])
                    for entry in entries:
                        entry_id = entry.get("entry_id")
                        # Check for dataset DOI in entry metadata
                        dataset_doi = entry.get("metadata", {}).get("doi")
                        
                        links.append(DatasetLink(
                            source_doi=doi,
                            dataset_doi=dataset_doi,
                            dataset_url=f"https://nomad-lab.eu/prod/v1/gui/entry/{entry_id}",
                            relation_type="IsRelatedTo",
                            repository="NOMAD_OPTIMADE",
                            confidence="inferred",
                            raw=entry
                        ))
                        
        except Exception as e:
            errors.append(str(e))
            
        return AdapterResult(
            adapter_name=self.name,
            input_doi=doi,
            links=links,
            errors=errors
        )
