import re
import io
import requests
import pdfplumber
from utils import get_with_retry

UNPAYWALL_BASE = "https://api.unpaywall.org/v2"
DOI_REGEX = re.compile(r'\b10\.\d{4,}/[^\s\,\;\]\)\"]+')

DATASET_DOI_PREFIXES = {
    "10.5281",   # Zenodo
    "10.1594",   # PANGAEA
    "10.17632",  # Mendeley Data
    "10.6084",   # figshare
    "10.25504",  # IEDA/EarthChem
    "10.11588",  # HeiDATA
    "10.18419",  # DaRUS (Stuttgart)
    "10.48550",  # arXiv datasets
}

def get_pdf_url(article_doi: str, email: str) -> str | None:
    """Get the best open access PDF URL from Unpaywall."""
    url = f"{UNPAYWALL_BASE}/{article_doi}"
    params = {"email": email}
    
    response = get_with_retry(url, params=params, timeout=15)
    if not response or response.status_code != 200:
        return None
        
    try:
        data = response.json()
        best_oa = data.get("best_oa_location")
        if best_oa:
            return best_oa.get("url_for_pdf")
    except Exception:
        pass
    return None

def extract_dois_from_pdf(pdf_url: str) -> list[str]:
    """Download PDF and extract all DOIs from full text."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = get_with_retry(pdf_url, headers=headers, timeout=30)
    if not response or response.status_code != 200:
        return []
    
    dois = set()
    try:
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for match in DOI_REGEX.findall(text):
                    # Clean the DOI (remove trailing punctuation)
                    clean_doi = match.rstrip(".,;)]}")
                    dois.add(clean_doi)
    except Exception:
        return []
    
    return list(dois)

def filter_likely_dataset_dois(dois: list[str]) -> list[str]:
    """Pre-filter DOIs by known dataset repository prefixes."""
    return [d for d in dois if any(d.startswith(p) for p in DATASET_DOI_PREFIXES)]
