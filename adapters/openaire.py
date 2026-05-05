from .base import BaseAdapter
from discovery_models import AdapterResult, DatasetLink
from utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class OpenAIREAdapter(BaseAdapter):
    """Adapter for the OpenAIRE Graph API."""
    name = "OpenAIRE"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://api.openaire.eu/graph/researchProducts"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent
        )

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        
        params = {
            "relatedDOI": normalized_input,
            "type": "dataset",
            "page": 1,
            "pageSize": 50,
        }
        
        try:
            response = self.session.get(
                "", # Base URL is the endpoint
                params=params,
                rate_limit_delay=self.config.get("rate_limit_delay_seconds", 1.0),
                retries=self.http_config.retry_attempts,
                backoff=self.http_config.retry_backoff_seconds
            )
            
            if response and response.status_code == 200:
                data = response.json()
                for item in data.get("results", []):
                    for pid in item.get("pids", []):
                        if pid.get("scheme") == "doi":
                            dataset_doi = pid.get("value")
                            if dataset_doi:
                                links.append(DatasetLink(
                                    source_doi=doi,
                                    dataset_doi=dataset_doi.strip(),
                                    relation_type="Unknown", # Graph API flatter response
                                    repository="OpenAIRE",
                                    confidence="confirmed",
                                    raw=item
                                ))
        except Exception as e:
            return AdapterResult(adapter_name=self.name, input_doi=doi, errors=[str(e)])
            
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links)
