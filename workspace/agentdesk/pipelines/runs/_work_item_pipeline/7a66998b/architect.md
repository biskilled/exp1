# Architect

# Technical Architecture Plan: Email Verification Feature

## Executive Summary
This plan adds email verification to the existing Create Account and Sign In flows. The implementation is **additive and non-breaking** — verified users see no change, unverified users are gated at sign-in and prompted to verify. No UI form changes required; verification happens post-registration via email link.

---

## 1. Implementation Plan (Execution Order)

### Phase 1: Database & Core Infrastructure
1. **Create `email_verifications` table** to store tokens, expiry, and usage state
2. **Add `is_verified` and `verified_at` columns to `users` table**
3. **Create migration scripts** for safe deployment with backward compatibility
4. **Set up email service integration** (configure provider, templates, error handling)

### Phase 2: Backend Logic
5. **Create `EmailVerificationService`** class with token generation, validation, and resend logic
6. **Create `EmailService`** class to handle email sending with retry and logging
7. **Modify `CreateAccountService`** to trigger email send post-registration
8. **Create `/api/auth/verify-email` endpoint** to handle token validation
9. **Create `/api/auth/resend-verification-email` endpoint** with rate limiting
10. **Modify authentication middleware** to check verification status
11. **Create verification link generation utility** with secure token generation

### Phase 3: Sign-In & Access Control
12. **Modify Sign In endpoint** to return verification status in response
13. **Add verification check middleware** to all protected routes
14. **Create verification gating logic** — block unverified users from authenticated areas
15. **Create redirect/prompt logic** for unverified users attempting protected access

### Phase 4: Frontend Integration
16. **Create email verification success page** (`/verify-email-success`)
17. **Create email verification error page** (`/verify-email-error`)
18. **Modify Sign In response handler** to detect and display unverified state
19. **Create inline resend component** for Sign In and error pages
20. **Add rate limit visual feedback** (disable resend button during cooldown)

### Phase 5: Monitoring & Testing
21. **Add logging & metrics** for email sends, verifications, token expiry
22. **Create database queries** for reporting (unverified account counts, resend rates)
23. **Write unit tests** for token generation, expiry, single-use validation
24. **Write integration tests** for end-to-end verification flow
25. **Document email templates & variable placeholders**

### Phase 6: Deployment & Legacy Handling
26. **Create data migration** for existing users (set as verified if needed per decision)
27. **Add feature flag** to enable/disable verification enforcement (for gradual rollout)
28. **Create runbook** for monitoring verification metrics in production
29. **Set up alerts** for email delivery failures, high unverified account rates

---

## 2. Files to Create or Modify

### 2.1 Database Files

#### **NEW: `database/migrations/001_add_email_verification.sql`**
```sql
-- Add verification columns to users table
ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN verified_at TIMESTAMP NULL;
ALTER TABLE users ADD INDEX idx_is_verified (is_verified);

-- Create email verifications table
CREATE TABLE email_verifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL UNIQUE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_expires_at (expires_at),
    INDEX idx_user_id_expires_at (user_id, expires_at)
);

-- Create rate limit tracking table for resends
CREATE TABLE verification_resend_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id_requested_at (user_id, requested_at)
);
```

#### **MODIFY: `database/migrations/rollback_001.sql`** (Rollback script)
```sql
DROP TABLE IF EXISTS verification_resend_logs;
DROP TABLE IF EXISTS email_verifications;
ALTER TABLE users DROP COLUMN verified_at;
ALTER TABLE users DROP COLUMN is_verified;
```

---

### 2.2 Backend Service Files

#### **NEW: `src/services/EmailVerificationService.ts`**
```typescript
// Responsibilities:
// - Generate cryptographically secure tokens (64-char hex string)
// - Store tokens in DB with 24-hour expiry
// - Validate tokens (check existence, expiry, single-use)
// - Mark tokens as used
// - Check resend rate limits (60-second cooldown)
// - Update user is_verified status
// - Return meaningful error codes for each failure case

// Key methods:
// - generateVerificationToken(userId): Promise<{token, expiresAt}>
// - validateToken(token): Promise<{isValid, userId, error?}>
// - markTokenAsUsed(token): Promise<void>
// - canResendEmail(userId): Promise<{allowed, secondsUntilNext}>
// - logResendAttempt(userId): Promise<void>
```

