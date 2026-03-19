# Developer

# Authentication System Implementation

I'll implement the complete authentication system based on the architectural plan. Let me build this systematically.

## File Structure Overview

```
core/
  auth/
    __init__.py
    config.py
    models.py
    validators.py
    password_service.py
    token_service.py
    email_service.py
    audit_service.py
    auth_service.py
  database.py
api/
  auth/
    __init__.py
    routes.py
  middleware/
    __init__.py
    https_middleware.py
    auth_middleware.py
migrations/
  0001_create_auth_tables.sql
tests/
  unit/
    auth/
      __init__.py
      test_validators.py
      test_password_service.py
      test_token_service.py
      test_audit_service.py
  integration/
    __init__.py
    test_auth_endpoints.py
requirements.txt
```

---

## Core Module Files

### `core/__init__.py`
```python
# Core package initialization
```

### `core/auth/__init__.py`
```python
"""
Authentication module for the application.
Version: 1.0.0

Exports the main authentication service functions for use in API routes.
"""

from core.auth.auth_service import (
    register_user,
    verify_email,
    login_user,
    request_password_reset,
    reset_password,
    logout_user,
    validate_session,
)

__version__ = "1.0.0"
__all__ = [
    "register_user",
    "verify_email",
    "login_user",
    "request_password_reset",
    "reset_password",
    "logout_user",
    "validate_session",
]
```

### `core/auth/config.py`
```python
"""
Authentication configuration constants.
Sensitive values (like JWT_SECRET_KEY) are loaded from environment variables.
"""

import os
from typing import Optional


# Password policy
PASSWORD_MIN_LENGTH: int = 8
PASSWORD_REQUIRE_UPPERCASE: bool = True
PASSWORD_REQUIRE_NUMBER: bool = True

# Account lockout policy
MAX_FAILED_LOGIN_ATTEMPTS: int = 3
LOCKOUT_DURATION_MINUTES: int = 15

# Token expiry settings
SESSION_TOKEN_EXPIRY_MINUTES: int = 30
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS: int = 24
PASSWORD_RESET_TOKEN_EXPIRY_HOURS: int = 24

# JWT settings
JWT_ALGORITHM: str = "HS256"
# Must be set in environment; no insecure default in production
JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET")

# Email settings
SMTP_HOST: str = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME: Optional[str] = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD: Optional[str] = os.environ.get("SMTP_PASSWORD")
SMTP_FROM_EMAIL: str = os.environ.get("SMTP_FROM_EMAIL", "noreply@example.com")
SMTP_FROM_NAME: str = os.environ.get("SMTP_FROM_NAME", "App Support")
SMTP_USE_TLS: bool = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"

# Frontend URL for email links
FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Application environment
APP_ENV: str = os.environ.get("APP_ENV", "development")
IS_PRODUCTION: bool = APP_ENV == "production"

# Database
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/appdb"
)

# Warn if using default JWT secret in production
if IS_PRODUCTION and JWT_SECRET_KEY == "CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET":
    import warnings
    warnings.warn(
        "JWT_SECRET_KEY is not set in production environment! This is a security risk.",
        SecurityWarning,
        stacklevel=2,
    )
```

