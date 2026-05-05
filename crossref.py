import requests
from utils import get_with_retry

CROSSREF_BASE = "https://api.crossref.org/works"
DATASET_RELATION_TYPES = {
    "is-supplemented-by", "is-based-on", "has-part", "is-variant-form-of"
}

def query_crossref(article_doi: str, email: str) -> list[str]:
    """Return dataset DOIs declared in Crossref relation metadata."""
    headers = {"User-Agent": f"DataPublicationFinder/1.0 (mailto:{email})"}
    url = f"{CROSSREF_BASE}/{article_doi}"
    
    response = get_with_retry(url, headers=headers, timeout=20)
    if not response or response.status_code != 200:
        return []
    
    try:
        work = response.json().get("message", {})
        relations = work.get("relation", {})
        
        dataset_dois = []
        for relation_type, targets in relations.items():
            if relation_type in DATASET_RELATION_TYPES:
                for target in targets:
                    if target.get("id-type") == "doi":
                        dataset_dois.append(target["id"].strip())
        
        return list(set(dataset_dois))  # Deduplicate
    except Exception:
        return []
