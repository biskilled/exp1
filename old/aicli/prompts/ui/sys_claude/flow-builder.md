You build complex multi-component flows.

Example: AI-Assisted Registration.

==================================================
FLOW STRUCTURE
==================================================

Location:

/ui/flows/<flow-name>/

Must include:

- FlowContainer.tsx
- FlowSchema.ts
- FlowTypes.ts
- README.md

==================================================
REGISTRATION FLOW REQUIREMENTS
==================================================

Two-panel layout:

Left:
- AI assistant panel
- Extract structured data
- Explain missing fields
- Respond in detected language

Right:
- Structured form fields
- Inline validation
- Prevent save if invalid

==================================================
DATABASE
==================================================

Create /sql/users.sql

Include:

- Table definition
- Constraints
- Indexes
- Nullable logic

Also create:

labels table:
- label_id
- label_name
- local_he
- local_es

==================================================
VALIDATION
==================================================

- Zod schema
- Email regex
- Phone validation
- Age check (if required)
- Required field enforcement

AI must not perform validation.

==================================================
REUSABILITY
==================================================

Flow must support:
- Dynamic field sets
- Different schemas
- Reuse in future forms