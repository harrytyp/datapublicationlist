import os
from typing import Optional
from pydantic import BaseModel, Field

class AdapterConfig(BaseModel):
    enabled: bool
    base_url: str
    max_results: int = 100
    timeout_seconds: int = 15
    rate_limit_delay_seconds: float = 1.0

class NASAADSConfig(AdapterConfig):
    api_token: Optional[str] = None

class HttpConfig(BaseModel):
    retry_attempts: int = 3
    retry_backoff_seconds: float = 2.0
    rate_limit_delay_seconds: float = 1.0
    user_agent: str = "stage3b-pipeline/1.0 (mailto:you@example.com)"

class Stage3bConfig(BaseModel):
    doe_data_explorer: AdapterConfig = AdapterConfig(
        enabled=True,
        base_url="https://www.osti.gov/dataexplorer/api/v1"
    )
    hepdata: AdapterConfig = AdapterConfig(
        enabled=True,
        base_url="https://www.hepdata.net"
    )
    nasa_ads: NASAADSConfig = NASAADSConfig(
        enabled=False,
        base_url="https://api.adsabs.harvard.edu/v1",
        api_token=os.getenv("ADS_API_TOKEN")
    )
    mdf: AdapterConfig = AdapterConfig(
        enabled=False,
        base_url="https://acdc.alcf.anl.gov/mdf"
    )
    nomad_optimade: AdapterConfig = AdapterConfig(
        enabled=False,
        base_url="https://nomad-lab.eu/prod/v1"
    )
    http: HttpConfig = HttpConfig()

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
