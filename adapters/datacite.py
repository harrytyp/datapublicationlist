from .base import BaseAdapter
from discovery_models import AdapterResult, DatasetLink
from utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class DataCiteAdapter(BaseAdapter):
    """Adapter for the DataCite REST API."""
    name = "DataCite"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://api.datacite.org/dois"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent
        )

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        errors = []
        page = 1
        
        while True:
            params = {
                "query": f'relatedIdentifiers.relatedIdentifier:"{normalized_input}"',
                "resource-type-id": "dataset",
                "page[size]": 50,
                "page[number]": page,
            }
            
            try:
                response = self.session.get(
                    "",
                    params=params,
                    rate_limit_delay=self.config.get("rate_limit_delay_seconds", 0.1),
                    retries=self.http_config.retry_attempts,
                    backoff=self.http_config.retry_backoff_seconds
                )
                
                if not response or response.status_code != 200:
                    break
                    
                data = response.json()
                items = data.get("data", [])
                for item in items:
                    ds_doi = item.get("attributes", {}).get("doi", "")
                    if ds_doi:
                        links.append(DatasetLink(
                            source_doi=doi,
                            dataset_doi=ds_doi.strip(),
                            relation_type="Unknown", # DataCite query is a reverse lookup
                            repository="DataCite",
                            confidence="confirmed",
                            raw=item
                        ))
                
                total_pages = data.get("meta", {}).get("totalPages", 1)
                if page >= total_pages:
                    break
                page += 1
                
            except Exception as e:
                errors.append(str(e))
                break
                
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links, errors=errors)
