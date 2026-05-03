# Developer

# Email Verification Feature Implementation

I'll implement the complete email verification feature based on the architecture plan. I'll analyze the existing patterns first, then provide all files in execution order.

---

## Phase 1: Database Migration

### File: `migrations/20240115_001_add_email_verification.sql`

```sql
-- Migration: Add Email Verification
-- Created: 2024-01-15
-- Description: Adds is_verified/verified_at to users table,
--              creates mng_email_verification_tokens and mng_email_resend_attempts tables.

BEGIN;

-- ============================================================
-- 1. Modify existing users table
-- ============================================================
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP NULL;

-- Grandfather existing users: treat pre-existing accounts as verified
-- so current users are not broken by this feature.
-- CHANGE THIS if you want retroactive verification enforcement.
UPDATE users SET is_verified = TRUE, verified_at = NOW() WHERE is_verified = FALSE;

-- ============================================================
-- 2. Create mng_email_verification_tokens
-- ============================================================
CREATE TABLE IF NOT EXISTS mng_email_verification_tokens (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token      VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP   NOT NULL,
    used_at    TIMESTAMP   NULL,
    created_at TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mng_evt_token
    ON mng_email_verification_tokens (token);

CREATE INDEX IF NOT EXISTS idx_mng_evt_user_id
    ON mng_email_verification_tokens (user_id);

CREATE INDEX IF NOT EXISTS idx_mng_evt_expires_at
    ON mng_email_verification_tokens (expires_at);

-- ============================================================
-- 3. Create mng_email_resend_attempts
-- ============================================================
CREATE TABLE IF NOT EXISTS mng_email_resend_attempts (
    id           UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    requested_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mng_era_user_requested
    ON mng_email_resend_attempts (user_id, requested_at);

COMMIT;
```

---

## Phase 1: Configuration

### File: `config/app.env` *(append to existing)*

```env
# ============================================================
# Email Verification Settings
# ============================================================
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS=24
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=60
EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS=5
EMAIL_VERIFICATION_LINK_BASE=https://app.platform.com/verify-email

# Email Dispatch
EMAIL_FROM_ADDRESS=noreply@platform.com
EMAIL_FROM_NAME=Platform Team

# Email Provider: 'sendgrid' | 'ses' | 'mailgun' | 'smtp'
EMAIL_PROVIDER=sendgrid

# SendGrid (populate if EMAIL_PROVIDER=sendgrid)
SENDGRID_API_KEY=

# AWS SES (populate if EMAIL_PROVIDER=ses)
AWS_SES_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Mailgun (populate if EMAIL_PROVIDER=mailgun)
MAILGUN_API_KEY=
MAILGUN_DOMAIN=
```

---

## Phase 2: Backend Service Layer

### File: `backend/config/settings.py` *(create or append email verification section)*

```python
"""
Application settings loaded from environment variables.
Email verification settings block — append to existing settings file.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailVerificationSettings:
    token_expiry_hours: int
    resend_cooldown_seconds: int
    max_resend_attempts: int
    link_base_url: str
    from_address: str
    from_name: str
    provider: str  # 'sendgrid' | 'ses' | 'mailgun' | 'smtp'

    # Provider-specific
    sendgrid_api_key: str | None
    aws_ses_region: str | None
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    mailgun_api_key: str | None
    mailgun_domain: str | None

    @classmethod
    def from_env(cls) -> "EmailVerificationSettings":
        return cls(
            token_expiry_hours=int(
                os.environ.get("EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS", "24")
            ),
            resend_cooldown_seconds=int(
                os.environ.get("EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS", "60")
            ),
            max_resend_attempts=int(
                os.environ.get("EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS", "5")
            ),
            link_base_url=os.environ.get(
                "EMAIL_VERIFICATION_LINK_BASE",
                "https://app.platform.com/verify-email",
            ),
            from_address=os.environ.get(
                "EMAIL_FROM_ADDRESS", "noreply@platform.com"
            ),
            from_name=os.environ.get("EMAIL_FROM_NAME", "Platform Team"),
            provider=os.environ.get("EMAIL_PROVIDER", "sendgrid"),
            sendgrid_api_key=os.environ.get("SENDGRID_API_KEY"),
            aws_ses_region=os.environ.get("AWS_SES_REGION", "us-east-1"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            mailgun_api_key=os.environ.get("MAILGUN_API_KEY"),
            mailgun_domain=os.environ.get("MAILGUN_DOMAIN"),
        )


# Singleton — imported by services
email_verification_settings = EmailVerificationSettings.from_env()
```

