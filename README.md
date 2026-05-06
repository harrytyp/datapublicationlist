# Data Publication Finder

A robust, modular Python pipeline to identify research datasets linked to scientific publications by integrating multiple metadata sources and full-text scanning.

## History & Credits

This tool was originally developed by **Kolja Knodel**, Data Steward of the [e-conversion](https://www.e-conversion.de/) research cluster. 

The project's origin and core purpose is to automate the discovery of formally declared data publications from traditional publication lists. The built-in website scraper was the first input source created, specifically tailored to help research clusters track their data impact by cross-referencing their official WordPress-based publication records with global data registries.

## Overview

This tool automates the discovery of formally and informally linked research data by cross-referencing publication lists with major metadata APIs and domain-specific repositories.

**Current Status (May 2026):** 4/8 adapters working, with DataCite providing the strongest dataset discovery capability. Tool successfully finds dataset links for registered publications.

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
    - Queries **DataCite**, **OpenAIRE Graph**, and **Crossref** for formal links.
4.  **Domain-Specific Discovery**: 
    - Queries specialized registries like **DOE Data Explorer**.
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

| Service | Category | Status | Domain | Confidence | Notes |
|---|---|---|---|---|---|
| **DataCite** | Core | ✅ **Working** | All domains | Depositor-asserted | Most effective adapter (5+ links found in testing) |
| **OpenAIRE Graph** | Core | ✅ **Working** | All domains | Confirmed/Inferred | No errors, but limited results (indexing lag) |
| **Crossref** | Core | ✅ **Working** | All domains | Confirmed | Fixed URL encoding; 404s indicate unregistered DOIs |
| **DOE Data Explorer** | Domain | ✅ **Working** | Energy, Materials | Confirmed | No errors in testing |
| **HEPData** | Domain | ❌ **Disabled** | Particle Physics | N/A | 403 Forbidden - API access restricted |
| **NASA ADS / SciX** | Domain | ❌ **Disabled** | Astrophysics | N/A | Requires API token (not configured) |
| **Materials Data Facility** | Domain | ❌ **Disabled** | Materials Science | N/A | 404 Not Found - endpoint changed/deprecated |
| **NOMAD / OPTIMADE** | Domain | ❌ **Disabled** | Computational Mat. | N/A | API doesn't support publication-to-dataset queries |

### Service Status Details (May 2026)

**✅ Working Services:**
- **DataCite**: Primary dataset discovery service. Found multiple Figshare-hosted datasets in testing. Uses reverse lookup to find datasets that reference publications.
- **OpenAIRE**: Comprehensive linkage database. Runs without errors but may have indexing delays for newer publications.
- **Crossref**: Official DOI registry relationships. Only works for publications registered with Crossref metadata.
- **DOE Data Explorer**: U.S. Department of Energy data portal. Reliable for energy/materials research.

**❌ Disabled Services:**
- **HEPData**: CERN's particle physics data repository. Currently returns 403 Forbidden errors, indicating access restrictions or API changes.
- **NASA ADS**: Astrophysics data system. Requires API token configuration (not included for privacy/security).
- **MDF**: Materials Data Facility. Globus endpoint returns 404, suggesting the service has moved or changed.
- **NOMAD**: Computational materials database. API v1 doesn't support searchable publication-to-dataset relationships.

### Testing Results

Recent testing (May 2026) with multiple publications found:
- **5 dataset links** discovered across test publications
- **DataCite** was the most effective (4/5 links)
- **OpenAIRE/Crossref** returned 0 links (likely due to indexing delays)
- All working adapters completed without errors
- Broken adapters properly disabled to avoid confusion

## Recent Updates (May 2026)

- **Fixed Crossref URL encoding**: Resolved 404 errors caused by improper DOI encoding in API paths
- **Updated DataCite adapter**: Improved relation type filtering and confidence levels
- **Fixed OpenAIRE adapter**: Added pagination, inverse lookups, and provider-based confidence scoring
- **Disabled broken adapters**: HEPData (403 Forbidden), MDF (404), NOMAD (unsupported API)
- **Enhanced error handling**: Better logging and graceful failure handling across all adapters

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
├── inputs/              # Drop-in publication files (.enl, .ris, .json)
├── ignored/             # All development files, test scripts, cache files, outputs (ignored - not in git)
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
