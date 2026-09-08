---
name: build:production
description: Target and build the application for production
---

<!--
Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Production Build Skill

This skill performs codebase quality linters and compiles the application into highly optimized production-ready static assets and server artifacts.

## 1. Objective
To enforce strict static analysis and compile frontend and backend deliverables, ensuring no quality warnings or compile errors exist before shipping to staging or production targets.

## 2. Workflow Steps

1. **Pre-build Quality Checks (Linting)**:
   - Run `npm run lint` to evaluate code formatting, style compliance, and static typing checks.
   - **CRITICAL**: If the linter reports errors, halt the build and address the syntax/styling issues immediately before proceeding.

2. **Production Compilation**:
   - Execute `npm run build` to package frontend source files into optimized distribution bundles (typically located under `./dist` or `./build`).
   - Confirm that the asset bundler completes with a zero exit code and outputs asset size details.

## 3. Verification & Deliverables
- Verify that compiled static bundles are successfully written to the project's target build folder.
- Inspect build logs for any bundle-size warnings or missing module errors.

## 4. Execution Example
Build the project for production:
```bash
agy build:production
```
