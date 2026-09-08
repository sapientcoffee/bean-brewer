---
name: git-delivery
description: Provides an emoji-powered, good-practice delivery pipeline to verify code quality, craft conventional atomic commits, and compile premium "What, Why, How" Pull Requests.
---

# 🚀 Skill: Modern Git Delivery Protocol (The Perfect Pour)

Welcome to the **Modern Git Delivery Protocol**! ☕✨
Just like a master barista cleans their machine, double-checks the grind, and serves the perfect cup, a software engineer must clean up debugging crumbs, verify code quality, structure neat atomic commits, and write a stunning Pull Request. 

This skill guides you through the ultimate post-development workflow to deliver features, fixes, and docs with absolute precision, high quality, and a touch of fun! 🎉

---

## 🧹 Step 1: The Leftover Sweeper (No Dust Behind!)
Before staging anything, let's make sure we aren't leaving any diagnostic clutter behind. We don't want our production logs filled with temporary print statements!

*   **Search and Destroy:** Scan your modified files for:
    *   `console.log`, `print()`, `var_dump`, `System.out.println` 🔍
    *   `TODO` placeholders or debug breakpoints (`debugger`, `pdb.set_trace()`, etc.) 🛑
    *   Commented-out blocks of dead code that should be deleted 🧟
*   **The Golden Rule:** Keep your diffs tight and intentional. If it was for debugging, sweep it away! 🧹

---

## 🔬 Step 2: Micro-Atomic Staging (Craft with Care)
A messy, massive single commit with 10 unrelated changes is hard to review and even harder to debug. 

*   **Atomic Commits:** Each commit should do **one logical thing** (e.g., add an interface, fix a validation rule, update documentation).
*   **Stage via Hunks:** Instead of a blind `git add .`, use interactive staging to review your changes block by block:
    ```bash
    git add -p
    ```
    This lets you say `y` (yes) or `n` (no) to each individual code change, ensuring only exactly what you want is staged. 🧐

---

## ✍️ Step 3: Conventional, Emoji-fied Commits
We follow the **Conventional Commits** standard, but we supercharge it with a splash of matching emojis to make our git log readable and vibrant! 🎨

### Commit Structure:
```text
<type>(<scope>): <emoji> <description in active voice>
```

### The Emoji Guide:
*   ✨ `feat`: A new feature (e.g., `feat(ui): ✨ add coffee strength slider`)
*   🐛 `fix`: A bug fix (e.g., `fix(api): 🐛 resolve decimal parsing overflow`)
*   📝 `docs`: Documentation changes (e.g., `docs(readme): 📝 add local dev setup instructions`)
*   ♻️ `refactor`: Restructuring code without changing behavior (e.g., `refactor(db): ♻️ extract connection pooler`)
*   ⚡ `perf`: Performance improvements (e.g., `perf(cache): ⚡ shift to lazy-loading collections`)
*   🧪 `test`: Adding or correcting tests (e.g., `test(auth): 🧪 add JWT validation suite`)
*   🔧 `chore`: Updating build tools, dependencies, or configs (e.g., `chore(deps): 🔧 upgrade lodash to 4.17.21`)

---

## ✈️ Step 4: Pre-Flight Check (Ready for Takeoff)
Never push code that breaks local systems! This saves CI/CD runner minutes and reviewer sanity. 

Before committing and pushing, run your local checks:
1.  **Format Check:** Auto-format code to match styling rules (e.g., `npm run format`, `prettier --write`). 🧼
2.  **Lint Check:** Run the linter to ensure code standards are met (e.g., `npm run lint`, `eslint .`). 🧐
3.  **Local Build:** Ensure the project compiles successfully. 🧱
4.  **Test Suite:** Run unit and integration tests (e.g., `npm test`, `pytest`). All tests must turn green! 🟢

---

## 🔀 Step 5: Linear History Alignment (Smooth Rebase)
To avoid messy merge commits and preserve a beautiful, clean linear history, always rebase onto your target branch before pushing.

```bash
# Fetch latest remote changes
git fetch origin

# Rebase your feature branch on top of main
git rebase origin/main
```
If there are any merge conflicts, resolve them block-by-block locally so they are already solved before your PR is opened! 🛠️

---

## 📄 Step 6: The "What, Why, How" PR Template
When you open a Pull Request using the GitHub CLI (`gh pr create`), use our premium, high-fidelity PR template. This makes your reviewers' lives wonderful and speeds up approvals! 🚀

### Pull Request Description Markdown Template:
```markdown
## ☕ The Perfect Pour: Pull Request Summary

### 🔍 What?
*Provide a concise, 1-2 sentence description of what this PR does.*

### 🎯 Why?
*Explain the motivation behind these changes. What problem does this solve, or what business/architectural value does it add?*

### 🛠️ How?
*Break down your technical implementation details:*
- **Component A:** Modified to...
- **Database/Schema:** Added...
- **API Surface:** Exposed endpoint...

### 🧪 Verification & Proof
*Detail how these changes were tested:*
- [ ] Unit tests passed green 🟢
- [ ] Manual walkthrough completed with the `record` command 📹
*Attach terminal playback links or screenshot embeds here:*
*Format: plans/feature/<slug>/walkthrough.gif (Use relative paths without leading slash for GH rendering!)*

### 🎉 Fun Fact of the Brew!
*Share a fun engineering, coffee, or code fact to put a smile on your reviewer's face!*
```

---

## 🚀 Step 7: Push & Create PR with gh CLI
The terminal is your canvas! Use `gh` over standard git commands to quickly push your changes and open your PR:

```bash
# Push your branch to remote
git push origin <your-branch-name>

# Create the pull request interactively using the template above
gh pr create --body-file - --web
```
*(Tip: Use `--web` to do a final visual check on GitHub before clicking merge!)*

Now sit back, take a sip of coffee, and watch the green checkmarks roll in! ☕🤖✨
