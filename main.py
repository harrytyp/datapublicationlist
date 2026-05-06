import csv
import json
import logging
import os
import sys
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
        "logging": {
            "level": "INFO",
            "file": None,
            "console": True,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "input_sources": {},
        "adapters": {}
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            user_config = json.load(f)
            default_config.update(user_config)
    return default_config

def setup_logging(config):
    """Setup logging based on configuration."""
    logging_config = config.get("logging", {})
    level = getattr(logging, logging_config.get("level", "INFO").upper())
    log_format = logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler if enabled
    if logging_config.get("console", True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if file specified
    log_file = logging_config.get("file")
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "."
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

config = load_config()
setup_logging(config)

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
                
                # Fetch article metadata for the report (including description)
                art_meta = get_doi_metadata(article["article_doi"], EMAIL)
                
                if not datasets:
                    # Still add the article to results so it appears in the report
                    results.append({
                        "article_doi": article["article_doi"],
                        "article_title": article["title"],
                        "article_authors": article["authors"],
                        "article_year": article["year"],
                        "article_description": art_meta.get("description", "No description available."),
                        "datasets": []
                    })
                else:
                    dataset_list = []
                    for ds in datasets:
                        dataset_list.append({
                            "dataset_doi": ds.get("doi"),
                            "dataset_title": ds.get("title"),
                            "dataset_type": ds.get("type"),
                            "dataset_url": ds.get("url") or (f"https://doi.org/{ds['doi']}" if ds.get('doi') else ""),
                            "discovery_source": ", ".join(ds.get("discovery_sources", ["Unknown"])),
                            "is_strong": ds.get("is_strong", False),
                            "relation_type": ds.get("relation_type", "Unknown")
                        })
                    
                    results.append({
                        "article_doi": article["article_doi"],
                        "article_title": article["title"],
                        "article_authors": article["authors"],
                        "article_year": article["year"],
                        "article_description": art_meta.get("description", "No description available."),
                        "datasets": dataset_list
                    })
            except Exception as e:
                print(f"Error processing article {article['article_doi']}: {e}")
    
    # 3. Save to Markdown Report
    if results:
        # Confidence indicator logic
        def get_confidence(repo, is_strong):
            curated_repos = {"CCDC", "FIZ ICSD", "Dryad"}
            if any(cr in repo for cr in curated_repos):
                return "✅ Curated deposit"
            if is_strong:
                return "☑️ Verified"
            return "⚠️ Unverified"

        # Summary stats
        total_pubs = len(results)
        total_datasets = sum(len(r["datasets"]) for r in results)
        repo_counts = {}
        conf_counts = {"✅ Curated deposit": 0, "☑️ Verified": 0, "⚠️ Unverified": 0}
        
        for r in results:
            for ds in r["datasets"]:
                repo = ds["discovery_source"].split(",")[0].strip()
                repo_counts[repo] = repo_counts.get(repo, 0) + 1
                conf = get_confidence(ds["discovery_source"], ds["is_strong"])
                conf_counts[conf] = conf_counts.get(conf, 0) + 1

        md_report = "# Data Discovery Report\n\n"
        md_report += f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        md_report += "## Summary\n"
        md_report += f"- **Total publications processed:** {total_pubs}\n"
        md_report += f"- **Total datasets found:** {total_datasets}\n\n"
        
        md_report += "### Breakdown by Repository\n"
        for repo, count in repo_counts.items():
            md_report += f"- {repo}: {count}\n"
        md_report += "\n"
        
        md_report += "### Breakdown by Confidence\n"
        for conf, count in conf_counts.items():
            md_report += f"- {conf}: {count}\n"
        md_report += "\n---\n\n"
        
        # Detailed Publications
        for r in results:
            doi = r["article_doi"]
            datasets = r["datasets"]
            
            md_report += f"## {r['article_title']}\n"
            md_report += f"**DOI:** [{doi}](https://doi.org/{doi}) | **Year:** {r['article_year']}\n"
            md_report += f"**Authors:** {r['article_authors']}\n"
            md_report += f"**Description:** {r['article_description']}\n"
            md_report += f"**Datasets:** `{len(datasets)} datasets`\n\n"
            
            if not datasets:
                md_report += "_No datasets found_\n\n"
            else:
                # Group by relation type
                relations = {}
                for ds in datasets:
                    rel = ds["relation_type"]
                    if rel not in relations: relations[rel] = []
                    relations[rel].append(ds)
                
                for rel, ds_list in relations.items():
                    md_report += f"### {rel}\n"
                    md_report += "| Dataset Title | Repository | Confidence | Type |\n"
                    md_report += "| --- | --- | --- | --- |\n"
                    for ds in ds_list:
                        url = ds["dataset_url"]
                        title = ds["dataset_title"]
                        repo = ds["discovery_source"]
                        conf = get_confidence(repo, ds["is_strong"])
                        dtype = ds["dataset_type"]
                        md_report += f"| [{title}]({url}) | {repo} | {conf} | {dtype} |\n"
                    md_report += "\n"
            
            md_report += "---\n\n"
            
        # JSON block at the end
        md_report += "## Machine-Readable Data\n\n"
        md_report += "```json\n"
        json_data = []
        for r in results:
            json_data.append({
                "publication": {
                    "doi": r["article_doi"],
                    "title": r["article_title"],
                    "year": r["article_year"],
                    "authors": r["article_authors"],
                    "description": r["article_description"],
                    "datasets": r["datasets"]
                }
            })
        md_report += json.dumps(json_data, indent=2)
        md_report += "\n```\n"
        
        with open("discovery_report.md", "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"Markdown report saved to: discovery_report.md")
    
    # 4. Save to CSV
    if results:
        # Flatten for CSV
        csv_rows = []
        for r in results:
            for ds in r["datasets"]:
                csv_rows.append({
                    "article_doi": r["article_doi"],
                    "article_title": r["article_title"],
                    "article_authors": r["article_authors"],
                    "article_year": r["article_year"],
                    "dataset_doi": ds["dataset_doi"],
                    "dataset_title": ds["dataset_title"],
                    "dataset_type": ds["dataset_type"],
                    "dataset_url": ds["dataset_url"],
                    "discovery_source": ds["discovery_source"],
                    "is_strong": ds["is_strong"],
                    "relation_type": ds["relation_type"]
                })
        
        if csv_rows:
            keys = csv_rows[0].keys()
            with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(csv_rows)
            print(f"Results saved to: {OUTPUT_FILE}")
        else:
            print("\nNo datasets found for any article.")
    else:
        print("\nNo articles processed.")


if __name__ == "__main__":
    main()
