"""Helpers for reading uploaded files within configured size limits."""

import json
from typing import Any, List

from fastapi import HTTPException, UploadFile

from testio.apps.server.settings import get_max_upload_bytes, get_max_upload_files
from testio.core.config_parser.data import TestSuiteConfig
from testio.core.config_parser.parsers import ConfigNotParsable, ConfigParser

_CHUNK_SIZE = 64 * 1024


def _too_large(label: str, limit: int) -> HTTPException:
    return HTTPException(
        status_code=413,
        detail=f"{label} exceeds the maximum allowed size of "
        f"{limit / (1024 * 1024):g} MB",
    )


async def read_upload_capped(upload: UploadFile, label: str) -> bytes:
    """Read ``upload`` in chunks, failing with 413 as soon as it exceeds
    TESTIO_MAX_UPLOAD_SIZE_MB (instead of reading the whole file first)."""
    limit = get_max_upload_bytes()
    chunks: List[bytes] = []
    size = 0
    while True:
        chunk = await upload.read(_CHUNK_SIZE)
        if not chunk:
            break
        size += len(chunk)
        if limit > 0 and size > limit:
            raise _too_large(label, limit)
        chunks.append(chunk)
    return b"".join(chunks)


def enforce_file_count(files: List[Any], label: str = "student_files") -> None:
    """Reject requests carrying more files than TESTIO_MAX_UPLOAD_FILES."""
    limit = get_max_upload_files()
    if limit > 0 and len(files) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"Too many {label}: at most {limit} files per request",
        )


async def read_config_upload(config_file: UploadFile) -> TestSuiteConfig:
    """Read, decode and validate an uploaded test-suite config (400 on error)."""
    if config_file.content_type and "json" not in config_file.content_type:
        raise HTTPException(
            status_code=400,
            detail="config_file must be a JSON file (content-type: application/json)",
        )
    content = await read_upload_capped(config_file, "config_file")
    try:
        config_json = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="config_file contains invalid JSON")
    return parse_config_or_400(config_json)


def parse_config_or_400(config_json: Any) -> TestSuiteConfig:
    """Validate a config dict, turning validation problems into HTTP 400."""
    try:
        return ConfigParser().parse_from_json(config_json)
    except ConfigNotParsable as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid test configuration: {exc.reason or exc}"
        )
