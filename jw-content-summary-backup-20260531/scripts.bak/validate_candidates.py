#!/usr/bin/env python3
"""
validate_candidates.py — validate candidates/*.md against extractor schema.

Usage:
  python scripts/validate_candidates.py books/<title>/candidates
  python scripts/validate_candidates.py --strict books/<title>/candidates

Output:
  JSON report: {ok, issues, warnings, schema_compliance, format_mismatches}

Default mode is compatibility-first: missing v4.4 quality fields are warnings.
Strict mode treats missing/invalid v4.4 fields as failures.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

BASE_FIELDS = [
    "id",
    "type",
    "source_chapter",
    "source_quote",
    "source_line",
    "summary",
    "keywords",
    "related",
    "v3_pass",
    "v3_reason",
]

SCHEMA = {
    "insight": BASE_FIELDS + ["common_sense", "author_reversal", "v2_scenario"],
    "principle": BASE_FIELDS + ["v2_scenario"],
    "framework": BASE_FIELDS + ["v2_scenario"],
    "case": BASE_FIELDS + ["linked_method_hint", "v2_scenario"],
    # v4.12: counter-example merged into boundary; keep alias for backward compat
    "counter-example": BASE_FIELDS,
    "glossary": BASE_FIELDS,
    "procedure": BASE_FIELDS + ["steps", "prerequisites", "outcome"],
    "boundary": BASE_FIELDS,
}

ALIASES = {
    "chapter": "source_chapter",
    "line": "source_line",
    "source": "source_chapter",
    "quote": "source_quote",
    "name": "title",
    "principle": "summary",
    "insight": "summary",
    "framework": "summary",
    "counter_intuitive": "v3_pass",
    "reasoning": "v3_reason",
    "connections": "related",
    "related_methods": "related",
    "what_it_is_not": None,
}

PLURAL_TO_TYPE = {
    "frameworks": "framework",
    "principles": "principle",
    "insights": "insight",
    "cases": "case",
    "counter-examples": "counter-example",
    "glossary": "glossary",
    "procedures": "procedure",
    "boundaries": "boundary",
}


def parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        try:
            return int(value)
        except ValueError:
            return value
    return value


def parse_listish(value: str) -> list[str] | None:
    value = value.strip()
    if value in ("[]", ""):
        return []
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed]
        except Exception:
            # Fall through to simple split for YAML-ish unquoted lists.
            inner = value[1:-1].strip()
            if not inner:
                return []
            return [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
    return None


def parse_entries(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries = []
    raw_blocks = re.split(r"\n(?=-?\s*id\s*:\s+)", "\n" + text)
    for block in raw_blocks:
        m = re.search(r"-?\s*id\s*:\s*(\S+)", block)
        entry_id = m.group(1) if m else None
        if not entry_id:
            if block.strip().startswith("#") or "## " in block[:80]:
                continue
            if "type:" not in block and "source_chapter:" not in block and "chapter:" not in block:
                continue

        fields: dict[str, Any] = {}
        for line in block.split("\n"):
            fm = re.match(r"^\s*-?\s*([A-Za-z_][\w\-]*)\s*:\s*(.*)", line)
            if fm:
                key = fm.group(1)
                val = fm.group(2).strip()
                fields[key] = parse_scalar(val)

        entries.append({"id": entry_id, "fields": fields, "block": block[:500]})
    return entries


def validate_source_line(value: Any) -> bool:
    if isinstance(value, int):
        return value > 0
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        return int(value.strip()) > 0
    return False


def validate_related(value: Any) -> bool:
    if isinstance(value, list):
        return True
    if isinstance(value, str):
        return parse_listish(value) is not None
    return False


def expected_type_for(path: Path) -> str:
    return PLURAL_TO_TYPE.get(path.stem, path.stem)


def validate_candidates(cdir: Path, strict: bool = False):
    issues: list[str] = []
    warnings: list[str] = []
    format_mismatches = []
    alias_occurrences = []
    schema_stats = {
        "total": 0,
        "compliant": 0,
        "missing_required": 0,
        "quote_too_long": 0,
        "missing_source_line": 0,
        "invalid_source_line": 0,
        "missing_related": 0,
        "invalid_related": 0,
    }

    for p in sorted(cdir.glob("*.md")):
        expected_type = expected_type_for(p)
        if expected_type not in SCHEMA:
            issues.append(f"{p.name}: unknown extractor type, no schema to validate against")
            continue

        required = SCHEMA[expected_type]
        entries = parse_entries(p)
        for entry in entries:
            schema_stats["total"] += 1
            flds = entry["fields"]
            eid = entry.get("id") or "?"

            missing = [f for f in required if f not in flds]
            # v4.4 fields are warning-only by default to avoid breaking old candidate archives.
            soft_missing = [f for f in missing if f in ("source_line", "related")]
            hard_missing = [f for f in missing if f not in ("source_line", "related")]

            if hard_missing or (strict and soft_missing):
                schema_stats["missing_required"] += 1
                issues.append(f"{p.name}#{eid}: missing required fields: {hard_missing + soft_missing if strict else hard_missing}")
            elif soft_missing:
                warnings.append(f"{p.name}#{eid}: missing v4.4 quality fields: {soft_missing}")

            if "source_line" not in flds:
                schema_stats["missing_source_line"] += 1
            elif not validate_source_line(flds.get("source_line")):
                schema_stats["invalid_source_line"] += 1
                msg = f"{p.name}#{eid}: source_line should be a positive integer, got {flds.get('source_line')!r}"
                (issues if strict else warnings).append(msg)

            if "related" not in flds:
                schema_stats["missing_related"] += 1
            elif not validate_related(flds.get("related")):
                schema_stats["invalid_related"] += 1
                msg = f"{p.name}#{eid}: related should be a list, got {flds.get('related')!r}"
                (issues if strict else warnings).append(msg)

            quote = str(flds.get("source_quote", ""))
            if quote and len(quote) > 150:
                schema_stats["quote_too_long"] += 1
                issues.append(f"{p.name}#{eid}: source_quote too long ({len(quote)} chars, max 150)")

            for alias, standard in ALIASES.items():
                if alias in flds and standard and standard not in flds:
                    alias_occurrences.append(f"{p.name}#{eid}: uses '{alias}' instead of '{standard}'")
                    format_mismatches.append({
                        "file": str(p),
                        "id": eid,
                        "alias_used": alias,
                        "standard_field": standard,
                    })

            v3 = flds.get("v3_pass", "")
            if not isinstance(v3, bool):
                if isinstance(v3, str) and v3.lower() in ("true", "false"):
                    pass
                else:
                    issues.append(f"{p.name}#{eid}: v3_pass should be boolean (true/false), got {v3!r}")

            if not hard_missing and not (strict and soft_missing):
                schema_stats["compliant"] += 1

    ok = len(issues) == 0 and len(format_mismatches) == 0
    return {
        "ok": ok,
        "strict": strict,
        "total_entries": schema_stats["total"],
        "compliant": schema_stats["compliant"],
        "missing_required_fields": schema_stats["missing_required"],
        "quotes_too_long": schema_stats["quote_too_long"],
        "missing_source_line": schema_stats["missing_source_line"],
        "invalid_source_line": schema_stats["invalid_source_line"],
        "missing_related": schema_stats["missing_related"],
        "invalid_related": schema_stats["invalid_related"],
        "format_mismatches": format_mismatches,
        "alias_occurrences": alias_occurrences,
        "warnings": warnings[:50],
        "issues": issues[:50],
    }


def main():
    parser = argparse.ArgumentParser(description="Validate jw-content-summary candidate files")
    parser.add_argument("candidates_dir", help="books/<title>/candidates directory")
    parser.add_argument("--strict", action="store_true", help="treat v4.4 quality field issues as failures")
    args = parser.parse_args()

    cdir = Path(args.candidates_dir).expanduser().resolve()
    if not cdir.exists():
        print(json.dumps({"ok": False, "error": f"Directory not found: {cdir}"}, ensure_ascii=False))
        return 1

    report = validate_candidates(cdir, strict=args.strict)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
