import re
import os

# DOI pattern: starts with 10. and looks like a DOI
DOI_PATTERN = rb'10\.\d{4,}/[^\s\,\;\]\)\"\^\<\>\x00-\x1f\x7f-\xff]+'
URL_PATTERN = rb'https?://[^\s\,\;\]\)\"\^\<\>\x00-\x1f\x7f-\xff]+'

def clean_doi(doi_str: str) -> str:
    """Clean a DOI string by removing trailing punctuation and extra garbage."""
    doi = doi_str.strip().rstrip('.,;)]}')
    
    # Handle the specific 'dirty' case: 10.1002/adfm.2020059771616-301X
    # If it ends with something that looks like an ISSN (4 digits, dash, 4 chars)
    issn_match = re.search(r'(\d{4}-\d{3}[\dX])$', doi)
    if issn_match:
        doi = doi[:-len(issn_match.group(1))]
    
    # Remove common suffixes found in EndNote binary blocks
    for suffix in ['English', 'German', 'Abstract']:
        if doi.endswith(suffix):
            doi = doi[:-len(suffix)]
            
    return doi

def extract_data_from_enl(filepath: str) -> dict:
    """
    Extract mapping of DOI -> URL and also find candidate dataset DOIs.
    Returns: {
        "doi_to_url": {doi: url},
        "dataset_dois": [doi],
        "all_urls": [url]
    }
    """
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return {"doi_to_url": {}, "dataset_dois": [], "all_urls": []}
        
    doi_to_url = {}
    dataset_dois = set()
    all_urls = set()
    
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
            
        # Find all URLs first
        urls = re.findall(URL_PATTERN, content)
        for url_bytes in urls:
            url = url_bytes.decode('ascii', errors='ignore')
            all_urls.add(url)
            
            # Try to find a DOI within this URL
            doi_match = re.search(rb'10\.\d{4,}/[^\s\^\<\>]+', url_bytes)
            if doi_match:
                raw_doi = doi_match.group(0).decode('ascii', errors='ignore')
                doi = clean_doi(raw_doi)
                if doi:
                    doi_to_url[doi] = url
        
        # Also find DOIs not in URLs
        dois = re.findall(DOI_PATTERN, content)
        for doi_bytes in dois:
            doi = clean_doi(doi_bytes.decode('ascii', errors='ignore'))
            if doi and doi not in doi_to_url:
                # We found a DOI but don't have a specific URL for it in this pass.
                # In a real ENL parser we'd chunk by entry, but regex is global.
                # For now, we'll store it as a candidate.
                dataset_dois.add(doi)
                
    except Exception as e:
        print(f"Error reading .enl file: {e}")
        
    return {
        "doi_to_url": doi_to_url,
        "dataset_dois": sorted(list(dataset_dois)),
        "all_urls": sorted(list(all_urls))
    }

if __name__ == "__main__":
    target_file = "e-conversion-Converted.enl"
    if os.path.exists(target_file):
        data = extract_data_from_enl(target_file)
        print(f"Found {len(data['doi_to_url'])} DOI-to-URL mappings.")
        print(f"Found {len(data['dataset_dois'])} additional DOI candidates.")
        if data['doi_to_url']:
            first_doi = list(data['doi_to_url'].keys())[0]
            print(f"Sample mapping: {first_doi} -> {data['doi_to_url'][first_doi]}")
    else:
        print(f"Please place {target_file} in the current directory.")
