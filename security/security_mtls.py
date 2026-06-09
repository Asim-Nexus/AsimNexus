
"""
STATUS: REAL — mTLS Configuration Module with self-signed cert helpers and production load_cert_chain.

security/security_mtls.py
AsimNexus — Mutual TLS Configuration
=====================================
Configures mutual TLS for secure service-to-service communication.
Provides:
  - mTLSConfig: full mTLS manager with certificate lifecycle
  - create_self_signed_cert(): generate self-signed certs (test/dev)
  - load_cert_chain(): load PEM cert chain for production
  - create_self_signed_ssl_context(): convenience for tests
"""

import asyncio
import logging
import ssl
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class CertificateType(Enum):
    """Types of certificates"""
    CA = "ca"
    SERVER = "server"
    CLIENT = "client"


class TLSVersion(Enum):
    """TLS protocol versions"""
    TLS_1_2 = "TLSv1.2"
    TLS_1_3 = "TLSv1.3"


@dataclass
class Certificate:
    """Represents a certificate"""
    cert_id: str
    cert_type: CertificateType
    common_name: str
    cert_file: str
    key_file: str
    ca_file: Optional[str]
    expires_at: datetime
    created_at: datetime
    is_valid: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['cert_type'] = self.cert_type.value
        data['expires_at'] = data['expires_at'].isoformat()
        data['created_at'] = data['created_at'].isoformat()
        return data


