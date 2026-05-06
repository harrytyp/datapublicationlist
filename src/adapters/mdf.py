from .base import BaseAdapter
from ..discovery_models import AdapterResult, DatasetLink
from ..utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class MDFAdapter(BaseAdapter):
    """
    MDF Adapter — CURRENTLY NON-FUNCTIONAL.
    
    As of May 2026, the MDF Globus search index returns 404 Not Found errors,
    indicating the endpoint has changed or is no longer available. This adapter
    is disabled by default and should not be expected to return results.
    """
    name = "MDF"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        # Override enabled to False since this adapter doesn't work
        self.enabled = False
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://search.api.globus.org/v1/index/2ba8ad7d-5983-403a-b16c-94119d592b23"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent
        )

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        try:
            params = {"q": f'"{normalized_input}"', "limit": 50, "advanced": "true"}
            response = self.session.get("search", params=params)
            if not response: return AdapterResult(adapter_name=self.name, input_doi=doi)
            data = response.json()
            results = data.get("gmeta", [])
            for res in results:
                content = res.get("entries", [{}])[0].get("content", {})
                if normalized_input in str(content):
                    dataset_doi = content.get("mdf", {}).get("doi")
                    dataset_url = content.get("mdf", {}).get("source_url")
                    links.append(DatasetLink(
                        source_doi=doi,
                        dataset_doi=dataset_doi,
                        dataset_url=dataset_url,
                        relation_type="IsRelatedTo",
                        repository=self.name,
                        confidence="inferred",
                        raw=res
                    ))
        except Exception as e:
            return AdapterResult(adapter_name=self.name, input_doi=doi, errors=[str(e)])
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links)
