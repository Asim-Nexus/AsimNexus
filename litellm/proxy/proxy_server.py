
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Simple ProxyConfig stub for litellm.proxy.proxy_server
"""
from dataclasses import dataclass


@dataclass
class ProxyConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    enable_tls: bool = False
    tls_cert_path: str | None = None
    tls_key_path: str | None = None