#### **NEW: `src/services/EmailService.ts`**
```typescript
// Responsibilities:
// - Send emails via configured provider (SendGrid/SES/Mailgun)
// - Render email templates with variables
// - Implement retry logic with exponential backoff
// - Log all send attempts (success/failure)
// - Handle provider-specific errors gracefully
// - Support template variables: {verificationLink}, {expiresInHours}, {userName}

// Key methods:
// - sendVerificationEmail(to, userName, verificationLink): Promise<{success, messageId?}>
// - sendResendConfirmation(to, verificationLink): Promise<{success, messageId?}>
// - Health check to verify provider connectivity
```

#### **MODIFY: `src/services/AccountService.ts` (or CreateAccountService)**
```typescript
// Add hook to send verification email after user creation:
// 1. Create user (existing logic)
// 2. Generate verification token via EmailVerificationService
// 3. Send email via EmailService
// 4. Handle email send failure (log error, mark user for retry, do NOT block sign-up)
// 5. Return user object with is_verified: false
```

#### **NEW: `src/middleware/VerificationMiddleware.ts`**
```typescript
// Responsibilities:
// - Extract user from JWT/session
// - Check is_verified status from DB or cache
// - If unverified AND route is protected: 
//   - Return 403 with error code "EMAIL_NOT_VERIFIED"
//   - Include resend endpoint URL in response
// - If verified: pass through
// - Cache verification status (5-minute TTL) to avoid DB hits on every request

// Attached to: All routes in /api/protected/*, /dashboard, /settings, etc.
```

#### **NEW: `src/middleware/RateLimitMiddleware.ts` (or enhance existing)**
```typescript
// Add resend-specific rate limit:
// - Key: `verification-resend:${userId}`
// - Limit: 1 request per 60 seconds
// - Return 429 with retry-after header if exceeded
```

---

### 2.3 API Endpoint Files

#### **NEW: `src/routes/auth/verifyEmail.ts`**
```typescript
// GET /api/auth/verify-email?token={token}
// OR POST /api/auth/verify-email with body {token}

// Flow:
// 1. Extract token from query or body
// 2. Call EmailVerificationService.validateToken(token)
// 3. If invalid/expired: return 400 with specific error (INVALID_TOKEN, EXPIRED_TOKEN, ALREADY_USED)
// 4. If valid:
//    a. Update users.is_verified = true, verified_at = NOW()
//    b. Mark token as used: email_verifications.used_at = NOW()
//    c. Invalidate any other pending tokens for this user (optional, for cleanliness)
//    d. Return 200 with success message
//    e. Frontend redirects to /verify-email-success

// Response format:
// Success: { success: true, message: "Email verified. You may now sign in." }
// Error: { success: false, code: "EXPIRED_TOKEN", message: "...", resendUrl: "/auth/resend-verification" }
```

#### **NEW: `src/routes/auth/resendVerificationEmail.ts`**
```typescript
// POST /api/auth/resend-verification-email
// Body: { email: string } (for password reset flow) OR { userId: string } (for logged-in users)

// Flow:
// 1. Lookup user by email or userId
// 2. Check if user already verified → return 400 "ALREADY_VERIFIED"
// 3. Check resend rate limit via VerificationMiddleware
// 4. If rate limited: return 429 with secondsUntilNext
// 5. If allowed:
//    a. Invalidate old token (optional: set used_at or delete)
//    b. Generate new token via EmailVerificationService
//    c. Send email via EmailService
//    d. Log resend attempt
//    e. Return 200 with success message
// 6. If email send fails: return 500, log incident for ops team

// Response format:
// Success: { success: true, message: "Verification email sent. Check your inbox." }
// Errors: 
//   - ALREADY_VERIFIED: "Account already verified."
//   - RATE_LIMITED: "Too many resend requests. Try again in {X} seconds."
//   - USER_NOT_FOUND: "No account found with that email."
```

#### **MODIFY: `src/routes/auth/signin.ts`** (or authenticate)
```typescript
// Existing sign-in endpoint
// After successful credential validation:
// 1. Fetch user.is_verified from DB
// 2. Include in response: { user, token, is_verified }
// 3. Frontend checks is_verified and handles accordingly

// Do NOT block sign-in at API level — let frontend decide UX
// (This allows flexibility: some apps block, others warn with banner)
// Exception: If requirements say BLOCK unverified → add check before returning token
```

#### **MODIFY: `src/routes/auth/createAccount.ts` (or signup)**
```typescript
// Existing create account endpoint
// After user creation success:
// 1. Async trigger: EmailVerificationService.generateVerificationToken(userId)
// 2. Async trigger: EmailService.sendVerificationEmail(email, userName, link)
// 3. Do NOT wait for email to complete — return success immediately
// 4. Return: { user, message: "Account created. Check your email to verify." }
// 5. Log any email send errors to monitoring system

// User-facing message should be clear:
// "Account created successfully. We've sent a verification email to {email}. 
//  Please check your inbox (and spam folder) within 24 hours."
```

