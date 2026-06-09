#!/usr/bin/env python3
"""
REAL test: P2P Transport TLS/mTLS (Phase 1A)
=============================================
Tests that P2PTransport correctly handles SSL/TLS connections.

Coverage:
- Self-signed TLS handshake between two transports
- is_secure property reflects TLS state
- get_stats() includes tls_enabled
- Connections fail when TLS mismatched (one side TLS, other not)
- BootstrapService with TLS
"""

import os
import sys
import ssl
import time
import asyncio
import logging
import socket
import random
from typing import Optional

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest

from mesh.p2p_transport import (
    P2PTransport,
    P2PMessage,
    PeerInfo,
    ConnectionState,
    WSMessageType,
    RPCMessageType,
    get_p2p_transport,
    reset_p2p_transport,
    RateLimitError,
)
from mesh.bootstrap import (
    BootstrapService,
    BootstrapNode,
    BootstrapRegion,
    RegisteredPeer,
    get_bootstrap_service,
    reset_bootstrap_service,
)

logger = logging.getLogger("TestMeshTransportTLS")
logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Avoid ephemeral port range (49152-65535) on Windows where UDP may be blocked
_EPHEMERAL_PORT_MAX = 49000


def find_free_port() -> int:
    """Find a free port outside the Windows ephemeral range for UDP compatibility."""
    for _ in range(50):
        port = random.randint(10000, _EPHEMERAL_PORT_MAX)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                # Also verify UDP is usable on this port
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as u:
                    u.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    # Fallback: let OS assign
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _generate_self_signed_cert(key_path: str, cert_path: str) -> None:
    """Generate a self-signed cert using cryptography library.

    Uses ipaddress standard library (not x509.IPAddress.from_string)
    for compatibility across cryptography versions.
    """
    import ipaddress
    from datetime import datetime, timedelta
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.COMMON_NAME, "asimnexus.test"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(1000)
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
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


def _create_self_signed_ssl_context() -> ssl.SSLContext:
    """Create a self-signed SSL context for testing.

    Uses cryptography library to generate a temporary self-signed
    certificate, loads it into an SSL context, then cleans up.
    """
    import tempfile

    tmpdir = tempfile.mkdtemp()
    key_path = os.path.join(tmpdir, "test.key")
    cert_path = os.path.join(tmpdir, "test.crt")

    _generate_self_signed_cert(key_path, cert_path)

    # Create SSL context
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(cert_path, key_path)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # No client cert verification for test

    # Cleanup temp files after context is loaded
    try:
        os.remove(key_path)
        os.remove(cert_path)
        os.rmdir(tmpdir)
    except Exception:
        pass

    return ctx


def _create_self_signed_client_context() -> ssl.SSLContext:
    """Create an SSL context for client-side connections (no client cert)."""
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # Accept self-signed server cert
    return ctx


@pytest.fixture
def event_loop():
    """Create a fresh event loop per test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Test: TLS Handshake
# ---------------------------------------------------------------------------

class TestTLSTransport:
    """TLS-enabled P2PTransport connections."""

    @pytest.mark.asyncio
    async def test_tls_handshake(self):
        """Two transports can connect with self-signed TLS certs."""
        server_ctx = _create_self_signed_ssl_context()
        client_ctx = _create_self_signed_client_context()

        server_port = find_free_port()
        server_udp = find_free_port()

        server = P2PTransport(
            node_id="tls-server",
            host="127.0.0.1",
            port_udp=server_udp,
            port_ws=server_port,
            ssl_context=server_ctx,
        )
        assert server.is_secure, "Server should report is_secure=True"

        client = P2PTransport(
            node_id="tls-client",
            host="127.0.0.1",
            port_udp=find_free_port(),
            port_ws=find_free_port(),
            ssl_context=client_ctx,
        )
        assert client.is_secure, "Client should report is_secure=True"

        try:
            await server.start()
            await client.start()

            # Connect client to server via TLS
            peer_id = await client.connect_peer("127.0.0.1", server_port, timeout=10.0)
            assert peer_id is not None, "TLS handshake should succeed"
            assert peer_id == "tls-server", f"Expected tls-server, got {peer_id}"

            # Verify stats show TLS enabled
            server_stats = server.get_stats()
            assert server_stats["tls_enabled"] is True
            assert server_stats["peers_connected"] >= 1

            client_stats = client.get_stats()
            assert client_stats["tls_enabled"] is True

            # Verify peer state
            server_peer = await server.get_peer("tls-client")
            assert server_peer is not None
            assert server_peer.connection_state == ConnectionState.CONNECTED

            client_peer = await client.get_peer("tls-server")
            assert client_peer is not None
            assert client_peer.connection_state == ConnectionState.CONNECTED

        finally:
            await client.stop()
            await server.stop()

    @pytest.mark.asyncio
    async def test_tls_mismatch_fails(self):
        """Connection fails when one side uses TLS and the other doesn't."""
        server_ctx = _create_self_signed_ssl_context()

        server_port = find_free_port()
        server_udp = find_free_port()

        server = P2PTransport(
            node_id="tls-server-only",
            host="127.0.0.1",
            port_udp=server_udp,
            port_ws=server_port,
            ssl_context=server_ctx,
        )
        assert server.is_secure

        # Client without TLS
        client = P2PTransport(
            node_id="plain-client",
            host="127.0.0.1",
            port_udp=find_free_port(),
            port_ws=find_free_port(),
            ssl_context=None,
        )
        assert not client.is_secure

        try:
            await server.start()
            await client.start()

            # Client without TLS tries to connect to TLS server — should fail
            peer_id = await client.connect_peer("127.0.0.1", server_port, timeout=5.0)
            assert peer_id is None, "TLS mismatch should fail to connect"

            # Server should NOT have the client in its peer list
            server_peer = await server.get_peer("plain-client")
            assert server_peer is None, (
                "Server should not have added plain-client after failed TLS handshake"
            )

        finally:
            await client.stop()
            await server.stop()

    @pytest.mark.asyncio
    async def test_tls_get_stats(self):
        """get_stats() correctly reports TLS state."""
        ctx = _create_self_signed_ssl_context()

        transport = P2PTransport(
            node_id="stats-tls-test",
            host="127.0.0.1",
            port_udp=find_free_port(),
            port_ws=find_free_port(),
            ssl_context=ctx,
        )

        stats = transport.get_stats()
        assert stats["tls_enabled"] is True
        assert transport.is_secure is True

        await transport.stop()

    @pytest.mark.asyncio
    async def test_tls_bootstrap_integration(self):
        """BootstrapService works with TLS-enabled transports."""
        server_ctx = _create_self_signed_ssl_context()

        bs_port = find_free_port()
        bs = BootstrapService(
            node_id="tls-bootstrap",
            is_bootstrap=True,
            port=bs_port,
            ssl_context=server_ctx,
        )
        try:
            await bs.start()

            # Client bootstrap request over TLS
            # request_bootstrap uses self._ssl_context internally
            # (passed via constructor), so no ssl= parameter needed
            response = await bs.request_bootstrap(
                bootstrap_address="127.0.0.1",
                bootstrap_port=bs_port,
            )
            assert response is not None, "TLS bootstrap request should succeed"
            assert response.success is True

        finally:
            await bs.stop()