---

### File: `backend/models/email_verification.py`

```python
"""
Pydantic/dataclass models for email verification domain objects.
These are NOT ORM models — they are plain data containers returned by services.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class VerificationErrorCode(str, Enum):
    TOKEN_NOT_FOUND = "TOKEN_NOT_FOUND"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_ALREADY_USED = "TOKEN_ALREADY_USED"


class ResendDeniedReason(str, Enum):
    COOLDOWN = "cooldown"
    LIMIT_EXCEEDED = "limit_exceeded"


@dataclass
class VerificationToken:
    id: UUID
    user_id: UUID
    token: str
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime


@dataclass
class VerificationResult:
    valid: bool
    error_code: VerificationErrorCode | None = None
    user_id: UUID | None = None

    @classmethod
    def success(cls, user_id: UUID) -> "VerificationResult":
        return cls(valid=True, user_id=user_id)

    @classmethod
    def failure(cls, error_code: VerificationErrorCode) -> "VerificationResult":
        return cls(valid=False, error_code=error_code)


@dataclass
class ResendCheckResult:
    can_resend: bool
    reason: ResendDeniedReason | None = None
    wait_seconds: int = 0

    @classmethod
    def allowed(cls) -> "ResendCheckResult":
        return cls(can_resend=True)

    @classmethod
    def denied_cooldown(cls, wait_seconds: int) -> "ResendCheckResult":
        return cls(
            can_resend=False,
            reason=ResendDeniedReason.COOLDOWN,
            wait_seconds=wait_seconds,
        )

    @classmethod
    def denied_limit_exceeded(cls) -> "ResendCheckResult":
        return cls(
            can_resend=False,
            reason=ResendDeniedReason.LIMIT_EXCEEDED,
            wait_seconds=0,
        )


@dataclass
class SendResult:
    status: str  # 'sent' | 'failed'
    message_id: str | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "sent"
```

---

### File: `backend/services/email_verification_service.py`

