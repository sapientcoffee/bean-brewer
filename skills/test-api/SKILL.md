---
name: test:api
description: Run local backend API validation scripts
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

# API Validation Test Skill

This skill executes local backend API validation test scripts sequentially to verify correct server routing, authentication, WebSocket handshakes, and wildcard path resolution.

## 1. Objective
To automate integration and regression testing for the backend API, confirming that all endpoints respond according to specification and that communication channels function reliably.

## 2. Prerequisites
- **Application Default Credentials (ADC)**: Ensure that Google Application Default Credentials are configured correctly on your workstation so that test scripts needing GCP services/APIs have permission.
- Ensure the local backend server is running (typically on port `3001`).

## 3. Workflow Steps

Run the following test scripts sequentially:

1. **API Routing and Endpoints (`test_api.mjs`)**:
   - Run `node test_api.mjs` to validate REST endpoints, payload parsing, and standard HTTP response status codes.

2. **Expanded Endpoint Coverage (`test_api2.mjs`)**:
   - Run `node test_api2.mjs` to execute secondary integration tests, edge cases, error handlers, and authenticated routes.

3. **WebSocket Connections (`test_ws.mjs`)**:
   - Run `node test_ws.mjs` to establish WebSocket connections and verify real-time events, subscription handshakes, and duplex message flow.

4. **Wildcard & Catch-all Paths (`test_wildcard.mjs`)**:
   - Run `node test_wildcard.mjs` to assert that wildcard routes and catch-all path fallback logic are handled correctly by the server.

Ensure all scripts execute successfully with a zero exit code.

## 4. Execution Example
Run the complete integration suite:
```bash
agy test:api
```
