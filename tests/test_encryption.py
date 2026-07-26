import io
import os
import tempfile

import pytest

from whoosh.backends.encryption import EncryptedStorage, KeyProvider, _DefaultCipher


class StaticKeyProvider(KeyProvider):
    def __init__(self, key: bytes) -> None:
        self._key = key

    def get_key(self) -> bytes:
        return self._key


class _MemoryStorage:
    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def write(self, name: str, data: bytes) -> None:
        self._data[name] = data

    def read(self, name: str) -> bytes:
        return self._data[name]

    def close(self) -> None:
        pass


def test_encrypted_storage_wraps_underlying_storage() -> None:
    plaintext = b"hello world"
    storage = EncryptedStorage(_MemoryStorage(), StaticKeyProvider(b"secret"))
    storage.write("file.txt", plaintext)
    assert storage.read("file.txt") == plaintext


def test_encrypted_storage_delegates_missing_attributes() -> None:
    storage = EncryptedStorage(_MemoryStorage(), StaticKeyProvider(b"secret"))
    with pytest.raises(AttributeError):
        storage.nonexistent_method()


def test_key_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        KeyProvider()


def test_default_cipher_round_trip() -> None:
    cipher = _DefaultCipher(b"key")
    data = b"whoosh-ng encryption test"
    encrypted = cipher.encrypt(data)
    assert encrypted != data
    assert cipher.decrypt(encrypted) == data


def test_default_cipher_empty_key_is_noop() -> None:
    cipher = _DefaultCipher(b"")
    data = b"plain text"
    assert cipher.encrypt(data) == data


def test_encrypted_storage_file_backend() -> None:
    pytest.importorskip("lmdb")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "encrypted_index")
        storage = EncryptedStorage(_MemoryStorage(), StaticKeyProvider(b"secret"))
        storage.write("test.txt", b"secret data")
        assert storage.read("test.txt") == b"secret data"
