from .base import BaseAdapter
from ..discovery_models import AdapterResult, DatasetLink
from ..utils import normalize_doi, HTTPSession
import logging

logger = logging.getLogger(__name__)

class OpenAIREAdapter(BaseAdapter):
    """Adapter for the ScholeXplorer (OpenAIRE) API for publication-dataset links."""
    name = "OpenAIRE"
    CONFIRMED_PROVIDERS = {"crossref", "datacite"}

    def __init__(self, config, http_config):
        super().__init__(config, http_config)
        # Using ScholeXplorer API which is dedicated to linkage discovery
        self.session = HTTPSession(
            base_url=config.get("base_url", "https://api.scholexplorer.openaire.eu/v3/Links"),
            timeout=config.get("timeout_seconds", 20),
            user_agent=http_config.user_agent
        )

    def _get_total_pages(self, data: dict) -> int:
        return int(
            data.get("totalPages")
            or data.get("page", {}).get("totalPages")
            or data.get("pagination", {}).get("totalPages")
            or 1
        )

    def _link_confidence(self, providers: list[str]) -> str:
        lowered = {p.strip().lower() for p in providers if isinstance(p, str)}
        return "confirmed" if lowered & self.CONFIRMED_PROVIDERS else "inferred"

    def _extract_links(self, doi: str, params: dict, seen: set[tuple]) -> list[DatasetLink]:
        links = []
        page = 0

        while True:
            params["page"] = page
            response = self.session.get(
                "",
                params=params,
                rate_limit_delay=self.config.get("rate_limit_delay_seconds", 0.5),
                retries=self.http_config.retry_attempts,
                backoff=self.http_config.retry_backoff_seconds
            )

            if not response or response.status_code != 200:
                break

            data = response.json()
            total_pages = self._get_total_pages(data)
            results = data.get("result", [])

            for link in results:
                target = link.get("target", {})
                if target.get("Type") != "Dataset":
                    continue

                tgt_ids = target.get("Identifier", [])
                dataset_doi = next(
                    (
                        i.get("ID", "").strip()
                        for i in tgt_ids
                        if i.get("IDScheme", "").strip().lower() == "doi" and i.get("ID")
                    ),
                    None
                )

                dataset_url = None
                if not dataset_doi:
                    dataset_url = next(
                        (
                            i.get("ID", "").strip()
                            for i in tgt_ids
                            if i.get("IDScheme", "").strip().lower() == "url" and i.get("ID")
                        ),
                        None
                    )

                if not dataset_doi and not dataset_url:
                    continue

                relation = link.get("RelationshipType", {})
                rel_name = relation.get("SubType") or relation.get("Name") or "Related"

                providers = [p.get("name", "") for p in link.get("LinkProvider", []) if p.get("name")]
                provider_str = f" via {', '.join(providers)}" if providers else ""
                confidence = self._link_confidence(providers)

                publishers = target.get("Publisher", [])
                repo_name = publishers[0].get("name") if publishers else "Unknown Repository"

                link_date = link.get("LinkPublicationDate", "Unknown Date")
                logger.info(f"[OpenAIRE] Found {rel_name} link to {repo_name} (Date: {link_date})")

                key = (
                    dataset_doi or "",
                    dataset_url or "",
                    rel_name,
                    repo_name,
                    provider_str,
                )
                if key in seen:
                    continue
                seen.add(key)

                links.append(DatasetLink(
                    source_doi=doi,
                    dataset_doi=dataset_doi,
                    dataset_url=dataset_url,
                    relation_type=rel_name,
                    repository=f"{repo_name}{provider_str}",
                    confidence=confidence,
                    raw=link
                ))

            page += 1
            if page >= total_pages:
                break

        return links

    def fetch(self, doi: str) -> AdapterResult:
        normalized_input = normalize_doi(doi)
        links = []
        seen = set()

        try:
            links.extend(self._extract_links(
                doi,
                {
                    "sourcePid": normalized_input,
                    "targetType": "Dataset",
                    "size": 100,
                },
                seen,
            ))

            links.extend(self._extract_links(
                doi,
                {
                    "targetPid": normalized_input,
                    "sourceType": "Dataset",
                    "size": 100,
                },
                seen,
            ))

        except Exception as e:
            return AdapterResult(adapter_name=self.name, input_doi=doi, errors=[str(e)])

        return AdapterResult(adapter_name=self.name, input_doi=doi, links=links)
