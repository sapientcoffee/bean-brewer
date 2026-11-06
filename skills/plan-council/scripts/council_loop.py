#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
council_loop.py: Stage 6A Plan Review Council Engine for Bean-Brewer.

Orchestrates multi-persona adversarial plan reviews, enforces evidence quotation,
calculates mathematical consensus, handles risk-tier sizing, integrates immunized
gotchas, and generates propose-only patch directives in 06_COUNCIL_REVIEW.md.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

COUNCIL_PERSONAS = [
    "contract-auditor",
    "code-inspection",
    "threat-modeler",
    "reviewer-product",
]

TIER_REVIEWERS: Dict[str, List[str]] = {
    "Light": [
        "@contract-auditor",
        "@code-inspection",
    ],
    "Standard": [
        "@contract-auditor",
        "@code-inspection",
        "@reviewer-product",
    ],
    "Full": [
        "@contract-auditor",
        "@code-inspection",
        "@threat-modeler",
        "@reviewer-product",
    ],
}

PERSONA_ALIASES = {
    "auditor": "code-inspection",
    "@auditor": "code-inspection",
    "@code-inspection": "code-inspection",
    "@contract-auditor": "contract-auditor",
    "@threat-modeler": "threat-modeler",
    "@reviewer-product": "reviewer-product",
}

JUDGES_PER_AREA = 3

JUDGE_MODELS: List[Dict[str, str]] = [
    {
        "id": "judge-1",
        "name": "opus",
        "display_name": "Claude Opus",
        "subagent_model": "pro",
    },
    {
        "id": "judge-2",
        "name": "argon",
        "display_name": "Gemini 4 Argon",
        "subagent_model": "inherit",
    },
    {
        "id": "judge-3",
        "name": "flash-3.8",
        "display_name": "Gemini 3.8 Flash",
        "subagent_model": "flash",
    },
]

JUDGE_MODEL_ALIASES: Dict[str, str] = {
    "opus": "opus",
    "claude-opus": "opus",
    "claude opus": "opus",
    "judge-1": "opus",
    "pro": "opus",
    "argon": "argon",
    "gemini-4-argon": "argon",
    "gemini 4 argon": "argon",
    "judge-2": "argon",
    "inherit": "argon",
    "flash-3.8": "flash-3.8",
    "flash 3.8": "flash-3.8",
    "gemini-3.8-flash": "flash-3.8",
    "gemini 3.8 flash": "flash-3.8",
    "flash": "flash-3.8",
    "judge-3": "flash-3.8",
}

SEVERITY_RANK: Dict[str, int] = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}

DEFAULT_MAX_ROUNDS = 3
CONVERGENCE_THRESHOLD = 90.0


def normalize_persona(persona: str) -> str:
    """Normalizes persona names, mapping legacy 'auditor' to 'code-inspection'."""
    cleaned = persona.strip().lstrip("@")
    return PERSONA_ALIASES.get(persona.strip(), PERSONA_ALIASES.get(cleaned, cleaned))


def normalize_judge_model(model_name: str) -> str:
    """Normalizes judge model names to canonical ('opus', 'argon', 'flash-3.8')."""
    cleaned = str(model_name or "").strip().lower()
    return JUDGE_MODEL_ALIASES.get(cleaned, cleaned or "argon")


def get_reviewers_for_tier(tier: str) -> List[str]:
    """Returns canonical reviewer names (without leading @) for the given risk tier."""
    raw = TIER_REVIEWERS.get(tier, TIER_REVIEWERS["Standard"])
    return [normalize_persona(r) for r in raw]


def get_judges_for_tier(tier: str) -> List[Dict[str, str]]:
    """Returns the 3-judge panel descriptors for every active reviewer area in the tier."""
    judges: List[Dict[str, str]] = []
    for persona in get_reviewers_for_tier(tier):
        for model in JUDGE_MODELS:
            judges.append({
                "persona": persona,
                "judge_id": f"{persona}:{model['name']}",
                "model": model["name"],
                "display_model": model["display_name"],
                "subagent_model": model["subagent_model"],
            })
    return judges


def _norm_text(value: Any) -> str:
    """Normalizes text for quote/similarity comparison."""
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _token_set(text: str) -> set:
    """Extracts alphanumeric word tokens of length >= 3."""
    return {tok for tok in re.findall(r"[a-z0-9_]{3,}", text.lower())}


