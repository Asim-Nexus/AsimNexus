"""
ObjectStore — Object storage wrapper for AsimNexus.

Wraps S3-compatible API (MinIO, AWS S3, Cloudflare R2, etc.)
with automatic local filesystem fallback.

Fallback chain: S3/MinIO → Local filesystem (data/object_store/)

Environment variables:
    ASIM_OBJECT_STORE_ENDPOINT   — S3 endpoint URL (default: http://localhost:9000)
    ASIM_ACCESS_KEY              — S3 access key
    ASIM_SECRET_KEY              — S3 secret key
    ASIM_OBJECT_STORE_REGION     — S3 region (default: auto)
    ASIM_OBJECT_STORE_BUCKET_PREFIX — Bucket name prefix (default: asimnexus)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ENV_ENDPOINT = "ASIM_OBJECT_STORE_ENDPOINT"
_ENV_ACCESS_KEY = "ASIM_ACCESS_KEY"
_ENV_SECRET_KEY = "ASIM_SECRET_KEY"
_ENV_REGION = "ASIM_OBJECT_STORE_REGION"
_ENV_BUCKET_PREFIX = "ASIM_OBJECT_STORE_BUCKET_PREFIX"

_DEFAULT_ENDPOINT = "http://localhost:9000"
_DEFAULT_REGION = "auto"
_DEFAULT_BUCKET_PREFIX = "asimnexus"
_DEFAULT_LOCAL_PATH = "data/object_store"

DEFAULT_BUCKETS: List[str] = [
    "raw-logs",
    "exports",
    "snapshots",
    "deployment-artifacts",
    "user-uploads",
    "mesh-offline-buffers",
    "backups",
    "audit-archive",
]


# ===================================================================
# ObjectStore
# ===================================================================


class ObjectStore:
    """
    Object storage for raw files, logs, exports, snapshots.

    Wraps S3-compatible API (MinIO, AWS S3, Cloudflare R2, etc.)
    with automatic local filesystem fallback.

    Fallback chain: S3/MinIO → Local filesystem (``data/object_store/``)

    Parameters
    ----------
    endpoint : str, optional
        S3 endpoint URL. Falls back to ``ASIM_OBJECT_STORE_ENDPOINT`` env var,
        then ``http://localhost:9000``.
    access_key : str, optional
        S3 access key. Falls back to ``ASIM_ACCESS_KEY`` env var.
    secret_key : str, optional
        S3 secret key. Falls back to ``ASIM_SECRET_KEY`` env var.
    region : str, optional
        S3 region. Falls back to ``ASIM_OBJECT_STORE_REGION`` env var,
        then ``auto``.
    bucket_prefix : str, optional
        Prefix for all bucket names. Falls back to
        ``ASIM_OBJECT_STORE_BUCKET_PREFIX`` env var, then ``asimnexus``.
    local_path : str, optional
        Local filesystem path for fallback storage. Defaults to
        ``data/object_store``.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "auto",
        bucket_prefix: str = "asimnexus",
        local_path: str = "data/object_store",
    ) -> None:
        # Resolve configuration from env vars with defaults
        self._endpoint: str = endpoint or os.environ.get(
            _ENV_ENDPOINT, _DEFAULT_ENDPOINT
        )
        self._access_key: Optional[str] = access_key or os.environ.get(
            _ENV_ACCESS_KEY
        )
        self._secret_key: Optional[str] = secret_key or os.environ.get(
            _ENV_SECRET_KEY
        )
        self._region: str = region or os.environ.get(
            _ENV_REGION, _DEFAULT_REGION
        )
        self._bucket_prefix: str = bucket_prefix or os.environ.get(
            _ENV_BUCKET_PREFIX, _DEFAULT_BUCKET_PREFIX
        )
        self._local_root: str = local_path

        # Runtime state
        self._s3_client: Any = None  # boto3 S3 client (sync, run in executor)
        self._connected: bool = False
        self._mode: str = "unknown"  # "s3" | "local"

        # Write lock for local filesystem operations
        self._local_lock: asyncio.Lock = asyncio.Lock()

        # Track created buckets for health checks
        self._created_buckets: List[str] = list(DEFAULT_BUCKETS)

        logger.info(
            "ObjectStore initialised (endpoint=%s, region=%s, bucket_prefix=%s, local_path=%s)",
            self._endpoint,
            self._region,
            self._bucket_prefix,
            self._local_root,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        """Whether the store currently has an active connection."""
        return self._connected

    @property
    def mode(self) -> str:
        """Current active storage mode (``s3`` or ``local``)."""
        return self._mode

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Initialize S3 client or set up local filesystem.

        Attempts to create a ``boto3`` S3 client and verify connectivity
        by listing buckets. If S3 is unavailable, falls back to the local
        filesystem. Creates default buckets in the active mode.
        """
        if self._connected:
            logger.debug("ObjectStore already connected")
            return

        # Attempt S3 connection
        s3_ok = await self._try_s3_connect()

        if s3_ok:
            self._mode = "s3"
            self._connected = True
            logger.info(
                "ObjectStore connected to S3/MinIO at %s",
                self._endpoint,
            )
            # Create default buckets in S3
            await self._ensure_default_buckets_s3()
            return

        # Fallback: local filesystem (always succeeds)
        logger.warning(
            "S3/MinIO unavailable, falling back to local filesystem: %s",
            self._local_root,
        )
        self._mode = "local"
        self._connected = True
        # Create default buckets on local filesystem
        await self._ensure_default_buckets_local()
        logger.info(
            "ObjectStore using local filesystem fallback at %s",
            self._local_root,
        )

    async def close(self) -> None:
        """Close the S3 client connection and release resources."""
        if self._s3_client is not None:
            # boto3 client doesn't have an explicit close,
            # but we clear the reference
            self._s3_client = None

        self._connected = False
        self._mode = "unknown"
        logger.info("ObjectStore closed")

    async def __aenter__(self) -> "ObjectStore":
        await self.connect()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Internal connection helpers
    # ------------------------------------------------------------------

    async def _try_s3_connect(self) -> bool:
        """Try to create a ``boto3`` S3 client and verify connectivity.

        Returns ``True`` if the client was created and can list buckets.
        """
        try:
            import boto3
            from botocore.client import Config as BotoConfig
        except ImportError:
            logger.debug("boto3 not installed — skipping S3 connection")
            return False

        try:
            loop = asyncio.get_running_loop()

            def _create_client() -> Any:
                client = boto3.client(
                    "s3",
                    endpoint_url=self._endpoint,
                    aws_access_key_id=self._access_key,
                    aws_secret_access_key=self._secret_key,
                    region_name=self._region,
                    config=BotoConfig(
                        connect_timeout=5,
                        read_timeout=30,
                        retries={"max_attempts": 3},
                        signature_version="s3v4",
                    ),
                )
                # Verify connection by listing buckets
                client.list_buckets()
                return client

            self._s3_client = await loop.run_in_executor(
                None, _create_client
            )
            logger.debug("S3 client created and verified successfully")
            return True

        except Exception as exc:
            logger.debug("S3 connection failed: %s", exc)
            self._s3_client = None
            return False

    async def _ensure_default_buckets_s3(self) -> None:
        """Create all default buckets in S3 if they don't exist."""
        if self._s3_client is None:
            return

        loop = asyncio.get_running_loop()

        for bucket in DEFAULT_BUCKETS:
            full_name = self._full_bucket_name(bucket)
            try:

                def _create_bucket(b: str = full_name) -> bool:
                    try:
                        existing = self._s3_client.list_buckets()
                        existing_names = [
                            eb["Name"] for eb in existing.get("Buckets", [])
                        ]
                        if b not in existing_names:
                            kwargs: Dict[str, Any] = {"Bucket": b}
                            if self._region != "auto":
                                kwargs["CreateBucketConfiguration"] = {
                                    "LocationConstraint": self._region
                                }
                            self._s3_client.create_bucket(**kwargs)
                            logger.debug("Created S3 bucket '%s'", b)
                        return True
                    except Exception as exc:
                        logger.debug(
                            "Failed to create S3 bucket '%s': %s", b, exc
                        )
                        return False

                await loop.run_in_executor(None, _create_bucket)

            except Exception as exc:
                logger.warning(
                    "Failed to ensure S3 bucket '%s': %s", full_name, exc
                )

    async def _ensure_default_buckets_local(self) -> None:
        """Create all default bucket directories on the local filesystem."""
        for bucket in DEFAULT_BUCKETS:
            bucket_path = os.path.join(
                self._local_root, self._full_bucket_name(bucket)
            )
            try:
                os.makedirs(bucket_path, exist_ok=True)
            except Exception as exc:
                logger.warning(
                    "Failed to create local bucket directory '%s': %s",
                    bucket_path,
                    exc,
                )

    def _full_bucket_name(self, bucket: str) -> str:
        """Return the full bucket name with prefix applied."""
        return f"{self._bucket_prefix}-{bucket}"

    # ------------------------------------------------------------------
    # Upload operations
    # ------------------------------------------------------------------

    async def upload(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Upload bytes to object store.

        Attempts S3 upload first. Falls back to local filesystem on failure.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).
        key : str
            Object key/path within the bucket.
        data : bytes
            Raw bytes to upload.
        content_type : str, optional
            MIME type of the object (e.g. ``application/json``).
        metadata : Dict[str, str], optional
            Custom metadata to attach to the object.

        Returns
        -------
        bool
            ``True`` if the upload succeeded.
        """
        if not self._connected:
            await self.connect()

        try:
            if self._mode == "s3" and self._s3_client is not None:
                return await self._s3_upload(
                    bucket, key, data, content_type, metadata
                )
            else:
                return await self._local_upload(
                    bucket, key, data, content_type
                )
        except Exception as exc:
            logger.error(
                "Upload failed (mode=%s, bucket=%s, key=%s): %s",
                self._mode,
                bucket,
                key,
                exc,
            )
            # Attempt fallback
            if self._mode == "s3":
                logger.warning(
                    "S3 upload failed, falling back to local filesystem"
                )
                return await self._local_upload(
                    bucket, key, data, content_type
                )
            return False

    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_path: str,
        content_type: Optional[str] = None,
    ) -> bool:
        """Upload a file from the local filesystem to object store.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).
        key : str
            Object key/path within the bucket.
        file_path : str
            Path to the local file to upload.
        content_type : str, optional
            MIME type of the object.

        Returns
        -------
        bool
            ``True`` if the upload succeeded.
        """
        try:
            async with aiofiles.open(file_path, mode="rb") as f:
                data = await f.read()
            return await self.upload(bucket, key, data, content_type)
        except Exception as exc:
            logger.error(
                "Upload file failed (path=%s, bucket=%s, key=%s): %s",
                file_path,
                bucket,
                key,
                exc,
            )
            return False

    async def _s3_upload(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Upload bytes via S3."""
        if self._s3_client is None:
            return False

        full_bucket = self._full_bucket_name(bucket)
        loop = asyncio.get_running_loop()

        def _do_upload() -> bool:
            try:
                put_kwargs: Dict[str, Any] = {
                    "Bucket": full_bucket,
                    "Key": key,
                    "Body": data,
                }
                if content_type:
                    put_kwargs["ContentType"] = content_type
                if metadata:
                    put_kwargs["Metadata"] = metadata
                self._s3_client.put_object(**put_kwargs)
                return True
            except Exception as exc:
                logger.error("S3 put_object failed: %s", exc)
                return False

        return await loop.run_in_executor(None, _do_upload)

    async def _local_upload(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
    ) -> bool:
        """Upload bytes to local filesystem."""
        full_bucket = self._full_bucket_name(bucket)
        dest = os.path.join(self._local_root, full_bucket, key)

        async with self._local_lock:
            try:
                dest_dir = os.path.dirname(dest)
                os.makedirs(dest_dir, exist_ok=True)

                async with aiofiles.open(dest, mode="wb") as f:
                    await f.write(data)

                # Write metadata sidecar if content_type is provided
                if content_type:
                    meta_path = dest + ".meta.json"
                    async with aiofiles.open(
                        meta_path, mode="w", encoding="utf-8"
                    ) as mf:
                        await mf.write(
                            json.dumps(
                                {
                                    "content_type": content_type,
                                    "size": len(data),
                                }
                            )
                        )

                return True

            except Exception as exc:
                logger.error("Local upload failed: %s", exc)
                return False

    # ------------------------------------------------------------------
    # Download operations
    # ------------------------------------------------------------------

    async def download(self, bucket: str, key: str) -> Optional[bytes]:
        """Download an object as bytes.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).
        key : str
            Object key/path within the bucket.

        Returns
        -------
        Optional[bytes]
            Object data as bytes, or ``None`` if not found.
        """
        if not self._connected:
            await self.connect()

        try:
            if self._mode == "s3" and self._s3_client is not None:
                return await self._s3_download(bucket, key)
            else:
                return await self._local_download(bucket, key)
        except Exception as exc:
            logger.error(
                "Download failed (mode=%s, bucket=%s, key=%s): %s",
                self._mode,
                bucket,
                key,
                exc,
            )
            # Attempt fallback
            if self._mode == "s3":
                logger.warning(
                    "S3 download failed, trying local filesystem"
                )
                return await self._local_download(bucket, key)
            return None

    async def download_to_file(
        self, bucket: str, key: str, dest_path: str
    ) -> bool:
        """Download an object to a local file.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).
        key : str
            Object key/path within the bucket.
        dest_path : str
            Destination path on the local filesystem.

        Returns
        -------
        bool
            ``True`` if the download succeeded.
        """
        try:
            data = await self.download(bucket, key)
            if data is None:
                return False

            dest_dir = os.path.dirname(dest_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)

            async with aiofiles.open(dest_path, mode="wb") as f:
                await f.write(data)

            return True

        except Exception as exc:
            logger.error(
                "Download to file failed (bucket=%s, key=%s, dest=%s): %s",
                bucket,
                key,
                dest_path,
                exc,
            )
            return False

    async def _s3_download(
        self, bucket: str, key: str
    ) -> Optional[bytes]:
        """Download an object from S3."""
        if self._s3_client is None:
            return None

        full_bucket = self._full_bucket_name(bucket)
        loop = asyncio.get_running_loop()

        def _do_download() -> Optional[bytes]:
            try:
                response = self._s3_client.get_object(
                    Bucket=full_bucket, Key=key
                )
                return response["Body"].read()
            except Exception as exc:
                logger.debug("S3 get_object failed: %s", exc)
                return None

        return await loop.run_in_executor(None, _do_download)

    async def _local_download(
        self, bucket: str, key: str
    ) -> Optional[bytes]:
        """Download an object from local filesystem."""
        full_bucket = self._full_bucket_name(bucket)
        source = os.path.join(self._local_root, full_bucket, key)

        async with self._local_lock:
            try:
                if not os.path.isfile(source):
                    logger.debug("Local file not found: %s", source)
                    return None

                async with aiofiles.open(source, mode="rb") as f:
                    return await f.read()

            except Exception as exc:
                logger.error("Local download failed: %s", exc)
                return None

    # ------------------------------------------------------------------
    # Delete operation
    # ------------------------------------------------------------------

    async def delete(self, bucket: str, key: str) -> bool:
        """Delete an object.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).
        key : str
            Object key/path within the bucket.

        Returns
        -------
        bool
            ``True`` if the deletion succeeded or the object did not exist.
        """
        if not self._connected:
            await self.connect()

        try:
            if self._mode == "s3" and self._s3_client is not None:
                return await self._s3_delete(bucket, key)
            else:
                return await self._local_delete(bucket, key)
        except Exception as exc:
            logger.error(
                "Delete failed (mode=%s, bucket=%s, key=%s): %s",
                self._mode,
                bucket,
                key,
                exc,
            )
            if self._mode == "s3":
                logger.warning(
                    "S3 delete failed, trying local filesystem"
                )
                return await self._local_delete(bucket, key)
            return False

    async def _s3_delete(self, bucket: str, key: str) -> bool:
        """Delete an object from S3."""
        if self._s3_client is None:
            return False

        full_bucket = self._full_bucket_name(bucket)
        loop = asyncio.get_running_loop()

        def _do_delete() -> bool:
            try:
                self._s3_client.delete_object(Bucket=full_bucket, Key=key)
                return True
            except Exception as exc:
                logger.error("S3 delete_object failed: %s", exc)
                return False

        return await loop.run_in_executor(None, _do_delete)

    async def _local_delete(self, bucket: str, key: str) -> bool:
        """Delete an object from local filesystem."""
        full_bucket = self._full_bucket_name(bucket)
        target = os.path.join(self._local_root, full_bucket, key)

        async with self._local_lock:
            try:
                if os.path.isfile(target):
                    os.remove(target)
                    # Also remove metadata sidecar if present
                    meta_path = target + ".meta.json"
                    if os.path.isfile(meta_path):
                        os.remove(meta_path)
                    return True
                # Object doesn't exist — consider deletion successful
                return True

            except Exception as exc:
                logger.error("Local delete failed: %s", exc)
                return False

    # ------------------------------------------------------------------
    # List operation
    # ------------------------------------------------------------------

    async def list(
        self, bucket: str, prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """List objects in a bucket with the given prefix.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).
        prefix : str, optional
            Object key prefix to filter by.

        Returns
        -------
        List[Dict[str, Any]]
            List of object metadata dicts with keys:
            ``key``, ``size``, ``last_modified``, ``etag``.
        """
        if not self._connected:
            await self.connect()

        try:
            if self._mode == "s3" and self._s3_client is not None:
                return await self._s3_list(bucket, prefix)
            else:
                return await self._local_list(bucket, prefix)
        except Exception as exc:
            logger.error(
                "List failed (mode=%s, bucket=%s, prefix=%s): %s",
                self._mode,
                bucket,
                prefix,
                exc,
            )
            return []

    async def _s3_list(
        self, bucket: str, prefix: str
    ) -> List[Dict[str, Any]]:
        """List objects in S3 with prefix."""
        if self._s3_client is None:
            return []

        full_bucket = self._full_bucket_name(bucket)
        loop = asyncio.get_running_loop()

        def _do_list() -> List[Dict[str, Any]]:
            try:
                results: List[Dict[str, Any]] = []
                paginator = self._s3_client.get_paginator(
                    "list_objects_v2"
                )
                for page in paginator.paginate(
                    Bucket=full_bucket, Prefix=prefix
                ):
                    for obj in page.get("Contents", []):
                        results.append(
                            {
                                "key": obj["Key"],
                                "size": obj["Size"],
                                "last_modified": obj["LastModified"].isoformat()
                                if hasattr(obj["LastModified"], "isoformat")
                                else str(obj["LastModified"]),
                                "etag": obj["ETag"].strip('"'),
                            }
                        )
                return results

            except Exception as exc:
                logger.debug("S3 list_objects failed: %s", exc)
                return []

        return await loop.run_in_executor(None, _do_list)

    async def _local_list(
        self, bucket: str, prefix: str
    ) -> List[Dict[str, Any]]:
        """List objects on local filesystem with prefix."""
        full_bucket = self._full_bucket_name(bucket)
        search_dir = os.path.join(self._local_root, full_bucket, prefix)

        async with self._local_lock:
            try:
                if not os.path.isdir(
                    os.path.dirname(search_dir)
                ) and not os.path.isdir(search_dir):
                    return []

                results: List[Dict[str, Any]] = []
                base = os.path.join(self._local_root, full_bucket)

                # Walk the directory tree
                for root_str, _dirs, files in os.walk(
                    os.path.dirname(search_dir) if os.path.isfile(search_dir)
                    else search_dir
                ):
                    for fname in files:
                        # Skip metadata sidecar files
                        if fname.endswith(".meta.json"):
                            continue

                        full_path = os.path.join(root_str, fname)
                        rel_path = os.path.relpath(full_path, base)
                        # Normalize path separators to forward slash
                        rel_key = rel_path.replace("\\", "/")

                        # Apply prefix filter
                        if prefix and not rel_key.startswith(prefix):
                            continue

                        try:
                            stat = os.stat(full_path)
                            results.append(
                                {
                                    "key": rel_key,
                                    "size": stat.st_size,
                                    "last_modified": time.strftime(
                                        "%Y-%m-%dT%H:%M:%S",
                                        time.gmtime(stat.st_mtime),
                                    ),
                                    "etag": "",
                                }
                            )
                        except Exception:
                            pass

                return results

            except Exception as exc:
                logger.debug("Local list failed: %s", exc)
                return []

    # ------------------------------------------------------------------
    # Exists operation
    # ------------------------------------------------------------------

    async def exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).
        key : str
            Object key/path within the bucket.

        Returns
        -------
        bool
            ``True`` if the object exists.
        """
        if not self._connected:
            await self.connect()

        try:
            if self._mode == "s3" and self._s3_client is not None:
                return await self._s3_exists(bucket, key)
            else:
                return await self._local_exists(bucket, key)
        except Exception as exc:
            logger.error(
                "Exists check failed (mode=%s, bucket=%s, key=%s): %s",
                self._mode,
                bucket,
                key,
                exc,
            )
            if self._mode == "s3":
                return await self._local_exists(bucket, key)
            return False

    async def _s3_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in S3."""
        if self._s3_client is None:
            return False

        full_bucket = self._full_bucket_name(bucket)
        loop = asyncio.get_running_loop()

        def _do_exists() -> bool:
            try:
                self._s3_client.head_object(
                    Bucket=full_bucket, Key=key
                )
                return True
            except Exception:
                return False

        return await loop.run_in_executor(None, _do_exists)

    async def _local_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists on local filesystem."""
        full_bucket = self._full_bucket_name(bucket)
        target = os.path.join(self._local_root, full_bucket, key)

        async with self._local_lock:
            return os.path.isfile(target)

    # ------------------------------------------------------------------
    # Presigned URL
    # ------------------------------------------------------------------

    async def get_presigned_url(
        self, bucket: str, key: str, expires_in: int = 3600
    ) -> Optional[str]:
        """Generate a presigned URL for temporary access to an object.

        Only available in S3 mode. Returns ``None`` in local mode.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).
        key : str
            Object key/path within the bucket.
        expires_in : int, optional
            Expiration time in seconds (default: 3600).

        Returns
        -------
        Optional[str]
            Presigned URL string, or ``None`` if unavailable.
        """
        if not self._connected:
            await self.connect()

        if self._mode != "s3" or self._s3_client is None:
            logger.debug(
                "Presigned URLs not available in local mode"
            )
            return None

        full_bucket = self._full_bucket_name(bucket)
        loop = asyncio.get_running_loop()

        def _do_presigned() -> Optional[str]:
            try:
                url = self._s3_client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": full_bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
            except Exception as exc:
                logger.error(
                    "Failed to generate presigned URL: %s", exc
                )
                return None

        return await loop.run_in_executor(None, _do_presigned)

    # ------------------------------------------------------------------
    # Bucket management
    # ------------------------------------------------------------------

    async def create_bucket(self, bucket: str) -> bool:
        """Create a bucket if it does not exist.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).

        Returns
        -------
        bool
            ``True`` if the bucket was created or already exists.
        """
        if not self._connected:
            await self.connect()

        full_name = self._full_bucket_name(bucket)

        try:
            if self._mode == "s3" and self._s3_client is not None:
                loop = asyncio.get_running_loop()

                def _do_create() -> bool:
                    try:
                        existing = self._s3_client.list_buckets()
                        existing_names = [
                            eb["Name"]
                            for eb in existing.get("Buckets", [])
                        ]
                        if full_name not in existing_names:
                            kwargs: Dict[str, Any] = {"Bucket": full_name}
                            if self._region != "auto":
                                kwargs[
                                    "CreateBucketConfiguration"
                                ] = {
                                    "LocationConstraint": self._region
                                }
                            self._s3_client.create_bucket(**kwargs)
                        return True
                    except Exception as exc:
                        logger.error(
                            "Failed to create S3 bucket '%s': %s",
                            full_name,
                            exc,
                        )
                        return False

                ok = await loop.run_in_executor(None, _do_create)
                if ok and full_name not in self._created_buckets:
                    self._created_buckets.append(full_name)
                return ok
            else:
                # Local filesystem
                bucket_path = os.path.join(
                    self._local_root, full_name
                )
                os.makedirs(bucket_path, exist_ok=True)
                if full_name not in self._created_buckets:
                    self._created_buckets.append(full_name)
                return True

        except Exception as exc:
            logger.error(
                "Failed to create bucket '%s': %s", full_name, exc
            )
            return False

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health(self) -> Dict[str, Any]:
        """Return a health snapshot of the object store.

        Returns
        -------
        Dict[str, Any]
            Keys: ``connected``, ``mode``, ``buckets``, ``total_objects``,
            ``latency_ms``.
        """
        start = time.monotonic()
        result: Dict[str, Any] = {
            "connected": self._connected,
            "mode": self._mode,
            "buckets": len(self._created_buckets),
            "total_objects": 0,
            "latency_ms": 0.0,
        }

        try:
            if self._mode == "s3" and self._s3_client is not None:
                # Count objects across all known buckets
                total = 0
                for bucket in self._created_buckets:
                    try:
                        objs = await self._s3_list(
                            bucket.replace(f"{self._bucket_prefix}-", ""),
                            "",
                        )
                        total += len(objs)
                    except Exception:
                        pass
                result["total_objects"] = total

            elif self._mode == "local":
                # Count objects across all known buckets on filesystem
                total = 0
                for bucket in self._created_buckets:
                    bucket_path = os.path.join(
                        self._local_root, bucket
                    )
                    if os.path.isdir(bucket_path):
                        for _root_str, _dirs, files in os.walk(
                            bucket_path
                        ):
                            total += len(
                                [
                                    f
                                    for f in files
                                    if not f.endswith(".meta.json")
                                ]
                            )
                result["total_objects"] = total

        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            result["connected"] = False

        result["latency_ms"] = (
            time.monotonic() - start
        ) * 1000
        return result

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_local_path(self, bucket: str, key: str) -> str:
        """Return the local filesystem path for a given bucket/key.

        This is useful for direct filesystem access when S3 is not
        available.

        Parameters
        ----------
        bucket : str
            Logical bucket name (prefix is applied automatically).
        key : str
            Object key/path within the bucket.

        Returns
        -------
        str
            Absolute local filesystem path.
        """
        full_bucket = self._full_bucket_name(bucket)
        return os.path.normpath(
            os.path.join(self._local_root, full_bucket, key)
        )