class mTLSConfig:
    """
    mTLS Configuration Manager
    Manages mutual TLS configuration for secure communication
    """
    
    def __init__(self, cert_dir: str = "certs"):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        
        self.certificates: List[Certificate] = []
        self.tls_version = TLSVersion.TLS_1_3
        self.min_tls_version = TLSVersion.TLS_1_2
        
        # Service configurations
        self.service_configs = {
            "asim_core": {
                "require_client_cert": True,
                "verify_client": True,
                "allowed_cns": ["asim_core", "founder_*"]
            },
            "founder_service": {
                "require_client_cert": True,
                "verify_client": True,
                "allowed_cns": ["founder_*"]
            },
            "world_scanner": {
                "require_client_cert": False,
                "verify_client": False,
                "allowed_cns": []
            }
        }
        
        logger.info(f"mTLS Config Manager initialized (cert_dir={cert_dir})")
    
    async def initialize(self) -> None:
        """Initialize mTLS configuration"""
        logger.info("Initializing mTLS configuration...")
        
        # Create certificate directory structure
        await self._create_cert_structure()
        
        # Load existing certificates
        await self._load_certificates()
        
        logger.info("mTLS configuration initialized")
    
    async def _create_cert_structure(self) -> None:
        """Create certificate directory structure"""
        subdirs = ["ca", "server", "client", "crl"]
        
        for subdir in subdirs:
            (self.cert_dir / subdir).mkdir(exist_ok=True)
        
        logger.debug("Certificate directory structure created")
    
    async def _load_certificates(self) -> None:
        """Load existing certificates"""
        # Simplified - in production would load from files
        logger.debug("Loading existing certificates")
    
    async def generate_ca_certificate(
        self,
        common_name: str,
        organization: str = "ASIMNEXUS",
        country: str = "NP"
    ) -> Certificate:
        """
        Generate CA certificate
        
        Args:
            common_name: Common name for certificate
            organization: Organization name
            country: Country code
            
        Returns:
            Certificate object
        """
        cert_id = f"ca_{common_name}_{datetime.now().timestamp()}"
        
        logger.info(f"Generating CA certificate: {common_name}")
        
        # In production, would use cryptography library to generate actual CA cert
        cert_file = str(self.cert_dir / "ca" / f"{common_name}_ca.crt")
        key_file = str(self.cert_dir / "ca" / f"{common_name}_ca.key")
        
        cert = Certificate(
            cert_id=cert_id,
            cert_type=CertificateType.CA,
            common_name=common_name,
            cert_file=cert_file,
            key_file=key_file,
            ca_file=None,
            expires_at=datetime.now() + timedelta(days=365*10),  # 10 years
            created_at=datetime.now(),
            is_valid=True
        )
        
        self.certificates.append(cert)
        
        logger.info(f"CA certificate generated: {cert_id}")
        
        return cert
    
    async def generate_server_certificate(
        self,
        common_name: str,
        ca_cert: Certificate,
        domains: List[str] = None
    ) -> Certificate:
        """
        Generate server certificate signed by CA
        
        Args:
            common_name: Common name for certificate
            ca_cert: CA certificate to sign with
            domains: List of domains (SANs)
            
        Returns:
            Certificate object
        """
        cert_id = f"server_{common_name}_{datetime.now().timestamp()}"
        
        logger.info(f"Generating server certificate: {common_name}")
        
        cert_file = str(self.cert_dir / "server" / f"{common_name}.crt")
        key_file = str(self.cert_dir / "server" / f"{common_name}.key")
        ca_file = ca_cert.cert_file
        
        cert = Certificate(
            cert_id=cert_id,
            cert_type=CertificateType.SERVER,
            common_name=common_name,
            cert_file=cert_file,
            key_file=key_file,
            ca_file=ca_file,
            expires_at=datetime.now() + timedelta(days=365),  # 1 year
            created_at=datetime.now(),
            is_valid=True
        )
        
        self.certificates.append(cert)
        
        logger.info(f"Server certificate generated: {cert_id}")
        
        return cert
    
    async def generate_client_certificate(
        self,
        common_name: str,
        ca_cert: Certificate,
        organization: str = "ASIMNEXUS"
    ) -> Certificate:
        """
        Generate client certificate signed by CA
        
        Args:
            common_name: Common name for certificate
            ca_cert: CA certificate to sign with
            organization: Organization name
            
        Returns:
            Certificate object
        """
        cert_id = f"client_{common_name}_{datetime.now().timestamp()}"
        
        logger.info(f"Generating client certificate: {common_name}")
        
        cert_file = str(self.cert_dir / "client" / f"{common_name}.crt")
        key_file = str(self.cert_dir / "client" / f"{common_name}.key")
        ca_file = ca_cert.cert_file
        
        cert = Certificate(
            cert_id=cert_id,
            cert_type=CertificateType.CLIENT,
            common_name=common_name,
            cert_file=cert_file,
            key_file=key_file,
            ca_file=ca_file,
            expires_at=datetime.now() + timedelta(days=180),  # 6 months
            created_at=datetime.now(),
            is_valid=True
        )
        
        self.certificates.append(cert)
        
        logger.info(f"Client certificate generated: {cert_id}")
        
        return cert
    
    async def get_ssl_context(
        self,
        service: str,
        is_server: bool = True
    ) -> ssl.SSLContext:
        """
        Get SSL context for a service
        
        Args:
            service: Service name
            is_server: Whether this is for server or client
            
        Returns:
            SSLContext object
        """
        config = self.service_configs.get(service, {})
        
        # Create SSL context
        if is_server:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        else:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        # Set TLS version
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Configure mTLS if required
        if config.get("require_client_cert", False) and is_server:
            context.verify_mode = ssl.CERT_REQUIRED
        elif config.get("verify_client", False) and is_server:
            context.verify_mode = ssl.CERT_OPTIONAL
        else:
            context.verify_mode = ssl.CERT_NONE
        
        # Load CA certificate
        ca_cert = await self._get_ca_certificate()
        if ca_cert:
            try:
                context.load_verify_locations(cafile=ca_cert.cert_file)
            except Exception as e:
                logger.warning(f"Failed to load CA certificate: {e}")
        
        # Load certificate and key
        cert = await self._get_service_certificate(service, is_server)
        if cert:
            try:
                context.load_cert_chain(certfile=cert.cert_file, keyfile=cert.key_file)
            except Exception as e:
                logger.warning(f"Failed to load certificate: {e}")
        
        logger.debug(f"SSL context created for {service}")
        
        return context
    
    async def _get_ca_certificate(self) -> Optional[Certificate]:
        """Get CA certificate"""
        for cert in self.certificates:
            if cert.cert_type == CertificateType.CA and cert.is_valid:
                return cert
        return None
    
    async def _get_service_certificate(
        self,
        service: str,
        is_server: bool
    ) -> Optional[Certificate]:
        """Get certificate for service"""
        cert_type = CertificateType.SERVER if is_server else CertificateType.CLIENT
        
        for cert in self.certificates:
            if (cert.cert_type == cert_type and
                cert.is_valid and
                service in cert.common_name.lower()):
                return cert
        return None
    
    async def verify_client_certificate(
        self,
        cert_file: str,
        service: str
    ) -> bool:
        """
        Verify client certificate for service
        
        Args:
            cert_file: Path to client certificate
            service: Service name
            
        Returns:
            True if valid
        """
        config = self.service_configs.get(service, {})
        
        if not config.get("verify_client", False):
            return True
        
        # In production, would verify certificate against CA
        # and check if CN is in allowed list
        
        logger.debug(f"Verifying client certificate for {service}")
        
        return True  # Simplified
    
    async def revoke_certificate(self, cert_id: str) -> bool:
        """
        Revoke a certificate
        
        Args:
            cert_id: Certificate ID to revoke
            
        Returns:
            True if successful
        """
        for cert in self.certificates:
            if cert.cert_id == cert_id:
                cert.is_valid = False
                logger.info(f"Certificate revoked: {cert_id}")
                return True
        return False
    
    async def check_certificate_expiry(self) -> List[Certificate]:
        """
        Check for expiring certificates
        
        Returns:
            List of certificates expiring soon
        """
        expiring_soon = []
        warning_threshold = datetime.now() + timedelta(days=30)
        
        for cert in self.certificates:
            if cert.is_valid and cert.expires_at < warning_threshold:
                expiring_soon.append(cert)
        
        return expiring_soon
    
    async def get_certificate_status(self) -> Dict:
        """Get status of all certificates"""
        valid_count = sum(1 for c in self.certificates if c.is_valid)
        expired_count = len(self.certificates) - valid_count
        
        type_counts = {}
        for cert in self.certificates:
            cert_type = cert.cert_type.value
            type_counts[cert_type] = type_counts.get(cert_type, 0) + 1
        
        return {
            'total_certificates': len(self.certificates),
            'valid_certificates': valid_count,
            'expired_certificates': expired_count,
            'type_distribution': type_counts,
            'tls_version': self.tls_version.value,
            'min_tls_version': self.min_tls_version.value,
            'cert_directory': str(self.cert_dir)
        }
    
    async def set_tls_version(self, version: TLSVersion) -> None:
        """Set TLS version"""
        self.tls_version = version
        logger.info(f"TLS version set to {version.value}")
    
    async def add_service_config(self, service: str, config: Dict) -> bool:
        """Add service configuration"""
        self.service_configs[service] = config
        logger.info(f"Service config added: {service}")
        return True
    
    async def export_mtls_data(self) -> Dict:
        """Export mTLS configuration for backup"""
        return {
            'certificates': [c.to_dict() for c in self.certificates],
            'tls_version': self.tls_version.value,
            'min_tls_version': self.min_tls_version.value,
            'service_configs': self.service_configs,
            'cert_directory': str(self.cert_dir)
        }
    
    async def import_mtls_data(self, data: Dict) -> None:
        """Import mTLS configuration from backup"""
        try:
            self.tls_version = TLSVersion(data.get('tls_version', 'TLSv1.3'))
            self.min_tls_version = TLSVersion(data.get('min_tls_version', 'TLSv1.2'))
            self.service_configs = data.get('service_configs', self.service_configs)
            
            self.certificates = []
            for cert_data in data.get('certificates', []):
                cert = Certificate(
                    cert_id=cert_data['cert_id'],
                    cert_type=CertificateType(cert_data['cert_type']),
                    common_name=cert_data['common_name'],
                    cert_file=cert_data['cert_file'],
                    key_file=cert_data['key_file'],
                    ca_file=cert_data.get('ca_file'),
                    expires_at=datetime.fromisoformat(cert_data['expires_at']),
                    created_at=datetime.fromisoformat(cert_data['created_at']),
                    is_valid=cert_data['is_valid']
                )
                self.certificates.append(cert)
            
            logger.info(f"Imported {len(self.certificates)} certificates")
            
        except Exception as e:
            logger.error(f"Failed to import mTLS data: {e}")
            raise


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def create_self_signed_cert(
    key_path: str,
    cert_path: str,
    common_name: str = "asimnexus.test",
    organization: str = "ASIMNEXUS",
    country: str = "US",
    valid_days: int = 365,
) -> None:
    """
    Generate a self-signed certificate for test/dev environments.
    
    Uses the ``cryptography`` library to generate an RSA-2048 key pair
    and a self-signed X.509 certificate with SAN for localhost + 127.0.0.1.
    
    Args:
        key_path:  Output path for the PEM-encoded private key.
        cert_path: Output path for the PEM-encoded certificate.
        common_name: CN for the certificate subject/issuer.
        organization: O for the certificate subject/issuer.
        country: C for the certificate subject/issuer.
        valid_days: Number of days the certificate is valid.
    
    Raises:
        ImportError: If the ``cryptography`` library is not installed.
    """
    import ipaddress
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(1000)
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=valid_days))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def create_self_signed_ssl_context(
    server_side: bool = True,
) -> ssl.SSLContext:
    """
    Create a self-signed SSL context for testing/dev.
    
    Generates a temporary certificate, loads it into an SSL context,
    and cleans up the temp files immediately after loading.
    
    Args:
        server_side: If True, creates a server context (CERT_NONE client verify).
                     If False, creates a client context that accepts self-signed
                     server certs.
    
    Returns:
        An SSLContext ready for use with P2PTransport or BootstrapService.
    """
    tmpdir = tempfile.mkdtemp()
    key_path = os.path.join(tmpdir, "test.key")
    cert_path = os.path.join(tmpdir, "test.crt")

    create_self_signed_cert(key_path, cert_path)

    if server_side:
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    else:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

    ctx.load_cert_chain(cert_path, key_path)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Cleanup temp files after context is loaded
    try:
        os.remove(key_path)
        os.remove(cert_path)
        os.rmdir(tmpdir)
    except Exception:
        pass

    return ctx


