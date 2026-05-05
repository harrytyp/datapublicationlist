import sys
from main import process_article, load_config
from src.pdf_scanner import get_pdf_url, extract_dois_from_pdf, filter_likely_dataset_dois
from src.enl_parser import extract_data_from_enl

def test_single_article(doi, enl_file=None, force_pdf_url=None):
    config = load_config()
    email = config["email"]
    
    print(f"--- Testing Article: {doi} ---")
    
    # 1. Get PDF URL
    pdf_url = force_pdf_url
    if not pdf_url:
        print("[INFO] Querying Unpaywall for PDF URL...")
        pdf_url = get_pdf_url(doi, email)
    
    if not pdf_url:
        print("[ERROR] No PDF URL found for this DOI.")
        return

    print(f"[PDF] Attempting to download and scan: {pdf_url}")
    
    # 2. Extract DOIs from PDF
    raw_dois = extract_dois_from_pdf(pdf_url)
    print(f"[PDF] Extracted {len(raw_dois)} raw DOIs from PDF.")
    
    # 3. Filter for datasets
    dataset_candidates = filter_likely_dataset_dois(raw_dois)
    
    if dataset_candidates:
        print(f"[SUCCESS] Found {len(dataset_candidates)} dataset-like DOIs:")
        for ds in dataset_candidates:
            print(f"  - {ds}")
    else:
        print("[INFO] No dataset-like DOIs found in the PDF text.")

if __name__ == "__main__":
    # arXiv DOI (Always allows downloads)
    test_doi = "10.48550/arXiv.1901.00001" 
    # Known direct PDF link
    direct_pdf = "https://arxiv.org/pdf/1901.00001.pdf"
    
    test_single_article(test_doi, force_pdf_url=direct_pdf)
