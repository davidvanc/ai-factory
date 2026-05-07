#!/usr/bin/env python3
"""
factory_baseline.py — aggregeer pipeline-stats uit job logs.

Run: python3 scripts/factory_baseline.py [--limit N] [--json]
"""
import argparse
import json
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path.home() / "ai-factory-worker" / "logs"


def parse_log(path: Path):
    """Parse één job log. Return None als corrupt/incompleet."""
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    attempts = data.get("attempts", {})
    if not isinstance(attempts, dict):
        return None

    duration = None
    if "start" in data and "end" in data:
        try:
            duration = (
                datetime.fromisoformat(data["end"])
                - datetime.fromisoformat(data["start"])
            ).total_seconds()
        except (ValueError, TypeError):
            pass

    final_num = data.get("final_attempt")
    final = attempts.get(f"attempt_{final_num}", {}) if final_num else {}
    first = attempts.get("attempt_1", {})

    used_premium = any(
        a.get("model") == "developer_premium" for a in attempts.values()
    )

    plan = data.get("plan") if isinstance(data.get("plan"), dict) else {}

    return {
        "log_file": path.name,
        "task": data.get("task"),
        "project_name": plan.get("project_name"),
        "status": data.get("status"),
        "duration_s": duration,
        "n_attempts": len(attempts),
        "final_verdict": final.get("verdict"),
        "first_attempt_approved": first.get("verdict") == "APPROVED",
        "first_attempt_tests_passed": first.get("tests_passed", False),
        "used_premium": used_premium,
        "sum_dev_s": sum(a.get("dev_duration", 0) or 0 for a in attempts.values()),
        "sum_test_s": sum(a.get("test_duration", 0) or 0 for a in attempts.values()),
        "sum_judge_s": sum(a.get("judge_duration", 0) or 0 for a in attempts.values()),
        "sum_build_s": sum(a.get("build_duration", 0) or 0 for a in attempts.values()),
        "start": data.get("start"),
    }


def aggregate(jobs):
    n = len(jobs)
    if n == 0:
        return {"n_runs": 0}

    succ = [j for j in jobs if j["status"] == "success"]
    fail = [j for j in jobs if j["status"] != "success"]
    durs = [j["duration_s"] for j in succ if j["duration_s"]]
    atts = [j["n_attempts"] for j in succ]

    return {
        "n_runs": n,
        "n_success": len(succ),
        "n_failed": len(fail),
        "success_rate": len(succ) / n,
        "first_attempt_approved_rate": sum(1 for j in jobs if j["first_attempt_approved"]) / n,
        "first_attempt_tests_passed_rate": sum(1 for j in jobs if j["first_attempt_tests_passed"]) / n,
        "premium_usage_rate": sum(1 for j in jobs if j["used_premium"]) / n,
        "mean_attempts_to_success": statistics.mean(atts) if atts else None,
        "max_attempts_to_success": max(atts) if atts else None,
        "median_duration_s": statistics.median(durs) if durs else None,
        "p90_duration_s": statistics.quantiles(durs, n=10)[-1] if len(durs) >= 10 else None,
        "mean_dev_s": statistics.mean(j["sum_dev_s"] for j in succ) if succ else None,
        "mean_test_s": statistics.mean(j["sum_test_s"] for j in succ) if succ else None,
        "mean_judge_s": statistics.mean(j["sum_judge_s"] for j in succ) if succ else None,
    }


def fmt_num(v, decimals=1):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.{decimals}f}"
    return str(v)


def fmt_pct(v):
    return f"{v*100:.1f}%" if v is not None else "n/a"


def format_report_md(jobs, agg):
    if agg.get("n_runs", 0) == 0:
        return "# Factory Baseline Metrics\n\n_Geen logs gevonden._\n"

    rows = [
        ("Totaal runs", agg["n_runs"]),
        ("Geslaagd", f"{agg['n_success']} ({fmt_pct(agg['success_rate'])})"),
        ("Mislukt", agg["n_failed"]),
        ("First-attempt APPROVED rate", fmt_pct(agg["first_attempt_approved_rate"])),
        ("First-attempt tests passed rate", fmt_pct(agg["first_attempt_tests_passed_rate"])),
        ("Premium model usage rate", fmt_pct(agg["premium_usage_rate"])),
        ("Gem. pogingen tot succes", fmt_num(agg["mean_attempts_to_success"], 2)),
        ("Max pogingen tot succes", fmt_num(agg["max_attempts_to_success"], 0)),
        ("Mediaan duur (s)", fmt_num(agg["median_duration_s"])),
        ("P90 duur (s)", fmt_num(agg["p90_duration_s"])),
        ("Gem. dev fase (s)", fmt_num(agg["mean_dev_s"])),
        ("Gem. test fase (s)", fmt_num(agg["mean_test_s"])),
        ("Gem. judge fase (s)", fmt_num(agg["mean_judge_s"])),
    ]

    lines = [
        "# Factory Baseline Metrics",
        f"_Gegenereerd: {datetime.now().strftime('%Y-%m-%d %H:%M')}_  ",
        f"_Basis: {agg['n_runs']} job logs_",
        "",
        "## Aggregaten",
        "",
        "| Metric | Waarde |",
        "|---|---|",
    ]
    for k, v in rows:
        lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "## Recente runs (max 20)",
        "",
        "| Project | Status | Pogingen | Duur | Premium | Verdict |",
        "|---|---|---|---|---|---|",
    ]

    sorted_jobs = sorted(jobs, key=lambda j: j.get("start") or "", reverse=True)
    for j in sorted_jobs[:20]:
        dur = f"{j['duration_s']:.0f}s" if j["duration_s"] else "n/a"
        lines.append(
            f"| {j.get('project_name') or '?'} "
            f"| {j.get('status') or '?'} "
            f"| {j['n_attempts']} "
            f"| {dur} "
            f"| {'yes' if j['used_premium'] else 'no'} "
            f"| {j.get('final_verdict') or '-'} |"
        )
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Max N nieuwste logs")
    ap.add_argument("--json", action="store_true", help="JSON output ipv Markdown")
    ap.add_argument("--logs-dir", type=Path, default=LOGS_DIR)
    args = ap.parse_args()

    if not args.logs_dir.exists():
        print(f"FOUT: logs dir bestaat niet: {args.logs_dir}", file=sys.stderr)
        sys.exit(1)

    log_files = sorted(
        args.logs_dir.glob("job_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if args.limit:
        log_files = log_files[: args.limit]

    jobs = []
    n_skipped = 0
    for path in log_files:
        parsed = parse_log(path)
        if parsed is None:
            n_skipped += 1
            continue
        jobs.append(parsed)

    agg = aggregate(jobs)

    if args.json:
        print(json.dumps({"aggregate": agg, "jobs": jobs, "n_skipped": n_skipped}, indent=2, default=str))
    else:
        print(format_report_md(jobs, agg))
        if n_skipped:
            print(f"_Note: {n_skipped} log files overgeslagen (corrupt/incompleet)_")


if __name__ == "__main__":
    main()
