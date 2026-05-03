# Architect

# Technical Architecture Plan: Email Verification Feature

---

## Executive Summary

This feature adds email verification to the **existing** registration and sign-in flows without rebuilding authentication. The implementation layer includes:

1. **Database schema** — New `email_verification_tokens` table + `is_verified` flag on `users`
2. **Backend services** — Token generation, email dispatch, verification logic, and resend rate-limiting
3. **API endpoints** — Verify token endpoint + resend token endpoint
4. **Middleware** — Verification check on protected resource access
5. **Frontend integration** — Sign-in banner for unverified users, verification success page
6. **Email templates** — Single branded verification email template

---

## Implementation Plan (Execution Order)

### Phase 1: Data Model & Infrastructure (Days 1–2)

#### 1. **Create Database Schema Changes**
   - **File:** `migrations/[timestamp]_add_email_verification.sql`
   - **Changes:**
     - Add `is_verified` BOOLEAN column to `users` table (default: `FALSE`)
     - Add `verified_at` TIMESTAMP column to `users` table (nullable, NULL until verified)
     - Create new table `email_verification_tokens`:
       ```sql
       CREATE TABLE email_verification_tokens (
         id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
         user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
         token VARCHAR(255) NOT NULL UNIQUE,
         expires_at TIMESTAMP NOT NULL,
         used_at TIMESTAMP NULL,
         created_at TIMESTAMP DEFAULT NOW(),
         INDEX idx_token (token),
         INDEX idx_user_id (user_id),
         INDEX idx_expires_at (expires_at)
       );
       ```
     - Create `email_resend_attempts` table for rate-limiting:
       ```sql
       CREATE TABLE email_resend_attempts (
         id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
         user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
         requested_at TIMESTAMP DEFAULT NOW(),
         INDEX idx_user_id_requested (user_id, requested_at)
       );
       ```

#### 2. **Add Configuration File**
   - **File:** `config/email_verification.env`
   - **Content:**
     ```
     TOKEN_EXPIRY_HOURS=24
     RESEND_COOLDOWN_SECONDS=60
     MAX_RESEND_ATTEMPTS_PER_ACCOUNT=5
     EMAIL_FROM_ADDRESS=noreply@platform.com
     EMAIL_SERVICE=sendgrid  # or aws_ses, mailgun
     SENDGRID_API_KEY=<key>
     VERIFICATION_LINK_BASE=https://app.platform.com/verify-email
     ```

---

### Phase 2: Backend Service Layer (Days 2–4)

#### 3. **Create Token Generation & Cryptography Service**
   - **File:** `backend/services/email_verification_service.py` (or `.ts`)
   - **Functions:**
     ```
     - generate_secure_token(user_id: UUID) -> str
       • Uses secrets.token_urlsafe(32) or equivalent crypto-random
       • Returns 44-char base64 string
       • No collisions with existing tokens
     
     - create_verification_token(user_id: UUID) -> VerificationToken
       • Calls generate_secure_token()
       • Inserts into email_verification_tokens with expires_at = NOW + 24h
       • Returns token object with user_id, token, expires_at
     
     - verify_token(token: str) -> VerificationResult
       • Queries email_verification_tokens by token
       • Checks: exists? expired? already_used?
       • Returns {valid: bool, error_code: str, user_id: UUID?}
       • Error codes: TOKEN_NOT_FOUND, TOKEN_EXPIRED, TOKEN_ALREADY_USED
     
     - mark_token_used(token: str, user_id: UUID) -> bool
       • Sets used_at = NOW in email_verification_tokens
       • Updates users.is_verified = TRUE, verified_at = NOW
       • Cleans up email_resend_attempts for user_id
       • Returns success flag
     
     - can_resend_email(user_id: UUID) -> {can_resend: bool, wait_seconds: int}
       • Queries email_resend_attempts for user_id in last 60s
       • If count >= 1 within 60s: return {can_resend: false, wait_seconds: X}
       • If count >= MAX_RESEND_ATTEMPTS_PER_ACCOUNT total: return {can_resend: false, reason: 'limit_exceeded'}
       • Otherwise: return {can_resend: true}
     
     - record_resend_attempt(user_id: UUID) -> bool
       • Inserts row into email_resend_attempts with user_id, NOW
       • Returns success
     ```

