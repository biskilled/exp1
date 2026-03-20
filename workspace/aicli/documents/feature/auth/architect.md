# Architect

# Technical Architecture: Email Verification Feature

---

## 1. Implementation Plan

### Phase 1: Database & Token Infrastructure (Steps 1–3)
1. **Create `email_verification_tokens` table** to store cryptographically secure tokens with expiration and single-use enforcement.
2. **Add `email_verified` boolean column to `users` table** (default: `false`) to track verification status.
3. **Add `email_verified_at` timestamp column to `users` table** to record when verification occurred.

### Phase 2: Email Service Integration (Steps 4–5)
4. **Integrate email service client** (SendGrid selected as default; configurable via env var) to send transactional emails.
5. **Create email template** for verification emails with embedded token link, expiration notice, and clear CTA.

### Phase 3: Token Generation & Verification Logic (Steps 6–8)
6. **Implement `generateVerificationToken(userId, email)`** — server-side token generator using `crypto.randomBytes(32)` hashed with SHA-256; store token, userId, email, expiration (now + 24h), and used flag in DB.
7. **Implement `verifyEmailToken(token)`** — lookup token, validate expiration, validate not-yet-used, mark as used, set `email_verified=true` and `email_verified_at=now()` on user.
8. **Implement `requestVerificationEmail(userId, email)`** — rate-limit check (60s cooldown), generate new token, send email asynchronously; return cooldown end timestamp to client.

### Phase 4: Create Account Flow Enhancement (Steps 9–10)
9. **Modify Create Account endpoint POST `/auth/register`** — on successful user creation, synchronously generate token and enqueue email send (fire-and-forget async task); return existing success response without changes to form or UX.
10. **Ensure email send completes within 2 minutes** via background job queue (Bull/RabbitMQ) with 30-second SLA; log failures for monitoring.

### Phase 5: Sign In Flow Enhancement (Steps 11–12)
11. **Modify Sign In endpoint POST `/auth/login`** — on successful authentication, return user object with `email_verified` flag; client conditionally renders verification banner.
12. **Create `GET /auth/verification-status`** — authenticated endpoint returning `{ email_verified: boolean, last_resend_at: timestamp }` to drive client-side cooldown timer.

### Phase 6: Email Verification Endpoint (Steps 13–14)
13. **Create `GET /auth/verify-email?token=<token>`** — validate token, mark as used, update user, redirect to success page (`/auth/verification-success`) with success message in query param or session flash.
14. **Create `GET /auth/verification-success`** — public page displaying success message; if token invalid/expired in session, redirect to error page instead.

### Phase 7: Error Handling & Self-Service (Steps 15–16)
15. **Create `GET /auth/verify-email?token=<expired-or-used-token>`** — detect invalid/expired state, display error message, render "Request new verification email" button linking to resend endpoint.
16. **Create `POST /auth/resend-verification`** — authenticated endpoint; rate-limit (60s), generate new token, send email, return `{ cooldown_until: timestamp }`.

### Phase 8: Protected Resource Middleware (Steps 17–18)
17. **Create authentication middleware `requireVerifiedEmail`** — check `user.email_verified === true`; if false, redirect to `/auth/awaiting-verification`.
18. **Apply middleware to all protected routes** — identify all routes requiring verification (e.g., `/dashboard`, `/api/protected/*`); update route definitions.

### Phase 9: Awaiting Verification Screen (Steps 19–20)
19. **Create `/auth/awaiting-verification` page** — displays message, resend button with cooldown timer, logout option.
20. **Integrate WebSocket or polling** (optional, low priority) — real-time verification status updates as alternative to page refresh.

### Phase 10: Testing & Monitoring (Steps 21–22)
21. **Add unit tests** for token generation, expiration logic, rate-limiting, and email send.
22. **Add integration tests** for full flow: register → receive email → click link → redirect → access protected resource.

---

## 2. Files to Change