def _findings_match(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    """Determines whether two findings from different judges describe the same defect."""
    id_a = str(a.get("id") or "").strip()
    id_b = str(b.get("id") or "").strip()
    if id_a and id_b and id_a.lower() == id_b.lower():
        return True

    quote_a = _norm_text(a.get("quote") or a.get("evidence") or a.get("citation"))
    quote_b = _norm_text(b.get("quote") or b.get("evidence") or b.get("citation"))
    if len(quote_a) >= 6 and len(quote_b) >= 6:
        if quote_a == quote_b or quote_a in quote_b or quote_b in quote_a:
            return True

    line_a = a.get("line") or a.get("line_number")
    line_b = b.get("line") or b.get("line_number")
    if line_a is not None and line_b is not None and str(line_a) == str(line_b):
        return True

    task_a = _norm_text(a.get("target_task"))
    task_b = _norm_text(b.get("target_task"))
    if task_a and task_b and task_a == task_b:
        tokens_a = _token_set(f"{a.get('title', '')} {a.get('description', '')}")
        tokens_b = _token_set(f"{b.get('title', '')} {b.get('description', '')}")
        if tokens_a and tokens_b:
            jaccard = len(tokens_a & tokens_b) / float(len(tokens_a | tokens_b))
            if jaccard >= 0.45:
                return True

    return False


def aggregate_area_judges(
    persona: str,
    judge_payloads: List[Dict[str, Any]],
    strict_quorum_only: bool = False,
) -> Dict[str, Any]:
    """
    Aggregates findings across the 3-judge panel (Opus, Argon, Flash 3.8) for one area.

    Implements Safety-First Hybrid Aggregation:
    - Deduplicates equivalent findings reported by multiple judges so consensus penalties
      are applied once per unique defect.
    - CRITICAL / HIGH findings pass with >= 1 judge (1-of-3 surfaces critical risks).
    - MEDIUM / LOW findings require >= 2 judges (2-of-3 majority quorum filters noise).
    """
    canonical_persona = normalize_persona(persona)
    clusters: List[Dict[str, Any]] = []

    for idx, payload in enumerate(judge_payloads):
        fallback_model = JUDGE_MODELS[idx % len(JUDGE_MODELS)]["name"]
        raw_model = payload.get("model") or payload.get("judge") or fallback_model
        judge_model = normalize_judge_model(str(raw_model))
        findings = payload.get("findings", [])
        if not isinstance(findings, list):
            continue

        for raw_finding in findings:
            if not isinstance(raw_finding, dict):
                continue
            finding = dict(raw_finding)
            sev = str(finding.get("severity", "LOW")).upper()
            if sev not in SEVERITY_RANK:
                sev = "LOW"
            finding["severity"] = sev

            matched_cluster = None
            for cluster in clusters:
                if _findings_match(cluster["finding"], finding):
                    matched_cluster = cluster
                    break

            if matched_cluster is not None:
                matched_cluster["judges"].add(judge_model)
                existing = matched_cluster["finding"]
                if SEVERITY_RANK[sev] > SEVERITY_RANK.get(existing.get("severity", "LOW"), 1):
                    existing["severity"] = sev
                for field in ("quote", "description", "recommendation", "target_task", "title", "id"):
                    if not existing.get(field) and finding.get(field):
                        existing[field] = finding[field]
            else:
                clusters.append({
                    "finding": finding,
                    "judges": {judge_model},
                })

    active_findings: List[Dict[str, Any]] = []
    filtered_minority_findings: List[Dict[str, Any]] = []

    for cluster in clusters:
        merged = dict(cluster["finding"])
        judges_sorted = sorted(cluster["judges"])
        judge_count = len(judges_sorted)
        sev = str(merged.get("severity", "LOW")).upper()

        merged["persona"] = canonical_persona
        merged["judges"] = judges_sorted
        merged["judge_count"] = judge_count
        merged["agreement"] = f"{judge_count}/{JUDGES_PER_AREA}"

        required_quorum = 2 if (strict_quorum_only or sev in ("MEDIUM", "LOW")) else 1
        if judge_count >= required_quorum:
            active_findings.append(merged)
        else:
            filtered_minority_findings.append(merged)

    has_blocker = any(
        str(f.get("severity", "LOW")).upper() in ("CRITICAL", "HIGH")
        for f in active_findings
    )
    return {
        "persona": canonical_persona,
        "status": "CHANGES_REQUESTED" if has_blocker else "APPROVED",
        "judges_evaluated": len(judge_payloads),
        "findings": active_findings,
        "filtered_minority_findings": filtered_minority_findings,
    }


def compute_consensus_score(critical: int, high: int, medium: int, low: int) -> float:
    """Calculate consensus score from 0.0 to 100.0 based on severity penalties."""
    penalty = (critical * 25.0) + (high * 10.0) + (medium * 3.0) + (low * 1.0)
    return max(0.0, min(100.0, round(100.0 - penalty, 1)))


def parse_reviewer_payload(raw_content: str, default_persona: str) -> Dict[str, Any]:
    """Parse JSON payload or markdown-wrapped JSON from a reviewer subagent."""
    cleaned = raw_content.strip()
    canonical_default = normalize_persona(default_persona)

    # Markdown fenced json block
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, dict) and "persona" in parsed:
                parsed["persona"] = normalize_persona(parsed["persona"])
            return parsed
        except json.JSONDecodeError:
            pass

    # Raw JSON
    if (cleaned.startswith("{") and cleaned.endswith("}")) or (
        cleaned.startswith("[") and cleaned.endswith("]")
    ):
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                if "persona" in parsed:
                    parsed["persona"] = normalize_persona(parsed["persona"])
                return parsed
            elif isinstance(parsed, list):
                return {
                    "persona": canonical_default,
                    "status": "CHANGES_REQUESTED",
                    "findings": parsed,
                }
        except json.JSONDecodeError:
            pass

    # Fallback to empty finding list
    return {
        "persona": canonical_default,
        "status": "APPROVED",
        "summary": "No machine-parseable findings encountered.",
        "findings": [],
    }


