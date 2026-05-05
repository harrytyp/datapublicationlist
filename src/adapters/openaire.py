from .base import BaseAdapter
from ..discovery_models import AdapterResult, DatasetLink
from ..utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class OpenAIREAdapter(BaseAdapter):
    """Adapter for the ScholeXplorer (OpenAIRE) API for publication-dataset links."""
    name = "OpenAIRE"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        # Using ScholeXplorer API which is dedicated to linkage discovery
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://api-beta.scholexplorer.openaire.eu/v3/Links"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent
        )

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        
        params = {
            "sourcePid": normalized_input,
            "targetType": "dataset",
            "size": 100,
            "page": 0
        }
        
        try:
            response = self.session.get(
                "", 
                params=params,
                rate_limit_delay=self.config.get("rate_limit_delay_seconds", 0.5),
                retries=self.http_config.retry_attempts,
                backoff=self.http_config.retry_backoff_seconds
            )
            
            if response and response.status_code == 200:
                data = response.json()
                results = data.get("result", [])
                
                for link in results:
                    target = link.get("target", {})
                    tgt_ids = target.get("Identifier", [])
                    
                    # Extract DOI if available
                    dataset_doi = next(
                        (i["ID"] for i in tgt_ids if i.get("IDScheme") == "doi"),
                        None
                    )
                    
                    # Also try to find a URL if no DOI
                    dataset_url = None
                    if not dataset_doi:
                        dataset_url = next(
                            (i["ID"] for i in tgt_ids if i.get("IDScheme") == "url"),
                            None
                        )
                    
                    relation = link.get("RelationshipType", {})
                    rel_name = f"{relation.get('Name', 'Related')}"
                    if relation.get('SubType'):
                        rel_name += f" ({relation.get('SubType')})"
                        
                    logger.info(f"[OpenAIRE] Found link: {doi} -> {dataset_doi or dataset_url}")
                    links.append(DatasetLink(
                        source_doi=doi,
                        dataset_doi=dataset_doi.strip() if dataset_doi else None,
                        dataset_url=dataset_url.strip() if dataset_url else None,
                        relation_type=rel_name,
                        repository="OpenAIRE/ScholeXplorer",
                        confidence="confirmed",
                        raw=link
                    ))
        except Exception as e:
            return AdapterResult(adapter_name=self.name, input_doi=doi, errors=[str(e)])
            
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links)
