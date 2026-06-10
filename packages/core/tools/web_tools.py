#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade Web Tools for Agent System

Tool functions for web search, fetching URLs, and CSS-selector scraping.
Each function has a TOOL_DEFINITION dict for OpenAI-compatible function calling,
proper error handling, and structured JSON-serializable return values.

Security: These are SECURE-level tools (read-only operations).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger("AsimNexus.Tools.Web")

# ─── Constants ─────────────────────────────────────────────────────────────────

_DEFAULT_SEARCH_RESULTS = 5
_DEFAULT_FETCH_TIMEOUT = 15
_MAX_RESPONSE_SIZE = 2 * 1024 * 1024  # 2 MB
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 "
    "AsimNexusAgent/1.0"
)


# ─── Helper ────────────────────────────────────────────────────────────────────

def _safe_result(success: bool, data: Any = None,
                 error: Optional[str] = None, **extra) -> Dict:
    """Build a standardized result dict."""
    result = {"success": success, "error": error}
    if data is not None:
        result["data"] = data
    result.update(extra)
    return result


def _validate_url(url: str) -> bool:
    """Basic URL validation."""
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


def _truncate_text(text: str, max_len: int = 10000) -> str:
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n... [Truncated at {max_len} chars]"


# ─── TOOL: web_search ──────────────────────────────────────────────────────────

TOOL_DEFINITION_WEB_SEARCH = {
    "name": "web_search",
    "description": "Search the web for information. Returns a list of search results with titles, URLs, and snippets.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string."
            },
            "num_results": {
                "type": "integer",
                "description": "Number of search results to return (default: 5, max: 20).",
                "default": 5
            }
        },
        "required": ["query"]
    }
}


def web_search(query: str, num_results: int = _DEFAULT_SEARCH_RESULTS) -> Dict[str, Any]:
    """Perform a web search using configured search provider.

    Supports multiple backends:
    1. DuckDuckGo (via duckduckgo_search library) - default
    2. Google Custom Search (if API keys configured)
    3. Local fallback with mock results for development

    Args:
        query: Search query.
        num_results: Number of results to return (max 20).

    Returns:
        Dict with keys: success, results (list of {title, url, snippet}), total_estimated
    """
    logger.info(f"Web search: '{query}' (results={num_results})")

    num_results = min(max(1, num_results), 20)

    # Try DuckDuckGo first (no API key needed)
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = []
            for i, r in enumerate(ddgs.text(query, max_results=num_results)):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
                if len(results) >= num_results:
                    break

            if results:
                logger.info(f"DuckDuckGo returned {len(results)} results")
                return _safe_result(
                    success=True,
                    data={
                        "results": results,
                        "total_estimated": len(results),
                        "source": "duckduckgo",
                    }
                )
    except ImportError:
        logger.debug("duckduckgo_search not available, trying fallbacks")
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")

    # Try Google Custom Search if configured
    google_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("ASIM_GOOGLE_API_KEY")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID") or os.environ.get("ASIM_GOOGLE_CSE_ID")

    if google_api_key and google_cse_id:
        try:
            import httpx
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": google_api_key,
                "cx": google_cse_id,
                "q": query,
                "num": min(num_results, 10),  # Google max 10 per request
            }
            response = httpx.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                results = [
                    {
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                    }
                    for item in items
                ]
                logger.info(f"Google Search returned {len(results)} results")
                return _safe_result(
                    success=True,
                    data={
                        "results": results,
                        "total_estimated": data.get("searchInformation", {}).get("totalResults", len(results)),
                        "source": "google",
                    }
                )
            else:
                logger.warning(f"Google Search API error: {response.status_code}")
        except ImportError:
            logger.debug("httpx not available for Google Search")
        except Exception as e:
            logger.warning(f"Google Search failed: {e}")

    # Fallback: return informative message
    logger.warning("No search backend available")
    return _safe_result(
        success=False,
        error=(
            "No search backend configured. Install 'duckduckgo_search' package "
            "or configure GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables."
        )
    )


# ─── TOOL: web_fetch ───────────────────────────────────────────────────────────

TOOL_DEFINITION_WEB_FETCH = {
    "name": "web_fetch",
    "description": "Fetch the content of a URL. Returns the raw HTML/text content.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to fetch."
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 15).",
                "default": 15
            }
        },
        "required": ["url"]
    }
}


