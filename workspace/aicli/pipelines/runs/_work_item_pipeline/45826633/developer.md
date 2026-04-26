# Developer

# Email Verification Feature — Complete Implementation

I'll implement this as a complete, production-ready feature based on the architect's plan. I'll use **Node.js/Express + TypeScript + PostgreSQL (with raw SQL migrations) + AWS SES** as the stack, inferring conventions from the architect's file paths.

---

## Database Migrations

### `database/migrations/001_add_mng_verification_tokens.sql`

```sql
-- Migration 001: Create mng_verification_tokens table
-- Stores cryptographically secure, single-use email verification tokens

CREATE TABLE IF NOT EXISTS mng_verification_tokens (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token       VARCHAR(64) NOT NULL,
  expires_at  TIMESTAMP   NOT NULL,
  redeemed_at TIMESTAMP   NULL DEFAULT NULL,
  created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_mng_verification_tokens_token UNIQUE (token)
);

CREATE INDEX IF NOT EXISTS idx_mng_verification_tokens_token
  ON mng_verification_tokens (token);

CREATE INDEX IF NOT EXISTS idx_mng_verification_tokens_user_id
  ON mng_verification_tokens (user_id);

CREATE INDEX IF NOT EXISTS idx_mng_verification_tokens_expires_at
  ON mng_verification_tokens (expires_at);

COMMENT ON TABLE mng_verification_tokens IS
  'Single-use email verification tokens with 24-hour expiry';
COMMENT ON COLUMN mng_verification_tokens.redeemed_at IS
  'NULL = unused/valid; non-NULL = already used (soft invalidation)';
```

---

### `database/migrations/002_add_mng_resend_cooldown.sql`

```sql
-- Migration 002: Create mng_resend_cooldown table
-- Enforces minimum 60-second cooldown between resend requests per user

CREATE TABLE IF NOT EXISTS mng_resend_cooldown (
  id             UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  last_resend_at TIMESTAMP NOT NULL DEFAULT NOW(),
  resend_count   INTEGER   NOT NULL DEFAULT 1,
  created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMP NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_mng_resend_cooldown_user_id UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS idx_mng_resend_cooldown_user_id
  ON mng_resend_cooldown (user_id);

COMMENT ON TABLE mng_resend_cooldown IS
  'Tracks last verification email resend time per user for rate-limiting';
COMMENT ON COLUMN mng_resend_cooldown.resend_count IS
  'Total lifetime resend requests; reserved for future hard-cap enforcement';
```

---

### `database/migrations/003_add_users_verified_at.sql`

```sql
-- Migration 003: Add verified_at to users table and backfill existing users
-- Pre-existing users are grandfathered in as verified (verified_at = created_at)

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP NULL DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_users_verified_at
  ON users (verified_at)
  WHERE verified_at IS NULL; -- partial index: fast lookup of unverified users

-- Backfill: all existing users are considered verified
-- created_at used to preserve chronological accuracy; falls back to NOW()
UPDATE users
  SET verified_at = COALESCE(created_at, NOW())
WHERE verified_at IS NULL;

COMMENT ON COLUMN users.verified_at IS
  'NULL = unverified (pending email confirmation); non-NULL = verified timestamp';
```

---

### `database/migrations/index.ts`

```typescript
// database/migrations/index.ts
// Migration runner — executes SQL migration files in order, tracking state in a
// schema_migrations table. Each migration is idempotent (IF NOT EXISTS / IF EXISTS guards).

import fs from 'fs';
import path from 'path';
import { Pool } from 'pg';

const MIGRATIONS_DIR = path.resolve(__dirname);

const MIGRATION_FILES = [
  '001_add_mng_verification_tokens.sql',
  '002_add_mng_resend_cooldown.sql',
  '003_add_users_verified_at.sql',
];

async function ensureMigrationsTable(pool: Pool): Promise<void> {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version    VARCHAR(255) PRIMARY KEY,
      applied_at TIMESTAMP    NOT NULL DEFAULT NOW()
    )
  `);
}

async function getAppliedMigrations(pool: Pool): Promise<Set<string>> {
  const result = await pool.query<{ version: string }>(
    'SELECT version FROM schema_migrations ORDER BY version ASC'
  );
  return new Set(result.rows.map((r) => r.version));
}

