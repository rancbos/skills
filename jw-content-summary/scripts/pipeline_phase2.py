#!/usr/bin/env python3
"""
Phase 2 统一管道：validate → cluster → score → build_summary_plan
替代 4 脚本分步调用，消除 CLI 参数顺序陷阱。

Usage:
    python pipeline_phase2.py <candidates_dir> <output_dir>
"""
import subprocess, sys, json, os
from pathlib import Path

SCRIPTS = Path(__file__).parent


def run_cmd(args, cwd=None):
    """Run a subprocess, return (exit_code, stdout_str, stderr_str)."""
    r = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=120)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def parse_test(candidates_dir):
    """Quick parse test: verify scripts can read candidate fields correctly. Also preview clustering."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("cluster_mod", SCRIPTS / "cluster_candidates.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    cdir = Path(candidates_dir)
    items = mod.read_candidates(cdir)
    if not items:
        return {"ok": False, "error": "read_candidates returned 0 items — check field format (bold **field**: vs plain field:)", "count": 0}

    # Check for header-only junk entries
    junk = [it for it in items if not it.get("keywords") and it["id"].endswith("-0")]
    real = [it for it in items if it not in junk]

    types = {}
    for it in real:
        types.setdefault(it["type"], []).append(it["id"])

    # Clustering preview: run cluster at default threshold and report stats
    preview_clusters = mod.cluster(real)
    preview_quality = mod.detect_quality(preview_clusters, real)
    suggested_merges = preview_quality.get("suggested_merges", [])
    # Also try lower threshold for fragmented books
    low_clusters = mod.cluster(real, threshold=0.25)
    low_quality = mod.detect_quality(low_clusters, real)

    return {
        "ok": True,
        "count": len(real),
        "junk_count": len(junk),
        "types": {k: len(v) for k, v in types.items()},
        "sample": [{"id": it["id"], "title": it["title"][:40], "type": it["type"], "kw_count": len(it.get("keywords", []))} for it in real[:3]],
        "cluster_preview": {
            "threshold_0.35": {
                "clusters": len(preview_clusters),
                "single_member_ratio": preview_quality["single_member_ratio"],
                "suggested_merges": len(suggested_merges),
            },
            "threshold_0.25": {
                "clusters": len(low_clusters),
                "single_member_ratio": low_quality["single_member_ratio"],
            },
        },
    }


def run_pipeline(candidates_dir, output_dir):
    candidates = Path(candidates_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    results = {"stages": {}}

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

    results["stages"]["plan"] = {
        "recommended": len(plan.get("recommended_units", plan.get("recommended", []))),
        "appendix": len(plan.get("appendix_units", plan.get("appendix", []))),
        "weak": len(plan.get("excluded_or_weak", plan.get("weak", [])))
    }
    print(f"[plan] recommended={results['stages']['plan']['recommended']} "
          f"appendix={results['stages']['plan']['appendix']}")

    # Write pipeline result
    result_file = output / "phase2_result.json"
    with open(result_file, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python pipeline_phase2.py <candidates_dir> <output_dir> [--dry-run]")
        sys.exit(1)

    cand_dir = sys.argv[1]
    out_dir = sys.argv[2]
    dry_run = "--dry-run" in sys.argv

    if not Path(cand_dir).is_dir():
        print(f"ERROR: candidates_dir '{cand_dir}' not found")
        sys.exit(1)

    if dry_run:
        # Quick parse test only — no cluster/score/plan
        print("[dry-run] Testing candidate parsing...")
        result = parse_test(cand_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["ok"] else 1)

    results = run_pipeline(cand_dir, out_dir)

    # Summary
    s = results["stages"]
    print(f"\n--- Pipeline Complete ---")
    print(f"  validate: {s['validate'].get('ok', 'N/A')}")
    print(f"  cluster:  {s['cluster']['cluster_count']} clusters")
    print(f"  score:    {s['score']['candidate_count']} candidates, avg={s['score']['avg_score']}")
    print(f"  plan:     {s['plan']['recommended']} recommended + {s['plan']['appendix']} appendix")
