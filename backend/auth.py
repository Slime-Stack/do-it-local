"""API key authentication."""
import os
import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Cache the expected key
_expected_key: str | None = None


def _get_expected_key() -> str:
    """Get the expected API key from env or Secret Manager."""
    global _expected_key
    if _expected_key:
        return _expected_key

    key = os.getenv("API_KEY")
    if key:
        _expected_key = key
        return key

    raise ValueError("API_KEY environment variable not set")


async def verify_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    """Validate the API key from X-API-Key header."""
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    expected = _get_expected_key()
    if not secrets.compare_digest(api_key, expected):
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key
