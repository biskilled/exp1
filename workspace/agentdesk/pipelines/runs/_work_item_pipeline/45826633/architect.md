# Architect

# Technical Architecture: Email Verification Feature

> **Status:** Architecture phase in progress. Six critical open questions from PM analysis remain unresolved. This plan assumes stakeholder decisions below; any deviation will require re-architecture.

---

## CRITICAL ASSUMPTIONS (Must Be Confirmed Before Dev Starts)

| Question | Assumed Answer | Impact | Risk if Wrong |
|----------|----------------|--------|---------------|
| **Token Expiry** | 24 hours | `verification_tokens.expires_at` calculation | If security mandates 1 hour, token logic & email template must change |
| **Resend Attempt Cap** | No hard cap; 60s rate-limit only | Rate-limit middleware; no account lockout logic | If a hard cap (e.g., 5 attempts) is required, add `resend_count` tracking & account review trigger |
| **Existing User Backfill** | All pre-existing users grandfathered as verified (`verified_at = NOW()`) | Pre-migration script required; no retroactive enforcement | If retroactive verification required, scope expands significantly (email campaign, user communication, UX overhaul) |
| **Email Service** | AWS SES (common in existing stacks; SendGrid/Mailgun if already contracted) | All email sending logic uses chosen provider SDK | Wrong choice = vendor lock-in; email delivery failures |
| **Unverified User Access** | Full redirect to "Awaiting Verification" screen (non-blocking banner at Sign In, but no access to protected resources until verified) | Middleware/route guards check `verified_at` before resource access | If partial access allowed, auth checks must be granular per-resource |
| **UI Changes Approval** | Design team has reviewed "Awaiting Verification" screen, verification banner, and token error pages | No rework post-dev; components ship with design sign-off | If design review happens during dev, timeline slips 1–2 weeks |

**→ Confirm all six assumptions with stakeholders before proceeding to Developer phase.**

---

## 1. IMPLEMENTATION PLAN (Execution Order)

### Phase 1: Database & Core Token Infrastructure (Days 1–2)

**1.1** Create `verification_tokens` table
- Stores unique, single-use tokens with expiry and redemption metadata
- Indexed on `token` and `user_id` for fast lookups
- Primary key: `id`; unique constraint on `token`

**1.2** Alter `users` table
- Add `verified_at` column (nullable TIMESTAMP; NULL = unverified, set to NOW() on successful verification)
- Add index on `verified_at` for querying verified vs. unverified users
- Backfill existing users: `UPDATE users SET verified_at = created_at`

**1.3** Create `resend_cooldown` table (or cache layer if using Redis)
- Tracks last resend timestamp per user to enforce 60-second cooldown
- Stores: `user_id`, `last_resend_at`
- Used to calculate remaining cooldown on frontend

### Phase 2: Backend Token & Email Logic (Days 2–4)

**2.1** Implement token generation & storage
- Create `TokenService` class with `generateToken(userId)` method
- Uses `crypto.randomBytes(32).toString('hex')` for cryptographically secure token
- Stores token in `verification_tokens` with `expires_at = NOW() + 24 hours`
- Returns token string and token object (id, user_id, expires_at)

**2.2** Implement email sending
- Create `EmailService` class with `sendVerificationEmail(email, token, baseUrl)` method
- Integrates AWS SES (or configured provider)
- Email template: Plain-text + HTML with verification link: `{baseUrl}/verify-email?token={token}`
- Email subject: `"Confirm Your Email Address"`
- No styling changes to existing brand; use existing email template if available

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
  1. Look up token in `verification_tokens` by `token` string
  2. Check `expires_at > NOW()` (if expired, return 410 Gone with error message)
  3. Check `redeemed_at IS NULL` (if already used, return 409 Conflict with "already used" message)
  4. Set `users.verified_at = NOW()` for token's user
  5. Set `verification_tokens.redeemed_at = NOW()` (mark as used)
  6. Delete token from `verification_tokens` (optional; can soft-delete by setting `redeemed_at`)
  7. Return 200 OK with success message
- Response: `{ success: true, message: "Email verified! Your account is now active." }`