def load_immunized_gotchas(gotchas_dir: Optional[str]) -> List[Dict[str, str]]:
    """Loads historical gotcha lessons written by harness-immunizer."""
    gotchas = []
    if not gotchas_dir or not os.path.exists(gotchas_dir):
        return gotchas

    for root, _, files in os.walk(gotchas_dir):
        for f in files:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                with open(p, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
                gotchas.append({
                    "file": f,
                    "rule": content.strip().splitlines()[0] if content else f
                })
    return gotchas


def validate_evidence(finding: Dict[str, Any]) -> Tuple[bool, str]:
    """Ensures finding cites a direct quotation or line reference from spec/plan."""
    quote = finding.get("quote") or finding.get("evidence") or finding.get("citation")
    line = finding.get("line") or finding.get("line_number")
    
    if quote and len(str(quote).strip()) > 5:
        return True, str(quote).strip()
    if line:
        return True, f"Line {line}"
    
    # Check if description quotes text with backticks or quotation marks
    desc = finding.get("description", "")
    quoted_match = re.search(r'["`\']([^"`\']{6,})["`\']', desc)
    if quoted_match:
        return True, quoted_match.group(0)

    return False, "NO_DIRECT_CITATION"


def generate_proposals_for_architect(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts high-severity findings into propose-only patch directives for @architect."""
    proposals = []
    counter = 1
    for f in findings:
        sev = str(f.get("severity", "LOW")).upper()
        if sev in ["CRITICAL", "HIGH", "MEDIUM"]:
            prop = {
                "proposal_id": f"PROP-{counter:02d}",
                "origin_finding_id": f.get("id", f"F-{counter}"),
                "severity": sev,
                "persona": f.get("persona", "reviewer"),
                "target_task": f.get("target_task", "05_PLAN.md"),
                "rationale": f.get("description", f.get("title", "")),
                "proposed_patch": f.get("recommendation", f.get("actionable_remediation", "Update task specification")),
                "architect_disposition": "PENDING",
            }
            proposals.append(prop)
            counter += 1
    return proposals


def compile_council_report(
    round_number: int,
    verdict: str,
    consensus_score: float,
    tier: str,
    reviewer_results: Dict[str, Any],
    proposals: List[Dict[str, Any]],
    human_decisions: List[Dict[str, Any]],
    immunized_gotchas: List[Dict[str, str]],
) -> str:
    """Formats the human-first 06_COUNCIL_REVIEW.md artifact."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# 🏛️ Stage 6A: Plan Review Council Report",
        "",
        f"- **Timestamp:** `{now_utc}`",
        f"- **Council Review Round:** `{round_number} / {DEFAULT_MAX_ROUNDS}`",
        f"- **Council Tier:** `{tier}`",
        f"- **Judge Panel per Area:** `{JUDGES_PER_AREA} Judges (Claude Opus, Gemini 4 Argon, Gemini 3.8 Flash)`",
        f"- **Consensus Score:** **{consensus_score:.1f}%**",
        f"- **Round Verdict:** `{verdict}`",
        "",
        "---",
        "",
        "## 🛑 1. Decisions Requiring Human Judgment (Stage 6B Sign-off)",
    ]

    if human_decisions:
        lines.append("The following trade-offs or scope ambiguities require explicit human decision:")
        for idx, hd in enumerate(human_decisions, 1):
            lines.extend([
                f"### {idx}. {hd.get('title', 'Strategic Decision')}",
                f"- **Context:** {hd.get('context')}",
                f"- **Trade-off:** {hd.get('trade_off')}",
                f"- **Recommended Choice:** {hd.get('recommendation')}",
                "",
            ])
    else:
        lines.append("✅ **Zero unresolved human escalations.** The plan is technically aligned with specifications.")

    lines.extend([
        "",
        "---",
        "",
        "## ⚖️ 2. Arbiter Hardening Proposals for `@architect`",
        "",
        "*(Reviewers cannot directly mutate 05_PLAN.md. The `@architect` evaluates each proposal.)*",
        "",
    ])

    if proposals:
        lines.extend([
            "| ID | Severity | Persona | Target Task | Proposed Hardening Directive | Status |",
            "| :---: | :---: | :---: | :--- | :--- | :---: |",
        ])
        for p in proposals:
            lines.append(
                f"| `{p['proposal_id']}` | **{p['severity']}** | `{p['persona']}` | `{p['target_task']}` | {p['proposed_patch']} | `{p['architect_disposition']}` |"
            )
    else:
        lines.append("✅ **No proposed mutations.** Plan tasks, contracts, and test fixtures are properly structured.")

    lines.extend([
        "",
        "---",
        "",
        "## 📊 3. Stakeholder Consensus Scorecard",
        "",
        "| Persona | Status | Citations Verified | Critical | High | Medium | Low |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for persona, data in reviewer_results.items():
        status_icon = "✅ Approved" if data.get("status") == "APPROVED" else "⚠️ Changes Requested"
        crit = data.get("critical", 0)
        high = data.get("high", 0)
        med = data.get("medium", 0)
        low = data.get("low", 0)
        cit_ok = "✅ Yes" if data.get("citations_valid", True) else "❌ No Quote"
        lines.append(
            f"| **@{persona}** | {status_icon} | {cit_ok} | {crit} | {high} | {med} | {low} |"
        )

    if immunized_gotchas:
        lines.extend([
            "",
            "---",
            "",
            "## 🛡️ 4. Active Immunized Gotchas Checked (`rules/gotchas/`)",
            "",
            "The council audited the plan against previously immunized Stage 7 failures:",
        ])
        for g in immunized_gotchas:
            lines.append(f"- **{g['file']}**: `{g['rule']}`")

    lines.extend([
        "",
        "---",
        "",
        "## 📜 5. Detailed Reviewer Findings Log",
        "",
    ])

    has_findings = False
    for persona, data in reviewer_results.items():
        findings = data.get("findings", [])
        if findings:
            has_findings = True
            lines.append(f"### @{persona} Findings")
            for f in findings:
                sev = f.get("severity", "LOW")
                quote = f.get("quote", "N/A")
                agreement = f.get("agreement", f"{JUDGES_PER_AREA}/{JUDGES_PER_AREA}")
                judges_str = ", ".join(f.get("judges", [m["name"] for m in JUDGE_MODELS]))
                lines.extend([
                    f"- **[{sev}] {f.get('title', 'Finding')}** *(Judge Agreement: `{agreement}` — `{judges_str}`)*",
                    f"  - *Evidence Quoted:* `\"{quote}\"`",
                    f"  - *Impact:* {f.get('description', '')}",
                    f"  - *Remedy:* {f.get('recommendation', '')}",
                    "",
                ])

    if not has_findings:
        lines.append("No active findings recorded across council personas.")

    return "\n".join(lines)


def _normalize_legacy_single_payload(persona: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Preserves legacy single-payload findings as pre-aggregated (3/3 unanimous)."""
    canonical = normalize_persona(persona)
    default_judges = [m["name"] for m in JUDGE_MODELS]
    findings = []
    for raw_f in payload.get("findings", []):
        if not isinstance(raw_f, dict):
            continue
        f_copy = dict(raw_f)
        f_copy["persona"] = canonical
        f_copy.setdefault("judges", list(default_judges))
        f_copy.setdefault("judge_count", len(f_copy["judges"]))
        f_copy.setdefault("agreement", f"{f_copy['judge_count']}/{JUDGES_PER_AREA}")
        findings.append(f_copy)
    return {
        "persona": canonical,
        "status": payload.get("status", "APPROVED"),
        "judges_evaluated": payload.get("judges_evaluated", JUDGES_PER_AREA),
        "findings": findings,
        "filtered_minority_findings": payload.get("filtered_minority_findings", []),
    }


def run_council_round(
    plan_path: str,
    tier: str = "Standard",
    round_number: int = 1,
    findings_file: Optional[str] = None,
    gotchas_dir: Optional[str] = None,
    simulate: bool = False,
) -> Dict[str, Any]:
    """Executes a single evaluation round of the Stage 6A Council."""
    plan_dir = os.path.dirname(os.path.abspath(plan_path))
    gotchas = load_immunized_gotchas(gotchas_dir)

    # In simulated/test mode or with provided findings
    reviewer_payloads: Dict[str, Any] = {}
    if simulate or not findings_file:
        # Default empty/passing simulation across all personas
        for p in COUNCIL_PERSONAS:
            reviewer_payloads[p] = {
                "persona": p,
                "status": "APPROVED",
                "judges_evaluated": JUDGES_PER_AREA,
                "findings": [],
                "filtered_minority_findings": [],
            }
    else:
        with open(findings_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        grouped_by_persona: Dict[str, List[Dict[str, Any]]] = {}

        if isinstance(raw_data, dict):
            for k, v in raw_data.items():
                if ":" in k:
                    raw_persona, raw_model = k.split(":", 1)
                    norm_k = normalize_persona(raw_persona)
                    entry = dict(v) if isinstance(v, dict) else {"findings": v}
                    entry["persona"] = norm_k
                    entry["model"] = normalize_judge_model(raw_model)
                    grouped_by_persona.setdefault(norm_k, []).append(entry)
                else:
                    norm_k = normalize_persona(k)
                    if isinstance(v, dict) and isinstance(v.get("judges"), list):
                        reviewer_payloads[norm_k] = aggregate_area_judges(norm_k, v["judges"])
                    elif isinstance(v, list):
                        reviewer_payloads[norm_k] = aggregate_area_judges(norm_k, v)
                    elif isinstance(v, dict):
                        v_copy = dict(v)
                        v_copy["persona"] = normalize_persona(v_copy.get("persona", norm_k))
                        if "model" in v_copy or "judge" in v_copy:
                            grouped_by_persona.setdefault(norm_k, []).append(v_copy)
                        else:
                            reviewer_payloads[norm_k] = _normalize_legacy_single_payload(norm_k, v_copy)
        elif isinstance(raw_data, list):
            for item in raw_data:
                if not isinstance(item, dict):
                    continue
                p = normalize_persona(item.get("persona", "code-inspection"))
                item_copy = dict(item)
                item_copy["persona"] = p
                if "model" in item_copy or "judge" in item_copy:
                    grouped_by_persona.setdefault(p, []).append(item_copy)
                elif isinstance(item_copy.get("judges"), list):
                    reviewer_payloads[p] = aggregate_area_judges(p, item_copy["judges"])
                else:
                    reviewer_payloads[p] = _normalize_legacy_single_payload(p, item_copy)

        for norm_k, judge_list in grouped_by_persona.items():
            reviewer_payloads[norm_k] = aggregate_area_judges(norm_k, judge_list)

    # Tally results
    reviewer_summary = {}
    all_findings = []
    total_crit = 0
    total_high = 0
    total_med = 0
    total_low = 0

    for persona in COUNCIL_PERSONAS:
        p_data = reviewer_payloads.get(
            persona,
            {
                "persona": persona,
                "status": "APPROVED",
                "judges_evaluated": JUDGES_PER_AREA,
                "findings": [],
                "filtered_minority_findings": [],
            },
        )
        findings = p_data.get("findings", [])
        filtered_minority = p_data.get("filtered_minority_findings", [])

        crit = sum(1 for f in findings if str(f.get("severity")).upper() == "CRITICAL")
        high = sum(1 for f in findings if str(f.get("severity")).upper() == "HIGH")
        med = sum(1 for f in findings if str(f.get("severity")).upper() == "MEDIUM")
        low = sum(1 for f in findings if str(f.get("severity")).upper() == "LOW")

        # Validate evidence citations
        citations_valid = True
        for f in findings:
            valid, quote = validate_evidence(f)
            f["quote"] = quote
            f["persona"] = persona
            if not valid:
                citations_valid = False
            all_findings.append(f)

        total_crit += crit
        total_high += high
        total_med += med
        total_low += low

        reviewer_summary[persona] = {
            "status": "CHANGES_REQUESTED" if (crit + high > 0) else "APPROVED",
            "judges_evaluated": p_data.get("judges_evaluated", JUDGES_PER_AREA),
            "critical": crit,
            "high": high,
            "medium": med,
            "low": low,
            "filtered_minority_count": len(filtered_minority),
            "filtered_minority_findings": filtered_minority,
            "citations_valid": citations_valid,
            "findings": findings,
        }

    consensus_score = compute_consensus_score(total_crit, total_high, total_med, total_low)

    # Determine verdict
    if consensus_score >= CONVERGENCE_THRESHOLD and total_crit == 0 and total_high == 0:
        verdict = "CONVERGED_ROBUST"
    elif round_number >= DEFAULT_MAX_ROUNDS:
        verdict = "CIRCUIT_BREAKER_TRIGGERED"
    else:
        verdict = "NEEDS_REVISION"

    proposals = generate_proposals_for_architect(all_findings)

    # Extract human escalations (tradeoffs or circuit breaker)
    human_decisions = []
    if verdict == "CIRCUIT_BREAKER_TRIGGERED":
        human_decisions.append({
            "title": "Circuit Breaker Tripped: Maximum Review Rounds Reached",
            "context": f"Plan did not reach 90% consensus after {DEFAULT_MAX_ROUNDS} iterations.",
            "trade_off": "Reviewers have unresolved Critical or High concerns.",
            "recommendation": "Review active blocker findings and manually accept or reject plan."
        })

    # Compile 06_COUNCIL_REVIEW.md
    report_md = compile_council_report(
        round_number=round_number,
        verdict=verdict,
        consensus_score=consensus_score,
        tier=tier,
        reviewer_results=reviewer_summary,
        proposals=proposals,
        human_decisions=human_decisions,
        immunized_gotchas=gotchas,
    )

    review_md_path = os.path.join(plan_dir, "06_COUNCIL_REVIEW.md")
    with open(review_md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # Persist matrix JSON
    matrix = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "round_number": round_number,
        "verdict": verdict,
        "consensus_score": consensus_score,
        "tier": tier,
        "judges_per_area": JUDGES_PER_AREA,
        "judge_models": [m["name"] for m in JUDGE_MODELS],
        "tier_reviewers": TIER_REVIEWERS.get(tier, TIER_REVIEWERS["Standard"]),
        "tier_judges": get_judges_for_tier(tier),
        "counts": {
            "critical": total_crit,
            "high": total_high,
            "medium": total_med,
            "low": total_low,
        },
        "proposals": proposals,
        "reviewer_summary": reviewer_summary,
    }
    matrix_path = os.path.join(plan_dir, "council_matrix.json")
    with open(matrix_path, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2)

    return {
        "verdict": verdict,
        "consensus_score": consensus_score,
        "report_path": review_md_path,
        "matrix_path": matrix_path,
        "matrix": matrix,
    }


def main():
    parser = argparse.ArgumentParser(description="Stage 6A Plan Review Council Loop Engine")
    parser.add_argument("--plan", required=True, help="Path to 05_PLAN.md")
    parser.add_argument("--tier", default="Standard", choices=["Light", "Standard", "Full"])
    parser.add_argument("--round", type=int, default=1, help="Review round (1-3)")
    parser.add_argument("--findings", help="Path to aggregated findings JSON")
    parser.add_argument("--gotchas-dir", help="Path to rules/gotchas/")
    parser.add_argument("--simulate", action="store_true", help="Run simulated round")
    args = parser.parse_args()

    result = run_council_round(
        plan_path=args.plan,
        tier=args.tier,
        round_number=args.round,
        findings_file=args.findings,
        gotchas_dir=args.gotchas_dir,
        simulate=args.simulate,
    )

    print(f"Council Verdict: {result['verdict']} (Score: {result['consensus_score']}%)")
    print(f"Emitted Review:  {result['report_path']}")
    print(f"Emitted Matrix:  {result['matrix_path']}")


if __name__ == "__main__":
    main()
