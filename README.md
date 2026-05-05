# Data Publication Finder

A robust, modular Python pipeline to identify research datasets linked to scientific publications by integrating multiple metadata sources and full-text scanning.

## Overview

This tool automates the discovery of formally and informally linked research data by cross-referencing a WordPress-based publication list with major metadata APIs, domain-specific repositories, and full-text PDF scanning.

### How it Works

The discovery process follows a multi-stage pipeline:

1.  **Metadata Acquisition**: 
    - Scrapes the research cluster's publication list for DOIs, titles, and authors.
    - Results are cached locally in `scraper_cache.json` for performance.
2.  **EndNote Linkage**: 
    - Parses `.enl` library files to map article DOIs to direct PDF or repository URLs.
    - Intelligently handles "dirty" identifiers and legacy mappings.
3.  **Core API Discovery**: 
    - Queries **OpenAIRE Graph**, **Crossref**, and **DataCite** for formal `is-supplemented-by` or `has-part` relationships.
4.  **Domain-Specific Discovery**: 
    - Queries specialized registries like **DOE Data Explorer** and **HEPData** for formally declared data links in Physics and Energy research.
5.  **Full-Text Fallback (Optional)**: 
    - If no formal link is found, scans the article's PDF (via ENL link or Unpaywall) for DOI mentions of known data repositories.
6.  **Validation & Enrichment**: 
    - Confirms all candidates against DataCite/Crossref and fetches human-readable titles and resource types.

## Supported Discovery Services

| Service | Category | Enabled by default | Domain | Confidence |
|---|---|---|---|---|
| OpenAIRE Graph | Core | ✅ Yes | All domains | Confirmed |
| Crossref | Core | ✅ Yes | All domains | Confirmed |
| DataCite | Core | ✅ Yes | All domains | Confirmed |
| DOE Data Explorer | Domain | ✅ Yes | Energy, Materials | Confirmed |
| HEPData | Domain | ✅ Yes | Particle Physics | Confirmed |
| NASA ADS / SciX | Domain | ❌ No | Astrophysics | Inferred |
| Materials Data Facility | Domain | ❌ No | Materials Science | Inferred |
| NOMAD / OPTIMADE | Domain | ❌ No | Computational Mat. | Inferred |

## Project Structure

```text
├── main.py              # Main pipeline entry point
├── config.json          # User configuration (Email, limits, etc.)
├── test_pdf_scan.py     # Diagnostic tool for PDF scanning
├── src/                 # Internal discovery logic
│   ├── adapters/        # Discovery service implementations
│   ├── discovery_pipeline.py
│   ├── discovery_models.py
│   ├── utils.py         # Shared HTTP & DOI utilities
│   └── ... (scrapers, parsers, scanners)
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/harrytyp/datapublicationlist.git
   cd publication_finder
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.json` before running. Key settings include:

- **`email`**: Required for the "polite pool" (Crossref/Unpaywall).
- **`skip_pdf_scan`**: Set to `true` (default) for fast API-only discovery.
- **`process_limit`**: Set to a number for testing, or `null` for full run.
- **`adapters`**: Enable or disable specific discovery services.

## Usage

Run the main script:
```bash
python main.py
```

The results are saved to `data_publication_dois.csv` with full provenance, including article metadata and the originating dataset repository.

## License

MIT
