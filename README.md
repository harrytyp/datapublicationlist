# Data Publication Finder

A modular Python tool to identify research datasets linked to a research cluster's publication list. 

## Overview

This tool automates the discovery of formally and informally linked research data by cross-referencing a WordPress-based publication list with major metadata APIs and full-text PDF scanning.

### How it Works

The tool follows a multi-stage pipeline to ensure maximum discovery:

1.  **Metadata Acquisition (Website)**: 
    - The tool scrapes all 29 pages of the [e-conversion publication list](https://www.e-conversion.de/de/publikationen/).
    - It extracts full BibTeX metadata (DOI, Title, Authors, Year) for each entry.
    - Results are cached in `scraper_cache.json` for instant reuse.
2.  **EndNote Linkage (ENL File)**: 
    - It parses the provided `.enl` library file using a binary-safe regex.
    - It maps the website DOIs to the corresponding URLs/Links stored in EndNote.
    - It intelligently cleans "dirty" DOIs (e.g., handles cases where ISSNs are concatenated to the DOI in URLs).
3.  **Formal API Discovery**: 
    - For each article, the tool queries **OpenAIRE**, **Crossref**, and **DataCite**.
    - It looks for formal metadata relationships such as `is-supplemented-by` or `has-part`.
4.  **Full-Text Fallback (PDF Scanning)**: 
    - If no formal link is found, the tool attempts to scan the article's PDF.
    - **Priority**: It uses the direct link found in your `.enl` file.
    - **Fallback**: It queries **Unpaywall** for an Open Access PDF URL.
    - The PDF is downloaded in memory and scanned for DOIs belonging to known data repositories (Zenodo, Figshare, Dryad, etc.).
5.  **Validation & Metadata Enrichment**: 
    - Every candidate dataset found is validated against **DataCite/Crossref** to confirm its resource type.
    - The tool fetches the **Dataset Title** and **Type** to provide a human-readable report.
6.  **Consolidated Output**: 
    - All findings are merged into a single CSV, mapping each source article to its linked datasets.

## Project Structure

- `main.py`: Orchestrates the entire pipeline.
- `scraper.py`: Handles website scraping with pagination and caching.
- `enl_parser.py`: Parses EndNote `.enl` files for DOI-to-URL mappings.
- `openaire.py`, `crossref.py`, `datacite.py`: API client modules.
- `pdf_scanner.py`: Extracts DOIs from PDF full-text.
- `resolver.py`: Resolves DOI metadata and classifies resource types.
- `config.json`: Configuration for API keys, email, and processing limits.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd publication_finder
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.json` before running:

```json
{
    "email": "your-email@example.com",
    "output_file": "data_publication_dois.csv",
    "enl_file": "e-conversion-Converted.enl",
    "max_workers": 4,
    "process_limit": null
}
```

- **email**: Required for the Crossref/Unpaywall "polite pool".
- **process_limit**: Set to a number (e.g., `5`) for testing, or `null` for full execution.

## Usage

Run the main script:

```bash
python main.py
```

The results will be saved to `data_publication_dois.csv` with the following columns:
- `article_doi`, `article_title`, `article_authors`, `article_year`
- `enl_url`: Link to the article/PDF found in EndNote.
- `dataset_doi`, `dataset_title`, `dataset_type`: Metadata for the identified dataset.

## License

MIT
