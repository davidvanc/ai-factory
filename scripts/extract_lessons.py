#!/usr/bin/env python3
"""
extract_lessons.py — standalone lesson extractor (geen DB-write).

Leest een job log + bijbehorende snapshots, beslist eligibility,
roept LLM aan met de extraction prompt, print de JSON output.

Usage:
    python scripts/extract_lessons.py <path-to-job-log.json>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.llm.client import LLMClient


SYSTEM_PROMPT = """You extract lessons from a code-generation pipeline. A "run" is a sequence of
attempts where the pipeline failed at least once, then succeeded. Your job is
to identify transferable insights from the fail->success transition — and, more
often, to refuse.

You default to refusing. Most fail->success transitions yield no transferable
lesson. Refusing is the correct, valuable output. Do not produce a lesson to
"be helpful." A lessons DB filled with weak guidance is worse than empty —
it pollutes future Developer prompts.

# What a good lesson looks like

Grounded in:
  (a) one specific test or failing criterion that went FAIL -> PASS,
  (b) one specific code change in the diff that caused (a),
  (c) a principle that would help a Developer on a *different but similar*
      task in the same domain produce better code on the first attempt.

Good examples:
  * "Roman numeral conversion requires subtractive pairs (IV, IX, XL, XC, CD, CM)
     handled before greedy decomposition." (domain_knowledge)
  * "ISBN-13 checksum uses alternating weights of 1 and 3 across the first
     12 digits, validated mod 10 against the 13th." (domain_knowledge)
  * "FastAPI GET endpoints with optional query params must use Query(default=...)
     not bare type annotations, otherwise the framework returns 422 instead of
     letting the handler decide." (code_pattern)
  * "Pydantic Settings cached at module level needs explicit re-instantiation
     in pytest fixtures when monkeypatching env vars." (test_fixture)

Bad output (you MUST refuse these):
  * "Validate inputs carefully" — generic, already implied.
  * "Handle edge cases" — meaningless without specifics.
  * "Use type hints" — boilerplate, not a lesson.
  * "Test passed after fixing the bug" — no insight.
  * "Don't use User-Agent sniffing to detect TestClient" — too task-specific to
     this exact bug; would only ever apply to the same bug.

# Note on failure types

failure_context.phase can be:
  * "tester" — pytest or functional smoke test failed (see TESTS FAILING and issues)
  * "judge_rejected" — pytest passed but Judge rejected on quality grounds
                       (see verdict_reason and failing_criteria)

For judge_rejected, "what was wrong" lives in failing_criteria, not in failing_tests.

# Required reasoning (do silently before deciding)

1. CAUSAL ANCHOR. Identify what specifically transitioned FAIL -> PASS.
   * For tester failures: which failing test or scenario got fixed?
   * For judge rejections: which failing_criterion got addressed?
   If multiple things changed, identify the *primary* one whose fix likely
   cascaded. If you can't, refuse — causality too murky.

2. CODE ATTRIBUTION. In the diff between LAST_FAILING_CODE and APPROVED_CODE,
   identify the specific change responsible for (1). Cite it concretely.
   If the diff has multiple unrelated changes (refactors, formatting, retries)
   and you cannot isolate the causal one, refuse.

3. TRANSFER TEST. Imagine a *different* task in the same domain. Would your
   guidance actually change the code a Developer writes on that task?
   If no, refuse — too task-specific.

4. CONFIDENCE.
   0.9-1.0 — single transitioning failure, isolated code change, clean pattern.
   0.7-0.9 — single failure, diff has confounds you reasoned through.
   0.5-0.7 — multiple failures transitioned, you inferred a primary.
   < 0.5  — refuse.

# Output

If any step 1-3 fails, or confidence < 0.5, return exactly:

{"emit": false, "reason": "<specific: 'multiple confounded diff changes', 'no single causal failure', 'insight not transferable', 'guidance too generic', etc.>"}

Otherwise return exactly:

{
  "emit": true,
  "category": "code_pattern" | "domain_knowledge" | "infrastructure" | "test_fixture",
  "trigger_signal": "<8-15 words: failure pattern that should retrieve this lesson>",
  "guidance": "<15-30 words: imperative or declarative, the sentence injected into Developer prompts>",
  "confidence_score": <0.5 to 1.0>,
  "reasoning": "<2-3 sentences: what transitioned, what change caused it, why it transfers>"
}

