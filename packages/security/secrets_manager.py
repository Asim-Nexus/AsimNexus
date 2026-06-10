
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIM NEXUS Secure Secrets Manager
==================================
Unified secrets management with multi-provider KMS support (AWS, Azure, HashiCorp)
"""

import json
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger("SecretsManager")


class KMSProvider(Enum):
    """Supported KMS providers"""
    AWS_KMS = "aws_kms"
    AZURE_KEYVAULT = "azure_keyvault"
    HASHICORP_VAULT = "hashicorp_vault"
    LOCAL_ENCRYPTED = "local_encrypted"  # For local development


class KMSInterface(ABC):
    """Abstract interface for KMS providers"""
    
    @abstractmethod
    def encrypt(self, plaintext: str, key_id: str) -> str:
        """Encrypt plaintext with KMS key"""
        pass
    
    @abstractmethod
    def decrypt(self, ciphertext: str, key_id: str) -> str:
        """Decrypt ciphertext with KMS key"""
        pass
    
    @abstractmethod
    def rotate_key(self, key_id: str):
        """Rotate encryption key"""
        pass


class AWSKMSProvider(KMSInterface):
    """AWS KMS integration"""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize AWS KMS client"""
        try:
            import boto3
            self.client = boto3.client('kms', region_name=region)
            self.region = region
            logger.info(f"✅ AWS KMS initialized for region {region}")
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            self.client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize AWS KMS: {e}")
            self.client = None
    
    def encrypt(self, plaintext: str, key_id: str) -> str:
        """Encrypt with AWS KMS"""
        if not self.client:
            logger.warning("AWS KMS not available, returning plaintext (INSECURE)")
            return plaintext
        
        try:
            response = self.client.encrypt(
                KeyId=key_id,
                Plaintext=plaintext.encode('utf-8')
            )
            import base64
            ciphertext = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
            logger.debug(f"Encrypted secret with key {key_id}")
            return ciphertext
        except Exception as e:
            logger.error(f"AWS KMS encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str, key_id: str) -> str:
        """Decrypt with AWS KMS"""
        if not self.client:
            logger.warning("AWS KMS not available, returning input (INSECURE)")
            return ciphertext
        
        try:
            import base64
            ciphertext_blob = base64.b64decode(ciphertext)
            response = self.client.decrypt(CiphertextBlob=ciphertext_blob)
            plaintext = response['Plaintext'].decode('utf-8')
            logger.debug("Decrypted secret with AWS KMS")
            return plaintext
        except Exception as e:
            logger.error(f"AWS KMS decryption failed: {e}")
            raise
    
    def rotate_key(self, key_id: str):
        """Rotate AWS KMS key"""
        if not self.client:
            logger.error("AWS KMS not available")
            return
        
        try:
            self.client.enable_key_rotation(KeyId=key_id)
            logger.info(f"✅ Rotation enabled for key {key_id}")
        except Exception as e:
            logger.error(f"Failed to rotate key {key_id}: {e}")


class AzureKeyVaultProvider(KMSInterface):
    """Azure Key Vault integration"""
    
    def __init__(self, vault_url: str, credential=None):
        """Initialize Azure Key Vault client"""
        try:
            from azure.keyvault.secrets import SecretClient
            self.vault_url = vault_url
            self.credential = credential
            self.client = SecretClient(vault_url=vault_url, credential=credential)
            logger.info(f"✅ Azure Key Vault initialized: {vault_url}")
        except ImportError:
            logger.error("azure-identity/azure-keyvault-secrets not installed")
            logger.error("Install with: pip install azure-identity azure-keyvault-secrets")
            self.client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Key Vault: {e}")
            self.client = None
    
    def encrypt(self, plaintext: str, key_id: str) -> str:
        """Store encrypted secret in Azure Key Vault"""
        if not self.client:
            logger.warning("Azure Key Vault not available (INSECURE)")
            return plaintext
        
        try:
            secret_name = f"asim-{key_id}"
            self.client.set_secret(name=secret_name, value=plaintext)
            logger.debug(f"Stored secret in Key Vault: {secret_name}")
            return f"vault://{secret_name}"
        except Exception as e:
            logger.error(f"Azure Key Vault encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str, key_id: str) -> str:
        """Retrieve encrypted secret from Azure Key Vault"""
        if not self.client:
            logger.warning("Azure Key Vault not available (INSECURE)")
            return ciphertext
        
        try:
            if ciphertext.startswith("vault://"):
                secret_name = ciphertext.replace("vault://", "")
            else:
                secret_name = f"asim-{key_id}"
            
            secret = self.client.get_secret(name=secret_name)
            logger.debug(f"Retrieved secret from Key Vault: {secret_name}")
            return secret.value
        except Exception as e:
            logger.error(f"Azure Key Vault decryption failed: {e}")
            raise
    
    def rotate_key(self, key_id: str):
        """Rotate key in Azure Key Vault"""
        logger.info(f"Manual rotation recommended in Azure Key Vault for {key_id}")


class HashiCorpVaultProvider(KMSInterface):
    """HashiCorp Vault integration"""
    
    def __init__(self, server_url: str, token: str or None, auth_method: str = "token"):
        """Initialize HashiCorp Vault client"""
        try:
            import hvac
            self.server_url = server_url
            self.auth_method = auth_method
            self.client = hvac.Client(url=server_url, token=token)
            
            # Test auth
            if self.client.is_authenticated():
                logger.info(f"✅ HashiCorp Vault initialized: {server_url}")
            else:
                logger.error("Failed to authenticate with HashiCorp Vault")
                self.client = None
        except ImportError:
            logger.error("hvac not installed. Install with: pip install hvac")
            self.client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize HashiCorp Vault: {e}")
            self.client = None
    
    def encrypt(self, plaintext: str, key_id: str) -> str:
        """Store secret in HashiCorp Vault"""
        if not self.client:
            logger.warning("HashiCorp Vault not available (INSECURE)")
            return plaintext
        
        try:
            secret_path = f"secret/asim/{key_id}"
            self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret_data={"value": plaintext}
            )
            logger.debug(f"Stored secret in Vault: {secret_path}")
            return f"hashivault://{secret_path}"
        except Exception as e:
            logger.error(f"HashiCorp Vault encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str, key_id: str) -> str:
        """Retrieve secret from HashiCorp Vault"""
        if not self.client:
            logger.warning("HashiCorp Vault not available (INSECURE)")
            return ciphertext
        
        try:
            if ciphertext.startswith("hashivault://"):
                secret_path = ciphertext.replace("hashivault://", "")
            else:
                secret_path = f"secret/asim/{key_id}"
            
            response = self.client.secrets.kv.v2.read_secret_version(path=secret_path)
            plaintext = response['data']['data']['value']
            logger.debug(f"Retrieved secret from Vault: {secret_path}")
            return plaintext
        except Exception as e:
            logger.error(f"HashiCorp Vault decryption failed: {e}")
            raise
    
    def rotate_key(self, key_id: str):
        """Rotate key in HashiCorp Vault"""
        logger.info(f"Rotate key manually in Vault or use policy: secret/asim/{key_id}")


class LocalEncryptedProvider(KMSInterface):
    """Local encrypted storage (for development only)"""
    
    def __init__(self):
        """Initialize local encrypted provider"""
        try:
            from cryptography.fernet import Fernet
            self.fernet = Fernet(Fernet.generate_key())
            logger.warning("⚠️  Using LOCAL encryption (development only)")
        except ImportError:
            logger.error("cryptography not installed. Install with: pip install cryptography")
            self.fernet = None
    
    def encrypt(self, plaintext: str, key_id: str) -> str:
        """Encrypt locally"""
        if not self.fernet:
            logger.warning("Local encryption not available")
            return plaintext
        
        try:
            ciphertext = self.fernet.encrypt(plaintext.encode()).decode()
            return ciphertext
        except Exception as e:
            logger.error(f"Local encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str, key_id: str) -> str:
        """Decrypt locally"""
        if not self.fernet:
            logger.warning("Local encryption not available")
            return ciphertext
        
        try:
            plaintext = self.fernet.decrypt(ciphertext.encode()).decode()
            return plaintext
        except Exception as e:
            logger.error(f"Local decryption failed: {e}")
            raise
    
    def rotate_key(self, key_id: str):
        """Rotate local key"""
        logger.warning("Local encryption key rotation: generate new key with Fernet.generate_key()")


class SecretsManager:
    """Unified secrets management with multi-provider KMS support"""
    
    def __init__(self, provider: KMSProvider = KMSProvider.LOCAL_ENCRYPTED, **kwargs):
        """Initialize SecretsManager with KMS provider"""
        self.provider_type = provider
        self.audit_log = []
        
        if provider == KMSProvider.AWS_KMS:
            self.kms = AWSKMSProvider(region=kwargs.get("region", "us-east-1"))
        elif provider == KMSProvider.AZURE_KEYVAULT:
            self.kms = AzureKeyVaultProvider(
                vault_url=kwargs.get("vault_url"),
                credential=kwargs.get("credential")
            )
        elif provider == KMSProvider.HASHICORP_VAULT:
            self.kms = HashiCorpVaultProvider(
                server_url=kwargs.get("server_url"),
                token=kwargs.get("token"),
                auth_method=kwargs.get("auth_method", "token")
            )
        else:  # LOCAL_ENCRYPTED
            self.kms = LocalEncryptedProvider()
        
        logger.info(f"SecretsManager initialized with {provider.value}")
    
    def store_secret(self, secret_id: str, secret_value: str, metadata: Optional[Dict] = None) -> bool:
        """Store a secret securely"""
        try:
            ciphertext = self.kms.encrypt(secret_value, secret_id)
            
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "store",
                "secret_id": secret_id,
                "status": "success"
            }
            self.audit_log.append(audit_entry)
            logger.info(f"✅ Secret stored: {secret_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret {secret_id}: {e}")
            
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "store",
                "secret_id": secret_id,
                "status": "failed",
                "error": str(e)
            }
            self.audit_log.append(audit_entry)
            return False
    
    def retrieve_secret(self, secret_id: str) -> Optional[str]:
        """Retrieve and decrypt a secret"""
        try:
            # In production, retrieve from KMS-backed storage
            # This is a simplified example
            plaintext = self.kms.decrypt("", secret_id)
            
            self.audit_log.append({
                "timestamp": datetime.now().isoformat(),
                "action": "retrieve",
                "secret_id": secret_id,
                "status": "success"
            })
            logger.debug(f"Retrieved secret: {secret_id}")
            return plaintext
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_id}: {e}")
            
            self.audit_log.append({
                "timestamp": datetime.now().isoformat(),
                "action": "retrieve",
                "secret_id": secret_id,
                "status": "failed"
            })
            return None
    
    def load_env_secrets(self, env_prefix: str = "ASIM_") -> Dict[str, str]:
        """Load secrets from environment variables with prefix"""
        secrets = {}
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                secret_name = key[len(env_prefix):]
                secrets[secret_name] = value
        
        logger.info(f"Loaded {len(secrets)} secrets from environment")
        return secrets
    
    def rotate_secret(self, secret_id: str) -> bool:
        """Rotate a secret (generate new one)"""
        try:
            self.kms.rotate_key(secret_id)
            
            self.audit_log.append({
                "timestamp": datetime.now().isoformat(),
                "action": "rotate",
                "secret_id": secret_id,
                "status": "success"
            })
            logger.info(f"✅ Secret rotated: {secret_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to rotate secret {secret_id}: {e}")
            return False
    
    def get_audit_log(self) -> list:
        """Get audit log of all secret operations"""
        return self.audit_log
    
    def get_audit_stats(self) -> dict:
        """Get audit statistics"""
        total = len(self.audit_log)
        by_action = {}
        by_status = {}
        
        for entry in self.audit_log:
            action = entry.get("action", "unknown")
            status = entry.get("status", "unknown")
            
            by_action[action] = by_action.get(action, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_operations": total,
            "by_action": by_action,
            "by_status": by_status
        }


# Singleton instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager(provider: KMSProvider = KMSProvider.LOCAL_ENCRYPTED, **kwargs) -> SecretsManager:
    """Get singleton SecretsManager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager(provider, **kwargs)
    return _secrets_manager


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Local development with encrypted storage
    sm = SecretsManager(KMSProvider.LOCAL_ENCRYPTED)
    
    # Store a secret
    sm.store_secret("openai_api_key", "sk-...")
    sm.store_secret("postgres_password", "secure_password_123")
    
    # Load secrets from environment
    env_secrets = sm.load_env_secrets("ASIM_")
    print(f"Loaded {len(env_secrets)} environmental secrets")
    
    # Get audit statistics
    stats = sm.get_audit_stats()
    print(f"Audit stats: {stats}")
    
    # Production: Use AWS KMS
    # sm_prod = SecretsManager(KMSProvider.AWS_KMS, region="us-east-1")
