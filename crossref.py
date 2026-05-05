import requests

CROSSREF_BASE = "https://api.crossref.org/works"
DATASET_RELATION_TYPES = {
    "is-supplemented-by", "is-based-on", "has-part", "is-variant-form-of"
}

def query_crossref(article_doi: str, email: str) -> list[str]:
    """Return dataset DOIs declared in Crossref relation metadata."""
    headers = {"User-Agent": f"DataPublicationFinder/1.0 (mailto:{email})"}
    try:
        r = requests.get(f"{CROSSREF_BASE}/{article_doi}", headers=headers, timeout=20)
        if r.status_code != 200:
            return []
        
        work = r.json().get("message", {})
        relations = work.get("relation", {})
        
        dataset_dois = []
        for relation_type, targets in relations.items():
            if relation_type in DATASET_RELATION_TYPES:
                for target in targets:
                    if target.get("id-type") == "doi":
                        dataset_dois.append(target["id"].strip())
        
        return dataset_dois
    except Exception as e:
        # print(f"Crossref query error for {article_doi}: {e}")
        return []
