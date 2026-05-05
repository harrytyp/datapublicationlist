# Data Publication Finder

A modular Python tool to identify research datasets linked to a research cluster's publication list. 

## Overview

This tool automates the discovery of formally and informally linked research data by cross-referencing a WordPress-based publication list with major metadata APIs and full-text PDF scanning.

### Features

- **Dual DOI Sourcing**: Merges publications scraped from the e-conversion website with entries from an EndNote (`.enl`) library.
- **Smart Metadata Parsing**: Extracts BibTeX metadata from the web and cleans "dirty" DOIs from EndNote URLs.
- **Multi-Stage Discovery**:
  - Queries **OpenAIRE**, **Crossref**, and **DataCite** for formal dataset relations.
  - Falls back to **Full-Text PDF Scanning** via Unpaywall and EndNote links.
- **Source Mapping**: Produces a comprehensive CSV mapping every dataset found back to its source article metadata.
- **Efficient & Respectful**: Features a local scraping cache and built-in rate-limiting.

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
