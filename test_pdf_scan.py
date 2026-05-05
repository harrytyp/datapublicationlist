import sys
from main import process_article, load_config
from pdf_scanner import get_pdf_url, extract_dois_from_pdf, filter_likely_dataset_dois
from enl_parser import extract_data_from_enl

def test_single_article(doi, enl_file=None, force_pdf_url=None):
    config = load_config()
    email = config["email"]
    
    print(f"--- Testing Article: {doi} ---")
    
    pdf_url = force_pdf_url
    if not pdf_url:
        # 1. Check ENL mapping
        enl_url = None
        if enl_file:
            print(f"Checking ENL file: {enl_file}")
            enl_data = extract_data_from_enl(enl_file)
            enl_url = enl_data["doi_to_url"].get(doi)
            if enl_url:
                print(f"[ENL] Found URL: {enl_url}")
            else:
                print("[ENL] No URL found for this DOI in ENL file.")

        # 2. Try to get PDF URL
        pdf_url = enl_url if enl_url else get_pdf_url(doi, email)
    
    if not pdf_url:
        print("[PDF] Could not find a PDF URL.")
        return

    # Clean the URL if it has garbage at the end (from ENL extraction)
    if ".pdf" in pdf_url:
        pdf_url = pdf_url.split(".pdf")[0] + ".pdf"

    print(f"[PDF] Attempting to download and scan: {pdf_url}")
    
    # 3. Extract DOIs
    raw_dois = extract_dois_from_pdf(pdf_url)
    print(f"[PDF] Extracted {len(raw_dois)} raw DOIs from PDF.")
    
    # 4. Filter for datasets
    dataset_candidates = filter_likely_dataset_dois(raw_dois)
    if dataset_candidates:
        print(f"[SUCCESS] Found {len(dataset_candidates)} dataset candidates in PDF:")
        for d in dataset_candidates:
            print(f"  - {d}")
    else:
        print("[INFO] No dataset-like DOIs found in the PDF text.")

if __name__ == "__main__":
    # arXiv DOI (Always allows downloads)
    test_doi = "10.48550/arXiv.1901.00001" 
    # Known direct PDF link
    direct_pdf = "https://arxiv.org/pdf/1901.00001.pdf"
    
    test_single_article(test_doi, force_pdf_url=direct_pdf)