| File Path | Changes | Rationale |
|-----------|---------|-----------|
| `database/migrations/001_create_email_verification_tokens.sql` | **Create new table** with columns: `id`, `user_id` (FK), `email`, `token` (UNIQUE), `expires_at`, `used_at`, `created_at`. | Store token state with expiration and single-use enforcement. |
| `database/migrations/002_add_email_verified_to_users.sql` | **Add columns** `email_verified` (BOOLEAN DEFAULT false), `email_verified_at` (TIMESTAMP NULL). | Track verification status and timestamp per user. |
| `src/config/email.config.ts` | **Create new file** with SendGrid client initialization, template IDs, sender email config. | Centralize email service configuration. |
| `src/templates/emails/verification-email.html` | **Create new file** with HTML email template including token link, expiration notice, brand assets. | Email template content. |
| `src/services/tokenService.ts` | **Create new file** with `generateVerificationToken()`, `verifyEmailToken()`, helper functions. | Encapsulate token logic. |
| `src/services/emailService.ts` | **Create new file** with `sendVerificationEmail()`, email queue management, error handling. | Encapsulate email sending. |
| `src/services/rateLimitService.ts` | **Create new file** (or extend if exists) with `checkResendCooldown()`, `recordResendAttempt()`. | Rate-limit logic for resend requests. |
| `src/routes/auth.routes.ts` | **Modify** POST `/auth/register` — add token generation and async email send. | Trigger email on account creation. |
| `src/routes/auth.routes.ts` | **Add** POST `/auth/resend-verification` — rate-limited resend endpoint. | Self-service resend flow. |
| `src/routes/auth.routes.ts` | **Add** GET `/auth/verify-email?token=<token>` — token validation and user activation. | Email link verification flow. |
| `src/routes/auth.routes.ts` | **Add** GET `/auth/verification-status` — return verification status + cooldown. | Client can render banner + timer. |
| `src/middleware/requireVerifiedEmail.ts` | **Create new file** with middleware checking `user.email_verified`. | Protect routes from unverified users. |
| `src/routes/index.ts` | **Add** `requireVerifiedEmail` middleware to protected routes (e.g., `/dashboard`, `/api/protected`). | Enforce verification on protected resources. |
| `src/pages/auth/VerificationSuccess.tsx` | **Create new file** — success page after token click, shows confirmation message. | Post-verification landing page. |
| `src/pages/auth/AwaitingVerification.tsx` | **Create new file** — intermediate page for unverified users, resend button + timer. | UX for unverified users blocked from protected resources. |
| `src/pages/auth/SignIn.tsx` | **Modify** — conditionally render verification banner if `user.email_verified === false`. | Show prompt on sign-in for unverified users. |
| `src/pages/auth/CreateAccount.tsx` | **No visual changes** — backend sends email; frontend UX unchanged. | Acceptance criteria: form layout unmodified. |
| `src/components/VerificationBanner.tsx` | **Create new file** — reusable banner component with resend button + cooldown timer. | DRY: use in SignIn and AwaitingVerification pages. |
| `src/utils/tokenUtils.ts` | **Create new file** — helper functions for token encoding/decoding, timestamp validation. | Utility functions for token handling. |
| `tests/unit/tokenService.test.ts` | **Create new file** — unit tests for token generation, expiration, single-use. | Token logic tests. |
| `tests/integration/emailVerification.test.ts` | **Create new file** — end-to-end tests: register → email → verify → access protected. | Integration tests. |
| `.env.example` | **Add** `EMAIL_SERVICE=sendgrid`, `SENDGRID_API_KEY`, `VERIFICATION_TOKEN_EXPIRY_HOURS=24`, `RESEND_COOLDOWN_SECONDS=60`. | Config template. |

---

## 3. New Components

### 3.1 Database Tables

#### `email_verification_tokens`
```sql
CREATE TABLE email_verification_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  token VARCHAR(255) NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  used_at TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT now(),
  INDEX(user_id),
  INDEX(token),
  INDEX(expires_at)
);
```

### 3.2 User Table Additions
```sql
ALTER TABLE users
ADD COLUMN email_verified BOOLEAN DEFAULT false,
ADD COLUMN email_verified_at TIMESTAMP NULL;
```

---

### 3.3 Service Functions

#### `tokenService.ts`
```typescript
export async function generateVerificationToken(
  userId: string,
  email: string,
  expiryHours: number = 24
): Promise<{ token: string; expiresAt: Date }> {
  // Generate 32-byte random token, hash with SHA-256
  const rawToken = crypto.randomBytes(32).toString('hex');
  const hashedToken = crypto
    .createHash('sha256')
    .update(rawToken)
    .digest('hex');
  const expiresAt = new Date(Date.now() + expiryHours * 60 * 60 * 1000);

  await db.query(
    `INSERT INTO email_verification_tokens (user_id, email, token, expires_at)
     VALUES ($1, $2, $3, $4)`,
    [userId, email, hashedToken, expiresAt]
  );

  return { token: rawToken, expiresAt };
}

export async function verifyEmailToken(token: string): Promise<{ userId: string; email: string }> {
  const hashedToken = crypto.createHash('sha256').update(token).digest('hex');

  const result = await db.query(
    `SELECT id, user_id, email, expires_at, used_at
     FROM email_verification_tokens
     WHERE token = $1`,
    [hashedToken]
  );

  if (!result.rows.length) throw new Error('INVALID_TOKEN');
  
  const row = result.rows[0];
  
  if (new Date() > new Date(row.expires_at)) throw new Error('TOKEN_EXPIRED');
  if (row.used_at) throw new Error('TOKEN_ALREADY_USED');

  // Mark token as used and update user
  await db.query('BEGIN');
  try {
    await db.query(
      `UPDATE email_verification_tokens SET used_at = now() WHERE id = $1`,
      [row.id]
    );
    await db.query(
      `UPDATE users SET email_verified = true, email_verified_at = now() WHERE id = $1`,
      [row.user_id]
    );
    await db.query('COMMIT');
  } catch (e) {
    await db.query('ROLLBACK');
    throw e;
  }

  return { userId: row.user_id, email: row.email };
}
```

