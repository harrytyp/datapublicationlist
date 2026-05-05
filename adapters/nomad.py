from .base import BaseAdapter
from discovery_models import AdapterResult, DatasetLink
from utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class NOMADAdapter(BaseAdapter):
    """Adapter for the NOMAD / OPTIMADE API (Experimental)."""
    name = "NOMAD"

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://nomad-lab.eu/prod/v1"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent
        )

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        try:
            # 1. OPTIMADE references query
            params = {"filter": f'doi="{normalized_input}"', "page_limit": 25}
            try:
                response = self.session.get("optimade/references", params=params)
                if response and response.status_code == 200:
                    refs = response.json().get("data", [])
                    for ref in refs:
                        structs = ref.get("relationships", {}).get("structures", {}).get("data", [])
                        for struct in structs:
                            struct_id = struct.get("id")
                            links.append(DatasetLink(
                                source_doi=doi,
                                dataset_url=f"{self.session.base_url}/optimade/structures/{struct_id}",
                                relation_type="IsRelatedTo",
                                repository=self.name,
                                confidence="inferred",
                                raw=ref
                            ))
            except Exception: pass

            # 2. NOMAD native API fallback
            if not links:
                params = {"q": f"references.doi:{normalized_input}", "pagination[page_size]": 25}
                response = self.session.get("api/v1/entries", params=params)
                if response and response.status_code == 200:
                    entries = response.json().get("data", [])
                    for entry in entries:
                        entry_id = entry.get("entry_id")
                        dataset_doi = entry.get("metadata", {}).get("doi")
                        links.append(DatasetLink(
                            source_doi=doi,
                            dataset_doi=dataset_doi,
                            dataset_url=f"https://nomad-lab.eu/prod/v1/gui/entry/{entry_id}",
                            relation_type="IsRelatedTo",
                            repository=self.name,
                            confidence="inferred",
                            raw=entry
                        ))
        except Exception as e:
            return AdapterResult(adapter_name=self.name, input_doi=doi, errors=[str(e)])
        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links)
