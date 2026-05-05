from abc import ABC, abstractmethod
import logging
from typing import Optional
from ..models import AdapterResult

logger = logging.getLogger(__name__)

class BaseAdapter(ABC):
    """Abstract base class for all dataset discovery adapters."""
    
    name: str = "Base"
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.enabled

    @abstractmethod
    def fetch(self, doi: str) -> AdapterResult:
        """All logic for one DOI lives here."""
        pass

    def run(self, doi: str) -> AdapterResult:
        """Calls fetch() if enabled, otherwise returns a skipped result."""
        if not self.enabled:
            return AdapterResult(
                adapter_name=self.name,
                input_doi=doi,
                skipped=True
            )
        
        try:
            return self.fetch(doi)
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching DOI {doi}: {e}")
            return AdapterResult(
                adapter_name=self.name,
                input_doi=doi,
                errors=[str(e)]
            )
