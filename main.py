import csv
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

from src.pdf_scanner import get_pdf_url, extract_dois_from_pdf, filter_likely_dataset_dois
from src.resolver import is_data_publication, get_doi_metadata
from src.discovery_pipeline import DiscoveryPipeline
from src.input_pipeline import InputPipeline

# Configuration
CONFIG_PATH = "config.json"

def load_config():
    """Load configuration from config.json."""
    default_config = {
        "email": "your-email@example.com",
        "output_file": "data_publication_dois.csv",
        "max_workers": 4,
        "process_limit": None,
        "skip_pdf_scan": True,
        "input_sources": {},
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
MAX_WORKERS = config["max_workers"]
PROCESS_LIMIT = config["process_limit"]
SKIP_PDF_SCAN = config.get("skip_pdf_scan", True)

# Initialize Pipelines
input_pipeline = InputPipeline(config)
discovery_pipeline = DiscoveryPipeline(config)

def process_article(article: dict) -> list[dict]:
    """Process a single article to find linked datasets and return their metadata."""
    doi = article["article_doi"]
    extra = article.get("extra_data", {})
    enl_url = extra.get("enl_url")
    
    confirmed_datasets = []

    # 1. Unified API Discovery (Core + Domain-Specific)
    discovery_links = discovery_pipeline.get_all_links(doi)
    
    for link in discovery_links:
        if link.dataset_doi:
            if link.dataset_doi.strip().lower() == doi.strip().lower():
                continue
            
            # Find if we already have this DOI
            existing_meta = next((d for d in confirmed_datasets if d.get("doi") == link.dataset_doi), None)
            
            if existing_meta:
                # Add source to existing if not present
                if link.repository not in existing_meta["discovery_sources"]:
                    existing_meta["discovery_sources"].append(link.repository)
            else:
                meta = get_doi_metadata(link.dataset_doi, EMAIL)
                if meta["type"] in ["dataset", "data paper", "datapaper", "software", "collection"]:
                    meta["discovery_sources"] = [link.repository]
                    meta["is_strong"] = link.is_strong
                    meta["relation_type"] = link.relation_type
                    confirmed_datasets.append(meta)
        elif link.dataset_url:
            confirmed_datasets.append({
                "doi": None,
                "title": f"[{link.repository}] Linked Data",
                "type": "dataset (url only)",
                "url": link.dataset_url,
                "discovery_sources": [link.repository],
                "is_strong": link.is_strong,
                "relation_type": link.relation_type
            })

    # 2. PDF Fallback if no candidates found so far
    if not confirmed_datasets and not SKIP_PDF_SCAN:
        pdf_url = enl_url if enl_url else get_pdf_url(doi, EMAIL)
        if pdf_url:
            raw_dois = extract_dois_from_pdf(pdf_url)
            pdf_candidates = filter_likely_dataset_dois(raw_dois)
            for candidate in pdf_candidates:
                if candidate.strip().lower() != doi.strip().lower():
                    # Find if we already have this DOI
                    existing_meta = next((d for d in confirmed_datasets if d.get("doi") == candidate), None)
                    if existing_meta:
                        if "PDF Scanner" not in existing_meta["discovery_sources"]:
                            existing_meta["discovery_sources"].append("PDF Scanner")
                    else:
                        meta = get_doi_metadata(candidate, EMAIL)
                        if meta["type"] in ["dataset", "data paper", "datapaper", "software", "collection"]:
                            meta["discovery_sources"] = ["PDF Scanner"]
                            confirmed_datasets.append(meta)

    return confirmed_datasets

def main():
    print("=== Data Publication Finder ===")
    
    # 1. Collect Article DOIs from all sources
    print("Collecting publications from input sources...")
    articles = input_pipeline.collect_articles()
    
    if not articles:
        print("No articles found in any input source. Check your config.json.")
        return

    # Limit processing if configured
    if PROCESS_LIMIT:
        print(f"Limiting process to first {PROCESS_LIMIT} articles for testing.")
        articles = articles[:PROCESS_LIMIT]

    # 2. Process each article
    results = []
    print(f"\nProcessing {len(articles)} articles for linked datasets...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_article, art): art for art in articles}
        
        for future in tqdm(futures, total=len(futures), desc="Discovery"):
            article = futures[future]
            try:
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
                        "discovery_source": ", ".join(ds.get("discovery_sources", ["Unknown"])),
                        "input_source": article.get("extra_data", {}).get("source_name", "Unknown"),
                        "is_strong": ds.get("is_strong", False),
                        "relation_type": ds.get("relation_type", "Unknown")
                    })
            except Exception as e:
                print(f"Error processing article {article['article_doi']}: {e}")

    # 3. Save to Markdown Report
    if results:
        md_report = "# Data Discovery Report\n\n"
        md_report += f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Group by article
        articles_map = {}
        for r in results:
            doi = r["article_doi"]
            if doi not in articles_map:
                articles_map[doi] = {
                    "title": r["article_title"],
                    "authors": r["article_authors"],
                    "year": r["article_year"],
                    "strong": [],
                    "weak": []
                }
            if r["is_strong"]:
                articles_map[doi]["strong"].append(r)
            else:
                articles_map[doi]["weak"].append(r)
        
        for doi, data in articles_map.items():
            md_report += f"## {data['title']}\n"
            md_report += f"**DOI:** [{doi}](https://doi.org/{doi}) | **Year:** {data['year']}\n\n"
            md_report += f"**Authors:** {data['authors']}\n\n"
            
            if data["strong"]:
                md_report += "### ✅ Formal Supplements\n"
                md_report += "| Dataset Title | Repository / Source | Relation |\n"
                md_report += "| --- | --- | --- |\n"
                for ds in data["strong"]:
                    url = ds["dataset_url"]
                    title = ds["dataset_title"]
                    md_report += f"| [{title}]({url}) | {ds['discovery_source']} | {ds['relation_type']} |\n"
                md_report += "\n"
                
            if data["weak"]:
                md_report += "### 🔍 Other Mentions & Related Data\n"
                md_report += "| Dataset Title | Repository / Source | Relation |\n"
                md_report += "| --- | --- | --- |\n"
                for ds in data["weak"]:
                    url = ds["dataset_url"]
                    title = ds["dataset_title"]
                    md_report += f"| [{title}]({url}) | {ds['discovery_source']} | {ds['relation_type']} |\n"
                md_report += "\n"
            
            md_report += "---\n\n"
            
        with open("discovery_report.md", "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"Markdown report saved to: discovery_report.md")

    # 4. Save to CSV
    if results:
        # Filter out the internal 'is_strong' for the CSV if desired, or keep it
        keys = results[0].keys()
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to: {OUTPUT_FILE}")
    else:
        print("\nNo datasets found.")

if __name__ == "__main__":
    main()
