from .base import BaseAdapter
from ..discovery_models import AdapterResult, DatasetLink
from ..utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class DataCiteAdapter(BaseAdapter):
    """Adapter for the DataCite REST API."""
    name = "DataCite"

    STRONG_RELATION_TYPES = {
        "IsSupplementTo",
        "IsPartOf",
        "IsPublishedIn",
        "IsDerivedFrom",
        "IsCompiledBy",
    }

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://api.datacite.org/dois"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent
        )

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi).lower()
        links = []
        errors = []
        page = 1
        
        while True:
            params = {
                "query": (
                    f'relatedIdentifiers.relatedIdentifier:"{normalized_input}" AND '
                    f'relatedIdentifiers.relatedIdentifierType:DOI'
                ),
                "resource-type-id": "dataset",
                "page[size]": 50,
                "page[number]": page,
            }
            
            try:
                response = self.session.get(
                    "",
                    params=params,
                    rate_limit_delay=self.config.get("rate_limit_delay_seconds", 0.1),
                    retries=self.http_config.retry_attempts,
                    backoff=self.http_config.retry_backoff_seconds
                )
                
                if not response or response.status_code != 200:
                    break
                    
                data = response.json()
                items = data.get("data", [])
                for item in items:
                    ds_doi = item.get("attributes", {}).get("doi", "")
                    if not ds_doi:
                        continue

                    related_ids = item.get("attributes", {}).get("relatedIdentifiers", [])
                    matched_relation = next(
                        (
                            r for r in related_ids
                            if r.get("relatedIdentifier", "").strip().lower() == normalized_input
                            and r.get("relatedIdentifierType", "").strip().upper() == "DOI"
                        ),
                        None
                    )

                    if not matched_relation:
                        continue

                    relation_type = matched_relation.get("relationType", "Unknown")
                    if relation_type not in self.STRONG_RELATION_TYPES:
                        continue

                    links.append(DatasetLink(
                        source_doi=doi,
                        dataset_doi=ds_doi.strip(),
                        relation_type=relation_type,
                        repository="DataCite",
                        confidence="inferred",
                        raw=item
                    ))
                
                total_pages = data.get("meta", {}).get("totalPages", 1)
                if page >= total_pages:
                    break
                page += 1
                
            except Exception as e:
                errors.append(str(e))
                break
                
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links, errors=errors)
