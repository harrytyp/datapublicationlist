from .base import BaseAdapter
from discovery_models import AdapterResult, DatasetLink
from utils import normalize_doi, HTTPSession
import logging
import re

logger = logging.getLogger(__name__)

class NASAADSAdapter(BaseAdapter):
    """Adapter for the NASA ADS / SciX API (Experimental)."""
    name = "NASA_ADS"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://api.adsabs.harvard.edu/v1"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent,
            api_token=config.get("api_token")
        )

    def fetch(self, doi: str) -> AdapterResult:
        if not self.config.get("api_token"):
            return AdapterResult(adapter_name=self.name, input_doi=doi, errors=["ADS_API_TOKEN not set"])
            
        normalized_input = normalize_doi(doi)
        links = []
        try:
            params = {"q": f"doi:{normalized_input}", "fl": "bibcode", "rows": 5}
            response = self.session.get("search/query", params=params)
            if not response: return AdapterResult(adapter_name=self.name, input_doi=doi)
            docs = response.json().get("response", {}).get("docs", [])
            if not docs: return AdapterResult(adapter_name=self.name, input_doi=doi)
            
            bibcode = docs[0].get("bibcode")
            res_response = self.session.get(f"resolver/{bibcode}/data")
            if not res_response: return AdapterResult(adapter_name=self.name, input_doi=doi)
                
            res_links = res_response.json().get("links", [])
            for link in res_links:
                if link.get("type") == "data":
                    url = link.get("url")
                    dataset_doi = None
                    doi_match = re.search(r'10\.\d{4,}/[^\s\,\;\]\)\"]+', url)
                    if doi_match: dataset_doi = doi_match.group(0).rstrip(".")
                    
                    links.append(DatasetLink(
                        source_doi=doi,
                        dataset_doi=dataset_doi,
                        dataset_url=url,
                        relation_type="IsRelatedTo",
                        repository=self.name,
                        confidence="inferred",
                        raw=link
                    ))
        except Exception as e:
            return AdapterResult(adapter_name=self.name, input_doi=doi, errors=[str(e)])
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links)
