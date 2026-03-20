# Architect

# Technical Architecture: Email Verification Feature

> **Status:** Architecture phase in progress. Six critical open questions from PM analysis remain unresolved. This plan assumes stakeholder decisions below; any deviation will require re-architecture.

---

## CRITICAL ASSUMPTIONS (Must Be Confirmed Before Dev Starts)

| Question | Assumed Answer | Impact | Risk if Wrong |
|----------|----------------|--------|---------------|
| **Token Expiry** | 24 hours | `mng_verification_tokens.expires_at` calculation | If security mandates 1 hour, token logic & email template must change |
| **Resend Attempt Cap** | No hard cap; 60s rate-limit only | Rate-limit middleware; no account lockout logic | If a hard cap (e.g., 5 attempts) is required, add `resend_count` tracking & account review trigger |
| **Existing User Backfill** | All pre-existing users grandfathered as verified (`verified_at = NOW()`) | Pre-migration script required; no retroactive enforcement | If retroactive verification required, scope expands significantly (email campaign, user communication, UX overhaul) |
| **Email Service** | AWS SES (common in existing stacks; SendGrid/Mailgun if already contracted) | All email sending logic uses chosen provider SDK | Wrong choice = vendor lock-in; email delivery failures |
| **Unverified User Access** | Full redirect to "Awaiting Verification" screen (non-blocking banner at Sign In, but no access to protected resources until verified) | Middleware/route guards check `verified_at` before resource access | If partial access allowed, auth checks must be granular per-resource |
| **UI Changes Approval** | Design team has reviewed "Awaiting Verification" screen, verification banner, and token error pages | No rework post-dev; components ship with design sign-off | If design review happens during dev, timeline slips 1–2 weeks |

**→ Confirm all six assumptions with stakeholders before proceeding to Developer phase.**

---

## 1. IMPLEMENTATION PLAN (Execution Order)

### Phase 1: Database & Core Token Infrastructure (Days 1–2)

**1.1** Create `mng_verification_tokens` table
- Stores unique, single-use tokens with expiry and redemption metadata
- Indexed on `token` and `user_id` for fast lookups
- Primary key: `id`; unique constraint on `token`

**1.2** Create `mng_resend_cooldown` table (or cache layer if using Redis)
- Tracks last resend timestamp per user to enforce 60-second cooldown
- Stores: `user_id`, `last_resend_at`
- Used to calculate remaining cooldown on frontend

**1.3** Alter existing `users` table (or equivalent; prefix not applied as this table pre-exists)
- Add `verified_at` column (nullable TIMESTAMP; NULL = unverified, set to NOW() on successful verification)
- Add index on `verified_at` for querying verified vs. unverified users
- Backfill existing users: `UPDATE users SET verified_at = created_at`

### Phase 2: Backend Token & Email Logic (Days 2–4)

**2.1** Implement token generation & storage
- Create `TokenService` class with `generateToken(userId)` method
- Uses `crypto.randomBytes(32).toString('hex')` for cryptographically secure token
- Stores token in `mng_verification_tokens` with `expires_at = NOW() + 24 hours`
- Returns token string and token object (id, user_id, expires_at)

**2.2** Implement email sending
- Create `EmailService` class with `sendVerificationEmail(email, token, baseUrl)` method
- Integrates AWS SES (or configured provider)
- Email template: Plain-text + HTML with verification link: `{baseUrl}/verify-email?token={token}`
- Email subject: `"Confirm Your Email Address"`
- No styling changes to existing brand; use existing email template wrapper if available

**2.3** Hook email into registration flow
- Modify existing **Create Account** endpoint (`POST /auth/register` or equivalent)
- After successful user creation, call `TokenService.generateToken(userId)` and `EmailService.sendVerificationEmail()`
- Wrap in background job (Bull, Celery, or SQS) to send async (not blocking HTTP response)
- Job should retry up to 3 times with exponential backoff (1s, 2s, 4s)
- Return 201 Created to user immediately; email delivery is fire-and-forget

**2.4** Implement token verification endpoint
- Create `POST /auth/verify-email` endpoint
- Input: `{ token: string }`
- Logic:
  1. Look up token in `mng_verification_tokens` by `token` string
  2. Check `expires_at > NOW()` (if expired, return 410 Gone with error message)
  3. Check `redeemed_at IS NULL` (if already used, return 409 Conflict with "already used" message)
  4. Set `users.verified_at = NOW()` for token's user
  5. Set `mng_verification_tokens.redeemed_at = NOW()` (mark as used; soft-delete)
  6. Return 200 OK with success message
- Response: `{ success: true, message: "Email verified! Your account is now active." }`

