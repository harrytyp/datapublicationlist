import csv
import time
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from scraper import scrape_dois, PUBLICATIONS_URL
from enl_parser import extract_data_from_enl
from openaire import query_openaire
from crossref import query_crossref
from datacite import query_datacite
from pdf_scanner import get_pdf_url, extract_dois_from_pdf, filter_likely_dataset_dois
from resolver import is_data_publication, get_doi_metadata

# Load configuration
CONFIG_PATH = "config.json"

def load_config():
    default_config = {
        "email": "your-email@example.com",
        "output_file": "data_publication_dois.csv",
        "enl_file": "e-conversion-Converted.enl",
        "max_workers": 4,
        "process_limit": None,
        "skip_pdf_scan": False,
        "api_keys": {"openaire": None}
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                user_config = json.load(f)
                default_config.update(user_config)
            except Exception:
                pass
    return default_config

config = load_config()
EMAIL = config["email"]
OUTPUT_FILE = config["output_file"]
ENL_FILE = config["enl_file"]
MAX_WORKERS = config["max_workers"]
PROCESS_LIMIT = config["process_limit"]
SKIP_PDF_SCAN = config.get("skip_pdf_scan", False)

def process_article(article: dict, enl_url: str = None) -> list[dict]:
    """Process a single article to find linked datasets and return their metadata."""
    doi = article["article_doi"]
    candidate_dois = set()

    # Stage 3: API lookups
    candidate_dois.update(query_openaire(doi))
    candidate_dois.update(query_crossref(doi, EMAIL))
    candidate_dois.update(query_datacite(doi))

    # Stage 4: PDF fallback if no candidates found
    if not candidate_dois and not SKIP_PDF_SCAN:
        # Prioritize URL from ENL file
        pdf_url = enl_url if enl_url else get_pdf_url(doi, EMAIL)
        if pdf_url:
            raw_dois = extract_dois_from_pdf(pdf_url)
            candidate_dois.update(filter_likely_dataset_dois(raw_dois))

    # Remove the article DOI itself from candidates
    candidate_dois.discard(doi)

    # Resolve and classify
    confirmed_datasets = []
    for candidate in candidate_dois:
        time.sleep(0.1)  # Rate limiting
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
    enl_doi_to_url = {}
    enl_dataset_candidates = set()
    if os.path.exists(ENL_FILE):
        print(f"\nScanning {ENL_FILE} for additional metadata and candidates...")
        enl_data = extract_data_from_enl(ENL_FILE)
        enl_doi_to_url = enl_data["doi_to_url"]
        likely_datasets = filter_likely_dataset_dois(enl_data["dataset_dois"])
        enl_dataset_candidates.update(likely_datasets)
        print(f"Extracted {len(enl_doi_to_url)} DOI-to-URL mappings and {len(likely_datasets)} dataset candidates.")
    
    if not web_articles:
        print("No articles found on the website. Exiting.")
        return

    if PROCESS_LIMIT:
        print(f"\nLimit applied: processing only the first {PROCESS_LIMIT} articles.")
        web_articles = web_articles[:PROCESS_LIMIT]

    # 3. Process each article
    print("\nProcessing articles for linked datasets...")
    results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_article, a, enl_doi_to_url.get(a["article_doi"])): a 
            for a in web_articles
        }
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Discovery"):
            article = futures[future]
            try:
                datasets = future.result()
                if not datasets:
                    # Add article anyway but with no datasets found
                    results.append({
                        "article_doi": article["article_doi"],
                        "article_title": article.get("title", ""),
                        "article_authors": article.get("authors", ""),
                        "article_year": article.get("year", ""),
                        "enl_url": enl_doi_to_url.get(article["article_doi"], ""),
                        "dataset_doi": "",
                        "dataset_title": "",
                        "dataset_type": ""
                    })
                else:
                    for ds in datasets:
                        results.append({
                            "article_doi": article["article_doi"],
                            "article_title": article.get("title", ""),
                            "article_authors": article.get("authors", ""),
                            "article_year": article.get("year", ""),
                            "enl_url": enl_doi_to_url.get(article["article_doi"], ""),
                            "dataset_doi": ds["doi"],
                            "dataset_title": ds["title"],
                            "dataset_type": ds["type"]
                        })
            except Exception as e:
                print(f"Error processing {article['article_doi']}: {e}")

    # 4. Handle independent ENL candidates
    if enl_dataset_candidates:
        print("\nVerifying dataset candidates from ENL file...")
        for candidate in tqdm(enl_dataset_candidates, desc="Resolving ENL candidates"):
            meta = get_doi_metadata(candidate, EMAIL)
            if meta["type"] in ["dataset", "data paper", "datapaper", "software", "collection"]:
                results.append({
                    "article_doi": "Independent ENL Candidate",
                    "article_title": "",
                    "article_authors": "",
                    "article_year": "",
                    "enl_url": "",
                    "dataset_doi": meta["doi"],
                    "dataset_title": meta["title"],
                    "dataset_type": meta["type"]
                })

    # Write output
    print(f"\nSaving results to {OUTPUT_FILE}...")
    keys = ["article_doi", "article_title", "article_authors", "article_year", "enl_url", "dataset_doi", "dataset_title", "dataset_type"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    # Count datasets
    found_datasets = [r for r in results if r["dataset_doi"]]
    print(f"Done! {len(found_datasets)} dataset-article mappings saved to {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()
