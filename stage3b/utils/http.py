import time
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AdapterHTTPError(Exception):
    """Exception for HTTP errors in adapters."""
    def __init__(self, status_code: int, url: str, response_body: str):
        self.status_code = status_code
        self.url = url
        self.response_body = response_body
        super().__init__(f"HTTP {status_code} error at {url}")

class HTTPSession:
    """Shared HTTP session wrapper for Stage 3b adapters."""
    
    def __init__(self, base_url: str, timeout: int = 20, user_agent: str = "", api_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"User-Agent": user_agent}
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
        self.last_request_time = 0.0

    def get(self, endpoint: str, params: Optional[dict] = None, rate_limit_delay: float = 1.0, retries: int = 3, backoff: float = 2.0):
        """Perform a GET request with retry and rate-limiting."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Log outgoing request (redact DOI)
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
