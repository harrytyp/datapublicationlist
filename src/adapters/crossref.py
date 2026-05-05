from .base import BaseAdapter
from ..discovery_models import AdapterResult, DatasetLink
from ..utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class CrossrefAdapter(BaseAdapter):
    """Adapter for the Crossref REST API."""
    name = "Crossref"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://api.crossref.org/works"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent
        )
        self.dataset_relation_types = {
            "is-supplemented-by", "is-based-on", "has-part", "is-variant-form-of"
        }

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        
        try:
            response = self.session.get(
                normalized_input,
                rate_limit_delay=self.config.get("rate_limit_delay_seconds", 0.1),
                retries=self.http_config.retry_attempts,
                backoff=self.http_config.retry_backoff_seconds
            )
            
            if response and response.status_code == 200:
                work = response.json().get("message", {})
                relations = work.get("relation", {})
                
                for rel_type, targets in relations.items():
                    if rel_type in self.dataset_relation_types:
                        for target in targets:
                            if target.get("id-type") == "doi":
                                dataset_doi = target["id"].strip()
                                links.append(DatasetLink(
                                    source_doi=doi,
                                    dataset_doi=dataset_doi,
                                    relation_type=rel_type,
                                    repository="Crossref",
                                    confidence="confirmed",
                                    raw=target
                                ))
        except Exception as e:
            return AdapterResult(adapter_name=self.name, input_doi=doi, errors=[str(e)])
            
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links)
