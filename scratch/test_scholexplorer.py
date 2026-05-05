import requests

# A Nature Scientific Data paper known to have formally linked datasets
# Wilkinson et al. 2016 "The FAIR Guiding Principles" - widely cited, has DataCite-registered datasets
TEST_DOIS = [
    "10.1038/sdata.2016.18",   # FAIR principles paper - Scientific Data
    "10.1594/PANGAEA.896660",  # PANGAEA paper with known dataset links
    "10.5281/zenodo.3490058",  # Zenodo-published paper with explicit dataset relations
]

BASE_URL = "https://api-beta.scholexplorer.openaire.eu/v3/Links"

for doi in TEST_DOIS:
    print(f"\n{'='*60}")
    print(f"Testing DOI: {doi}")
    print(f"{'='*60}")
    
    params = {
        "sourcePid": doi,
        "targetType": "dataset",
        "size": 10,
        "page": 0
    }
    
    try:
        r = requests.get(BASE_URL, params=params, timeout=15)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            total = data.get("totalLinks", data.get("total", "?"))
            results = data.get("result", [])
            print(f"Total links: {total}")
            print(f"Results in this page: {len(results)}")
            
            for i, link in enumerate(results[:3]):  # show first 3
                src_type = link.get("source", {}).get("Type", "?")
                tgt_type = link.get("target", {}).get("Type", "?")
                relation = link.get("RelationshipType", {})
                providers = [p.get("name") for p in link.get("LinkProvider", [])]
                
                tgt_ids = link.get("target", {}).get("Identifier", [])
                tgt_doi = next(
                    (i["ID"] for i in tgt_ids if i.get("IDScheme") == "doi"),
                    "no DOI"
                )
                
                print(f"\n  Link {i+1}:")
                print(f"    source type : {src_type}")
                print(f"    target type : {tgt_type}")
                print(f"    target DOI  : {tgt_doi}")
                print(f"    relation    : {relation.get('Name')} / {relation.get('SubType')}")
                print(f"    provider(s) : {providers}")
        else:
            print(f"Response body: {r.text[:300]}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