export async function runMigrations(pool: Pool): Promise<void> {
  await ensureMigrationsTable(pool);
  const applied = await getAppliedMigrations(pool);

  for (const file of MIGRATION_FILES) {
    if (applied.has(file)) {
      console.log(`[migrations] Skipping ${file} (already applied)`);
      continue;
    }

    const filePath = path.join(MIGRATIONS_DIR, file);
    const sql = fs.readFileSync(filePath, 'utf-8');

    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      await client.query(sql);
      await client.query(
        'INSERT INTO schema_migrations (version) VALUES ($1)',
        [file]
      );
      await client.query('COMMIT');
      console.log(`[migrations] Applied ${file}`);
    } catch (err) {
      await client.query('ROLLBACK');
      console.error(`[migrations] Failed to apply ${file}:`, err);
      throw err;
    } finally {
      client.release();
    }
  }

  console.log('[migrations] All migrations up to date');
}
```

---

## Backend Models

### `backend/src/models/User.ts`

```typescript
// backend/src/models/User.ts
// Extend the existing User model with the new verified_at field.
// IMPORTANT: Only the addition is shown — merge this into your existing model file.

export interface User {
  id: string;
  email: string;
  password_hash: string;
  created_at: Date;
  updated_at: Date;
  // === NEW FIELD ===
  verified_at: Date | null; // NULL = unverified; Date = verified timestamp
}

// Type guard: checks if a user has completed email verification
export function isVerified(user: Pick<User, 'verified_at'>): boolean {
  return user.verified_at !== null && user.verified_at !== undefined;
}
```

---

### `backend/src/models/MngVerificationToken.ts`

```typescript
// backend/src/models/MngVerificationToken.ts

export interface MngVerificationToken {
  id: string;
  user_id: string;
  token: string;
  expires_at: Date;
  redeemed_at: Date | null;
  created_at: Date;
}

// Represents an active (unredeemed, unexpired) token
export interface ActiveVerificationToken extends MngVerificationToken {
  redeemed_at: null;
}

export function isExpired(token: MngVerificationToken): boolean {
  return token.expires_at <= new Date();
}

export function isRedeemed(token: MngVerificationToken): boolean {
  return token.redeemed_at !== null;
}

export function isValid(token: MngVerificationToken): boolean {
  return !isExpired(token) && !isRedeemed(token);
}
```

---

### `backend/src/models/MngResendCooldown.ts`

```typescript
// backend/src/models/MngResendCooldown.ts

export interface MngResendCooldown {
  id: string;
  user_id: string;
  last_resend_at: Date;
  resend_count: number;
  created_at: Date;
  updated_at: Date;
}

export const RESEND_COOLDOWN_SECONDS = 60;

// Returns number of seconds remaining in cooldown; 0 if cooldown has passed
export function getCooldownRemaining(cooldown: MngResendCooldown | null): number {
  if (!cooldown) return 0;

  const elapsed = Math.floor(
    (Date.now() - new Date(cooldown.last_resend_at).getTime()) / 1000
  );
  const remaining = RESEND_COOLDOWN_SECONDS - elapsed;
  return remaining > 0 ? remaining : 0;
}
```

---

## Database Layer

### `backend/src/database/index.ts`

```typescript
// backend/src/database/index.ts
// Central database connection pool. Modify existing file to export the pool.

import { Pool } from 'pg';

// Validate required env vars at startup
const required = ['DATABASE_URL'];
for (const key of required) {
  if (!process.env[key]) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
}

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 5_000,
  ssl: process.env.NODE_ENV === 'production'
    ? { rejectUnauthorized: true }
    : false,
});

pool.on('error', (err) => {
  console.error('[db] Unexpected pool error:', err);
});

// Thin query wrapper with logging in non-production environments
export async function query<T extends object = Record<string, unknown>>(
  text: string,
  params?: unknown[]
): Promise<T[]> {
  const start = Date.now();
  try {
    const result = await pool.query<T>(text, params);
    if (process.env.NODE_ENV !== 'production') {
      console.debug(`[db] query (${Date.now() - start}ms):`, text.slice(0, 80));
    }
    return result.rows;
  } catch (err) {
    console.error('[db] Query error:', { text, params, err });
    throw err;
  }
}

// For transactions requiring atomic operations
export { Pool } from 'pg';
```

---

## Services

### `backend/src/services/TokenService.ts`

```typescript
// backend/src/services/TokenService.ts
// Handles all verification token lifecycle: generation, validation, redemption.

import crypto from 'crypto';
import { pool, query } from '../database';
import {
  MngVerificationToken,
  isExpired,
  isRedeemed,
} from '../models/MngVerificationToken';

