# ☕ Bean-Brewer

> High-Pressure Implementation Forge: Technical extraction, architectural contracts, TDD code loops, and Git PR delivery (Stages 3–9).

---

## ☕ Why "The Brewer"? (The Metaphor)

In specialty coffee brewing, the espresso machine is where preparation turns into reality. Under 9 bars of controlled pressure and calibrated temperature, hot water is forced through tamped grounds to extract oils, soluble flavors, and dense golden crema.

In software engineering, **`bean-brewer`** is the execution forge:
- It takes an approved `02_PRD.md` (roasted by `bean-roaster` or milled by `bean-grinder`).
- Under rigorous test-driven discipline, it extracts existing codebase contracts, designs target specifications (`04_SPEC.md`), slices tasks into vertical units (`05_PLAN.md`), and unleashes autonomous engineering subagents to write and audit code (`app_build/`).
- It captures verifiable terminal walkthroughs (`/record`) and packages atomic, conventional commits into rich GitHub Pull Requests.

---

## 🏛️ Origin & Architectural Rationale

### Spawned from `bean-to-cup`
**`bean-brewer`** was extracted from the monolithic [`bean-to-cup`](https://github.com/sapientcoffee/bean-to-cup) repository as part of a modular decomposition of the Antigravity barista swarm.

### Why Decompose?
1. **Developer & CI/CD Isolation:** Software engineers and automated execution loops only need the implementation, testing, and git delivery suite—without the overhead of product discovery or incident management plugins.
2. **Lean Plugin Footprint:** Decouples 12 heavy engineering skills, 8 subagents, terminal recorders, and git hook scripts from the rest of the workspace.
3. **Strict Contract Handoffs:** Consumes standardized `02_PRD.md` files as an immutable contract, guaranteeing that execution cannot begin without validated requirements.
4. **Independent Tooling Evolution:** Worktree management, testing harnesses, and terminal recording engines can evolve and upgrade without risking stability in discovery or monitoring tools.

---

## 🚀 Capabilities & Stages Reference (Stages 3–9)

| Stage | Skill / Agent | Description |
| :---: | :--- | :--- |
| **3** | **`research` (`skills/research`)** | Blind, factual codebase analysis. Extracts existing models, routes, and schemas into `03_EXTRACTION.md`. |
| **4** | **`@architect` (`agents/system-design.md`)** | System architecture specification. Emits physical schema contracts in `contracts/` and documents target architecture in `04_SPEC.md`. |
| **5** | **`@architect` (`skills/sync`)** | Cuts vertical implementation slices, performs dependency mapping in `05_PLAN.md`, and synchronizes tasks to GitHub issues. |
| **6** | **Human Review Gate (🛑)** | Halts execution to present the specification, contracts, and plan to the user for explicit approval. |
| **7** | **`@engineer` & `@auditor`** | Autonomous TDD execution loops: `generate-code` writes code slices, `audit-code` verifies quality, `test-api` validates backend endpoints, and `build-production` verifies production builds. |
| **8** | **`record` (`skills/record`)** | Captures terminal interactions and compiles them into animated GIFs and `.cast` files for verifiable visual proof in `08_WALKTHROUGH.md`. |
| **9** | **`git-delivery` & `github-workflow`** | Uses git worktrees (`worktree`) and GitHub CLI (`gh`) to create atomic conventional commits and raise rich "What, Why, How" Pull Requests. |
| **Misc** | **`archive`, `motivate`** | Moves spent grounds into `./plans/archive/` and delivers coffee-themed encouragement. |

---

## 🤖 Barista Engineering Swarm

`bean-brewer` provides 8 specialized subagents ready for dispatch:
- **`@architect`**: System design and physical contract modeling.
- **`@engineer`**: Test-driven implementation and code generation.
- **`@auditor`**: Quality verification and regression testing.
- **`@code-review`**: Code inspection and standards auditing.
- **`@scout`**: Blind AST exploration and fact gathering.
- **`@codebase-analyzer`**: Static analysis and architectural topology mapping.
- **`@context-mapping`**: Bounded context and dependency analysis.
- **`@pattern-recognition`**: Design pattern and architectural smell identification.

---

## 🔄 Delivery Workflow

```mermaid
graph TD
    PRD[02_PRD.md from bean-roaster] --> Stage3["Stage 3: /research<br/>(03_EXTRACTION.md)"]
    Stage3 --> Stage4["Stage 4: @architect<br/>(04_SPEC.md & contracts/)"]
    Stage4 --> Stage5["Stage 5: @architect<br/>(05_PLAN.md & Vertical Slices)"]
    Stage5 --> Gate{Stage 6: Human Gate}
    Gate -->|Approved| Stage7["Stage 7: TDD Loop<br/>(@engineer + @auditor)"]
    Stage7 --> Stage8["Stage 8: /record<br/>(Asciinema Walkthrough GIF)"]
    Stage8 --> Stage9["Stage 9: git-delivery<br/>(Worktrees + gh PR)"]
    
    Stage5 -.->|Sync Kanban| Cup["bean-cup (visual-dashboard.html)"]
    Stage7 -.->|Task Updates| Cup
```

---

## 🔌 Decoupled Telemetry

`bean-brewer` includes `scripts/sync_dashboard_if_available.py`:
- Automatically updates `visual-dashboard.html` in `bean-cup` if installed.
- Silently succeeds if `bean-cup` is absent, allowing pure standalone headless execution in CI or isolated environments.

---

## 📦 Installation

```bash
# Install to local Antigravity plugin registry
./install.sh

# Or install via agy CLI
agy plugin install .
```

---

## 📜 License
Apache-2.0 - Copyright 2026 Google LLC.
