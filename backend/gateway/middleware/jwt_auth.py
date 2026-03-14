"""JWT authentication middleware -- decrypts NextAuth v4 JWE tokens.

NextAuth v4 (JWT strategy) encrypts session tokens as JWE using:
- Key derivation: HKDF(SHA-256, secret, salt="", info="NextAuth.js Generated Encryption Key")
- Encryption: A256GCM with "dir" key management

This middleware extracts the Authorization: Bearer <token> header, decrypts
the JWE, and sets request.state.user_email, request.state.user_id, and
request.state.company_id for downstream route handlers.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.shared.config import get_settings
from backend.shared.db import get_connection

logger = logging.getLogger(__name__)

_EXEMPT_PATHS = {
    "/api/health",
    "/api/health/ready",
    "/api/stripe/webhook",
    "/api/sms/webhook",
}
_EXEMPT_PREFIXES = (
    "/docs",
    "/openapi",
    "/redoc",
)


def _base64url_decode(s: str) -> bytes:
    """Decode base64url without padding."""
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _derive_encryption_key(secret: str) -> bytes:
    """Derive the 256-bit encryption key NextAuth uses for JWE."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"",
        info=b"NextAuth.js Generated Encryption Key",
    )
    return hkdf.derive(secret.encode("utf-8"))


def decrypt_nextauth_jwt(token: str, secret: str) -> dict:
    """Decrypt a NextAuth v4 JWE compact-serialization token.

    Returns the decrypted payload as a dict.
    Raises ValueError on any decryption failure.
    """
    parts = token.split(".")
    if len(parts) != 5:
        raise ValueError(f"Invalid JWE: expected 5 parts, got {len(parts)}")

    header_b64, _enc_key_b64, iv_b64, ciphertext_b64, tag_b64 = parts

    iv = _base64url_decode(iv_b64)
    ciphertext = _base64url_decode(ciphertext_b64)
    tag = _base64url_decode(tag_b64)

    key = _derive_encryption_key(secret)
    aesgcm = AESGCM(key)

    # AAD (Additional Authenticated Data) is the ASCII-encoded protected header
    aad = header_b64.encode("ascii")

    # AES-GCM expects nonce, ciphertext||tag, aad
    plaintext = aesgcm.decrypt(iv, ciphertext + tag, aad)
    return json.loads(plaintext)


def _extract_email(request: Request) -> Optional[str]:
    """Try to extract user email from JWT in Authorization header or query param.

    EventSource (SSE) cannot send custom headers, so we also accept
    ``?token=<jwt>`` for SSE stream endpoints.
    """
    token: Optional[str] = None

    # 1. Prefer Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    # 2. Fall back to ?token= query param (for EventSource / SSE)
    if not token:
        token = request.query_params.get("token")

    if not token:
        return None

    secret = get_settings().NEXTAUTH_SECRET
    if not secret:
        logger.error("NEXTAUTH_SECRET not configured -- cannot validate JWTs")
        return None

    try:
        payload = decrypt_nextauth_jwt(token, secret)
    except Exception as exc:
        logger.debug("JWT decryption failed: %s", exc)
        return None

    email = payload.get("email")
    if not email or not isinstance(email, str):
        logger.debug("JWT payload missing email field: %s", list(payload.keys()))
        return None

    return email


def _lookup_user_company(email: str) -> tuple[Optional[str], Optional[str]]:
    """Look up user_id and company_id from the database by email.

    Returns (user_id, company_id) or (None, None) if not found.
    Uses a direct sync DB call (not the async store function) because
    middleware dispatch runs in a sync-compatible context.
    """
    try:
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT id, company_id FROM users WHERE email = %s",
                (email,),
            )
            row = cur.fetchone()
            if row:
                return str(row[0]), str(row[1])
    except Exception as exc:
        logger.debug("User lookup failed for %s: %s", email, exc)
    return None, None


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Validate NextAuth JWT and attach user email, id, and company_id to request state."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip exempt paths
        if path in _EXEMPT_PATHS or path.startswith(_EXEMPT_PREFIXES):
            request.state.user_email = None
            request.state.user_id = None
            request.state.company_id = None
            response = await call_next(request)
            return response

        # Try JWT-based auth
        email = _extract_email(request)
        request.state.user_email = email

        # Look up user_id and company_id from DB
        if email:
            user_id, company_id = _lookup_user_company(email)
            request.state.user_id = user_id
            request.state.company_id = company_id
        else:
            request.state.user_id = None
            request.state.company_id = None

        response = await call_next(request)
        return response


def attach_jwt_auth(app: FastAPI) -> None:
    """Add JWT auth middleware to the FastAPI app."""
    app.add_middleware(JWTAuthMiddleware)
    logger.info("JWT auth middleware attached")