**2.5** Implement resend verification email endpoint
- Create `POST /auth/resend-verification` endpoint
- Input: `{ email: string }` (or use authenticated user if already signed in)
- Logic:
  1. Look up user by email
  2. Check if user is already verified (`verified_at IS NOT NULL`) → return 400 "Already verified"
  3. Check cooldown: `SELECT last_resend_at FROM resend_cooldown WHERE user_id = ? AND last_resend_at > NOW() - INTERVAL 60 SECONDS`
     - If cooldown active, return 429 Too Many Requests with `{ remaining_seconds: X }`
  4. Invalidate existing unused tokens: `UPDATE verification_tokens SET redeemed_at = NOW() WHERE user_id = ? AND redeemed_at IS NULL`
  5. Generate new token and send email (same as **2.3**)
  6. Update `resend_cooldown.last_resend_at = NOW()`
  7. Return 200 OK

**2.6** Implement protected resource guard
- Create middleware/decorator: `requireVerified` or `@VerifyEmail`
- Checks `users.verified_at IS NOT NULL` for authenticated requests
- If unverified, return 403 Forbidden with redirect hint: `{ error: "Email not verified", redirect: "/awaiting-verification" }`
- Apply this middleware to ALL protected routes (existing protected endpoints should already require authentication; this adds the verification layer on top)

### Phase 3: Sign In Flow Enhancement (Days 4–5)

**3.1** Modify existing Sign In endpoint
- After successful authentication (user credentials valid), check `users.verified_at`
- If verified: Return existing 200 OK response (no change to current behavior)
- If unverified: Still return 200 OK with JWT/session token (user is authenticated), but include flag: `{ authenticated: true, verified: false, message: "Please verify your email to access protected features" }`
- Frontend intercepts and shows banner/inline prompt on next page load

**3.2** Create "Awaiting Verification" screen endpoint
- Create `GET /auth/awaiting-verification` (protected by auth middleware, not by `requireVerified`)
- Returns a lightweight HTML/JSON response showing:
  - User's email address (partially masked for privacy: `user@exa***le.com`)
  - "Resend verification email" button
  - Resend cooldown status (if active, show countdown timer; if inactive, button enabled)
  - Link back to Sign In if user wants to switch accounts
- This screen is shown when unverified user attempts to access protected resource or after Sign In if unverified

### Phase 4: Frontend Components (Days 5–6)

**4.1** Verification banner on Sign In form
- Component: `EmailVerificationBanner` (render-only, no state change to existing Sign In form)
- Conditions for display:
  - User just signed in
  - Response included `{ verified: false }`
  - OR check `localStorage.pending_verification_email` flag
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
- Renders data from `GET /auth/awaiting-verification`
- Content:
  ```
  ┌─────────────────────────────────────────────────┐
  | 📧 Verify Your Email                            |
  | We sent a link to: user@example.com             |
  | Click the link in the email to activate your    |
  | account. Didn't receive it?                     |
  | [Resend Email] [Change Email] [Sign Out]        |
  └─────────────────────────────────────────────────┘
  ```
- "Resend Email" button wired to `POST /auth/resend-verification`
- "Change Email" → Sign Out and return to Register form
- Countdown timer logic: `useEffect(() => { setRemaining(...) }, [cooldownEnd])`

**4.3** Create email verification link handler
- Route: `/verify-email?token=<TOKEN>`
- On load:
  1. Extract `token` from query string
  2. Call `POST /auth/verify-email` with token
  3. If 200: Show success message "✓ Email verified! Redirecting..." → navigate to `/` or `/dashboard` (authenticated home)
  4. If 410: Show "Link expired. [Request new link]" → POST `/auth/resend-verification` if user is authenticated
  5. If 409: Show "This link has already been used. [Back to Sign In]" → navigate to `/sign-in`
  6. If 401: Show "Session expired. [Sign in again]" → navigate to `/sign-in`

**4.4** Update protected route guards
- Wrap all protected routes with `<RequireVerified>` component
- If `verified: false`, redirect to `/awaiting-verification` instead of rendering protected content
- Preserve user's intended destination for redirect-after-verify (optional UX improvement)

### Phase 5: Testing & QA (Days 6–7)

**5.1** Unit tests
- `TokenService.generateToken()` — verify token uniqueness and format
- `TokenService.verifyToken()` — expiry check, single-use enforcement, user lookup
- `EmailService.sendVerificationEmail()` — mock AWS SES, verify email template rendering
- Resend cooldown logic — verify 60s enforcement and reset

