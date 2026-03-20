# Reviewer

```json
{
  "passed": false,
  "score": 4,
  "issues": [
    "Implementation is incomplete — cuts off mid-file in EmailService.ts without finishing AWS SES client setup, email template loading, or the sendVerificationEmail method",
    "No frontend implementation provided despite architect plan specifying 4 new components (EmailVerificationBanner, AwaitingVerificationScreen, VerifyEmailPage, RequireVerified) and modifications to existing auth pages",
    "Missing critical route handlers: POST /auth/verify-email, POST /auth/resend-verification, GET /auth/awaiting-verification not implemented",
    "No background job implementation (SendVerificationEmailJob.ts) for async email delivery with retry logic and exponential backoff",
    "Email templates (verificationEmail.html, verificationEmail.txt) referenced but not provided",
    "No unit or integration tests provided despite architect plan requiring comprehensive test coverage across token lifecycle, expiry, single-use enforcement, resend cooldown, and E2E flows",
    "Missing middleware implementation (requireVerified.ts) to enforce email verification on protected routes",
    "AuthContext/auth state management modifications for verified flag not provided; unclear how frontend will track/persist verification status",
    "No error handling or validation for edge cases: what happens if user registration succeeds but email send fails? How are job retries logged?",
    "Environment configuration incomplete: .env.example additions not provided; AWS SES credentials validation missing",
    "Migration runner (database/migrations/index.ts) provided but not integrated into app startup — no initialization hook shown",
    "No transaction error handling for concurrent resend requests or race conditions during token redemption",
    "Backfill strategy for existing users (UPDATE users SET verified_at = created_at) could fail if created_at is NULL; no null-coalescing shown in actual migration SQL"
  ],
  "suggestions": [
    "Complete EmailService.ts with full AWS SES client initialization, template rendering, error handling, and method signatures matching TokenService calls",
    "Provide all 4 frontend components with state management: EmailVerificationBanner (with cooldown timer logic), AwaitingVerificationScreen (masked email display), VerifyEmailPage (token extraction and verification), RequireVerified (route guard)",
    "Implement POST /auth/verify-email and POST /auth/resend-verification route handlers with proper error responses (410 for expired, 409 for already-used, 429 for cooldown, 400 for already verified)",
    "Implement SendVerificationEmailJob.ts with Bull/Celery/SQS integration, 3-retry logic with exponential backoff (1s, 2s, 4s), and error logging",
    "Create email templates (HTML + plain text) with verification link, branding consistency, and fallback plain-text version",
    "Write unit tests for TokenService (generateToken uniqueness, redeemToken expiry/single-use checks), EmailService mock, resend cooldown math; write integration tests for full registration→verification flow and error paths",
    "Implement requireVerified middleware that checks user.verified_at and returns 403 with redirect hint; apply globally to protected routes in Express middleware stack",
    "Add verified flag to AuthContext and sync with sign-in response (verified: boolean field); persist in sessionStorage for banner visibility after page reload",
    "Add null-coalescing to migration 003: UPDATE users SET verified_at = COALESCE(created_at, NOW()) — or validate no NULL created_at exists before migration",
    "Call runMigrations(pool) in app.ts startup sequence before listening; add error handling to prevent server start if migrations fail",
    "Add transactional safety: wrap resend-verification and verify-email logic in explicit client.query('BEGIN'/'COMMIT'/'ROLLBACK') blocks to handle concurrent requests",
    "Provide .env.example additions for EMAIL_PROVIDER, AWS_SES_REGION, AWS_SES_ACCESS_KEY_ID, AWS_SES_SECRET_ACCESS_KEY, EMAIL_FROM_ADDRESS",
    "Add logging/instrumentation: log token generation, email sends, verification successes, and resend attempts with user_id for audit trail"
  ],
  "summary": "Implementation incomplete and truncated mid-file; missing all frontend components, route handlers, background job, email templates, tests, and middleware. Core backend services partially started but unfinished. Cannot assess correctness against acceptance criteria."
}
```