**2.5** Implement resend verification email endpoint
- Create `POST /auth/resend-verification` endpoint
- Input: `{ email: string }` (or use authenticated user if already signed in)
- Logic:
  1. Look up user by email
  2. Check if user is already verified (`verified_at IS NOT NULL`) → return 400 "Already verified"
  3. Check cooldown via `mng_resend_cooldown`: `SELECT last_resend_at WHERE user_id = ? AND last_resend_at > NOW() - INTERVAL 60 SECONDS`
     - If cooldown active, return 429 Too Many Requests with `{ remaining_seconds: X }`
  4. Invalidate existing unused tokens: `UPDATE mng_verification_tokens SET redeemed_at = NOW() WHERE user_id = ? AND redeemed_at IS NULL`
  5. Generate new token and send email (same as **2.3**)
  6. Upsert `mng_resend_cooldown.last_resend_at = NOW()` for this user
  7. Return 200 OK

**2.6** Implement protected resource guard
- Create middleware/decorator: `requireVerified`
- Checks `users.verified_at IS NOT NULL` for authenticated requests
- If unverified, return 403 Forbidden with redirect hint: `{ error: "Email not verified", redirect: "/awaiting-verification" }`
- Apply this middleware to ALL protected routes (on top of existing authentication middleware)

### Phase 3: Sign In Flow Enhancement (Days 4–5)

**3.1** Modify existing Sign In endpoint
- After successful credential validation, check `users.verified_at`
- If verified: Return existing 200 OK response unchanged
- If unverified: Still return 200 OK with JWT/session token (user is authenticated), but include flag: `{ authenticated: true, verified: false, message: "Please verify your email to access protected features" }`
- Frontend intercepts and shows banner/inline prompt

**3.2** Create "Awaiting Verification" screen endpoint
- Create `GET /auth/awaiting-verification` (protected by auth middleware only, NOT by `requireVerified`)
- Returns:
  - User's partially masked email address (e.g., `user@exa***le.com`)
  - Current cooldown status: `{ cooldown_active: bool, remaining_seconds: int }`
  - Query `mng_resend_cooldown` to compute remaining seconds

### Phase 4: Frontend Components (Days 5–6)

**4.1** Verification banner on Sign In form
- Component: `EmailVerificationBanner`
- Display conditions: user signed in with `{ verified: false }` in response, or `localStorage.pending_verification_email` flag is set
- Content:
  ```
  ┌──────────────────────────────────────────────┐
  | ⚠️  Email Not Verified                        |
  | We sent a verification link to your email.   |
  | [Resend Email] [Dismiss]                     |
  └──────────────────────────────────────────────┘
  ```
- Button states:
  - Normal: `[Resend Email]` clickable
  - Cooldown active: `[Resend Email (0:45)]` disabled with countdown
  - Success: "✓ Email sent. Check your inbox." (auto-dismiss after 3s)

**4.2** Create "Awaiting Verification" screen component
- Route: `/awaiting-verification`
- Fetches data from `GET /auth/awaiting-verification`
- Content:
  ```
  ┌─────────────────────────────────────────────────┐
  | 📧 Verify Your Email                            |
  | We sent a link to: user@exa***le.com            |
  | Click the link in the email to activate your    |
  | account. Didn't receive it?                     |
  | [Resend Email] [Change Email] [Sign Out]        |
  └─────────────────────────────────────────────────┘
  ```
- "Resend Email" button wired to `POST /auth/resend-verification`
- "Change Email" → Sign Out and return to Register form
- Countdown timer logic: `useEffect(() => { setRemaining(...) }, [cooldownEnd])`

**4.3** Create email verification link handler page
- Route: `/verify-email?token=<TOKEN>`
- On load:
  1. Extract `token` from query string
  2. Call `POST /auth/verify-email` with token
  3. If 200: Show "✓ Email verified! Redirecting..." → navigate to `/dashboard`
  4. If 410: Show "Link expired. [Request new link]" → call `POST /auth/resend-verification` if user is authenticated
  5. If 409: Show "This link has already been used. [Back to Sign In]"
  6. If 401: Show "Session expired. [Sign in again]"

**4.4** Update protected route guards
- Wrap all protected routes with `<RequireVerified>` component
- If `verified: false`, redirect to `/awaiting-verification` instead of rendering protected content
- Preserve intended destination in query param for redirect-after-verify (e.g., `/awaiting-verification?next=/dashboard`)

### Phase 5: Testing & QA (Days 6–7)

**5.1** Unit tests
- `TokenService.generateToken()` — token uniqueness and format
- `TokenService.verifyToken()` — expiry check, single-use enforcement, user lookup
- `EmailService.sendVerificationEmail()` — mock AWS SES, verify template rendering
- Resend cooldown logic — verify 60s enforcement and reset against `mng_resend_cooldown`

