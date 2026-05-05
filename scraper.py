import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import os
import time

PUBLICATIONS_URL = "https://www.e-conversion.de/de/publikationen/"
CACHE_FILE = "scraper_cache.json"

def scrape_dois(url: str, use_cache: bool = True) -> list[dict]:
    """Scrape all article DOIs and metadata from the cluster publications page, handling pagination and caching."""
    
    # 1. Check cache first
    if use_cache and os.path.exists(CACHE_FILE):
        print(f"Loading publications from cache: {CACHE_FILE}")
        try:
            with open(CACHE_FILE, "r") as f:
                cached_data = json.load(f)
                if cached_data:
                    return cached_data
        except Exception as e:
            print(f"Error reading cache: {e}. Proceeding with fresh scrape.")

    publications = []
    
    # First request to get the total number of pages
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching initial page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Try to find total pages from "X von Y" text in tablenav-pages
    total_pages = 1
    nav_text = soup.find("div", class_="tablenav-pages")
    if nav_text:
        match = re.search(r'von\s+(\d+)', nav_text.get_text())
        if match:
            total_pages = int(match.group(1))
    
    print(f"Found {total_pages} pages of publications.")
    
    # Loop through all pages
    for page in tqdm(range(1, total_pages + 1), desc="Scraping pages"):
        page_url = f"{url}?limit={page}"
        try:
            time.sleep(0.5)  # Rate limiting between page requests
            r = requests.get(page_url, timeout=30)
            r.raise_for_status()
            page_soup = BeautifulSoup(r.text, "html.parser")
            
            # Find all bibtex blocks
            bibtex_blocks = page_soup.find_all("div", class_="tp_bibtex_entry")
            if not bibtex_blocks:
                # Fallback to whole text if specific blocks not found
                raw_text = page_soup.get_text()
                entries = re.findall(r'@article\{.*?\}', raw_text, re.DOTALL)
                for entry in entries:
                    doi_match = re.search(r'doi\s*=\s*\{(10\.\d{4,}/[^\}]+)\}', entry)
                    title_match = re.search(r'title\s*=\s*\{([^\}]+)\}', entry)
                    author_match = re.search(r'author\s*=\s*\{([^\}]+)\}', entry)
                    year_match = re.search(r'year\s*=\s*\{(\d{4})\}', entry)
                    
                    if doi_match:
                        publications.append({
                            "article_doi": doi_match.group(1).strip(),
                            "title": title_match.group(1).strip() if title_match else "",
                            "authors": author_match.group(1).strip() if author_match else "",
                            "year": year_match.group(1).strip() if year_match else ""
                        })
            else:
                for block in bibtex_blocks:
                    block_text = block.get_text()
                    doi_match = re.search(r'doi\s*=\s*\{(10\.\d{4,}/[^\}]+)\}', block_text)
                    title_match = re.search(r'title\s*=\s*\{([^\}]+)\}', block_text)
                    author_match = re.search(r'author\s*=\s*\{([^\}]+)\}', block_text)
                    year_match = re.search(r'year\s*=\s*\{(\d{4})\}', block_text)
                    
                    if doi_match:
                        publications.append({
                            "article_doi": doi_match.group(1).strip(),
                            "title": title_match.group(1).strip() if title_match else "",
                            "authors": author_match.group(1).strip() if author_match else "",
                            "year": year_match.group(1).strip() if year_match else ""
                        })
                        
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            continue
            
    # Deduplicate
    seen = set()
    unique_publications = []
    for pub in publications:
        if pub["article_doi"] not in seen:
            unique_publications.append(pub)
            seen.add(pub["article_doi"])
    
    # Save to cache
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(unique_publications, f, indent=4)
    except Exception as e:
        print(f"Error saving cache: {e}")
            
    return unique_publications

if __name__ == "__main__":
    res = scrape_dois(PUBLICATIONS_URL)
    print(f"Total articles found: {len(res)}")
