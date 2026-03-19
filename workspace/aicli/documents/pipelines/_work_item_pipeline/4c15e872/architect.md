# Architect

# Technical Implementation Plan: Authentication (auth)

## Phase 1: Project Structure & Dependencies

### 1. Create Core Authentication Module
**File:** `core/auth/__init__.py`
- Initialize auth package with version and exports

**File:** `core/auth/models.py`
- Create `User` model with fields:
  - `id` (UUID primary key)
  - `email` (String, unique, indexed)
  - `password_hash` (String, bcrypt hashed)
  - `is_email_verified` (Boolean, default False)
  - `email_verified_at` (DateTime, nullable)
  - `is_active` (Boolean, default True)
  - `is_locked` (Boolean, default False)
  - `locked_until` (DateTime, nullable)
  - `failed_login_attempts` (Integer, default 0)
  - `last_login_at` (DateTime, nullable)
  - `created_at` (DateTime)
  - `updated_at` (DateTime)

- Create `EmailVerificationToken` model with fields:
  - `id` (UUID primary key)
  - `user_id` (Foreign key to User)
  - `token` (String, unique, indexed)
  - `expires_at` (DateTime)
  - `created_at` (DateTime)

- Create `PasswordResetToken` model with fields:
  - `id` (UUID primary key)
  - `user_id` (Foreign key to User)
  - `token` (String, unique, indexed)
  - `expires_at` (DateTime, 24 hour expiry)
  - `used_at` (DateTime, nullable)
  - `created_at` (DateTime)

- Create `AuditLog` model with fields:
  - `id` (UUID primary key)
  - `user_id` (Foreign key to User, nullable)
  - `event_type` (String enum: LOGIN, LOGOUT, FAILED_LOGIN, PASSWORD_RESET_REQUESTED, PASSWORD_RESET_COMPLETED, REGISTRATION)
  - `email` (String, for tracking failed attempts before account creation)
  - `ip_address` (String)
  - `user_agent` (String)
  - `status` (String: SUCCESS, FAILURE)
  - `error_message` (String, nullable)
  - `created_at` (DateTime)

### 2. Add Dependencies
**File:** `requirements.txt` (append)
```
bcrypt==4.1.1
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
email-validator==2.1.0
```

### 3. Create Configuration Module
**File:** `core/auth/config.py`
- Define constants:
  - `PASSWORD_MIN_LENGTH = 8`
  - `PASSWORD_REQUIRE_UPPERCASE = True`
  - `PASSWORD_REQUIRE_NUMBER = True`
  - `MAX_FAILED_LOGIN_ATTEMPTS = 3`
  - `LOCKOUT_DURATION_MINUTES = 15`
  - `SESSION_TOKEN_EXPIRY_MINUTES = 30`
  - `EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 24`
  - `PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 24`
  - `JWT_ALGORITHM = "HS256"`
  - `JWT_SECRET_KEY = <load from environment>`

---

## Phase 2: Authentication Service Layer

### 4. Create Password Validation Service
**File:** `core/auth/validators.py`

**Function:** `validate_password(password: str) -> tuple[bool, str]`
- Check length >= 8
- Check for at least 1 uppercase letter
- Check for at least 1 number
- Return (is_valid, error_message)

**Function:** `validate_email(email: str) -> tuple[bool, str]`
- Use email-validator library
- Return (is_valid, error_message)

### 5. Create Password Hashing Service
**File:** `core/auth/password_service.py`

**Function:** `hash_password(password: str) -> str`
- Use bcrypt with salt rounds = 12
- Return hashed password

**Function:** `verify_password(plain_password: str, hashed_password: str) -> bool`
- Compare plain password against bcrypt hash
- Return boolean

### 6. Create Token Service
**File:** `core/auth/token_service.py`

**Function:** `create_session_token(user_id: UUID, email: str) -> str`
- Create JWT with:
  - `sub` (subject): user_id
  - `email`: user email
  - `exp`: current_time + 30 minutes
  - `iat`: current_time
  - Algorithm: HS256
- Return signed token

**Function:** `verify_session_token(token: str) -> dict | None`
- Verify JWT signature and expiry
- Return payload dict or None if invalid

**Function:** `generate_random_token() -> str`
- Generate 32-byte random token, hex-encoded
- Return token string