def web_fetch(url: str, timeout: int = _DEFAULT_FETCH_TIMEOUT) -> Dict[str, Any]:
    """Fetch content from a URL.

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Dict with keys: success, content, url, content_type, status_code
    """
    logger.info(f"Fetching URL: {url}")

    if not _validate_url(url):
        return _safe_result(False, error=f"Invalid URL: {url}")

    try:
        import httpx

        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
            max_redirects=5,
        ) as client:
            response = client.get(url)

        if response.status_code >= 400:
            logger.warning(f"HTTP {response.status_code} for {url}")
            return _safe_result(
                False,
                error=f"HTTP {response.status_code}: {response.reason_phrase}",
                status_code=response.status_code,
                url=url,
            )

        content_type = response.headers.get("content-type", "")

        # Check if response is HTML or text
        if "text/" in content_type or "application/json" in content_type or "application/xml" in content_type:
            content = response.text
        else:
            # Binary content — return metadata only
            content_length = len(response.content)
            logger.info(f"Binary content at {url} ({content_length} bytes)")
            return _safe_result(
                success=True,
                data={
                    "url": url,
                    "content_type": content_type,
                    "size_bytes": content_length,
                    "note": "Binary content not displayed",
                    "content": None,
                }
            )

        # Truncate if too large
        truncated = _truncate_text(content)
        if truncated != content:
            logger.info(f"Response truncated from {len(content)} to {len(truncated)} chars")

        return _safe_result(
            success=True,
            data={
                "url": url,
                "content": truncated,
                "content_type": content_type,
                "status_code": response.status_code,
            }
        )

    except ImportError:
        logger.error("httpx library not available")
        return _safe_result(False, error="httpx library not installed. Run: pip install httpx")
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {url}")
        return _safe_result(False, error=f"Request timed out after {timeout}s")
    except httpx.HTTPError as e:
        logger.warning(f"HTTP error fetching {url}: {e}")
        return _safe_result(False, error=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: web_scrape ──────────────────────────────────────────────────────────

TOOL_DEFINITION_WEB_SCRAPE = {
    "name": "web_scrape",
    "description": "Scrape content from a URL using a CSS selector. Returns matching elements.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to scrape."
            },
            "selector": {
                "type": "string",
                "description": "CSS selector to target elements (e.g., 'article p', '.content', '#main')."
            },
            "attribute": {
                "type": "string",
                "description": "Attribute to extract from elements (e.g., 'href', 'src'). If not specified, extracts text content.",
                "default": ""
            }
        },
        "required": ["url", "selector"]
    }
}


def web_scrape(url: str, selector: str, attribute: str = "") -> Dict[str, Any]:
    """Scrape content from a URL using a CSS selector.

    Args:
        url: URL to scrape.
        selector: CSS selector string.
        attribute: If provided, extract this attribute instead of text.

    Returns:
        Dict with keys: success, elements (list of scraped items), count, url
    """
    logger.info(f"Scraping {url} with selector '{selector}'")

    if not _validate_url(url):
        return _safe_result(False, error=f"Invalid URL: {url}")

    try:
        import httpx
        from selectolax.parser import HTMLParser

        with httpx.Client(
            timeout=_DEFAULT_FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        ) as client:
            response = client.get(url)

        if response.status_code >= 400:
            return _safe_result(
                False,
                error=f"HTTP {response.status_code}: {response.reason_phrase}",
                status_code=response.status_code,
            )

        # Parse HTML
        parser = HTMLParser(response.text)
        elements = parser.css(selector)

        if not elements:
            logger.info(f"No elements found for selector '{selector}' on {url}")
            return _safe_result(
                success=True,
                data={"url": url, "selector": selector, "elements": [], "count": 0}
            )

        # Extract text or attribute
        results = []
        for el in elements:
            if attribute:
                value = el.attributes.get(attribute, "")
            else:
                value = el.text(deep=True, separator=" ").strip()
            if value:  # Skip empty results
                results.append(value)

        return _safe_result(
            success=True,
            data={
                "url": url,
                "selector": selector,
                "elements": results[:100],  # Limit to 100 elements
                "count": len(results),
                "total_matched": len(elements),
            }
        )

    except ImportError as e:
        missing = "selectolax" if "selectolax" in str(e) else "httpx"
        logger.error(f"Missing library: {missing}")
        return _safe_result(False, error=f"{missing} library not installed. Run: pip install {missing}")
    except httpx.TimeoutException:
        logger.warning(f"Timeout scraping {url}")
        return _safe_result(False, error=f"Request timed out")
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return _safe_result(False, error=str(e))