```python
"""
Email Verification Service

Handles all business logic for:
  - Token generation and storage
  - Token validation
  - Token invalidation (mark used + activate user)
  - Resend rate limiting (cooldown + lifetime cap)
  - Resend attempt recording

Database calls use parameterized queries via the project's existing
`get_db_connection()` context manager. Adjust import if your project
uses SQLAlchemy sessions, asyncpg, etc.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from math import ceil
from uuid import UUID

from backend.config.settings import email_verification_settings as cfg
from backend.db import get_db_connection  # adjust to your DB layer
from backend.models.email_verification import (
    ResendCheckResult,
    ResendDeniedReason,
    VerificationErrorCode,
    VerificationResult,
    VerificationToken,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def generate_secure_token() -> str:
    """
    Generate a cryptographically secure, URL-safe token.
    secrets.token_urlsafe(32) produces a ~44-character base64url string.
    """
    return secrets.token_urlsafe(32)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Token lifecycle
# ---------------------------------------------------------------------------


def create_verification_token(user_id: UUID) -> VerificationToken:
    """
    1. Invalidate any existing unused tokens for this user.
    2. Generate a new secure token.
    3. Persist and return the new VerificationToken.

    Raises:
        RuntimeError: On unrecoverable DB error.
    """
    token_value = generate_secure_token()
    now = _now_utc()
    expires_at = now + timedelta(hours=cfg.token_expiry_hours)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Step 1: Invalidate prior unused tokens so old links stop working.
            cur.execute(
                """
                UPDATE mng_email_verification_tokens
                SET    used_at = %s
                WHERE  user_id = %s
                  AND  used_at IS NULL
                """,
                (now, str(user_id)),
            )

            # Step 2: Insert the new token.
            cur.execute(
                """
                INSERT INTO mng_email_verification_tokens
                    (user_id, token, expires_at, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id, user_id, token, expires_at, used_at, created_at
                """,
                (str(user_id), token_value, expires_at, now),
            )
            row = cur.fetchone()

        conn.commit()

    logger.info("Created verification token for user_id=%s", user_id)

    return VerificationToken(
        id=row[0],
        user_id=row[1],
        token=row[2],
        expires_at=row[3],
        used_at=row[4],
        created_at=row[5],
    )


def verify_token(token: str) -> VerificationResult:
    """
    Validate a verification token string.

    Checks in order:
      1. Token exists in DB         → TOKEN_NOT_FOUND
      2. Token already used         → TOKEN_ALREADY_USED
      3. Token expired              → TOKEN_EXPIRED
      4. All pass                   → valid, returns user_id

    Does NOT mark the token as used — call mark_token_used() separately.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, expires_at, used_at
                FROM   mng_email_verification_tokens
                WHERE  token = %s
                """,
                (token,),
            )
            row = cur.fetchone()

    if row is None:
        logger.warning("verify_token: token not found")
        return VerificationResult.failure(VerificationErrorCode.TOKEN_NOT_FOUND)

    user_id, expires_at, used_at = row[0], row[1], row[2]

    if used_at is not None:
        logger.warning("verify_token: token already used, user_id=%s", user_id)
        return VerificationResult.failure(VerificationErrorCode.TOKEN_ALREADY_USED)

    # Make expires_at timezone-aware if the DB returns naive datetime
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < _now_utc():
        logger.warning("verify_token: token expired, user_id=%s", user_id)
        return VerificationResult.failure(VerificationErrorCode.TOKEN_EXPIRED)

    return VerificationResult.success(user_id=UUID(str(user_id)))


def mark_token_used(token: str, user_id: UUID) -> bool:
    """
    Atomically in one transaction:
      1. Mark the token as used.
      2. Activate the user (is_verified = TRUE, verified_at = NOW).
      3. Clean up resend attempt history for this user.

    Returns True on success.
    Raises RuntimeError on DB failure (caller should return 500).
    """
    now = _now_utc()

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                # 1. Mark token used
                cur.execute(
                    """
                    UPDATE mng_email_verification_tokens
                    SET    used_at = %s
                    WHERE  token   = %s
                      AND  used_at IS NULL
                    """,
                    (now, token),
                )
                if cur.rowcount == 0:
                    # Token was already used by a concurrent request
                    conn.rollback()
                    raise ValueError("Token already consumed by concurrent request")

                # 2. Activate the user
                cur.execute(
                    """
                    UPDATE users
                    SET    is_verified = TRUE,
                           verified_at = %s
                    WHERE  id = %s
                    """,
                    (now, str(user_id)),
                )

                # 3. Remove resend attempt history (clean up)
                cur.execute(
                    """
                    DELETE FROM mng_email_resend_attempts
                    WHERE user_id = %s
                    """,
                    (str(user_id),),
                )

            conn.commit()
            logger.info("User verified successfully: user_id=%s", user_id)
            return True

        except Exception:
            conn.rollback()
            logger.exception("mark_token_used failed for user_id=%s", user_id)
            raise


# ---------------------------------------------------------------------------
# Resend rate limiting
# ---------------------------------------------------------------------------


def can_resend_email(user_id: UUID) -> ResendCheckResult:
    """
    Check whether a user is permitted to request another verification email.

    Rules (checked in order):
      1. Cooldown  — no request in the last N seconds
      2. Lifetime cap — total resend count < MAX_RESEND_ATTEMPTS
    """
    cooldown_seconds
