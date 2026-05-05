from .base import BaseAdapter
from ..discovery_models import AdapterResult, DatasetLink
from ..utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class MDFAdapter(BaseAdapter):
    """Adapter for the Materials Data Facility (MDF) API (Experimental)."""
    name = "MDF"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://acdc.alcf.anl.gov/mdf"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent
        )

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        try:
            params = {"q": f'"{normalized_input}"', "limit": 50}
            response = self.session.get("search", params=params)
            if not response: return AdapterResult(adapter_name=self.name, input_doi=doi)
            results = response.json().get("results", [])
            for res in results:
                if normalized_input in str(res):
                    dataset_doi = res.get("mdf", {}).get("doi")
                    dataset_url = res.get("mdf", {}).get("source_url")
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