### 7. Create Email Service
**File:** `core/auth/email_service.py`

**Function:** `send_verification_email(email: str, user_name: str, verification_token: str, frontend_url: str) -> bool`
- Send HTML email with verification link: `{frontend_url}/verify-email?token={verification_token}`
- Return success boolean
- Log any failures

**Function:** `send_password_reset_email(email: str, reset_token: str, frontend_url: str) -> bool`
- Send HTML email with reset link: `{frontend_url}/reset-password?token={reset_token}`
- Return success boolean
- Log any failures

### 8. Create Audit Logging Service
**File:** `core/auth/audit_service.py`

**Function:** `log_auth_event(event_type: str, email: str | None, user_id: UUID | None, ip_address: str, user_agent: str, status: str, error_message: str | None = None) -> AuditLog`
- Create and persist AuditLog record
- Return created log entry

---

## Phase 3: Authentication Business Logic

### 9. Create Authentication Service
**File:** `core/auth/auth_service.py`

**Function:** `register_user(email: str, password: str, ip_address: str, user_agent: str) -> dict`
- Validate email format
- Check email doesn't already exist (case-insensitive)
- Validate password complexity
- Hash password
- Create User record (is_email_verified=False)
- Generate and store EmailVerificationToken (expires in 24 hours)
- Send verification email
- Log REGISTRATION event with SUCCESS
- Return dict: `{success: True, user_id: UUID, message: "Check your email to verify"}`
- On error: log REGISTRATION event with FAILURE and return appropriate error

**Function:** `verify_email(token: str, ip_address: str, user_agent: str) -> dict`
- Find EmailVerificationToken by token
- Verify not expired
- Update User.is_email_verified = True, email_verified_at = now
- Delete verification token
- Log success event
- Return dict: `{success: True, message: "Email verified"}`
- On error: log failure and return error dict

**Function:** `login_user(email: str, password: str, ip_address: str, user_agent: str) -> dict`
- Find User by email (case-insensitive)
- If user not found: log FAILED_LOGIN event and return generic error
- If user.is_locked and locked_until > now: log FAILED_LOGIN and return "Account locked, try again at HH:MM"
- If not user.is_email_verified: log FAILED_LOGIN and return "Email not verified"
- Verify password against hash
- If password incorrect:
  - Increment user.failed_login_attempts
  - If >= 3: set user.is_locked = True, locked_until = now + 15 minutes
  - Log FAILED_LOGIN event
  - Return generic error message
- If password correct:
  - Reset user.failed_login_attempts = 0
  - Set user.is_locked = False
  - Set user.last_login_at = now
  - Create session token
  - Log LOGIN event with SUCCESS
  - Return dict: `{success: True, token: session_token, user_id: UUID, email: email}`

