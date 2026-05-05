from .base import BaseAdapter
from discovery_models import AdapterResult, DatasetLink
from utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class DOEDataExplorerAdapter(BaseAdapter):
    """Adapter for the DOE Data Explorer (DDE) API."""
    name = "DOE_DDE"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://www.osti.gov/dataexplorer/api/v1"),
            timeout=config.get("timeout_seconds", 15),
            user_agent=http_config.user_agent
        )

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        errors = []
        page = 1
        max_rows = self.config.get("max_results", 100)
        
        while True:
            params = {"q": normalized_input, "rows": max_rows, "page": page}
            try:
                response = self.session.get(
                    "records", 
                    params=params, 
                    rate_limit_delay=self.config.get("rate_limit_delay_seconds", 1.0),
                    retries=self.http_config.retry_attempts,
                    backoff=self.http_config.retry_backoff_seconds
                )
                
                if not response: break
                data = response.json()
                if not isinstance(data, list): break
                
                for record in data:
                    related_ids = record.get("related_identifiers", [])
                    matched_relation = None
                    for rel in related_ids:
                        if rel.get("identifier_type") == "DOI":
                            if normalize_doi(rel.get("related_identifier")) == normalized_input:
                                matched_relation = rel.get("relation", "Unknown")
                                break
                    
                    if matched_relation:
                        dataset_doi = record.get("doi")
                        osti_id = record.get("osti_id")
                        dataset_url = f"https://www.osti.gov/dataexplorer/biblio/{osti_id}" if osti_id else None
                        
                        links.append(DatasetLink(
                            source_doi=doi,
                            dataset_doi=dataset_doi,
                            dataset_url=dataset_url,
                            relation_type=matched_relation,
                            repository=self.name,
                            confidence="confirmed",
                            raw={"related_identifiers": related_ids}
                        ))
                
                if len(data) < max_rows: break
                page += 1
            except Exception as e:
                errors.append(str(e))
                break
                
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links, errors=errors)