#### 4. **Create Email Dispatch Service**
   - **File:** `backend/services/email_service.py`
   - **Functions:**
     ```
     - send_verification_email(user_id: UUID, email: str, verification_token: str) -> {status: str, message_id: str}
       • Constructs verification_url = VERIFICATION_LINK_BASE + ?token=<token>
       • Loads email template from backend/templates/email/verify_email.html
       • Renders template with {user_email: email, verification_link: url, expiry_hours: 24}
       • Dispatches via SendGrid / AWS SES / Mailgun (configured in env)
       • Returns {status: 'sent'|'failed', message_id: str, error: str?}
       • **Retry logic:** Exponential backoff, max 3 attempts over 5 minutes
       • **Async:** Must be non-blocking (queue-based or async task)
     ```

#### 5. **Create Email Template**
   - **File:** `backend/templates/email/verify_email.html`
   - **Content:**
     - Branded header (company logo)
     - Greeting: "Hi [user_email],"
     - Body text: "Confirm your email address to activate your account."
     - CTA button: "Verify Email Address" → `{{ verification_link }}`
     - Fine print: "This link expires in {{ expiry_hours }} hours. If you didn't create this account, please ignore this email."
     - Footer: Company info, unsubscribe (if applicable)

---

### Phase 3: API Endpoints & Middleware (Days 4–5)

#### 6. **Create Verification Endpoint**
   - **File:** `backend/routes/auth.py` (append to existing auth routes)
   - **Endpoint:** `POST /api/auth/verify-email`
   - **Implementation:**
     ```
     POST /api/auth/verify-email
     Body: { token: string }
     
     1. Call verify_token(token) -> VerificationResult
     2. If not valid:
        - Return 400 with {error: result.error_code, message: human_readable}
        - Log attempt
     3. If valid:
        - Call mark_token_used(token, user_id)
        - Call update_user(user_id, is_verified=TRUE, verified_at=NOW)
        - Return 200 with {status: 'verified', message: 'Email verified successfully', redirect_url: '/dashboard'}
     4. On any DB error: Return 500 with generic error message
     ```
   - **Response Codes:**
     - `200 OK` — Token verified, account activated
     - `400 BAD_REQUEST` — Invalid/expired/already-used token
     - `404 NOT_FOUND` — Token not found
     - `500 INTERNAL_SERVER_ERROR` — DB or service error

#### 7. **Create Resend Verification Email Endpoint**
   - **File:** `backend/routes/auth.py` (append)
   - **Endpoint:** `POST /api/auth/resend-verification-email`
   - **Implementation:**
     ```
     POST /api/auth/resend-verification-email
     Headers: Authorization: Bearer <jwt_token>
     Body: {} (empty or { email: string } for recovery flow)
     
     1. Extract user_id from JWT token
     2. Query users table for user_id, verify account exists and is NOT verified
     3. Call can_resend_email(user_id) -> {can_resend: bool, wait_seconds: int}
     4. If cannot resend:
        - Return 429 RATE_LIMIT with {error: 'rate_limited', retry_after_seconds: wait_seconds}
     5. If can resend:
        - Call create_verification_token(user_id) -> new token
        - Call record_resend_attempt(user_id)
        - Call send_verification_email(user_id, email_addr, token) [ASYNC]
        - Return 200 with {status: 'resent', message: 'Verification email sent'}
     6. On any error: Return 400 or 500 with appropriate message
     ```
   - **Response Codes:**
     - `200 OK` — Email resent successfully
     - `429 TOO_MANY_REQUESTS` — Cooldown active, include `Retry-After` header
     - `401 UNAUTHORIZED` — Invalid/missing JWT
     - `400 BAD_REQUEST` — Account already verified
     - `500 INTERNAL_SERVER_ERROR` — Email service failure

#### 8. **Create Verification Check Middleware**
   - **File:** `backend/middleware/auth_middleware.py` (append)
   - **Function:**
     ```
     verify_email_required(protected_routes: list[str]) -> middleware
       • Runs on ALL protected endpoints
       • Extracts user_id from JWT / session
       • Queries users.is_verified for user_id
       • If NOT verified AND route in protected_routes:
         - Return 403 FORBIDDEN with {error: 'email_not_verified', message: 'Please verify your email to access this resource'}
         - Do NOT block sign-in itself; only block downstream resources
       • If verified: Continue to endpoint
       • If user not found: Return 401 UNAUTHORIZED
     
     Protected routes default: All except /dashboard, /public, /auth/login, /auth/register
     ```

#### 9. **Integrate Verification Trigger into Existing Register Endpoint**
   - **File:** `backend/routes/auth.py` (modify existing `POST /api/auth/register`)
   - **Changes:**
     ```
     In the existing register() function, after successful user creation:
     
     1. Call create_verification_token(user_id) -> VerificationToken
     2. Call send_verification_email(user_id, email, token.token) [ASYNC, non-blocking]
     3. Return existing 201 success response (no visual change to register response)
     4. If email service fails:
        - Log error but do NOT fail registration
        - Queue retry or alert ops team
        - User can call resend endpoint later
     ```

