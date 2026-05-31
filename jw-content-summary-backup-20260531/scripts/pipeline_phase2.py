#!/usr/bin/env python3
"""
Phase 2 统一管道：validate → cluster → score → build_summary_plan
替代 4 脚本分步调用，消除 CLI 参数顺序陷阱。

Usage:
    python pipeline_phase2.py <candidates_dir> <output_dir>
"""
import subprocess, sys, json, os
from pathlib import Path

SCRIPTS = Path("/root/.hermes/skills/jw-content-summary/scripts")
SAFETY_MAX_CANDIDATES = 100
SAFETY_MAX_RECOMMENDED = 30


def run_cmd(args, cwd=None):
    """Run a subprocess, return (exit_code, stdout_str, stderr_str)."""
    r = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=120)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def run_pipeline(candidates_dir, output_dir):
    candidates = Path(candidates_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    results = {"stages": {}, "valve_triggered": False}

    # --- Stage 1: validate ---
    ec, out, err = run_cmd(
        ["python3", str(SCRIPTS / "validate_candidates.py"), str(candidates)]
    )
    if ec == 0:
        try:
            v = json.loads(out)
        except json.JSONDecodeError:
            v = {"ok": False, "raw": out[:200]}
    else:
        v = {"ok": False, "error": err or out}
    results["stages"]["validate"] = v
    print(f"[validate] ok={v.get('ok', False)}")

    # --- Stage 2: cluster ---
    clusters_file = output / "clusters.json"
    ec, out, err = run_cmd(
        ["python3", str(SCRIPTS / "cluster_candidates.py"),
         str(candidates), str(clusters_file)]
    )
    if ec == 0 and clusters_file.exists():
        with open(clusters_file) as f:
            clusters = json.load(f)
    else:
        clusters = {"clusters": [], "granularity": "per_file", "cluster_count": 0,
                     "error": err or out}
        with open(clusters_file, "w") as f:
            json.dump(clusters, f, indent=2)
    results["stages"]["cluster"] = {"cluster_count": clusters.get("cluster_count", 0)}
    print(f"[cluster] count={clusters.get('cluster_count', 0)}")

    # --- Stage 3: score ---
    scores_file = output / "candidate_scores.json"
    ec, out, err = run_cmd(
        ["python3", str(SCRIPTS / "score_candidates.py"),
         str(candidates), str(clusters_file), str(scores_file)]
    )
    if ec == 0 and scores_file.exists():
        with open(scores_file) as f:
            scores = json.load(f)
    else:
        scores = {"candidate_count": 0, "average_score": 0, "grade_distribution": {},
                  "error": err or out}
        with open(scores_file, "w") as f:
            json.dump(scores, f, indent=2)
    avg = scores.get("average_score", scores.get("avg_score", 0))
    results["stages"]["score"] = {"candidate_count": scores.get("candidate_count", 0),
                                   "avg_score": avg}
    print(f"[score] candidates={scores.get('candidate_count', 0)} avg={avg}")

    # --- Stage 4: build_summary_plan ---
    plan_file = output / "summary_plan.json"
    ec, out, err = run_cmd(
        ["python3", str(SCRIPTS / "build_summary_plan.py"),
         str(clusters_file), str(scores_file), str(plan_file)]
    )
    if ec == 0 and plan_file.exists():
        with open(plan_file) as f:
            plan = json.load(f)
    else:
        plan = {"recommended_units": [], "appendix_units": [], "excluded_or_weak": [], "error": err or out}
        with open(plan_file, "w") as f:
            json.dump(plan, f, indent=2)

    # --- Safety valve ---
    total = scores.get("candidate_count", 0)
    if total > SAFETY_MAX_CANDIDATES:
        plan["valve_triggered"] = True
        plan["valve_reason"] = (
            f"candidate_count={total} exceeds {SAFETY_MAX_CANDIDATES}; "
            f"limiting recommended to top-{SAFETY_MAX_RECOMMENDED}, rest → appendix"
        )
        recs = plan.get("recommended_units", plan.get("recommended", []))
        if isinstance(recs, list) and len(recs) > SAFETY_MAX_RECOMMENDED:
            plan["appendix_units"] = plan.get("appendix_units", plan.get("appendix", [])) + recs[SAFETY_MAX_RECOMMENDED:]
            plan["recommended_units"] = recs[:SAFETY_MAX_RECOMMENDED]
        results["valve_triggered"] = True
        with open(plan_file, "w") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)

    results["stages"]["plan"] = {
        "recommended": len(plan.get("recommended_units", plan.get("recommended", []))),
        "appendix": len(plan.get("appendix_units", plan.get("appendix", []))),
        "weak": len(plan.get("excluded_or_weak", plan.get("weak", [])))
    }
    results["valve_triggered"] = plan.get("valve_triggered", False)
    print(f"[plan] recommended={results['stages']['plan']['recommended']} "
          f"appendix={results['stages']['plan']['appendix']} "
          f"valve={results['valve_triggered']}")

    # Write pipeline result
    result_file = output / "phase2_result.json"
    with open(result_file, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pipeline_phase2.py <candidates_dir> <output_dir>")
        sys.exit(1)

    cand_dir = sys.argv[1]
    out_dir = sys.argv[2]

    if not Path(cand_dir).is_dir():
        print(f"ERROR: candidates_dir '{cand_dir}' not found")
        sys.exit(1)

    results = run_pipeline(cand_dir, out_dir)

    # Summary
    s = results["stages"]
    print(f"\n--- Pipeline Complete ---")
    print(f"  validate: {s['validate'].get('ok', 'N/A')}")
    print(f"  cluster:  {s['cluster']['cluster_count']} clusters")
    print(f"  score:    {s['score']['candidate_count']} candidates, avg={s['score']['avg_score']}")
    print(f"  plan:     {s['plan']['recommended']} recommended + {s['plan']['appendix']} appendix")
    if results["valve_triggered"]:
        print(f"  ⚠️ SAFETY VALVE TRIGGERED")