**Function:** `request_password_reset(email: str, ip_address: str, user_agent: str, frontend_url: str) -> dict`
- Find User by email (case-insensitive)
- If not found: return generic success message (don't reveal if email exists)
- Generate and store PasswordResetToken (expires in 24 hours)
- Send password reset email
- Log PASSWORD_RESET_REQUESTED event with SUCCESS
- Return dict: `{success: True, message: "Check your email for reset link"}`

**Function:** `reset_password(token: str, new_password: str, ip_address: str, user_agent: str) -> dict`
- Find PasswordResetToken by token
- If not found or expired: log PASSWORD_RESET_COMPLETED event with FAILURE and return error
- If already used (used_at is not null): log FAILURE and return error
- Validate new password complexity
- Hash new password
- Update User.password_hash
- Set PasswordResetToken.used_at = now
- Log PASSWORD_RESET_COMPLETED event with SUCCESS
- Return dict: `{success: True, message: "Password reset successful"}`

**Function:** `logout_user(user_id: UUID, ip_address: str, user_agent: str) -> dict`
- Log LOGOUT event with SUCCESS
- Return dict: `{success: True, message: "Logged out"}`

**Function:** `validate_session(token: str) -> dict | None`
- Call token_service.verify_session_token(token)
- If invalid: return None
- If valid: verify User exists, is_active, not is_locked (or lockout expired)
- Return user payload dict or None

---

## Phase 4: API Endpoints

### 10. Create Authentication Routes
**File:** `api/auth/routes.py`

**POST** `/api/auth/register`
- Input: `{email, password}`
- Extract ip_address from request headers (X-Forwarded-For or remote_addr)
- Extract user_agent from User-Agent header
- Call auth_service.register_user()
- Return JSON response with status 201 on success, 400/409 on validation error
- Enforce HTTPS via middleware

**POST** `/api/auth/verify-email`
- Input: `{token}`
- Call auth_service.verify_email()
- Return JSON response with status 200 on success, 400 on invalid/expired token

**POST** `/api/auth/login`
- Input: `{email, password}`
- Extract ip_address and user_agent
- Call auth_service.login_user()
- Return JSON response with `{token, user_id, email}` on success
- Return status 401 on failed login
- Enforce HTTPS

**POST** `/api/auth/password-reset-request`
- Input: `{email}`
- Extract ip_address and user_agent
- Extract frontend_url from query param (for email link generation)
- Call auth_service.request_password_reset()
- Always return 200 success (don't reveal email existence)

**POST** `/api/auth/password-reset`
- Input: `{token, new_password}`
- Extract ip_address and user_agent
- Call auth_service.reset_password()
- Return status 200 on success, 400 on invalid token

**POST** `/api/auth/logout`
- Require valid session token in Authorization header
- Extract user_id from token
- Extract ip_address and user_agent
- Call auth_service.logout_user()
- Return status 200

**GET** `/api/auth/me` (protected)
- Require valid session token in Authorization header
- Extract user_id from token
- Fetch User record
- Return JSON: `{user_id, email, created_at}` with status 200

### 11. Create HTTPS Middleware
**File:** `api/middleware/https_middleware.py`

**Function:** `enforce_https_middleware(request, call_next)`
- Check if request.url.scheme != "https"
- In production: reject with 403 Forbidden
- In development: allow but log warning
- Add Strict-Transport-Security header to responses
- Add X-Content-Type-Options: nosniff header

### 12. Create Authentication Middleware
**File:** `api/middleware/auth_middleware.py`

**Function:** `get_current_user(token: str = Header(None))`
- Extract token from "Authorization: Bearer {token}" header
- Call auth_service.validate_session(token)
- If invalid: raise HTTPException(status_code=401, detail="Invalid or expired token")
- Return user payload dict

---

## Phase 5: Database & Migration

### 13. Create Database Migration
**File:** `migrations/0001_create_auth_tables.sql`

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  is_email_verified BOOLEAN DEFAULT FALSE,
  email_verified_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  is_locked BOOLEAN DEFAULT FALSE,
  locked_until TIMESTAMP,
  failed_login_attempts INTEGER DEFAULT 0,
  last_login_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(LOWER(email));
CREATE INDEX idx_users_is_active ON users(is_active);

CREATE TABLE email_verification_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token VARCHAR(255) NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_email_tokens_user_id ON email_verification_tokens(user_id);
CREATE INDEX idx_email_tokens_token ON email_verification_tokens(token);

CREATE TABLE password_reset_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token VARCHAR(255) NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_password_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_tokens_token ON password_reset_tokens(token);

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  event_type VARCHAR(50) NOT NULL,
  email VARCHAR(255),
  ip_address VARCHAR(45),
  user_agent TEXT,
  status VARCHAR(20) NOT NULL,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

### 14. Create Database Connection Module
**File:** `core/database.py`
- Create SQLAlchemy engine with connection pooling
- Create session factory
- Implement context manager for transaction handling

---

## Phase 6: Testing & Configuration

### 15. Create Unit Tests
**File:** `tests/unit/auth/test_validators.py`
- Test password validation (all criteria)
- Test email validation

**File:** `tests/unit/auth/test_password_service.py`
- Test password hashing
- Test password verification

**File:** `tests/unit/auth/test_token_service.py`
- Test token creation and verification
- Test token expiry

**File:** `tests/unit/auth/test_audit_service.py`
- Test audit log creation

### 16. Create Integration Tests
**File:** `tests/integration/test_auth_endpoints.py`
- Test registration flow end-to-end
- Test login with valid/invalid credentials
- Test account lockout after 3 failed attempts
- Test password reset flow
- Test email verification requirement
- Test session token expiry
- Test HTTPS enforcement
- Test audit log