---

### Phase 4: Frontend Integration (Days 5–6)

#### 10. **Create Verification Success Page**
   - **File:** `frontend/pages/verify-email-success.jsx` (or `.vue`, `.tsx`)
   - **Component:**
     ```
     Route: /verify-email/success
     
     Renders:
     - Success icon/checkmark
     - Message: "Your email has been verified!"
     - Subtext: "Your account is now active. You can access all features."
     - CTA button: "Go to Dashboard" → redirects to /dashboard
     - No navigation back; prevents re-entering same token
     ```

#### 11. **Create Verification Error Page**
   - **File:** `frontend/pages/verify-email-error.jsx`
   - **Component:**
     ```
     Route: /verify-email/error?code=<error_code>
     Query params: code (TOKEN_EXPIRED | TOKEN_ALREADY_USED | TOKEN_NOT_FOUND)
     
     Renders:
     - Error icon
     - Conditional messages:
       - TOKEN_EXPIRED: "This link has expired. Request a new one below."
       - TOKEN_ALREADY_USED: "This link has already been used. Sign in to continue."
       - TOKEN_NOT_FOUND: "This link is invalid. Request a new one below."
     - CTA: "Resend Verification Email" button (opens modal or redirects to sign-in with resend prompt)
     - Fallback: "Back to Sign In" link
     ```

#### 12. **Modify Existing Sign-In Form**
   - **File:** `frontend/pages/sign-in.jsx` (or component path)
   - **Changes:**
     ```
     In handleSignInSuccess() callback after JWT is obtained:
     
     1. Call /api/auth/me or similar to fetch user.is_verified flag
     2. If is_verified === false:
        - Display inline banner (fixed, non-dismissable):
          • Icon + warning color
          • Text: "Your email has not been verified. Check your inbox for a verification email."
          • Actions:
            - "Resend verification email" button
            - "Change email?" link (optional, out of scope for now)
        - Do NOT redirect; allow user to stay on sign-in or navigate to dashboard
        - Banner shows countdown timer during resend cooldown
     3. If is_verified === true:
        - Remove banner, proceed with normal flow
     4. On resend button click:
        - Call POST /api/auth/resend-verification-email
        - Disable button, show countdown (60s)
        - Show toast: "Verification email sent"
        - On cooldown expire, re-enable button
     ```

#### 13. **Create Verification Link Handler Page**
   - **File:** `frontend/pages/verify-email.jsx`
   - **Component:**
     ```
     Route: /verify-email?token=<token>
     Query params: token (from email link)
     
     On mount:
     1. Extract token from query string
     2. Show loading spinner: "Verifying your email..."
     3. Call POST /api/auth/verify-email with { token: token }
     4. On success (200):
        - Clear token from URL (history.replaceState)
        - Redirect to /verify-email/success after 1s delay
     5. On error:
        - Parse error code from response
        - Redirect to /verify-email/error?code=<error_code>
     6. On network error:
        - Show error message with retry button
     ```

#### 14. **Add Unverified User Redirect Middleware (Optional)**
   - **File:** `frontend/middleware/auth.js` (or route guard)
   - **Context:** If stakeholder confirms full redirect (not banner) approach:
     ```
     In router.beforeEach() or similar:
     
     1. If route is protected AND user is authenticated AND user.is_verified === false:
        - Redirect to /verify-email/awaiting-verification
        - Show page with: "Please verify your email", resend option, sign-out option
     2. Otherwise: Allow navigation
     ```

---

### Phase 5: Testing & Deployment (Days 6–7)

#### 15. **Create Test Suite**
   - **File:** `backend/tests/test_email_verification.py`
   - **Test Cases:**
     ```
     ✓ test_generate_secure_token_uniqueness (100 tokens, no collisions)
     ✓ test_create_verification_token_expires_24h
     ✓ test_verify_token_valid
     ✓ test_verify_token_expired
     ✓ test_verify_token_already_used
     ✓ test_verify_token_not_found
     ✓ test_mark_token_used_updates_user
     ✓ test_can_resend_email_cooldown_active
     ✓ test_can_resend_email_cooldown_expired
     ✓ test_can_resend_email_attempt_limit_exceeded
     ✓ test_send_verification_email_success
     ✓ test_send_verification_email_retry_on_failure
     ✓ test_register_endpoint_triggers_email
     ✓ test_verify_endpoint_success
     ✓ test_verify_endpoint_expired_link
     ✓ test_resend_endpoint_rate_limit
     ✓ test_protected_resource_blocks_unverified
     ✓ test_protected_resource_
