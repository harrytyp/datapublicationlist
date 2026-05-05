from typing import Literal, List, Dict, Optional
from pydantic import BaseModel, Field

class DatasetLink(BaseModel):
    """Normalized output record produced by every adapter."""
    source_doi: str
    dataset_doi: Optional[str] = None
    dataset_url: Optional[str] = None
    relation_type: str = "Unknown"
    repository: str
    confidence: Literal["confirmed", "inferred"]
    raw: Dict = Field(default_factory=dict)

class AdapterResult(BaseModel):
    """Wraps the output of one adapter run."""
    adapter_name: str
    input_doi: str
    links: List[DatasetLink] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    skipped: bool = False
