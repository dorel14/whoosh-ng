from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class KeyProvider(ABC):
    """Abstract base class for encryption key providers.

    A key provider is responsible for supplying the encryption key used by
    :class:`EncryptedStorage`. Sub-classes can fetch keys from environment
    variables, a key management service, or any other source.
    """

    @abstractmethod
    def get_key(self) -> bytes:
        """Return the encryption key as bytes."""
        raise NotImplementedError


class EncryptedStorage:
    """Wrapper around a storage backend that encrypts/decrypts data.

    This is intentionally a thin wrapper: it delegates all storage operations
    to an underlying storage instance and only applies encryption to bytes
    passing through ``write``/``read``. It does not replace the storage
    backend; it wraps it.

    The actual cipher implementation is pluggable via the ``cipher`` argument
    so that projects can swap in their preferred encryption library without
    changing this wrapper.
    """

    def __init__(self, storage: Any, key_provider: KeyProvider, cipher: Any | None = None) -> None:
        self._storage = storage
        self._key_provider = key_provider
        self._cipher = cipher or _DefaultCipher(key_provider.get_key())

    def __getattr__(self, name: str) -> Any:
        return getattr(self._storage, name)

    def write(self, name: str, data: bytes) -> None:
        self._storage.write(name, self._cipher.encrypt(data))

    def read(self, name: str) -> bytes:
        return self._cipher.decrypt(self._storage.read(name))

    def close(self) -> None:
        if hasattr(self._storage, "close"):
            self._storage.close()


class _DefaultCipher:
    """Minimal XOR cipher for environments without a crypto dependency.

    This is provided as a fallback only. Production deployments should
    provide a real cipher implementation (AES-GCM, etc.).
    """

    def __init__(self, key: bytes) -> None:
        self._key = key

    def encrypt(self, data: bytes) -> bytes:
        key = self._key
        if not key:
            return data
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    def decrypt(self, data: bytes) -> bytes:
        return self.encrypt(data)
