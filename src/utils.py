import logging
import time
import requests
import re
from typing import Optional

# Configure basic logging
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

# --- HTTP Utilities ---

class AdapterHTTPError(Exception):
    """Exception for HTTP errors in adapters."""
    def __init__(self, status_code: int, url: str, response_body: str):
        self.status_code = status_code
        self.url = url
        self.response_body = response_body
        super().__init__(f"HTTP {status_code} error at {url}")

def get_with_retry(url, params=None, headers=None, timeout=20, retries=3, backoff=2):
    """Perform a GET request with retry logic for network errors and rate limits (429)."""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", backoff * (attempt + 1)))
                logger.warning(f"Rate limited by {url}, waiting {wait}s")
                time.sleep(wait)
                continue
            
            return r
            
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(backoff * (attempt + 1))
            
    logger.error(f"All {retries} attempts failed for {url}")
    return None

class HTTPSession:
    """Shared HTTP session wrapper for discovery adapters."""
    
    def __init__(self, base_url: str, timeout: int = 20, user_agent: str = "", api_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"User-Agent": user_agent}
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
        self.last_request_time = 0.0

    def get(self, endpoint: str, params: Optional[dict] = None, rate_limit_delay: float = 1.0, retries: int = 3, backoff: float = 2.0):
        """Perform a GET request with retry and rate-limiting."""
        if endpoint:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
        else:
            url = self.base_url
        
        # Log outgoing request (redact DOI for privacy/brevity)
        redacted_params = {}
        if params:
            for k, v in params.items():
                if isinstance(v, str) and v.startswith("10."):
                    redacted_params[k] = v[:8] + "..."
                else:
                    redacted_params[k] = v
        logger.debug(f"GET {url} params={redacted_params}")

        for attempt in range(retries):
            # Rate limiting
            elapsed = time.time() - self.last_request_time
            if elapsed < rate_limit_delay:
                time.sleep(rate_limit_delay - elapsed)
            
            try:
                response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
                self.last_request_time = time.time()
                
                if response.status_code in [429, 500, 502, 503, 504]:
                    wait = int(response.headers.get("Retry-After", backoff * (attempt + 1)))
                    logger.warning(f"Retrying {url} after {wait}s (Status {response.status_code})")
                    time.sleep(wait)
                    continue
                
                if response.status_code >= 400:
                    raise AdapterHTTPError(response.status_code, url, response.text)
                
                return response
            
            except (requests.RequestException, AdapterHTTPError) as e:
                if attempt == retries - 1:
                    logger.error(f"Failed request to {url}: {e}")
                    raise
                time.sleep(backoff * (attempt + 1))
        
        return None

# --- DOI Utilities ---

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