const TOKEN_EXPIRY_HOURS = 24;
const TOKEN_BYTES = 32; // 256-bit = 64 hex chars

export class TokenService {
  /**
   * Generates a new cryptographically secure token for the given user.
   * Invalidates any existing unused tokens for the user first (one active token at a time).
   */
  static async generateToken(userId: string): Promise<MngVerificationToken> {
    const token = crypto.randomBytes(TOKEN_BYTES).toString('hex');
    const expiresAt = new Date(Date.now() + TOKEN_EXPIRY_HOURS * 60 * 60 * 1000);

    const client = await pool.connect();
    try {
      await client.query('BEGIN');

      // Invalidate existing unused tokens for this user
      await client.query(
        `UPDATE mng_verification_tokens
         SET redeemed_at = NOW()
         WHERE user_id = $1 AND redeemed_at IS NULL`,
        [userId]
      );

      // Insert new token
      const result = await client.query<MngVerificationToken>(
        `INSERT INTO mng_verification_tokens (user_id, token, expires_at)
         VALUES ($1, $2, $3)
         RETURNING *`,
        [userId, token, expiresAt]
      );

      await client.query('COMMIT');
      return result.rows[0];
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }

  /**
   * Validates and redeems a token.
   * Returns the associated user_id on success.
   * Throws descriptive errors for expired/used/invalid tokens.
   */
  static async redeemToken(
    tokenString: string
  ): Promise<{ userId: string; token: MngVerificationToken }> {
    const rows = await query<MngVerificationToken>(
      `SELECT * FROM mng_verification_tokens WHERE token = $1 LIMIT 1`,
      [tokenString]
    );

    if (rows.length === 0) {
      throw new TokenNotFoundError('Verification token not found');
    }

    const tokenRecord = rows[0];

    if (isRedeemed(tokenRecord)) {
      throw new TokenAlreadyUsedError('This verification link has already been used');
    }

    if (isExpired(tokenRecord)) {
      throw new TokenExpiredError('This verification link has expired');
    }

    // Mark as redeemed and activate the user — must be atomic
    const client = await pool.connect();
    try {
      await client.query('BEGIN');

      await client.query(
        `UPDATE mng_verification_tokens SET redeemed_at = NOW() WHERE id = $1`,
        [tokenRecord.id]
      );

      await client.query(
        `UPDATE users SET verified_at = NOW() WHERE id = $1 AND verified_at IS NULL`,
        [tokenRecord.user_id]
      );

      await client.query('COMMIT');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }

    return { userId: tokenRecord.user_id, token: tokenRecord };
  }

  /**
   * Looks up active (unredeemed, unexpired) tokens for a user.
   * Used to check if a user already has a pending token.
   */
  static async getActiveToken(userId: string): Promise<MngVerificationToken | null> {
    const rows = await query<MngVerificationToken>(
      `SELECT * FROM mng_verification_tokens
       WHERE user_id = $1
         AND redeemed_at IS NULL
         AND expires_at > NOW()
       ORDER BY created_at DESC
       LIMIT 1`,
      [userId]
    );
    return rows[0] ?? null;
  }
}

// Typed errors for precise HTTP status mapping in route handlers
export class TokenNotFoundError extends Error {
  readonly code = 'TOKEN_NOT_FOUND';
  constructor(message: string) {
    super(message);
    this.name = 'TokenNotFoundError';
  }
}

export class TokenExpiredError extends Error {
  readonly code = 'TOKEN_EXPIRED';
  constructor(message: string) {
    super(message);
    this.name = 'TokenExpiredError';
  }
}

export class TokenAlreadyUsedError extends Error {
  readonly code = 'TOKEN_ALREADY_USED';
  constructor(message: string) {
    super(message);
    this.name = 'TokenAlreadyUsedError';
  }
}
```

---

### `backend/src/services/EmailService.ts`

```typescript
// backend/src/services/EmailService.ts
// Abstraction over email delivery. Currently implements AWS SES.
// Swap the inner implementation to switch providers without touching callers.

import {
  SESClient,
  SendEmailCommand,
  SendEmailCommandInput,
} from '@aws-sdk/client-ses';
import {
  loadVerificationEmailHtml,
  loadVerificationEmailText,
} from '../templates/emailTemplates';

// Validate required env vars once at module load
const requiredEnvVars = [
  'AWS_SES_REGION',
  'AWS_
