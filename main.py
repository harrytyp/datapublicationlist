import csv
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

from scraper import scrape_dois, PUBLICATIONS_URL
from enl_parser import extract_data_from_enl
from pdf_scanner import get_pdf_url, extract_dois_from_pdf, filter_likely_dataset_dois
from resolver import is_data_publication, get_doi_metadata
from discovery_pipeline import DiscoveryPipeline

# Configuration
CONFIG_PATH = "config.json"

def load_config():
    """Load configuration from config.json."""
    default_config = {
        "email": "your-email@example.com",
        "output_file": "data_publication_dois.csv",
        "enl_file": "e-conversion-Converted.enl",
        "max_workers": 4,
        "process_limit": None,
        "skip_pdf_scan": True,
        "adapters": {}
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            user_config = json.load(f)
            default_config.update(user_config)
    return default_config

config = load_config()
EMAIL = config["email"]
OUTPUT_FILE = config["output_file"]
ENL_FILE = config["enl_file"]
MAX_WORKERS = config["max_workers"]
PROCESS_LIMIT = config["process_limit"]
SKIP_PDF_SCAN = config.get("skip_pdf_scan", True)

# Initialize Discovery Pipeline
discovery_pipeline = DiscoveryPipeline(config)

def process_article(article: dict, enl_url: str = None) -> list[dict]:
    """Process a single article to find linked datasets and return their metadata."""
    doi = article["article_doi"]
    confirmed_datasets = []

    # 1. Unified API Discovery (Core + Domain-Specific)
    discovery_links = discovery_pipeline.get_all_links(doi)
    
    for link in discovery_links:
        if link.dataset_doi:
            # Avoid self-references
            if link.dataset_doi.strip().lower() == doi.strip().lower():
                continue
            # Deduplicate
            if not any(d["doi"] == link.dataset_doi for d in confirmed_datasets):
                meta = get_doi_metadata(link.dataset_doi, EMAIL)
                if meta["type"] in ["dataset", "data paper", "datapaper", "software", "collection"]:
                    confirmed_datasets.append(meta)
        elif link.dataset_url:
            # URL only entry
            confirmed_datasets.append({
                "doi": None,
                "title": f"[{link.repository}] Linked Data",
                "type": "dataset (url only)",
                "url": link.dataset_url
            })

    # 2. PDF Fallback if no candidates found so far
    if not confirmed_datasets and not SKIP_PDF_SCAN:
        pdf_url = enl_url if enl_url else get_pdf_url(doi, EMAIL)
        if pdf_url:
            raw_dois = extract_dois_from_pdf(pdf_url)
            pdf_candidates = filter_likely_dataset_dois(raw_dois)
            for candidate in pdf_candidates:
                if candidate.strip().lower() != doi.strip().lower():
                    if not any(d["doi"] == candidate for d in confirmed_datasets):
                        meta = get_doi_metadata(candidate, EMAIL)
                        if meta["type"] in ["dataset", "data paper", "datapaper", "software", "collection"]:
                            confirmed_datasets.append(meta)

    return confirmed_datasets

def main():
    print("=== Data Publication Finder ===")
    
    # 1. Scrape Article DOIs from website
    print(f"Scraping publications and metadata from: {PUBLICATIONS_URL}")
    web_articles = scrape_dois(PUBLICATIONS_URL)
    print(f"Found {len(web_articles)} articles with metadata on the website.")
    
    # 2. Extract mappings from ENL file
    print(f"Scanning {ENL_FILE} for additional metadata and candidates...")
    if os.path.exists(ENL_FILE):
        enl_data = extract_data_from_enl(ENL_FILE)
        enl_mappings = enl_data.get("doi_to_url", {})
        print(f"Extracted {len(enl_mappings)} DOI-to-URL mappings.")
    else:
        print(f"Warning: {ENL_FILE} not found. Skipping ENL parsing.")
        enl_mappings = {}

    # Limit processing if configured
    if PROCESS_LIMIT:
        print(f"Limiting process to first {PROCESS_LIMIT} articles for testing.")
        web_articles = web_articles[:PROCESS_LIMIT]

    # 3. Process each article
    results = []
    print("\nProcessing articles for linked datasets...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for article in web_articles:
            doi = article["article_doi"]
            enl_url = enl_mappings.get(doi)
            futures.append(executor.submit(process_article, article, enl_url))
        
        for i, future in enumerate(tqdm(futures, desc="Discovery")):
            article = web_articles[i]
            datasets = future.result()
            
            for ds in datasets:
                results.append({
                    "article_doi": article["article_doi"],
                    "article_title": article["title"],
                    "article_authors": article["authors"],
                    "article_year": article["year"],
                    "dataset_doi": ds.get("doi"),
                    "dataset_title": ds.get("title"),
                    "dataset_type": ds.get("type"),
                    "dataset_url": ds.get("url") or (f"https://doi.org/{ds['doi']}" if ds.get('doi') else ""),
                    "source_enl_url": enl_mappings.get(article["article_doi"], "")
                })

    # 4. Save to CSV
    if results:
        keys = results[0].keys()
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nSuccess! Found {len(results)} dataset links.")
        print(f"Results saved to: {OUTPUT_FILE}")
    else:
        print("\nNo datasets found.")

if __name__ == "__main__":
    main()
