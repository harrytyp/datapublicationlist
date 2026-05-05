import requests

DATACITE_BASE = "https://api.datacite.org/dois"

def query_datacite(article_doi: str) -> list[str]:
    """Return dataset DOIs on DataCite that reference the given article DOI."""
    params = {
        "query": f'relatedIdentifiers.relatedIdentifier:"{article_doi}"',
        "resource-type-id": "dataset",
        "page[size]": 50
    }
    try:
        r = requests.get(DATACITE_BASE, params=params, timeout=20)
        if r.status_code != 200:
            return []
        
        data = r.json()
        dataset_dois = []
        for item in data.get("data", []):
            doi = item.get("attributes", {}).get("doi", "")
            if doi:
                dataset_dois.append(doi.strip())
        
        return dataset_dois
    except Exception as e:
        # print(f"DataCite query error for {article_doi}: {e}")
        return []
