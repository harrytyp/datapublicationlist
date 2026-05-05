from .base import BaseAdapter
from ..models import AdapterResult, DatasetLink
from ..utils.doi import normalize_doi
from ..utils.http import HTTPSession
import logging

logger = logging.getLogger(__name__)

class MDFAdapter(BaseAdapter):
    """
    Adapter for the Materials Data Facility (MDF) API.
    
    Caveat: MDF does not publicly document a stable publication_doi metadata field. 
    This adapter uses free-text DOI matching and results should be manually validated.
    """
    name = "MDF"

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
            # MDF search often requires a complex query, 
            # here we use a free-text search for the DOI
            params = {
                "q": f'"{normalized_input}"',
                "limit": 50
            }
            
            # Note: MDF API endpoint for discovery might vary, 
            # using the provided base_url/search if applicable
            response = self.session.get("search", params=params)
            if not response:
                return AdapterResult(adapter_name=self.name, input_doi=doi)
                
            data = response.json()
            results = data.get("results", [])
            
            for res in results:
                # Basic validation: check if DOI appears in metadata
                meta_str = str(res)
                if normalized_input in meta_str:
                    dataset_doi = res.get("mdf", {}).get("doi")
                    dataset_url = res.get("mdf", {}).get("source_url")
                    
                    links.append(DatasetLink(
                        source_doi=doi,
                        dataset_doi=dataset_doi,
                        dataset_url=dataset_url,
                        relation_type="IsRelatedTo",
                        repository="MDF",
                        confidence="inferred",
                        raw=res
                    ))
                    
        except Exception as e:
            errors.append(str(e))
            
        return AdapterResult(
            adapter_name=self.name,
            input_doi=doi,
            links=links,
            errors=errors
        )
