import requests

OPENAIRE_BASE = "https://api.openaire.eu/search/datasets"

def query_openaire(article_doi: str) -> list[str]:
    """Return dataset DOIs linked to the given article DOI via OpenAIRE."""
    params = {
        "relatedDOI": article_doi,
        "format": "json",
        "size": 50
    }
    try:
        r = requests.get(OPENAIRE_BASE, params=params, timeout=20)
        if r.status_code != 200:
            return []
        
        data = r.json()
        results = data.get("response", {}).get("results", {}).get("result", [])
        
        if not isinstance(results, list):
            # Sometimes single results aren't in a list depending on the API version/format
            results = [results]
            
        dataset_dois = []
        for result in results:
            metadata = result.get("metadata", {}).get("oaf:entity", {})
            pids = metadata.get("oaf:result", {}).get("pid", [])
            if isinstance(pids, dict):
                pids = [pids]
            for pid in pids:
                if pid.get("@classid") == "doi":
                    dataset_dois.append(pid.get("$", "").strip())
        
        return [d for d in dataset_dois if d]
    except Exception as e:
        # print(f"OpenAIRE query error for {article_doi}: {e}")
        return []
