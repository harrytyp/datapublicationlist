from .base import BaseAdapter
from ..models import AdapterResult, DatasetLink
from ..utils.doi import normalize_doi
from ..utils.http import HTTPSession
import logging

logger = logging.getLogger(__name__)

class HEPDataAdapter(BaseAdapter):
    """Adapter for the HEPData API."""
    name = "HEPData"

    def __init__(self, config, http_config, emit_table_level_dois: bool = True):
        super().__init__(config)
        self.session = HTTPSession(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            user_agent=http_config.user_agent
        )
        self.http_config = http_config
        self.emit_table_level_dois = emit_table_level_dois

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        errors = []
        
        page = 1
        while page <= 10:
            params = {
                "q": normalized_input,
                "format": "json",
                "size": 25,
                "page": page
            }
            
            try:
                response = self.session.get(
                    "search/", 
                    params=params,
                    rate_limit_delay=self.config.rate_limit_delay_seconds,
                    retries=self.http_config.retry_attempts,
                    backoff=self.http_config.retry_backoff_seconds
                )
                
                if not response:
                    break
                    
                data = response.json()
                results = data.get("results", [])
                if not results:
                    break
                
                for hit in results:
                    # Check if search hit confirms DOI
                    # Search hits have limited info, so we often need to resolve the record
                    inspire_id = hit.get("inspire_id")
                    if not inspire_id:
                        continue
                    
                    # Resolve record
                    rec_response = self.session.get(f"record/ins{inspire_id}", params={"format": "json"})
                    if not rec_response:
                        continue
                        
                    rec_data = rec_response.json()
                    
                    # Confirm publication DOI
                    pub_doi = normalize_doi(rec_data.get("publication_doi", ""))
                    if not pub_doi:
                        # Fallback check
                        pub_info = rec_data.get("publication_info", {})
                        pub_doi = normalize_doi(pub_info.get("doi", ""))
                    
                    if pub_doi == normalized_input:
                        # Record-level DOI
                        hepdata_doi = rec_data.get("hepdata_doi")
                        links.append(DatasetLink(
                            source_doi=doi,
                            dataset_doi=hepdata_doi,
                            dataset_url=f"https://www.hepdata.net/record/ins{inspire_id}",
                            relation_type="IsSupplementTo",
                            repository="HEPData",
                            confidence="confirmed",
                            raw={"inspire_id": inspire_id, "hepdata_doi": hepdata_doi}
                        ))
                        
                        # Table-level DOIs
                        if self.emit_table_level_dois:
                            tables = rec_data.get("resources", []) or rec_data.get("tables", [])
                            for table in tables:
                                table_doi = table.get("doi")
                                if table_doi:
                                    links.append(DatasetLink(
                                        source_doi=doi,
                                        dataset_doi=table_doi,
                                        dataset_url=None, # Usually nested in record URL
                                        relation_type="HasPart",
                                        repository="HEPData",
                                        confidence="confirmed",
                                        raw={"table_id": table.get("id")}
                                    ))
                
                if len(results) < 25:
                    break
                page += 1
                
            except Exception as e:
                errors.append(str(e))
                break
                
        return AdapterResult(
            adapter_name=self.name,
            input_doi=doi,
            links=links,
            errors=errors
        )
