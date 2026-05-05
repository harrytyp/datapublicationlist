import re

def normalize_doi(doi: str) -> str:
    """Strips https://doi.org/ and leading/trailing whitespace; returns the bare 10.xxx/yyy form."""
    if not doi:
        return ""
    doi = doi.strip()
    doi = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:)', '', doi, flags=re.IGNORECASE)
    return doi.strip()

def is_valid_doi(doi: str) -> bool:
    """Returns True if the string matches a minimal DOI pattern (10.\\d{4,}/\\S+)."""
    if not doi:
        return False
    return bool(re.match(r'^10\.\d{4,}/\S+$', normalize_doi(doi)))

def doi_to_url(doi: str) -> str:
    """Returns 'https://doi.org/' + normalize_doi(doi)."""
    return f"https://doi.org/{normalize_doi(doi)}"