**5.2** Integration tests
- Register → Email sent → Token valid → Verify → Access protected resource ✓
- Expired token → Error message ✓
- Double-click token → Already used error ✓
- Resend within 60s → Cooldown error ✓
- Sign In unverified → Banner shown, no access to protected resources ✓
- Existing user backfill → All existing accounts marked verified ✓

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
| `backend/src/models/VerificationToken.ts` | ORM model for `verification_tokens` table | Schema, indexes, relations to User |
| `backend/src/services/TokenService.ts` | Token generation, validation, and redemption | `generateToken()`, `verifyToken()`, `getToken()` |
| `backend/src/services/EmailService.ts` | Email sending abstraction | `sendVerificationEmail(email, token, baseUrl)` |
| `backend/src/jobs/SendVerificationEmailJob.ts` | Background job for async email delivery | Retry logic, error handling |
| `backend/src/middlewares/requireVerified.ts` | Auth middleware enforcing email verification | 403 + redirect hint for unverified users |
| `backend/src/routes/authRoutes.ts` (new endpoints) | POST `/auth/verify-email`, POST `/auth/resend-verification`, GET `/auth/awaiting-verification` | Request validation, error responses |
| `database/migrations/001_add_email_verification.sql` | Database schema changes | `verification_tokens` table, `users.verified_at` column |
| `frontend/src/components/EmailVerificationBanner.tsx` | In-form verification prompt | Resend button, cooldown timer, success message |
| `frontend/src/components/AwaitingVerificationScreen.tsx` | Full-page verification awaiting screen | Email display, resend logic, sign-out link |
| `frontend/src/pages/VerifyEmailPage.tsx` | Email verification link handler | Token extraction, API call, success/error states |
| `frontend/src/components/RequireVerified.tsx` | Protected route wrapper | Redirect to `/awaiting-verification` if unverified |
| `frontend/src/hooks/useVerificationStatus.ts` | React hook for verification state | Poll status, manage local state |
| `backend/src/templates/verificationEmail.html` | Email HTML template | Branding, token link, clear CTA |
| `backend/src/templates/verificationEmail.txt` | Email plain-text fallback | Token link, instructions |

### **Modified Files**

| Path | Changes |
|------|---------|
| `backend/src/models/User.ts` | Add `verified_at?: Date` field; update constructor to initialize as NULL |
| `backend/src/routes/authRoutes.ts` | Hook email sending into `POST /auth/register` or `POST /auth/create-account` endpoint |
| `backend/src/database/index.ts` | Register `VerificationToken` model with ORM |
| `backend/src/app.ts` or `server.ts` | Register `requireVerified` middleware on all protected routes (or use route-level guards) |
| `frontend/src/pages/SignInPage.tsx` | Add `<EmailVerificationBanner />` conditionally based on response flag |
| `frontend/src/routes/ProtectedRoute.tsx` or `Layout.tsx` | Wrap with `<RequireVerified>` guard; check `verified: false` in auth state |
| `database/migrations/index.ts` | Register new migration `001_add_email_verification.sql` |
| `.env.example` | Add `EMAIL_SERVICE=aws_ses`, `AWS_SES_REGION`, `EMAIL_FROM_ADDRESS` |

---

## 3. NEW COMPONENTS & FUNCTIONS

### **Backend**

#### `TokenService` Class
```typescript
class TokenService {
  async generateToken(userId: string): Promise<{ token: string; expiresAt: Date }> {
    // Generate cryptographically secure 32-byte token, hex-encoded
    const token = crypto.randomBytes(32).toString('hex');
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours
    
    const record = await VerificationToken.create({
      token,
      userId,
      expiresAt,
      redeemedAt: null,
    });
    return { token: record.token, expiresAt: record.expiresAt };
  }

  async verifyToken(token: string): Promise<{ userId: string; email: string }> {
    const record = await VerificationToken.findOne({ token });
    if (!record) throw new NotFoundError('Invalid token');
    if (record.redeemedAt) throw new ConflictError('Token already used');
    if (new Date() > record.expiresAt) throw new GoneError('Token expired');
    
    const user = await User.findById(record.userId);
    await User.update(record.userId, { verified_at: new Date() });
    await VerificationToken.update(record.id,
