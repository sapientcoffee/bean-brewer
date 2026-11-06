---
id: 02_EXTRACTION
type: extraction
name: 02_EXTRACTION
description: 02_EXTRACTION (2_blind_research)
status: draft
stage: 2_blind_research
generated:
  by: bean-brewer/research
  at: '2026-11-06T16:37:18Z'
sources:
- id: 01_QUESTIONS
  resource: .scratch/coffee-mood-app/01_QUESTIONS.md
stages_completed:
  2_blind_research: bean-brewer/research (2026-11-06T16:37:18Z)
---

# ☕ Blind Cupping: Codebase & Runtime Extraction (`02_EXTRACTION`)

## 1. Technical Invariants & Runtime Extraction
- **Environment**: Linux x86_64 workspace with standard web browsers and headless testing harnesses.
- **Serving Architecture**: Pure client-side static bundle (`app/index.html`, `app/styles.css`, `app/app.js`).
- **Data Layer**: Static immutable lookup tables in `app/data/coffee_moods.js` mapping mood keys (`focus`, `sluggish`, `stressed`, `creative`, `social`, `midnight`) to coffee bean, roast, ratio, temperature, and brew steps.
- **Contract Schema**: Standard JSON schema definition in `contracts/coffee-mood-schema.json`.
- **Testing Seam Availability**: Standard python HTTP/unittest testing harness or node script capable of asserting DOM structure, JSON contract adherence, and logic calculations.