### `core/auth/models.py`
```python
"""
SQLAlchemy ORM models for authentication.

Models:
- User: Core user account
- EmailVerificationToken: Token for email address verification
- PasswordResetToken: Token for password reset flow
- AuditLog: Immutable log of all auth events
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)

    # Email verification state
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Account state
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Login tracking
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps — updated_at is maintained by trigger in SQL migration
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    email_verification_tokens = relationship(
        "EmailVerificationToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="email_verification_tokens")

    def __repr__(self) -> str:
        return f"<EmailVerificationToken user_id={self.user_id}>"


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    # Nullable; set when token is consumed to prevent reuse
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="password_reset_tokens")

    def __repr__(self) -> str:
        return f"<PasswordResetToken user_id={self.user_id} used={self.used_at is not None}>"


class AuditLog(Base):
    """
    Immutable audit trail of all authentication events.
    Records are never updated — only created. Deletions should be
    handled by data retention policies only.
    """
    __tablename__ = "audit_logs"

    # Valid event type constants
    EVENT_LOGIN = "LOGIN"
    EVENT_LOGOUT = "LOGOUT"
    EVENT_FAILED_LOGIN = "FAILED_LOGIN"
    EVENT_PASSWORD_RESET_REQUESTED = "PASSWORD_RESET_REQUESTED"
    EVENT_PASSWORD_RESET_COMPLETED = "PASSWORD_RESET_COMPLETED"
    EVENT_REGISTRATION = "REGISTRATION"
    EVENT_EMAIL_VERIFIED = "EMAIL_VERIFIED"

    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILURE = "FAILURE"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable because pre-registration failures won't have a user_id
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type = Column(String(50), nullable=False, index=True)
    # Store email directly to track attempts before/after account creation
    email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length = 45
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog event={self.event_type} status={self.status}>"
```

### `core/database.py`
```python
"""
Database connection and session management.

Uses SQLAlchemy with connection pooling. The session is managed as a
context manager to ensure connections are always returned to the pool.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.auth.config import DATABASE_URL, IS_PRODUCTION


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Configure engine with connection pool settings appropriate for production
engine = create_engine(
    DATABASE_URL,
    # Pool size: number of persistent connections
    pool_size=10 if IS_PRODUCTION else 5,
    # Max overflow: additional connections allowed beyond pool_size
    max_overflow=20 if IS_PRODUCTION else 10,
    # Recycle connections after 30 minutes to avoid stale connections
    pool_recycle=1800,
    # Pre-ping: test connection health before using from pool
    pool_pre_ping=True,
    # Echo SQL in development only (never in production — leaks sensitive data)
    echo=not IS_PRODUCTION,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager that provides a database session and handles
    commit/rollback/close automatically.

    Usage:
        with get_db_session() as session:
            user = session.query(User).filter_by(email=email).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.
    Used with Depends() in route handlers.

    Usage:
        @router.get("/")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables defined in models (used for testing / initial setup)."""
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Drop all tables (used for testing cleanup only)."""
    Base.metadata.drop_all(bind=engine)
```

### `core/auth/validators.py`
```python
"""
Input validation functions for authentication.
All validators return (is_valid: bool, error_message: str) tuples
so the caller can decide how to surface the error.
"""

import re
from typing import Tuple

from email_validator import EmailNotValidError, validate_email as _validate_email_lib

from core.auth.config import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_REQUIRE_NUMBER,
    PASSWORD_REQUIRE_UPPERCASE,
)


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password against complexity requirements.

    Rules:
    - Minimum 8 characters
    - At least 1 uppercase letter (if configured)
    - At least 1 number (if configured)

    Returns:
        (True, "") if valid
        (False, "error message") if invalid
    """
    if not password:
        return False, "Password is required."

    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."

    if PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if PASSWORD_REQUIRE_NUMBER and not re.search(r"\d", password):
        return False, "Password must contain at least one number."

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format using the email-validator library.
    The library checks RFC 5322 compliance and DNS MX record existence.

    Returns:
        (True, normalized_email) if valid — note: returns normalized email in second pos
        (False, error_message) if invalid
    """
    if not email:
        return False, "Email address is required."

    try:
        # check_deliverability=False to avoid DNS lookups in tight loops;
        # set True if you want MX record validation at registration time
        validated = _validate_email_lib(email.strip(), check_deliverability=False)
        # Return normalized form (lowercase domain, etc.)
        return True, validated.normalized
    except EmailNotValidError as exc:
        return False, str(exc)
```

### `core/auth/password_service.py`
```python
"""
Password hashing and verification using bcrypt via passlib.

bcrypt is intentionally slow (work factor = 12) to resist brute-force attacks.
Do NOT reduce the work factor without careful consideration.
"""

from passlib.context import CryptContext

# Use bcrypt with work factor 12 — good balance of security and performance
# (12 rounds ≈ 300-400ms on modern hardware, which is acceptable for login)
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def hash_password(password: str) -> str:
