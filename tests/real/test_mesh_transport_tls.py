#!/usr/bin/env python3
"""
TLS integration tests for P2P Transport Layer (Phase 1A).
=========================================================
Tests TLS/mTLS secured WebSocket connections between transports,
including rejection of non-TLS clients, and bootstrap over TLS.

Requires: cryptography (already installed)
"""

import os
import sys
import ssl
import time
import json
import struct
import asyncio
import logging
import socket
import datetime
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Generator
from contextlib import contextmanager

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest

# ---------------------------------------------------------------------------
# Self-signed certificate generation using cryptography
# ---------------------------------------------------------------------------

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, asymmetric, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


def _generate_self_signed_cert(
    common_name: str = "127.0.0.1",
    san_dns: Optional[str] = None,
) -> Tuple[bytes, bytes]:
    """Generate a self-signed CA certificate and private key.

    The generated certificate has BasicConstraints(ca=True) so it can be
    used as a CA for signing other certs in mTLS tests.

    Returns:
        (cert_pem_bytes, key_pem_bytes)
    """
    if san_dns is None:
        san_dns = common_name

    private_key = _generate_key()
    cert = _build_cert(
        private_key, common_name, san_dns, private_key, common_name,
        ca=True,
    )
    return _serialize_key_cert(private_key, cert)


def _generate_key() -> rsa.RSAPrivateKey:
    """Generate a 2048-bit RSA private key."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )


def _build_cert(
    subject_key: rsa.RSAPrivateKey,
    subject_cn: str,
    san_dns: str,
    issuer_key: rsa.RSAPrivateKey,
    issuer_cn: str,
    ca: bool = False,
) -> x509.Certificate:
    """Build and sign a certificate (self-signed or CA-signed).

    Args:
        ca: If True, add BasicConstraints(ca=True) extension (for CA certs).
    """
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AsimNexus Test"),
        x509.NameAttribute(NameOID.COMMON_NAME, subject_cn),
    ])
    issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AsimNexus Test"),
        x509.NameAttribute(NameOID.COMMON_NAME, issuer_cn),
    ])
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(subject_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now() - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now() + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(san_dns)]),
            critical=False,
        )
    )
    if ca:
        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
    return builder.sign(issuer_key, hashes.SHA256(), default_backend())


def _serialize_key_cert(
    private_key: rsa.RSAPrivateKey,
    cert: x509.Certificate,
) -> Tuple[bytes, bytes]:
    """Serialize a private key and certificate to PEM bytes."""
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def _generate_ca_signed_cert(
    ca_cert_pem: bytes,
    ca_key_pem: bytes,
    common_name: str = "127.0.0.1",
    san_dns: Optional[str] = None,
) -> Tuple[bytes, bytes]:
    """Generate a certificate signed by the given CA.

    Returns:
        (signed_cert_pem_bytes, key_pem_bytes)
    """
    if san_dns is None:
        san_dns = common_name

    # Deserialize CA
    ca_cert = x509.load_pem_x509_certificate(ca_cert_pem, default_backend())
    ca_key = serialization.load_pem_private_key(
        ca_key_pem, password=None, backend=default_backend()
    )
    ca_cn = ca_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value

    # Generate new keypair and sign with CA
    subject_key = _generate_key()
    cert = _build_cert(
        subject_key=subject_key,
        subject_cn=common_name,
        san_dns=san_dns,
        issuer_key=ca_key,  # type: ignore
        issuer_cn=str(ca_cn),
    )
    return _serialize_key_cert(subject_key, cert)


# ---------------------------------------------------------------------------
# Temporary cert file helpers
# ---------------------------------------------------------------------------

@contextmanager
def _temp_pem_file(data: bytes, suffix: str = ".pem") -> Generator[str, None, None]:
    """Write PEM bytes to a temporary file, yield the path, then clean up."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    try:
        yield path
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _make_tls_server_ctx(cert_pem: bytes, key_pem: bytes) -> ssl.SSLContext:
    """Create a TLS server SSLContext with cert/key from PEM bytes."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    with _temp_pem_file(cert_pem, "_cert.pem") as cert_path, \
         _temp_pem_file(key_pem, "_key.pem") as key_path:
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _make_tls_client_ctx() -> ssl.SSLContext:
    """Create a TLS client SSLContext (no verification, for tests)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _make_mtls_server_ctx(
    server_cert_pem: bytes,
    server_key_pem: bytes,
    ca_cert_pem: bytes,
) -> ssl.SSLContext:
    """Create an mTLS server SSLContext requiring client certs signed by CA."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    with _temp_pem_file(ca_cert_pem, "_ca.pem") as ca_path, \
         _temp_pem_file(server_cert_pem, "_scert.pem") as cert_path, \
         _temp_pem_file(server_key_pem, "_skey.pem") as key_path:
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        ctx.load_verify_locations(cafile=ca_path)
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


def _make_mtls_client_ctx(
    client_cert_pem: bytes,
    client_key_pem: bytes,
) -> ssl.SSLContext:
    """Create an mTLS client SSLContext with client cert."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    with _temp_pem_file(client_cert_pem, "_ccert.pem") as cert_path, \
         _temp_pem_file(client_key_pem, "_ckey.pem") as key_path:
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def event_loop():
    """Create a fresh event loop per test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_free_port() -> int:
    """Find a free TCP/UDP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


from mesh.p2p_transport import (
    P2PTransport,
    P2PMessage,
    PeerInfo,
    ConnectionState,
    WSMessageType,
    get_p2p_transport,
    reset_p2p_transport,
)
from mesh.bootstrap import (
    BootstrapService,
    BootstrapNode,
    BootstrapRegion,
    get_bootstrap_service,
    reset_bootstrap_service,
)

logger = logging.getLogger("TestMeshTransportTLS")
logger.setLevel(logging.DEBUG)


# ═══════════════════════════════════════════════════════════════════════════
# TestTLSConnection — TLS handshake between two transports
# ═══════════════════════════════════════════════════════════════════════════

class TestTLSConnection:
    """Basic TLS-secured WebSocket connections."""

    @pytest.mark.asyncio
    async def test_tls_handshake_succeeds(self):
        """Two transports connect with TLS — HELLO/ACK completes."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        ws_port = find_free_port()
        udp_a = find_free_port()
        udp_b = find_free_port()

        # Generate TLS certs and create contexts
        cert_pem, key_pem = _generate_self_signed_cert("127.0.0.1")
        server_ctx = _make_tls_server_ctx(cert_pem, key_pem)
        client_ctx = _make_tls_client_ctx()

        server = P2PTransport(
            node_id="tls-server",
            host="127.0.0.1",
            port_udp=udp_a,
            port_ws=ws_port,
            ssl_context=server_ctx,
        )
        await server.start()
        assert server.is_secure, "Server should report is_secure=True"

        client = P2PTransport(
            node_id="tls-client",
            host="127.0.0.1",
            port_udp=udp_b,
            port_ws=find_free_port(),
            ssl_context=client_ctx,
        )
        await client.start()

        try:
            peer_id = await client.connect_peer("127.0.0.1", ws_port, timeout=10.0)
            assert peer_id == "tls-server", (
                f"Expected tls-server, got {peer_id}"
            )

            # Verify connection state
            peer = await client.get_peer("tls-server")
            assert peer is not None
            assert peer.connection_state == ConnectionState.CONNECTED

            # Verify server sees the client
            server_peer = await server.get_peer("tls-client")
            assert server_peer is not None
            assert server_peer.connection_state == ConnectionState.CONNECTED
        finally:
            await client.stop()
            await server.stop()

    @pytest.mark.asyncio
    async def test_encrypted_communication(self):
        """Data sent over TLS is received correctly (decrypted on both ends)."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        ws_port = find_free_port()
        udp_a = find_free_port()
        udp_b = find_free_port()

        cert_pem, key_pem = _generate_self_signed_cert("127.0.0.1")
        server_ctx = _make_tls_server_ctx(cert_pem, key_pem)
        client_ctx = _make_tls_client_ctx()

        server = P2PTransport(
            node_id="enc-server",
            host="127.0.0.1",
            port_udp=udp_a,
            port_ws=ws_port,
            ssl_context=server_ctx,
        )

        received_messages = []

        async def on_sync(msg: P2PMessage):
            received_messages.append(msg)

        server.on_ws_message("test_data", on_sync)
        await server.start()

        client = P2PTransport(
            node_id="enc-client",
            host="127.0.0.1",
            port_udp=udp_b,
            port_ws=find_free_port(),
            ssl_context=client_ctx,
        )
        await client.start()

        try:
            peer_id = await client.connect_peer("127.0.0.1", ws_port, timeout=10.0)
            assert peer_id == "enc-server"

            peer = await client.get_peer("enc-server")
            assert peer is not None

            # Send a message over the TLS connection
            test_msg = P2PMessage(
                msg_type="test_data",
                sender_id="enc-client",
                msg_id="tls-test-1",
                payload={"hello": "world", "number": 42},
            )
            sent = await client.send_ws(peer, test_msg)
            assert sent, "Message should be sent successfully"

            await asyncio.sleep(0.5)

            # Verify message was received on the server side
            assert len(received_messages) > 0, (
                "Server should have received the message over TLS"
            )
            received = received_messages[0]
            assert received.payload["hello"] == "world"
            assert received.payload["number"] == 42
        finally:
            await client.stop()
            await server.stop()

    @pytest.mark.asyncio
    async def test_tls_stats_reporting(self):
        """Transport stats correctly report TLS enabled."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        cert_pem, key_pem = _generate_self_signed_cert("127.0.0.1")
        ctx = _make_tls_server_ctx(cert_pem, key_pem)

        transport = P2PTransport(
            node_id="stats-test",
            host="127.0.0.1",
            port_udp=find_free_port(),
            port_ws=find_free_port(),
            ssl_context=ctx,
        )
        await transport.start()

        stats = transport.get_stats()
        assert stats["tls_enabled"] is True
        assert transport.is_secure is True

        await transport.stop()


# ═══════════════════════════════════════════════════════════════════════════
# TestTLSHandshake — Mutual TLS (mTLS) with client certs
# ═══════════════════════════════════════════════════════════════════════════

class TestTLSHandshake:
    """Mutual TLS (mTLS) connections with client certificate verification."""

    @pytest.mark.asyncio
    async def test_mtls_handshake_succeeds(self):
        """mTLS handshake succeeds with valid client cert."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        ws_port = find_free_port()
        udp_a = find_free_port()
        udp_b = find_free_port()

        # Generate CA, server, and client certs
        ca_cert_pem, ca_key_pem = _generate_self_signed_cert("CA-Test")
        server_cert_pem, server_key_pem = _generate_ca_signed_cert(
            ca_cert_pem, ca_key_pem, "127.0.0.1"
        )
        client_cert_pem, client_key_pem = _generate_ca_signed_cert(
            ca_cert_pem, ca_key_pem, "127.0.0.1-client", "test-client"
        )

        # Create contexts using temp files
        server_ctx = _make_mtls_server_ctx(server_cert_pem, server_key_pem, ca_cert_pem)
        client_ctx = _make_mtls_client_ctx(client_cert_pem, client_key_pem)

        server = P2PTransport(
            node_id="mtls-server",
            host="127.0.0.1",
            port_udp=udp_a,
            port_ws=ws_port,
            ssl_context=server_ctx,
        )
        await server.start()

        client = P2PTransport(
            node_id="mtls-client",
            host="127.0.0.1",
            port_udp=udp_b,
            port_ws=find_free_port(),
            ssl_context=client_ctx,
        )
        await client.start()

        try:
            peer_id = await client.connect_peer(
                "127.0.0.1", ws_port, timeout=10.0
            )
            assert peer_id == "mtls-server", (
                f"mTLS handshake failed: got {peer_id}"
            )

            peer = await client.get_peer("mtls-server")
            assert peer is not None
            assert peer.connection_state == ConnectionState.CONNECTED
        finally:
            await client.stop()
            await server.stop()

    @pytest.mark.asyncio
    async def test_mtls_client_cert_verified(self):
        """Server verifies the client certificate in mTLS mode."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        ws_port = find_free_port()
        udp_a = find_free_port()
        udp_b = find_free_port()

        ca_cert_pem, ca_key_pem = _generate_self_signed_cert("CA-Verify")
        server_cert_pem, server_key_pem = _generate_ca_signed_cert(
            ca_cert_pem, ca_key_pem, "127.0.0.1"
        )
        client_cert_pem, client_key_pem = _generate_ca_signed_cert(
            ca_cert_pem, ca_key_pem, "verified-client", "verified-client.local"
        )

        server_ctx = _make_mtls_server_ctx(server_cert_pem, server_key_pem, ca_cert_pem)
        client_ctx = _make_mtls_client_ctx(client_cert_pem, client_key_pem)

        server = P2PTransport(
            node_id="mtls-verify-server",
            host="127.0.0.1",
            port_udp=udp_a,
            port_ws=ws_port,
            ssl_context=server_ctx,
        )
        await server.start()

        client = P2PTransport(
            node_id="mtls-verify-client",
            host="127.0.0.1",
            port_udp=udp_b,
            port_ws=find_free_port(),
            ssl_context=client_ctx,
        )
        await client.start()

        try:
            peer_id = await client.connect_peer(
                "127.0.0.1", ws_port, timeout=10.0
            )
            assert peer_id == "mtls-verify-server", (
                f"mTLS with verified client failed: got {peer_id}"
            )

            # Verify we can exchange messages
            peer = await client.get_peer("mtls-verify-server")
            assert peer is not None
            assert peer.connection_state == ConnectionState.CONNECTED

            # Send a test message
            test_msg = P2PMessage(
                msg_type="verify_test",
                sender_id="mtls-verify-client",
                msg_id="mTLS-verify-1",
                payload={"status": "verified"},
            )
            sent = await client.send_ws(peer, test_msg, retry=False)
            # The message should be deliverable over the mTLS channel
            assert sent, "Message should be sent over verified mTLS"
        finally:
            await client.stop()
            await server.stop()


# ═══════════════════════════════════════════════════════════════════════════
# TestTLSReject — Non-TLS client connecting to TLS server is rejected
# ═══════════════════════════════════════════════════════════════════════════

class TestTLSReject:
    """Non-TLS clients are rejected by TLS servers."""

    @pytest.mark.asyncio
    async def test_non_tls_client_rejected(self):
        """A client without SSL context cannot connect to a TLS server."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        ws_port = find_free_port()
        udp_a = find_free_port()
        udp_b = find_free_port()

        cert_pem, key_pem = _generate_self_signed_cert("127.0.0.1")
        server_ctx = _make_tls_server_ctx(cert_pem, key_pem)

        server = P2PTransport(
            node_id="tls-reject-server",
            host="127.0.0.1",
            port_udp=udp_a,
            port_ws=ws_port,
            ssl_context=server_ctx,
        )
        await server.start()

        # Client WITHOUT SSL context — should fail TLS handshake
        client = P2PTransport(
            node_id="plain-client",
            host="127.0.0.1",
            port_udp=udp_b,
            port_ws=find_free_port(),
            ssl_context=None,  # No TLS
        )
        await client.start()

        try:
            peer_id = await client.connect_peer(
                "127.0.0.1", ws_port, timeout=5.0
            )
            # Connection should fail — peer_id should be None
            assert peer_id is None, (
                "Non-TLS client should NOT be able to connect to TLS server"
            )
        finally:
            await client.stop()
            await server.stop()

    @pytest.mark.asyncio
    async def test_tls_server_rejects_wrong_cert(self):
        """A client with a cert signed by a different CA is rejected."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        ws_port = find_free_port()
        udp_a = find_free_port()
        udp_b = find_free_port()

        # Generate two different CA certs
        ca_server_pem, _ = _generate_self_signed_cert("Server-CA")
        ca_client_pem, _ = _generate_self_signed_cert("Client-CA")

        server_cert_pem, server_key_pem = _generate_self_signed_cert("127.0.0.1")
        client_cert_pem, client_key_pem = _generate_self_signed_cert(
            "rogue-client", "rogue.local"
        )

        # Server context — requires client cert, trusts only Server-CA
        # Client context — cert signed by Client-CA, NOT Server-CA
        server_ctx = _make_mtls_server_ctx(server_cert_pem, server_key_pem, ca_server_pem)
        client_ctx = _make_mtls_client_ctx(client_cert_pem, client_key_pem)

        server = P2PTransport(
            node_id="mtls-strict-server",
            host="127.0.0.1",
            port_udp=udp_a,
            port_ws=ws_port,
            ssl_context=server_ctx,
        )
        await server.start()

        client = P2PTransport(
            node_id="rogue-client",
            host="127.0.0.1",
            port_udp=udp_b,
            port_ws=find_free_port(),
            ssl_context=client_ctx,
        )
        await client.start()

        try:
            peer_id = await client.connect_peer(
                "127.0.0.1", ws_port, timeout=5.0
            )
            # mTLS should fail — client cert signed by wrong CA
            assert peer_id is None, (
                "Client with cert from wrong CA should be rejected"
            )
        finally:
            await client.stop()
            await server.stop()


# ═══════════════════════════════════════════════════════════════════════════
# TestTLSBootstrap — Bootstrap over TLS connection
# ═══════════════════════════════════════════════════════════════════════════

class TestTLSBootstrap:
    """Bootstrap service communication over TLS."""

    @pytest.mark.asyncio
    async def test_bootstrap_over_tls(self):
        """Bootstrap request/response works over TLS-encrypted TCP."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        bs_port = find_free_port()

        cert_pem, key_pem = _generate_self_signed_cert("127.0.0.1")
        server_ctx = _make_tls_server_ctx(cert_pem, key_pem)
        client_ctx = _make_tls_client_ctx()

        # Start bootstrap service with TLS
        bs = BootstrapService(
            node_id="tls-bootstrap",
            is_bootstrap=True,
            port=bs_port,
            ssl_context=server_ctx,
        )
        await bs.start()

        # Create a client bootstrap service (no self-bootstrap) to make request
        client_bs = BootstrapService(
            node_id="tls-bootstrap-client",
            is_bootstrap=False,
            ssl_context=client_ctx,
        )

        try:
            response = await client_bs.request_bootstrap(
                "127.0.0.1", bs_port,
            )
            assert response is not None, (
                "Bootstrap response should not be None over TLS"
            )
            assert response.success, (
                "Bootstrap request should succeed over TLS"
            )
            assert len(response.bootstrap_nodes) > 0, (
                "Should receive bootstrap nodes over TLS"
            )
        finally:
            await client_bs.stop()
            await bs.stop()

    @pytest.mark.asyncio
    async def test_bootstrap_tls_rejects_non_tls(self):
        """Bootstrap server rejects non-TLS clients."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        bs_port = find_free_port()

        cert_pem, key_pem = _generate_self_signed_cert("127.0.0.1")
        server_ctx = _make_tls_server_ctx(cert_pem, key_pem)

        # Bootstrap server with TLS
        bs = BootstrapService(
            node_id="tls-bs-reject",
            is_bootstrap=True,
            port=bs_port,
            ssl_context=server_ctx,
        )
        await bs.start()

        # Client WITHOUT TLS
        client_bs = BootstrapService(
            node_id="non-tls-client",
            is_bootstrap=False,
            ssl_context=None,
        )

        try:
            response = await client_bs.request_bootstrap(
                "127.0.0.1", bs_port,
            )
            # Without TLS connecting to TLS server, should fail
            assert response is None, (
                "Non-TLS bootstrap client should fail against TLS server"
            )
        finally:
            await client_bs.stop()
            await bs.stop()

    @pytest.mark.asyncio
    async def test_bootstrap_register_over_tls(self):
        """Peer registration works over TLS bootstrap connection."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography not available")

        bs_port = find_free_port()

        cert_pem, key_pem = _generate_self_signed_cert("127.0.0.1")
        server_ctx = _make_tls_server_ctx(cert_pem, key_pem)
        client_ctx = _make_tls_client_ctx()

        bs = BootstrapService(
            node_id="tls-bs-reg",
            is_bootstrap=True,
            port=bs_port,
            ssl_context=server_ctx,
        )
        await bs.start()

        client_bs = BootstrapService(
            node_id="registering-client",
            is_bootstrap=False,
            ssl_context=client_ctx,
        )

        try:
            response = await client_bs.request_bootstrap(
                "127.0.0.1", bs_port,
                register=True,
                port_ws=7333,
                port_udp=7332,
            )
            assert response is not None, (
                "Bootstrap response should succeed over TLS"
            )
            assert response.success, (
                "Registration request should succeed"
            )
        finally:
            await client_bs.stop()
            await bs.stop()


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main(["-v", __file__])
