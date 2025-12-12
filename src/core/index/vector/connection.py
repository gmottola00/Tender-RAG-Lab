"""Connection management for Milvus."""

from __future__ import annotations

from typing import Optional

from .config import MilvusConfig
from .exceptions import ConfigurationError, ConnectionError

try:
    from pymilvus import connections
except ImportError:  # pragma: no cover - optional dependency not installed
    connections = None  # type: ignore


class MilvusConnectionManager:
    """Manage lifecycle of a Milvus connection."""

    def __init__(self, config: MilvusConfig) -> None:
        if connections is None:
            raise ImportError("pymilvus is required for Milvus operations")
        if not config.uri:
            raise ConfigurationError("Milvus URI is required")
        self.config = config

    def connect(self) -> None:
        """Establish a connection if not already present."""
        try:
            if not connections.has_connection(self.config.alias):
                connections.connect(
                    alias=self.config.alias,
                    uri=self.config.uri,
                    user=self.config.user,
                    password=self.config.password,
                    secure=self.config.secure,
                    db_name=self.config.db_name,
                    timeout=self.config.timeout,
                )
        except Exception as exc:  # pragma: no cover - passthrough
            raise ConnectionError(f"Failed to connect to Milvus at {self.config.uri}") from exc

    def disconnect(self) -> None:
        """Close the connection."""
        try:
            if connections.has_connection(self.config.alias):
                connections.disconnect(self.config.alias)
        except Exception as exc:  # pragma: no cover - passthrough
            raise ConnectionError("Failed to disconnect Milvus") from exc

    def ensure(self) -> None:
        """Ensure an active connection."""
        self.connect()

    def get_alias(self) -> str:
        """Return the connection alias."""
        return self.config.alias


__all__ = ["MilvusConnectionManager"]
