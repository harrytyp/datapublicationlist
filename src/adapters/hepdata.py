from .base import BaseAdapter
from ..discovery_models import AdapterResult, DatasetLink
from ..utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class HEPDataAdapter(BaseAdapter):
    """Adapter for the HEPData API."""
    name = "HEPData"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://www.hepdata.net"),
            timeout=config.get("timeout_seconds", 15),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.session.headers["Accept"] = "application/json"
        self.emit_table_level_dois = config.get("emit_table_level_dois", True)

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        errors = []
        page = 1
        
        while page <= 10:
            params = {"q": normalized_input, "format": "json", "size": 25, "page": page}
            try:
                response = self.session.get(
                    "search/", 
                    params=params,
                    rate_limit_delay=self.config.get("rate_limit_delay_seconds", 1.0),
                    retries=self.http_config.retry_attempts,
                    backoff=self.http_config.retry_backoff_seconds
                )
                if not response: break
                data = response.json()
                results = data.get("results", [])
                if not results: break
                
                for hit in results:
                    inspire_id = hit.get("inspire_id")
                    if not inspire_id: continue
                    
                    rec_response = self.session.get(f"record/ins{inspire_id}", params={"format": "json"})
                    if not rec_response: continue
                    rec_data = rec_response.json()
                    
                    pub_doi = normalize_doi(rec_data.get("publication_doi", ""))
                    if not pub_doi:
                        pub_doi = normalize_doi(rec_data.get("publication_info", {}).get("doi", ""))
                    
                    if pub_doi == normalized_input:
                        hepdata_doi = rec_data.get("hepdata_doi")
                        links.append(DatasetLink(
                            source_doi=doi,
                            dataset_doi=hepdata_doi,
                            dataset_url=f"https://www.hepdata.net/record/ins{inspire_id}",
                            relation_type="IsSupplementTo",
                            repository=self.name,
                            confidence="confirmed",
                            raw={"inspire_id": inspire_id}
                        ))
                        
                        if self.emit_table_level_dois:
                            tables = rec_data.get("resources", []) or rec_data.get("tables", [])
                            for table in tables:
                                table_doi = table.get("doi")
                                if table_doi:
                                    links.append(DatasetLink(
                                        source_doi=doi,
                                        dataset_doi=table_doi,
                                        relation_type="HasPart",
                                        repository=self.name,
                                        confidence="confirmed",
                                        raw={"table_id": table.get("id")}
                                    ))
                if len(results) < 25: break
                page += 1
            except Exception as e:
                errors.append(str(e))
                break
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links, errors=errors)
