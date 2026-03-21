You build reusable UI modules.

==================================================
MODULE STRUCTURE
==================================================

Each module must exist under:

/ui/modules/<module-name>/

Must include:

- Component.tsx
- schema.ts
- types.ts
- translations.ts
- README.md
- index.ts

==================================================
REQUIREMENTS
==================================================

1. Use React Hook Form.
2. Use Zod schema.
3. Support English and Hebrew.
4. Be RTL compatible.
5. Be mobile responsive.
6. Expose:
   - getValue()
   - setValue()
   - validate()
   - onChange()

==================================================
README MUST INCLUDE
==================================================

- Purpose
- Props
- Validation rules
- Events
- RTL considerations
- LLM Prompt Description section

==================================================
FORBIDDEN
==================================================

- Hardcoded strings
- Inline validation logic
- Left/right fixed styling
- Business logic inside the component