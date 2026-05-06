import requests
from .utils import get_with_retry

DATASET_TYPES = {"dataset", "data paper", "datapaper", "software", "collection"}

def get_doi_metadata(doi: str, email: str) -> dict:
    """
    Returns metadata for a DOI: {'title': ..., 'type': ..., 'doi': ..., 'description': ...}
    Checks DataCite first, then Crossref.
    """
    # 1. Try DataCite
    url_dc = f"https://api.datacite.org/dois/{doi}"
    response = get_with_retry(url_dc, timeout=15)
    
    if response and response.status_code == 200:
        try:
            attrs = response.json().get("data", {}).get("attributes", {})
            title = attrs.get("titles", [{}])[0].get("title", "No Title")
            resource_type = attrs.get("types", {}).get("resourceTypeGeneral", "Unknown")
            description = attrs.get("description", "No description available.")
            return {
                "doi": doi,
                "title": title,
                "type": resource_type.lower(),
                "description": description
            }
        except Exception:
            pass
    
    # 2. Try Crossref as fallback
    url_cr = f"https://api.crossref.org/works/{doi}"
    headers = {"User-Agent": f"DataPublicationFinder/1.0 (mailto:{email})"}
    response = get_with_retry(url_cr, headers=headers, timeout=15)
    
    if response and response.status_code == 200:
        try:
            work = response.json().get("message", {})
            title = work.get("title", ["No Title"])[0]
            ctype = work.get("type", "unknown")
            # Crossref abstracts are sometimes in the 'abstract' field (HTML encoded)
            description = work.get("abstract", "No description available.")
            if description:
                # Basic cleanup of Crossref HTML abstracts
                import re
                description = re.sub('<[^<]+?>', '', description).strip()
            
            return {
                "doi": doi,
                "title": title,
                "type": ctype.lower(),
                "description": description
            }
        except Exception:
            pass
    
    return {"doi": doi, "title": "Unknown", "type": "unknown", "description": "No description available."}

def is_data_publication(doi: str, email: str) -> bool:
    """Return True if the DOI resolves to a dataset or data publication."""
    meta = get_doi_metadata(doi, email)
    return meta["type"] in DATASET_TYPES