#### `emailService.ts`
```typescript
import sgMail from '@sendgrid/mail';

sgMail.setApiKey(process.env.SENDGRID_API_KEY);

export async function sendVerificationEmail(
  email: string,
  verificationLink: string,
  expiresAt: Date
): Promise<void> {
  const expiresIn = Math.ceil((expiresAt.getTime() - Date.now()) / 1000 / 3600);

  const msg = {
    to: email,
    from: process.env.EMAIL_FROM || 'noreply@app.com',
    subject: 'Verify your email address',
    html: `
      <p>Click the link below to verify your email address (expires in ${expiresIn} hours):</p>
      <a href="${verificationLink}">${verificationLink}</a>
      <p>If you did not create an account, please ignore this email.</p>
    `,
  };

  // Enqueue async send (fire-and-forget with error logging)
  sgMail.send(msg).catch(err => {
    console.error(`Failed to send verification email to ${email}:`, err);
    // TODO: Log to monitoring service (DataDog, Sentry, etc.)
  });
}
```

#### `rateLimitService.ts`
```typescript
export async function checkResendCooldown(userId: string): Promise<{ allowed: boolean; cooldownUntil?: Date }> {
  const lastResend = await redis.get(`resend_cooldown:${userId}`);
  
  if (lastResend) {
    const cooldownEnd = new Date(parseInt(lastResend) + 60 * 1000);
    return { allowed: false, cooldownUntil: cooldownEnd };
  }
  
  return { allowed: true };
}

export async function recordResendAttempt(userId: string): Promise<void> {
  await redis.set(`resend_cooldown:${userId}`, Date.now().toString(), 'EX', 60);
}
```

---

### 3.4 API Endpoints

#### POST `/auth/resend-verification`
```typescript
export async function resendVerificationEmail(req: Request, res: Response) {
  const userId = req.user.id;
  const email = req.user.email;

  // Check cooldown
  const { allowed, cooldownUntil } = await checkResendCooldown(userId);
  if (!allowed) {
    return res.status(429).json({ error: 'COOLDOWN_ACTIVE', cooldownUntil });
  }

  // Generate token
  const { token, expiresAt } = await generateVerificationToken(userId, email);
  const verificationLink = `${process.env.APP_URL}/auth/verify-email?token=${token}`;

  // Send email
  await sendVerificationEmail(email, verificationLink, expiresAt);

  // Record cooldown
  await recordResendAttempt(userId);

  res.json({ cooldownUntil: new Date(Date.now() + 60 * 1000) });
}
```

#### GET `/auth/verify-email?token=<token>`
```typescript
export async function verifyEmail(req: Request, res: Response) {
  const { token } = req.query;

  try {
    const { userId } = await verifyEmailToken(token as string);
    
    // Set success flash or session
    req.session.verificationSuccess = true;
    res.redirect('/auth/verification-success');
  } catch (err) {
    if (err.message === 'TOKEN_EXPIRED' || err.message === 'TOKEN_ALREADY_USED') {
      res.redirect(`/auth/verification-error?reason=${err.message}`);
    } else {
      res.redirect('/auth/verification-error?reason=INVALID_TOKEN');
    }
  }
}
```

#### GET `/auth/verification-status`
```typescript
export async function getVerificationStatus(req: Request, res: Response) {
  const userId = req.user.id;
  const { allowed: resendAllowed, cooldownUntil } = await checkResendCooldown(userId);

  res.json({
    email_verified: req.user.email_verified,
    can_resend: resendAllowed,
    resend_cooldown_until: cooldownUntil || null,
  });
}
```

---

### 3.5 Middleware

#### `requireVerifiedEmail.ts`
```typescript
export function requireVerifiedEmail(req: Request, res: Response, next: NextFunction) {
  if (!req.user) {
    return res.redirect('/auth/login');
  }

  if (!req