**5.2** Integration tests
- Register → Email sent → Token valid → Verify → Access protected resource ✓
- Expired token → 410 error ✓
- Double-click token → 409 already used ✓
- Resend within 60s → 429 cooldown error ✓
- Sign In unverified → Banner shown, no access to protected resources ✓
- Existing user backfill → All pre-existing accounts marked verified ✓

**5.3** E2E tests (Cypress/Playwright)
- Full registration and verification flow
- Resend email with cooldown timer
- Token expiry simulation
- Unverified user redirect from protected route

---

## 2. FILES TO CREATE & MODIFY

### **New Files**

| Path | Purpose | Key Content |
|------|---------|-------------|
| `backend/src/models/MngVerificationToken.ts` | ORM model for `mng_verification_tokens` table | Schema, indexes, relation to User |
| `backend/src/models/MngResendCooldown.ts` | ORM model for `mng_resend_cooldown` table | Schema, relation to User |
| `backend/src/services/TokenService.ts` | Token generation, validation, and redemption | `generateToken()`, `verifyToken()`, `invalidateUserTokens()` |
| `backend/src/services/EmailService.ts` | Email sending abstraction | `sendVerificationEmail(email, token, baseUrl)` |
| `backend/src/jobs/SendVerificationEmailJob.ts` | Background job for async email delivery | Retry logic, exponential backoff, error handling |
| `backend/src/middlewares/requireVerified.ts` | Auth middleware enforcing email verification | 403 + redirect hint for unverified users |
| `backend/src/templates/verificationEmail.html` | Email HTML template | Branding, token link, CTA button |
| `backend/src/templates/verificationEmail.txt` | Email plain-text fallback | Token link, instructions |
| `database/migrations/001_add_mng_verification_tokens.sql` | Create `mng_verification_tokens` table | Full DDL with indexes and constraints |
| `database/migrations/002_add_mng_resend_cooldown.sql` | Create `mng_resend_cooldown` table | Full DDL with indexes |
| `database/migrations/003_add_users_verified_at.sql` | Alter `users` table + backfill | Add `verified_at`, index, backfill statement |
| `frontend/src/components/EmailVerificationBanner.tsx` | In-form verification prompt | Resend button, cooldown timer, success/dismissed states |
| `frontend/src/components/AwaitingVerificationScreen.tsx` | Full-page verification awaiting screen | Masked email display, resend logic, sign-out link |
| `frontend/src/pages/VerifyEmailPage.tsx` | Verification link handler page | Token extraction, API call, all error/success states |
| `frontend/src/components/RequireVerified.tsx` | Protected route wrapper | Redirect to `/awaiting-verification` if unverified |
| `frontend/src/hooks/useVerificationStatus.ts` | React hook for verification state | Derived state from auth context, cooldown tracking |

### **Modified Files**

| Path | Changes |
|------|---------|
| `backend/src/models/User.ts` | Add `verified_at?: Date \| null` field; ensure constructor initializes as `null` |
| `backend/src/routes/authRoutes.ts` | Add `POST /auth/verify-email`, `POST /auth/resend-verification`, `GET /auth/awaiting-verification`; modify `POST /auth/register` to trigger verification email job; modify `POST /auth/sign-in` to include `verified` flag in response |
| `backend/src/database/index.ts` | Register `MngVerificationToken` and `MngResendCooldown` models with ORM |
| `backend/src/app.ts` | Apply `requireVerified` middleware to all protected route groups |
| `frontend/src/pages/SignInPage.tsx` | Conditionally render `<EmailVerificationBanner />` when sign-in response includes `verified: false` |
| `frontend/src/routes/ProtectedRoute.tsx` | Wrap with `<RequireVerified>`; read `verified` from auth context; redirect if false |
| `frontend/src/context/AuthContext.tsx` | Store `verified` boolean alongside existing auth state; update on sign-in response and successful verification |
| `database/migrations/index.ts` | Register migrations 001, 002, and 003 in order |
| `.env.example` | Add `EMAIL_PROVIDER=aws_ses`, `AWS_SES_REGION=us-east-1`, `AWS_SES_ACCESS_KEY_ID`, `AWS_SES_SECRET_ACCESS_KEY`, `EMAIL_FROM_ADDRESS=noreply@yourdomain.com` |

---

## 3. NEW COMPONENTS & FUNCTIONS

### **Database Schema**

```sql
-- Migration 001: mng_verification_tokens
CREATE TABLE mng_verification_tokens (
  id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token         VARCHAR(64)   NOT NULL,
  expires_at    TIMESTAMP     NOT NULL,
  redeemed_at   TIMESTAMP     NULL DEFAULT NULL,
  created_at    TIMESTAMP     NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_mng_verification_tokens_token UNIQUE (token)
);

CREATE INDEX idx_mng_verification_tokens_token   ON mng_verification_tokens (token);
CREATE
