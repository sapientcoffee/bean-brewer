---
id: 06_WALKTHROUGH
type: walkthrough
name: 06_WALKTHROUGH
description: 06_WALKTHROUGH (8_verify)
status: draft
stage: 8_verify
generated:
  by: bean-brewer/record
  at: '2026-11-06T16:40:34Z'
sources:
- id: 07_VERIFICATION
  resource: 07_VERIFICATION.md
stages_completed:
  0_triage: cortado/greenfield
  7_tdd: code-implementation
  8_verify: bean-brewer/record (2026-11-06T16:40:34Z)
---

# ☕ Feature Walkthrough: Coffee Mood Selection Web App (`06_WALKTHROUGH`)

## 1. Executive Summary
The **Coffee Mood Selection Web App** connects mental & work states to calibrated specialty coffee extractions.
It provides an interactive mood grid, dynamic sensory pairing cards, real-time dosage & water volume math, and an automated brew timer with phase prompts.

## 2. Interactive Walkthrough & Workflow Verification

### Step 1: Mood Selection
- **Action**: User opens `app/index.html` and selects **🎯 Deep Focus**.
- **Result**: The UI highlights the active card and displays **Washed Colombian Huila** (Medium Roast, AeroPress inverted, 1:14.5 ratio, 90°C) with notes of *Milk Chocolate*, *Red Apple*, and *Toasted Pecan*.

### Step 2: Custom Serving Size & Temperature Scaling
- **Action**: User changes servings to **2 Cups (500ml)** and selects **Flash Chilled (Iced)**.
- **Result**:
  - Coffee dosage automatically recalculates from `17.2g` to `34.5g`.
  - Water volume dynamically partitions into `300ml hot water` (for initial extraction) and `200g ice` (for flash chilling).

### Step 3: Interactive Extraction Timer
- **Action**: User clicks **Start**.
- **Result**:
  - The countdown timer initiates from `02:30`.
  - The status displays **Bloom Phase (CO2 Release)** for the first 45 seconds, switches to **Main Extraction Pour**, and concludes with **Drawdown & Settling**.
  - On completion (`00:00`), phase announces *"☕ Extraction complete! Enjoy your mood cup."*

---

## 3. Local Verification Commands

```bash
# Run the complete unit test suite (53 tests) via agy CLI
agy test /home/robedwards/workspace/bean-brewer

# Open the standalone web application in any browser
xdg-open /home/robedwards/workspace/bean-brewer/app/index.html
```
