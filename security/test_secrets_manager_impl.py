
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

import pytest

from security.secrets_manager_impl import create_secrets_manager


def test_local_secrets_manager_store_and_retrieve(tmp_path):
    secrets_dir = tmp_path / "secrets"
    manager = create_secrets_manager(
        provider="local", encryption_key=None, storage_dir=str(secrets_dir)
    )

    assert manager.store_secret("test/api_key", "value-123") is True
    retrieved = manager.retrieve_secret("test/api_key")

    assert retrieved == "value-123"
    assert (secrets_dir / "test_api_key.enc").exists()


def test_local_secrets_manager_rotate_and_delete(tmp_path):
    secrets_dir = tmp_path / "secrets"
    manager = create_secrets_manager(
        provider="local", encryption_key=None, storage_dir=str(secrets_dir)
    )

    assert manager.store_secret("secret/test", "old-value") is True
    assert manager.rotate_secret("secret/test", "new-value") is True
    assert manager.retrieve_secret("secret/test") == "new-value"
    assert manager.delete_secret("secret/test") is True

    with pytest.raises(KeyError):
        manager.retrieve_secret("secret/test")


def test_invalid_provider_raises_value_error():
    with pytest.raises(ValueError):
        create_secrets_manager(provider="unsupported")