Output the JSON object only. No prose, no markdown fences.
"""


def find_attempts(run_log):
    """Vind approved attempt + de attempt direct ervoor (last_failing)."""
    attempts = run_log.get("attempts", {})
    approved_key = None
    for key, attempt in attempts.items():
        if attempt.get("verdict") == "APPROVED":
            approved_key = key
            break
    if not approved_key:
        return None, None, "geen APPROVED attempt gevonden"

    keys = list(attempts.keys())
    idx = keys.index(approved_key)
    if idx == 0:
        return None, None, f"approved is {approved_key} (eerste attempt) — geen multi-attempt success"
    return approved_key, keys[idx - 1], None


def load_snapshot(snapshot_dir, attempt_key):
    p = snapshot_dir / attempt_key / "files.json"
    return json.loads(p.read_text()) if p.exists() else None


def format_files(files):
    return "\n".join(f"=== {f.get('path','?')} ===\n{f.get('content','')}\n" for f in files)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: extract_lessons.py <path-to-job-log.json>")

    log_path = Path(sys.argv[1]).expanduser().resolve()
    if not log_path.exists():
        sys.exit(f"FOUT: log niet gevonden: {log_path}")

    run_log = json.loads(log_path.read_text())

    # Eligibility checks
    status = run_log.get("status")
    if status != "success":
        print(f"SKIP: status='{status}' — extractor draait alleen op success-runs")
        return

    final_attempt = run_log.get("final_attempt", 0)
    if final_attempt < 2:
        print(f"SKIP: final_attempt={final_attempt} — eerste-poging-success heeft geen lesson")
        return

    approved_key, last_failing_key, err = find_attempts(run_log)
    if err:
        print(f"SKIP: {err}")
        return

    print(f"Eligible: {last_failing_key} (failing) -> {approved_key} (approved)")

    snapshot_dir = log_path.parent / "snapshots" / log_path.stem
    last_failing_snap = load_snapshot(snapshot_dir, last_failing_key)
    approved_snap = load_snapshot(snapshot_dir, approved_key)

    if not last_failing_snap:
        print(f"SKIP: snapshot ontbreekt voor {last_failing_key} ({snapshot_dir})")
        return
    if not approved_snap:
        print(f"SKIP: snapshot ontbreekt voor {approved_key} ({snapshot_dir})")
        return

    # Inputs samenstellen
    task = run_log.get("task", "")
    plan = run_log.get("plan", {})
    project_name = plan.get("project_name", "unknown")

    last_failing = run_log["attempts"][last_failing_key]
    fc = last_failing.get("failure_context", {})

    user_prompt = f"""TASK: {task}
PROJECT: {project_name}

LAST FAILING ATTEMPT ({last_failing_key}) — failure_context:
  phase: {fc.get("phase", "?")}
  issues: {json.dumps(fc.get("issues", []), indent=2)}
  test_output_excerpt: {fc.get("test_output_excerpt", "")[:1500]}
  verdict_reason (if judge_rejected): {fc.get("verdict_reason", "n/a")}
  failing_criteria (if judge_rejected): {json.dumps(fc.get("failing_criteria", []), indent=2)}

TESTS FAILING IN LAST FAILING ATTEMPT (pytest):
{json.dumps(last_failing.get("failing_tests", []), indent=2)}

NOTE: In the APPROVED attempt below, all tests pass and the Judge approved.

--- LAST_FAILING_CODE ---
{format_files(last_failing_snap.get("files", []))}

--- APPROVED_CODE ---
{format_files(approved_snap.get("files", []))}
"""

    full_prompt = SYSTEM_PROMPT + "\n\n" + user_prompt
    print(f"Prompt size: {len(full_prompt)} chars")
    print("Calling LLM (role=planner -> Opus)...")

    client = LLMClient()
    response = client.generate(full_prompt, role="planner", temperature=0.3, stream=False)

    print("\n=== Raw response ===")
    print(response)
    print("=== End raw response ===\n")

    # Parse
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        result = json.loads(cleaned)
        print("=== Parsed result ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(f"FOUT: kon response niet parsen als JSON: {e}")


if __name__ == "__main__":
    main()
