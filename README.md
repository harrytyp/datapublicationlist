# Data Publication Finder

A robust, modular Python pipeline to identify research datasets linked to scientific publications by integrating multiple metadata sources and full-text scanning.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/status-active-green)

## Table of Contents
- [Overview](#overview)
- [How it Works](#how-it-works)
- [Input Sources](#input-sources)
- [Supported Discovery Services](#supported-discovery-services)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [History & Credits](#history--credits)
- [License](#license)

## Overview
 
 This tool automates the discovery of formally and informally linked research data by cross-referencing publication lists with major metadata APIs and domain-specific repositories.
 
 ### The core problem it solves
 Research data is only truly Findable if it is registered in a searchable index. In practice, many datasets are deposited in FAIR-compliant repositories (Zenodo, Figshare, etc.) but the link between the dataset and its parent publication is never surfaced — it sits buried in a DataCite metadata record that no one actively queries. The data is technically FAIR, but functionally invisible to the research community and the institution that funded it.
 
 This problem becomes particularly acute for larger research clusters and collaborative projects — such as DFG Clusters of Excellence, EU-funded consortia, or national research initiatives — which are routinely expected by funders and reviewers to demonstrate that their publications are accompanied by openly published data. With dozens or hundreds of papers produced across multiple institutes and working groups, there is no practical way to manually verify data publication compliance at scale. A data steward cannot simply ask every PI whether their dataset was deposited; the answer needs to be evidenced, not asserted.
 
 This tool closes that gap by automating the retrieval of existing FAIR-compliant links across multiple global registries, making the latent FAIRness of a research cluster's data visible in one consolidated report — and producing an auditable, machine-readable record that can be shared directly with funders or oversight bodies.
 
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
 
 **Current Status:** 4/8 adapters working, with DataCite providing the strongest dataset discovery capability. Tool successfully finds dataset links for registered publications.
 
 | Service | Category | Status | Domain | Confidence | Notes |

|---|---|---|---|---|---|
| **DataCite** | Core | ✅ **Working** | All domains | Depositor-asserted | Most effective adapter (5+ links found in testing); found Figshare-hosted datasets |
| **OpenAIRE Graph** | Core | ✅ **Working** | All domains | Confirmed/Inferred | No errors, but limited results (indexing lag) |
| **Crossref** | Core | ✅ **Working** | All domains | Confirmed | Fixed URL encoding; 404s indicate unregistered DOIs |
| **DOE Data Explorer** | Domain | ✅ **Working** | Energy, Materials | Confirmed | No errors in testing |
| **HEPData** | Domain | ❌ **Disabled** | Particle Physics | N/A | 403 Forbidden - API access restricted |
| **NASA ADS / SciX** | Domain | ❌ **Disabled** | Astrophysics | N/A | Requires API token (not configured) |
| **Materials Data Facility** | Domain | ❌ **Disabled** | Materials Science | N/A | 404 Not Found - endpoint changed/deprecated |
| **NOMAD / OPTIMADE** | Domain | ❌ **Disabled** | Computational Mat. | N/A | API doesn't support publication-to-dataset queries |

### Testing Results

Recent testing with multiple publications found:
- **5 dataset links** discovered across test publications
- **DataCite** was the most effective (4/5 links)
- **OpenAIRE/Crossref** returned 0 links (likely due to indexing delays)
- All working adapters completed without errors
- Broken adapters properly disabled to avoid confusion

See [CHANGELOG.md](CHANGELOG.md) for version history and recent updates.

## Project Structure

```text
├── main.py              # Main pipeline entry point
├── config.json          # User configuration (Email, limits, etc.)
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

**Prerequisites:**
- Python 3.8 or higher

1. Clone the repository:
   ```bash
   git clone https://github.com/harrytyp/datapublicationlist.git
   cd datapublicationlist
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
- **`logging`**: Configure logging output and verbosity.
- **`adapters`**: Enable or disable specific discovery services.

Example `config.json`:
```json
{
  "email": "you@example.com",
  "skip_pdf_scan": true,
  "process_limit": 10,
  "logging": {
    "level": "INFO",
    "file": "discovery.log",
    "console": true,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  "adapters": {
    "datacite": true,
    "openaire": true,
    "crossref": true,
    "doe_dde": true,
    "hepdata": false,
    "nasa_ads": false,
    "mdf": false,
    "nomad": false
  }
}
```

## Usage
 
 Run the main script:
 ```bash
 python main.py
 ```
 
 The tool generates two primary output files:
 1. **CSV (`data_publication_dois.csv`)**: A machine-readable table of all discovered links.
 2. **Markdown Report (`discovery_report.md`)**: A human-readable report following FAIR (Findable, Accessible, Interoperable, Reusable) principles, grouping datasets by publication and relation type, with confidence indicators and a final JSON data block.
 
 ### Sample Output
 
 #### CSV Format
 The CSV includes columns such as `doi`, `title`, `dataset_url`, `dataset_title`, `adapter`, and `confidence`.
 
 Example output:
 ```csv
 doi,title,dataset_url,dataset_title,adapter,confidence
 10.1038/s41586-020-2649-2,"Structural basis for...",https://doi.org/10.6084/m9.figshare.12671864,"Cryo-EM structure of...",DataCite,high
 ```
 
 #### FAIR Markdown Report
 The report is designed as an instrument for FAIR data management:
 - **Findable**: DOI-centric design anchors all publications and datasets to persistent identifiers, querying multiple global indices (DataCite, Crossref, OpenAIRE) to surface hidden links.
 - **Accessible**: All data is retrieved via standardized open APIs and presented with direct, clickable hyperlinks to repositories.
 - **Interoperable**: Utilizes community-standard relation types (e.g., `IsSupplementTo`) and provides a machine-readable JSON block for downstream automation.
 - **Reusable**: Implements a trust-signal system with confidence indicators (✅ Curated, ☑️ Verified, ⚠️ Unverified) and full provenance tracking of the discovery source.
 
 **Report Structure:**
 - **Summary**: Global stats on processed publications and dataset discovery.
 - **Detailed View**: Each publication is a section with its DOI, authors, and a short description.
 - **Dataset Grouping**: Datasets are grouped by relation with confidence badges.
 - **Machine-Readable Block**: A nested JSON array at the end for easy parsing.


## History & Credits

This tool was originally developed by **Kolja Knodel**, Data Steward of the [e-conversion](https://www.e-conversion.de/) research cluster.

The project's origin and core purpose is to automate the discovery of formally declared data publications from traditional publication lists. The built-in website scraper was the first input source created, specifically tailored to help research clusters track their data impact by cross-referencing their official WordPress-based publication records with global data registries.

## License

MIT
