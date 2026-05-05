import requests

DATASET_TYPES = {"dataset", "data paper", "datapaper", "software", "collection"}

def get_doi_metadata(doi: str, email: str) -> dict:
    """
    Returns metadata for a DOI: {'title': ..., 'type': ..., 'doi': ...}
    Checks DataCite first, then Crossref.
    """
    try:
        # Try DataCite
        r = requests.get(f"https://api.datacite.org/dois/{doi}", timeout=15)
        if r.status_code == 200:
            attrs = r.json().get("data", {}).get("attributes", {})
            title = attrs.get("titles", [{}])[0].get("title", "No Title")
            resource_type = attrs.get("types", {}).get("resourceTypeGeneral", "Unknown")
            return {
                "doi": doi,
                "title": title,
                "type": resource_type.lower()
            }
        
        # Try Crossref as fallback
        headers = {"User-Agent": f"DataPublicationFinder/1.0 (mailto:{email})"}
        r = requests.get(f"https://api.crossref.org/works/{doi}", headers=headers, timeout=15)
        if r.status_code == 200:
            work = r.json().get("message", {})
            title = work.get("title", ["No Title"])[0]
            ctype = work.get("type", "unknown")
            return {
                "doi": doi,
                "title": title,
                "type": ctype.lower()
            }
    except Exception:
        pass
    
    return {"doi": doi, "title": "Unknown", "type": "unknown"}

def is_data_publication(doi: str, email: str) -> bool:
    """Return True if the DOI resolves to a dataset or data publication."""
    meta = get_doi_metadata(doi, email)
    return meta["type"] in DATASET_TYPES