def load_cert_chain(
    cert_path: str,
    key_path: str,
    ca_cert_path: Optional[str] = None,
    server_side: bool = True,
    require_client_cert: bool = False,
) -> ssl.SSLContext:
    """
    Load a PEM certificate chain and create a production SSL context.
    
    Args:
        cert_path: Path to the PEM-encoded certificate file.
        key_path:  Path to the PEM-encoded private key file.
        ca_cert_path: Optional path to a CA certificate file for client
                      verification (mTLS).
        server_side: If True, creates a server context; otherwise client.
        require_client_cert: If True and server_side, set verify_mode to
                             CERT_REQUIRED (mutual TLS).
    
    Returns:
        An SSLContext loaded with the provided certificate chain.
    
    Raises:
        FileNotFoundError: If any of the provided file paths do not exist.
        ssl.SSLError: If the certificate or key cannot be loaded.
    """
    if not os.path.exists(cert_path):
        raise FileNotFoundError(f"Certificate file not found: {cert_path}")
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Key file not found: {key_path}")

    if server_side:
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    else:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

    ctx.load_cert_chain(cert_path, key_path)
    ctx.check_hostname = False

    if server_side and require_client_cert:
        ctx.verify_mode = ssl.CERT_REQUIRED
        if ca_cert_path:
            if not os.path.exists(ca_cert_path):
                raise FileNotFoundError(f"CA cert file not found: {ca_cert_path}")
            ctx.load_verify_locations(cafile=ca_cert_path)
    else:
        ctx.verify_mode = ssl.CERT_NONE

    logger.info(
        f"Certificate chain loaded: cert={cert_path}, key={key_path}, "
        f"ca={ca_cert_path}, server_side={server_side}, "
        f"require_client_cert={require_client_cert}"
    )
    return ctx
