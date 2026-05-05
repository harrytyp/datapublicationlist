# Stage 3b: Domain-Specific Discovery

This module extends the publication-to-dataset discovery pipeline with domain-specific adapters for Energy, Materials Science, and High-Energy Physics.

## Supported Services

| Service | Adapter class | Enabled by default | Auth required | Domain | Confidence |
|---|---|---|---|---|---|
| DOE Data Explorer | `DOEDataExplorerAdapter` | ✅ Yes | No | Energy, materials, physics | Confirmed |
| HEPData | `HEPDataAdapter` | ✅ Yes | No | High-energy physics | Confirmed |
| NASA ADS / SciX | `NASAADSAdapter` | ❌ No | Free API token (`ADS_API_TOKEN`) | Astrophysics, space physics | Inferred |
| Materials Data Facility | `MDFAdapter` | ❌ No | No | Materials science | Inferred |
| NOMAD / OPTIMADE | `NOMADOptimadeAdapter` | ❌ No | No | Computational materials | Inferred |

## Installation

Install the required dependencies:
```bash
pip install requests pydantic PyYAML
```

## Quick Start

```python
from stage3b.config import Stage3bConfig
from stage3b.pipeline import Stage3bPipeline

config = Stage3bConfig()
pipeline = Stage3bPipeline(config)

doi = "10.1021/acs.inorgchem.6c00670"
links = pipeline.get_all_links(doi)

for link in links:
    print(f"Found {link.repository} dataset: {link.dataset_doi or link.dataset_url} ({link.confidence})")
```

## Configuration

Override defaults by passing a dictionary to `Stage3bConfig.from_dict()` or by setting environment variables for secrets:

- **`ADS_API_TOKEN`**: Required for the NASA ADS adapter.

## Output Format

The primary output is a list of `DatasetLink` objects:
- `source_doi`: The input publication DOI.
- `dataset_doi`: DOI of the found dataset.
- `dataset_url`: Landing page URL.
- `confidence`: `"confirmed"` (structured metadata) or `"inferred"` (free-text or untyped).
- `repository`: The source service (e.g., `DOE_DDE`).

## Limitations

- **MDF, NOMAD, and ADS**: These adapters are experimental and disabled by default. Results are marked as `inferred` and should be manually validated.
- **DDE Filtering**: The DOE adapter performs strict client-side filtering on `related_identifiers` to ensure results are not just general text matches.
