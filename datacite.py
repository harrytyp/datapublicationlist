import requests
from utils import get_with_retry

DATACITE_BASE = "https://api.datacite.org/dois"

def query_datacite(article_doi: str) -> list[str]:
    """Return dataset DOIs on DataCite that reference the given article DOI, with pagination support."""
    dataset_dois = []
    page = 1
    
    while True:
        params = {
            "query": f'relatedIdentifiers.relatedIdentifier:"{article_doi}"',
            "resource-type-id": "dataset",
            "page[size]": 50,
            "page[number]": page,
        }
        
        response = get_with_retry(DATACITE_BASE, params=params, timeout=20)
        if not response or response.status_code != 200:
            break
            
        try:
            data = response.json()
            items = data.get("data", [])
            for item in items:
                doi = item.get("attributes", {}).get("doi", "")
                if doi:
                    dataset_dois.append(doi.strip())
            
            # Check for next page
            total_pages = data.get("meta", {}).get("totalPages", 1)
            if page >= total_pages:
                break
            page += 1
        except Exception:
            break
    
    return list(set(dataset_dois))  # Deduplicate
