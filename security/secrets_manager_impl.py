
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Secrets Manager - Multi-Provider Implementation
Supports: AWS KMS, HashiCorp Vault, Azure Key Vault, Local Encryption
"""

import os
import json
import logging
from typing import Optional
from abc import ABC, abstractmethod
from functools import lru_cache

try:
    import boto3
    from botocore.exceptions import ClientError as AWSClientError

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import hvac

    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False

try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False

try:
    from cryptography.fernet import Fernet

    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

logger = logging.getLogger(__name__)


class SecretsProvider(ABC):
    """Abstract base class for secrets providers"""

    @abstractmethod
    def retrieve_secret(self, secret_path: str) -> str:
        """Retrieve a secret from the provider"""
        pass

    @abstractmethod
    def store_secret(self, secret_path: str, secret_value: str) -> bool:
        """Store a secret in the provider"""
        pass

    @abstractmethod
    def rotate_secret(self, secret_path: str, new_value: str) -> bool:
        """Rotate a secret to a new value"""
        pass

    @abstractmethod
    def delete_secret(self, secret_path: str) -> bool:
        """Delete a secret from the provider"""
        pass


class LocalEncryptionProvider(SecretsProvider):
    """Local encrypted secrets storage using Fernet"""

    def __init__(
        self, encryption_key: Optional[str] = None, storage_dir: str = ".secrets"
    ):
        if not HAS_CRYPTO:
            raise ImportError("cryptography required for LocalEncryptionProvider")

        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

        # Generate or use provided encryption key
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate new key if not provided
            key = Fernet.generate_key()
            logger.warning(f"Generated new local encryption key: {key.decode()}")
            logger.warning("Store this key in a secure location!")
            self.cipher = Fernet(key)

    def _get_secret_file(self, secret_path: str) -> str:
        """Get file path for secret"""
        safe_name = secret_path.replace("/", "_").replace(":", "_")
        return os.path.join(self.storage_dir, f"{safe_name}.enc")

    def retrieve_secret(self, secret_path: str) -> str:
        """Retrieve encrypted secret from local file"""
        secret_file = self._get_secret_file(secret_path)
        try:
            with open(secret_file, "rb") as f:
                encrypted = f.read()
            decrypted = self.cipher.decrypt(encrypted)
            logger.info(f"Retrieved secret from {secret_file}")
            return decrypted.decode()
        except FileNotFoundError:
            logger.error(f"Secret not found: {secret_path}")
            raise KeyError(f"Secret not found: {secret_path}")
        except Exception as e:
            logger.error(f"Failed to retrieve secret: {e}")
            raise

    def store_secret(self, secret_path: str, secret_value: str) -> bool:
        """Store encrypted secret to local file"""
        secret_file = self._get_secret_file(secret_path)
        try:
            encrypted = self.cipher.encrypt(secret_value.encode())
            with open(secret_file, "wb") as f:
                f.write(encrypted)
            os.chmod(secret_file, 0o600)  # Read/write for owner only
            logger.info(f"Stored secret at {secret_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret: {e}")
            return False

    def rotate_secret(self, secret_path: str, new_value: str) -> bool:
        """Rotate secret to new value"""
        try:
            self.store_secret(secret_path, new_value)
            logger.info(f"Rotated secret: {secret_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to rotate secret: {e}")
            return False

    def delete_secret(self, secret_path: str) -> bool:
        """Delete secret from storage"""
        secret_file = self._get_secret_file(secret_path)
        try:
            os.remove(secret_file)
            logger.info(f"Deleted secret: {secret_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Secret not found: {secret_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret: {e}")
            return False


class AWSKMSProvider(SecretsProvider):
    """AWS Secrets Manager + KMS integration"""

    def __init__(self, region: str = "us-east-1"):
        if not HAS_BOTO3:
            raise ImportError("boto3 required for AWSKMSProvider")

        self.region = region
        self.client = boto3.client("secretsmanager", region_name=region)

    def retrieve_secret(self, secret_path: str) -> str:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_path)
            secret = response.get("SecretString") or response.get("SecretBinary")
            logger.info(f"Retrieved secret from AWS: {secret_path}")
            return secret
        except AWSClientError as e:
            logger.error(f"Failed to retrieve AWS secret {secret_path}: {e}")
            raise

    def store_secret(self, secret_path: str, secret_value: str) -> bool:
        """Store secret in AWS Secrets Manager"""
        try:
            try:
                self.client.update_secret(
                    SecretId=secret_path, SecretString=secret_value
                )
                logger.info(f"Updated secret in AWS: {secret_path}")
            except self.client.exceptions.ResourceNotFoundException:
                self.client.create_secret(Name=secret_path, SecretString=secret_value)
                logger.info(f"Created secret in AWS: {secret_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to store AWS secret: {e}")
            return False

    def rotate_secret(self, secret_path: str, new_value: str) -> bool:
        """Rotate AWS secret"""
        return self.store_secret(secret_path, new_value)

    def delete_secret(self, secret_path: str) -> bool:
        """Delete secret from AWS Secrets Manager"""
        try:
            self.client.delete_secret(
                SecretId=secret_path, ForceDeleteWithoutRecovery=False
            )
            logger.info(f"Marked secret for deletion in AWS: {secret_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete AWS secret: {e}")
            return False


class HashiCorpVaultProvider(SecretsProvider):
    """HashiCorp Vault integration"""

    def __init__(self, endpoint: str, token: str, path: str = "secret"):
        if not HAS_HVAC:
            raise ImportError("hvac required for HashiCorpVaultProvider")

        self.endpoint = endpoint
        self.token = token
        self.path = path
        self.client = hvac.Client(url=endpoint, token=token)

        # Verify connectivity
        try:
            self.client.is_authenticated()
            logger.info(f"Connected to Vault at {endpoint}")
        except Exception as e:
            logger.error(f"Failed to connect to Vault: {e}")
            raise

    def retrieve_secret(self, secret_path: str) -> str:
        """Retrieve secret from Vault"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=secret_path, mount_point=self.path
            )
            secret = response["data"]["data"].get("value") or json.dumps(
                response["data"]["data"]
            )
            logger.info(f"Retrieved secret from Vault: {secret_path}")
            return secret
        except Exception as e:
            logger.error(f"Failed to retrieve Vault secret {secret_path}: {e}")
            raise

    def store_secret(self, secret_path: str, secret_value: str) -> bool:
        """Store secret in Vault"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_path, secret={"value": secret_value}, mount_point=self.path
            )
            logger.info(f"Stored secret in Vault: {secret_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to store Vault secret: {e}")
            return False

    def rotate_secret(self, secret_path: str, new_value: str) -> bool:
        """Rotate secret in Vault"""
        return self.store_secret(secret_path, new_value)

    def delete_secret(self, secret_path: str) -> bool:
        """Delete secret from Vault"""
        try:
            self.client.secrets.kv.v2.delete_secret_version(
                path=secret_path, mount_point=self.path
            )
            logger.info(f"Deleted secret from Vault: {secret_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Vault secret: {e}")
            return False


class AzureKeyVaultProvider(SecretsProvider):
    """Azure Key Vault integration"""

    def __init__(self, vault_url: str, credential=None):
        if not HAS_AZURE:
            raise ImportError("azure-identity and azure-keyvault-secrets required")

        if credential is None:
            credential = DefaultAzureCredential()

        self.vault_url = vault_url
        self.client = SecretClient(vault_url=vault_url, credential=credential)
        logger.info(f"Connected to Azure Key Vault: {vault_url}")

    def retrieve_secret(self, secret_path: str) -> str:
        """Retrieve secret from Azure Key Vault"""
        try:
            response = self.client.get_secret(secret_path)
            logger.info(f"Retrieved secret from Azure: {secret_path}")
            return response.value
        except Exception as e:
            logger.error(f"Failed to retrieve Azure secret {secret_path}: {e}")
            raise

    def store_secret(self, secret_path: str, secret_value: str) -> bool:
        """Store secret in Azure Key Vault"""
        try:
            self.client.set_secret(secret_path, secret_value)
            logger.info(f"Stored secret in Azure: {secret_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to store Azure secret: {e}")
            return False

    def rotate_secret(self, secret_path: str, new_value: str) -> bool:
        """Rotate secret in Azure Key Vault"""
        return self.store_secret(secret_path, new_value)

    def delete_secret(self, secret_path: str) -> bool:
        """Delete secret from Azure Key Vault"""
        try:
            self.client.begin_delete_secret(secret_path)
            logger.info(f"Marked secret for deletion in Azure: {secret_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Azure secret: {e}")
            return False


class SecretsManager:
    """Unified secrets manager supporting multiple providers"""

    PROVIDERS = {
        "local": LocalEncryptionProvider,
        "aws": AWSKMSProvider,
        "hashicorp": HashiCorpVaultProvider,
        "azure": AzureKeyVaultProvider,
    }

    def __init__(self, provider: str = "local", **kwargs):
        """
        Initialize SecretsManager

        Args:
            provider: 'local', 'aws', 'hashicorp', or 'azure'
            **kwargs: Provider-specific arguments
        """
        if provider not in self.PROVIDERS:
            raise ValueError(
                f"Unknown provider: {provider}. Choose from {list(self.PROVIDERS.keys())}"
            )

        self.provider_name = provider
        provider_class = self.PROVIDERS[provider]

        try:
            self.provider = provider_class(**kwargs)
            logger.info(f"Initialized SecretsManager with {provider} provider")
        except ImportError as e:
            logger.error(f"Provider {provider} not available: {e}")
            raise

    @lru_cache(maxsize=128)
    def retrieve_secret(self, secret_path: str) -> str:
        """Retrieve and cache secret"""
        return self.provider.retrieve_secret(secret_path)

    def store_secret(self, secret_path: str, secret_value: str) -> bool:
        """Store secret"""
        self.retrieve_secret.cache_clear()  # Clear cache after store
        return self.provider.store_secret(secret_path, secret_value)

    def rotate_secret(self, secret_path: str, new_value: str) -> bool:
        """Rotate secret"""
        self.retrieve_secret.cache_clear()
        return self.provider.rotate_secret(secret_path, new_value)

    def delete_secret(self, secret_path: str) -> bool:
        """Delete secret"""
        self.retrieve_secret.cache_clear()
        return self.provider.delete_secret(secret_path)


# Factory function for convenient initialization
def create_secrets_manager(provider: Optional[str] = None, **kwargs) -> SecretsManager:
    """
    Create SecretsManager from environment or explicit config

    Environment variables:
    - VAULT_PROVIDER: 'local', 'aws', 'hashicorp', 'azure'
    - VAULT_ENDPOINT: For hashicorp
    - VAULT_TOKEN: For hashicorp
    - AWS_REGION: For aws
    - AZURE_VAULT_URL: For azure
    - ENCRYPTION_KEY: For local
    - SECRETS_DIR: For local
    """
    provider = provider or os.getenv("VAULT_PROVIDER", "local")
    supported_providers = {"local", "aws", "hashicorp", "azure"}

    if provider not in supported_providers:
        raise ValueError(
            f"Unknown provider: {provider}. Choose from {sorted(supported_providers)}"
        )

    if provider == "hashicorp":
        return SecretsManager(
            provider="hashicorp",
            endpoint=kwargs.get(
                "endpoint", os.getenv("VAULT_ENDPOINT", "http://localhost:8200")
            ),
            token=kwargs.get("token", os.getenv("VAULT_TOKEN")),
            path=kwargs.get("path", os.getenv("VAULT_PATH", "secret")),
        )
    elif provider == "aws":
        return SecretsManager(
            provider="aws",
            region=kwargs.get("region", os.getenv("AWS_REGION", "us-east-1")),
        )
    elif provider == "azure":
        return SecretsManager(
            provider="azure",
            vault_url=kwargs.get("vault_url", os.getenv("AZURE_VAULT_URL")),
        )
    else:  # local
        return SecretsManager(
            provider="local",
            encryption_key=kwargs.get("encryption_key", os.getenv("ENCRYPTION_KEY")),
            storage_dir=kwargs.get("storage_dir", os.getenv("SECRETS_DIR", ".secrets")),
        )


# Usage Examples

if __name__ == "__main__":
    # Local encryption (for dev)
    sm = create_secrets_manager()  # Defaults to local
    sm.store_secret("api-keys/openai", "sk-proj-xxx")
    key = sm.retrieve_secret("api-keys/openai")
    print(f"Retrieved: {key[:10]}...")

    # HashiCorp Vault (for prod)
    # sm = create_secrets_manager(provider='hashicorp')
    # key = sm.retrieve_secret('asimnexus/prod/openai_api_key')

    # AWS Secrets Manager
    # sm = create_secrets_manager(provider='aws')
    # key = sm.retrieve_secret('asimnexus/openai_api_key')
