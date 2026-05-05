from .base import BaseAdapter
from ..models import AdapterResult, DatasetLink
from ..utils.doi import normalize_doi, is_valid_doi
from ..utils.http import HTTPSession
import logging
import os
import re

logger = logging.getLogger(__name__)

class NASAADSAdapter(BaseAdapter):
    """
    Adapter for the NASA ADS / SciX API.
    
    Caveat: ADS link resolver exposes heterogeneous link types including mirror links, 
    article PDFs, and data links. The 'data' link type filters for dataset-like links, 
    but the field structure is marked internal and subject to change. 
    Treat results as enrichment, not authoritative.
    """
    name = "NASA_ADS"

    def __init__(self, config, http_config):
        super().__init__(config)
        self.session = HTTPSession(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            user_agent=http_config.user_agent,
            api_token=config.api_token
        )
        self.http_config = http_config

    def fetch(self, doi: str) -> AdapterResult:
        if not self.config.api_token:
            return AdapterResult(
                adapter_name=self.name,
                input_doi=doi,
                errors=["ADS_API_TOKEN not set"]
            )
            
        normalized_input = normalize_doi(doi)
        links = []
        errors = []
        
        try:
            # 1. Bibcode lookup
            params = {
                "q": f"doi:{normalized_input}",
                "fl": "bibcode,title,identifier",
                "rows": 5
            }
            
            response = self.session.get("search/query", params=params)
            if not response:
                return AdapterResult(adapter_name=self.name, input_doi=doi)
                
            data = response.json()
            docs = data.get("response", {}).get("docs", [])
            if not docs:
                return AdapterResult(adapter_name=self.name, input_doi=doi)
            
            bibcode = docs[0].get("bibcode")
            
            # 2. Resolver call
            res_response = self.session.get(f"resolver/{bibcode}/data")
            if not res_response:
                return AdapterResult(adapter_name=self.name, input_doi=doi)
                
            res_data = res_response.json()
            res_links = res_data.get("links", [])
            
            for link in res_links:
                if link.get("type") == "data":
                    url = link.get("url")
                    title = link.get("title")
                    
                    # DOI extraction from URL
                    dataset_doi = None
                    doi_match = re.search(r'10\.\d{4,}/[^\s\,\;\]\)\"]+', url)
                    if doi_match:
                        dataset_doi = doi_match.group(0).rstrip(".")
                    
                    links.append(DatasetLink(
                        source_doi=doi,
                        dataset_doi=dataset_doi,
                        dataset_url=url,
                        relation_type="IsRelatedTo",
                        repository="NASA_ADS",
                        confidence="inferred",
                        raw=link
                    ))
                    
        except Exception as e:
            errors.append(str(e))
            
        return AdapterResult(
            adapter_name=self.name,
            input_doi=doi,
            links=links,
            errors=errors
        )
