Switch to Flow Builder Mode.

Flow Name: Registration

Purpose:
AI-assisted onboarding flow for fintech application.

==================================================
USER BEHAVIOR
==================================================

- Users can browse anonymously.
- Registration is optional.
- Registration enables dashboards and advanced features.

Authentication Methods:
1. Gmail (Google OAuth)
2. Email + password

Minimal Registration:
- Gmail OR email/password

Extended Registration (for special services):
- Birthdate
- Address:
    - Country
    - Postcode
    - Street
    - Line2
- Tax country
- Certificate upload (ID images)

==================================================
UI REQUIREMENTS
==================================================

Two-panel layout:

Left Panel:
- AI assistant
- Responds in detected language
- Explains required data
- Extracts structured fields from free text
- Updates form in real-time

Right Panel:
- Structured editable form
- Inline validation
- Cannot save if invalid

Chat updates form.
Form updates AI context.

==================================================
DATABASE REQUIREMENTS
==================================================

Create /sql/users.sql including:

users table:
- seq (PK)
- create_date
- update_date
- auth_type (gmail | regular)
- email
- password_hash
- given_name
- family_name
- picture
- locale
- google_sub
- address_country
- address_postcode
- address_line1
- address_line2
- birth_date
- tax_country
- certificate1_image
- certificate2_image

Include:
- Indexes
- Constraints
- Nullable rules
- Required field definitions

Also create labels table:
- label_id
- label_name
- local_he
- local_es

==================================================
VALIDATION REQUIREMENTS
==================================================

- Zod schemas
- Email regex validation
- Phone validation
- Age validation (18+ if required)
- Required field enforcement
- AI must NOT perform validation

==================================================
REUSABILITY
==================================================

Flow must be reusable for:
- Different forms
- Different field sets
- Different schemas

Place under:
/ui/flows/registration/

==================================================
OUTPUT REQUIRED
==================================================

1. Architecture plan
2. Folder structure
3. Implementation
4. SQL file
5. Documentation
6. Compliance checklist

Follow mandatory generation process:
- First architecture plan
- Then implementation
- Then compliance check