import requests
from utils import get_with_retry

OPENAIRE_BASE = "https://api.openaire.eu/graph/researchProducts"

def query_openaire(article_doi: str) -> list[str]:
    """Return dataset DOIs from OpenAIRE Graph that are related to the given article DOI."""
    params = {
        "relatedDOI": article_doi,
        "type": "dataset",
        "page": 1,
        "pageSize": 50,
    }
    
    response = get_with_retry(OPENAIRE_BASE, params=params, timeout=20)
    if not response or response.status_code != 200:
        return []

    try:
        data = response.json()
        dataset_dois = []
        # The Graph API returns a flatter structure
        for item in data.get("results", []):
            # Each result has a list of 'pids' (Persistent Identifiers)
            for pid in item.get("pids", []):
                if pid.get("scheme") == "doi":
                    doi_val = pid.get("value")
                    if doi_val:
                        dataset_dois.append(doi_val.strip())
        
        return list(set(dataset_dois))  # Deduplicate
    except Exception:
        return []
