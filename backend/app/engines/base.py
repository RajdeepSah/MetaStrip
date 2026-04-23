from abc import ABC, abstractmethod


class BaseEngine(ABC):
    """Shared interface every metadata engine must implement."""

    @abstractmethod
    def extract(self, file_bytes: bytes) -> dict:
        """Extract metadata and return a structured findings dict."""
        ...

    @abstractmethod
    def strip(self, file_bytes: bytes) -> bytes:
        """Remove all metadata and return clean file bytes."""
        ...