---

### 2.4 Frontend Files

#### **NEW: `pages/verify-email-success.tsx`** (or `.jsx`)
```typescript
// Rendered after successful token validation via /api/auth/verify-email
// Display:
// - Success icon/message: "Your email has been verified!"
// - Call-to-action: "Continue to Sign In" button → /signin
// - Optional: Auto-redirect to /signin after 3 seconds
```

#### **NEW: `pages/verify-email-error.tsx`**
```typescript
// Rendered when verification link is invalid/expired
// Query params: ?code={ERROR_CODE}&email={EMAIL}
// Display based on code:
// - INVALID_TOKEN: "This link is invalid. Request a new verification email."
// - EXPIRED_TOKEN: "This link has expired. Request a new verification email."
// - ALREADY_USED: "This link has already been used. Request a new verification email."
// - USER_NOT_FOUND: "No account found. Create an account or sign in."

// Features:
// - Form to request resend (email pre-filled if in URL)
// - Resend button disabled during 60-second cooldown with countdown timer
// - Loading state while resend request is in flight
// - Success toast: "Verification email sent! Check your inbox."
```

#### **MODIFY: `components/SignInForm.tsx`**
```typescript
// After sign-in API call succeeds:
// 1. Check response.is_verified
// 2. If false:
//    a. Show modal/alert: "Account Not Verified"
//    b. Message: "We sent a verification email to {email}. 
//       Please verify before accessing your account."
//    c. Button: "Resend Verification Email"
//    d. Button: "Sign In with Different Account"
// 3. Prevent navigation to protected routes
// 4. Clear auth token from localStorage (do NOT set as logged in)

// OR if API returns 403 EMAIL_NOT_VERIFIED:
//    a. Same UX flow as above
```

#### **NEW: `components/ResendVerificationForm.tsx`**
```typescript
// Reusable component for resending verification emails
// Props: { email?, userId?, onSuccess?, onError? }
// Features:
// - Email input (editable or pre-filled)
// - Resend button (disabled during 60-second cooldown)
// - Countdown timer: "Resend available in {X}s"
// - Loading state during POST
// - Error/success toast notifications
// - Rate limit handling: show message "Try again in {X} seconds"
```

#### **MODIFY: `pages/signin.tsx`**
```typescript
// Add conditional rendering for unverified state:
// - Normal sign-in form if user not yet entered credentials
// - Unverified prompt if sign-in succeeded but account unverified
// - Include ResendVerificationForm in unverified prompt
```

#### **NEW: `utils/authRedirect.ts`**
```typescript
// Helper function for protected routes:
// - Check if user is authenticated AND verified
// - If not verified: redirect to /verify-email-error with email in query
// - If not authenticated: redirect to /signin
// Used in:
//   - Route guards / page layout wrappers
//   - Protected API client interceptor
```

---

### 2.5 Configuration & Utility Files

#### **NEW: `config/email.config.ts`**
```typescript
// Centralized email configuration:
// - Provider selection (SENDGRID | AWS_SES | MAILGUN)
// - API keys from env variables
// - From address and branding
// - Template IDs/names for each email type
// - Retry policy (max attempts, backoff strategy)
// - Verification link base URL

// Example:
export const emailConfig = {
  provider: process.env.EMAIL_PROVIDER || 'SENDGRID',
  sendgridApiKey: process.env.SENDGRID_API_KEY,
  fromEmail: process.env.EMAIL_FROM || 'noreply@platform.com',
  templates: {
    verification: 'd-xxxxx', // SendGrid template ID
  },
  verificationLinkBase: process.env.VERIFICATION_LINK_BASE || 'https://app.example.com/verify-email',
  tokenExpiry: 24 * 60 * 60, // 24 hours in seconds
  resendCooldown: 60, // 60 seconds
};
```

#### **NEW: `utils/tokenGenerator.ts`**
```typescript
// Crypto-secure token generation:
// - Use crypto.randomBytes(32) → hex string (64 chars)
// - Ensure uniqueness in DB before returning
// - No predictable patterns

export function generateVerificationToken(): string {
  return crypto.randomBytes(32).toString('hex');
}
```

#### **NEW: `utils/verificationLinkGenerator.ts`**
```typescript
// Build verification link:
// - Construct: {VERIFICATION_LINK_BASE}?token={TOKEN}
// - Optionally add email param: &email={EMAIL}
// - Return full URL for email template

export function generateVerificationLink(token: string, email?: string): string {
  const base = emailConfig.verificationLinkBase;
  const params = new URLSearchParams
