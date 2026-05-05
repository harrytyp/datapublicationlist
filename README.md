# Data Publication Finder

A robust, modular Python pipeline to identify research datasets linked to scientific publications by integrating multiple metadata sources and full-text scanning.

## Overview

This tool automates the discovery of formally and informally linked research data by cross-referencing a WordPress-based publication list with major metadata APIs, domain-specific repositories, and full-text PDF scanning.

### How it Works

The discovery process follows a multi-stage pipeline:

1.  **Flexible Input Collection**: 
    - The tool can gather publications from multiple sources simultaneously:
        - **Website**: Scrapes WordPress-based lists (e.g., e-conversion).
        - **EndNote (.enl)**: Parses binary library files for DOIs and PDF links.
        - **RIS (.ris)**: Standard citation format supported by most reference managers.
        - **JSON**: Simple structured list of articles.
2.  **Universal Deduplication**: 
    - Articles from all sources are merged and deduplicated by DOI.
3.  **Core API Discovery**: 
    - Queries **OpenAIRE Graph**, **Crossref**, and **DataCite** for formal links.
4.  **Domain-Specific Discovery**: 
    - Queries specialized registries like **DOE Data Explorer** and **HEPData**.
5.  **Full-Text Fallback (Optional)**: 
    - Scans article PDFs (via EndNote links or Unpaywall) for repository mentions.
6.  **Validation & Enrichment**: 
    - Confirms candidates and fetches metadata (Titles, Types).

## Input Sources

The tool features a **Zero-Config Drop-in** system. Simply place your publication files into the **`inputs/`** folder. The pipeline automatically detects the format and processes the content.

### Supported Drop-in Formats:
- **EndNote (`.enl`)**: Scans binary libraries for DOIs and PDF links.
- **RIS (`.ris`)**: Standard citation format (Zotero, Mendeley, etc.).
- **JSON (`.json`)**: Custom lists of articles.

### How to use:
1.  Place your `.enl` or `.ris` files into the `inputs/` directory.
2.  (Optional) The **Website Scraper** is enabled by default in `config.json` to fetch the cluster's official list.
3.  Run `python main.py`.

The tool will merge articles from all files in the `inputs/` folder and the website, deduplicate them by DOI, and start the discovery process.

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
