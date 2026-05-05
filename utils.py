import logging
import time
import requests

# Configure basic logging if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def get_with_retry(url, params=None, headers=None, timeout=20, retries=3, backoff=2):
    """
    Perform a GET request with retry logic for network errors and rate limits (429).
    Returns the response object if successful, or None if all attempts fail.
    """
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            
            # Handle rate limiting
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", backoff * (attempt + 1)))
                logger.warning(f"Rate limited by {url}, waiting {wait}s")
                time.sleep(wait)
                continue
            
            # Check for other HTTP errors (optional, but good practice)
            # We return the response anyway if it's not 429, 
            # let the caller decide what to do with 404, 500, etc.
            return r
            
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(backoff * (attempt + 1))
            
    logger.error(f"All {retries} attempts failed for {url}")
    return None
