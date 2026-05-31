#!/usr/bin/env python3
"""
decision_log.py — 跨会话决策记忆日志 v1.0

参考 daisy dexter_memory_log.py，简化为 A 股场景。
文件格式: [日期 | 代码 | 评级 | 状态] DECISION/REFLECTION, <!-- ENTRY_END --> 分隔
子命令: record / resolve / auto-resolve / list / context / stats / backtest
"""

import argparse, json, os, re, statistics, sys, time, math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "1.0.0"

DEFAULT_LOG = os.path.expanduser("~/.hermes/decisions/decision-log.md")
SEPARATOR = "\n\n<!-- ENTRY_END -->\n\n"
RATINGS = ["Buy", "Overweight", "Hold", "Underweight", "Sell"]


def _ensure_dir():
    os.makedirs(os.path.dirname(DEFAULT_LOG), exist_ok=True)


def _load_entries(log_path=None) -> List[Dict]:
    path = log_path or DEFAULT_LOG
    if not os.path.exists(path): return []
    text = Path(path).read_text(encoding="utf-8")
    entries = []
    for block in text.split(SEPARATOR):
        block = block.strip()
        if not block: continue
        entry = _parse_entry(block)
        if entry: entries.append(entry)
    return entries


def _parse_entry(block: str) -> Optional[Dict]:
    lines = block.strip().split("\n")
    if not lines: return None
    m = re.match(r"\[(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\]", lines[0])
    if not m: return None
    date, ticker, rating, status_str = [x.strip() for x in m.groups()]
    pending = "pending" in status_str.lower()
    raw_ret, alpha, holding = None, None, None
    if not pending:
        parts = re.findall(r"([+-]?\d+\.?\d*)", status_str)
        if len(parts) >= 1: raw_ret = parts[0] + "%"
        if len(parts) >= 2: alpha = parts[1] + "%"
        if len(parts) >= 3: holding = parts[2] + "d"
    full = "\n".join(lines[1:])
    d = re.search(r"DECISION:\n(.*?)(?=\nREFLECTION:|\Z)", full, re.DOTALL)
    r = re.search(r"REFLECTION:\n(.*?)$", full, re.DOTALL)
    return {"date": date, "ticker": ticker, "rating": rating, "pending": pending,
            "raw": raw_ret, "alpha": alpha, "holding": holding,
            "decision": d.group(1).strip() if d else "",
            "reflection": r.group(1).strip() if r else ""}


def _format_entry(e: Dict) -> str:
    tag = f"[{e['date']} | {e['ticker']} | {e['rating']} | "
    if e["pending"]: tag += "pending]"
    else: tag += f"{e.get('raw','?')} | {e.get('alpha','?')} | {e.get('holding','?')}]"
    parts = [tag, f"DECISION:\n{e['decision']}"]
    if e.get("reflection"): parts.append(f"REFLECTION:\n{e['reflection']}")
    return "\n\n".join(parts)


def _write_all(log_path, entries):
    blocks = [_format_entry(e) for e in entries]
    Path(log_path or DEFAULT_LOG).write_text(SEPARATOR.join(blocks) + SEPARATOR, encoding="utf-8")


def _parse_pct(s): return float(s.replace("%","+","").replace("+","").strip()) if s else None
def _parse_holding(s): return int(s.replace("d","").strip()) if s else None


def _emit(data, meta=None):
    r = {"ok": True, "source": "decision_log", "data": data, "ts": int(time.time())}
    if meta: r["meta"] = meta
    print(json.dumps(r, ensure_ascii=False, indent=2))


def _emit_err(code, msg):
    print(json.dumps({"ok": False, "source": "decision_log", "error": {"code": code, "message": msg},
                      "ts": int(time.time())}, ensure_ascii=False, indent=2))


def cmd_record(args):
    _ensure_dir()
    entries = _load_entries(args.log)
    for e in entries:
        if e["date"] == args.date and e["ticker"] == args.ticker and e["pending"]:
            _emit({"status": "skipped", "reason": "同日同代码已存在pending记录"})
            return 0
    tag = f"[{args.date} | {args.ticker} | {args.rating} | pending]"
    block = f"{tag}\nDECISION:\n{args.decision}\n"
    with open(args.log or DEFAULT_LOG, "a", encoding="utf-8") as f:
        f.write(block + SEPARATOR)
    _emit({"status": "recorded", "date": args.date, "ticker": args.ticker, "rating": args.rating})
    return 0


def cmd_resolve(args):
    entries = _load_entries(args.log)
    for i, e in enumerate(entries):
        if e["date"] == args.date and e["ticker"] == args.ticker and e["pending"]:
            st = f"{args.raw_return} | {args.alpha} | {args.holding}d"
            tag = f"[{args.date} | {args.ticker} | {args.rating or e['rating']} | {st}]"
            nb = f"{tag}\nDECISION:\n{e['decision']}\nREFLECTION:\n{args.reflection}\n"
            entries[i] = _parse_entry(nb)
            _write_all(args.log, entries)
            _emit({"status": "resolved", "date": args.date, "ticker": args.ticker})
            return 0
    _emit_err(4, "未找到匹配的pending记录")
    return 4


def cmd_auto_resolve(args):
    entries = _load_entries(args.log)
    for i, e in enumerate(entries):
        if e["date"] == args.date and e["ticker"] == args.ticker and e["pending"]:
            rr = (float(args.current_price) - float(args.entry_price)) / float(args.entry_price) * 100
            hd = (datetime.strptime(datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d") -
                  datetime.strptime(args.date, "%Y-%m-%d")).days
            st = f"{rr:+.1f}% | {rr:+.1f}% | {hd}d"
            tag = f"[{args.date} | {args.ticker} | {e['rating']} | {st}]"
            rf = args.reflection or "[auto-resolved]"
            nb = f"{tag}\nDECISION:\n{e['decision']}\nREFLECTION:\n{rf}\n"
            entries[i] = _parse_entry(nb)
            _write_all(args.log, entries)
            _emit({"status": "auto-resolved", "raw_return_pct": round(rr, 2), "holding_days": hd})
            return 0
    _emit_err(4, "未找到匹配的pending记录")
    return 4


def cmd_list(args):
    entries = _load_entries(args.log)
    if args.status == "pending": entries = [e for e in entries if e["pending"]]
    elif args.status == "resolved": entries = [e for e in entries if not e["pending"]]
    if args.ticker: entries = [e for e in entries if e["ticker"] == args.ticker]
    if hasattr(args, 'since') and args.since: entries = [e for e in entries if e["date"] >= args.since]
    _emit({"count": len(entries), "entries": entries})
    return 0


def cmd_context(args):
    entries = _load_entries(args.log)
    resolved = [e for e in entries if not e["pending"]]
    same = [e for e in resolved if e["ticker"] == args.ticker]
    cross = [e for e in resolved if e["ticker"] != args.ticker]
    lines = []
    if same:
        lines.append(f"## 历史决策记录 — {args.ticker}")
        for e in same[-args.n_same:]: lines.append(_format_entry(e))
    if cross and args.n_cross > 0:
        lines.append("## 跨标的决策教训")
        for e in cross[-args.n_cross:]:
            if e.get("reflection"): lines.append(f"- [{e['date']} | {e['ticker']} | {e['rating']}] {e['reflection'][:200]}")
    ctx = "\n\n".join(lines)
    _emit({"ticker": args.ticker, "n_same": len(same), "n_cross": min(len(cross), args.n_cross), "context": ctx})
    return 0


def cmd_stats(args):
    entries = _load_entries(args.log)
    pending = [e for e in entries if e["pending"]]
    resolved = [e for e in entries if not e["pending"]]
    if hasattr(args, 'since') and args.since: resolved = [e for e in resolved if e["date"] >= args.since]
    raws = [x for e in resolved if (x := _parse_pct(e["raw"])) is not None]
    alphas = [x for e in resolved if (x := _parse_pct(e["alpha"])) is not None]
    by_rating = {}
    for e in resolved:
        by_rating.setdefault(e["rating"], []).append(e)
    pr = {}
    for r, es in by_rating.items():
        a = [_parse_pct(e["alpha"]) for e in es if _parse_pct(e["alpha"]) is not None]
        if a: pr[r] = {"count": len(es), "mean_alpha_pct": round(statistics.fmean(a), 2),
                        "alpha_hit_rate": round(sum(1 for x in a if x > 0) / len(a), 3)}
    _emit({"total": len(entries), "pending": len(pending), "resolved": len(resolved),
           "win_rate": round(sum(1 for x in raws if x > 0) / len(raws), 3) if raws else None,
           "alpha_hit_rate": round(sum(1 for x in alphas if x > 0) / len(alphas), 3) if alphas else None,
           "mean_raw_pct": round(statistics.fmean(raws), 2) if raws else None,
           "mean_alpha_pct": round(statistics.fmean(alphas), 2) if alphas else None,
           "by_rating": pr})
    return 0


def cmd_backtest(args):
    entries = _load_entries(args.log)
    resolved = [e for e in entries if not e["pending"]]
    if hasattr(args, 'from_date') and args.from_date: resolved = [e for e in resolved if e["date"] >= args.from_date]
    if hasattr(args, 'to_date') and args.to_date: resolved = [e for e in resolved if e["date"] <= args.to_date]
    if args.rating and args.rating in RATINGS: resolved = [e for e in resolved if e["rating"] == args.rating]
    if not resolved: _emit_err(4, "无符合条件的已结算记录"); return 4
    rows = [{"alpha_pct": _parse_pct(e["alpha"]), "holding_days": _parse_holding(e["holding"]),
             "date": e["date"], "ticker": e["ticker"], "rating": e["rating"]} for e in resolved]

    def _bm(rs):
        a = [r["alpha_pct"] for r in rs if r["alpha_pct"] is not None]
        h = [r["holding_days"] for r in rs if r["holding_days"]]
        out = {"count": len(rs)}
        if a:
            out["mean_alpha_pct"] = round(statistics.fmean(a), 2)
            out["alpha_hit_rate"] = round(sum(1 for x in a if x > 0) / len(a), 3)
            if len(a) >= 2:
                sd = statistics.stdev(a)
                out["alpha_t_stat"] = round(statistics.fmean(a) / (sd / math.sqrt(len(a))), 2) if sd > 1e-9 else None
        if h: out["mean_holding_days"] = round(statistics.fmean(h), 1)
        ann = [r["alpha_pct"] * (365 / r["holding_days"]) for r in rs if r["alpha_pct"] and r["holding_days"]]
        if ann:
            out["annualized_alpha_pct"] = round(statistics.fmean(ann), 2)
            ds = [min(x, 0)**2 for x in ann]
            dd = math.sqrt(sum(ds) / len(ds)) if ds else 0
            out["sortino_like"] = round(statistics.fmean(ann) / dd, 2) if dd > 1e-9 else None
        return out

    by_r = {r: _bm(rs) for r, rs in {r["rating"]: [x for x in rows if x["rating"] == r["rating"]] for r in set(x["rating"] for x in rows)}.items()}
    rows.sort(key=lambda r: r["date"])
    curve, running, peak, md = [], 0.0, 0.0, 0.0
    for r in rows:
        if r["alpha_pct"] is None: continue
        running += r["alpha_pct"]; peak = max(peak, running); md = min(md, running - peak)
        curve.append({"date": r["date"], "cum_alpha_pct": round(running, 2)})
    _emit({"n_decisions": len(rows), "by_rating": by_r, "overall": _bm(rows),
           "cumulative_alpha_curve": curve, "max_cum_alpha_drawdown_pct": round(md, 2)})
    return 0


def main():
    p = argparse.ArgumentParser(f"decision_log v{VERSION}")
    sub = p.add_subparsers(dest="cmd")
    pr = sub.add_parser("record"); pr.add_argument("--date", required=True); pr.add_argument("--ticker", required=True)
    pr.add_argument("--rating", required=True, choices=RATINGS); pr.add_argument("--decision", required=True)
    pr.add_argument("--log", default=DEFAULT_LOG)
    ps = sub.add_parser("resolve"); ps.add_argument("--date", required=True); ps.add_argument("--ticker", required=True)
    ps.add_argument("--raw-return", required=True); ps.add_argument("--alpha", required=True)
    ps.add_argument("--holding", required=True); ps.add_argument("--reflection", required=True)
    ps.add_argument("--rating"); ps.add_argument("--log", default=DEFAULT_LOG)
    pa = sub.add_parser("auto-resolve"); pa.add_argument("--date", required=True); pa.add_argument("--ticker", required=True)
    pa.add_argument("--current-price", type=float, required=True); pa.add_argument("--entry-price", type=float, required=True)
    pa.add_argument("--reflection"); pa.add_argument("--log", default=DEFAULT_LOG)
    pl = sub.add_parser("list"); pl.add_argument("--status", choices=["all","pending","resolved"], default="all")
    pl.add_argument("--ticker"); pl.add_argument("--since"); pl.add_argument("--log", default=DEFAULT_LOG)
    pc = sub.add_parser("context"); pc.add_argument("--ticker", required=True)
    pc.add_argument("--n-same", type=int, default=3); pc.add_argument("--n-cross", type=int, default=2)
    pc.add_argument("--log", default=DEFAULT_LOG)
    pt = sub.add_parser("stats"); pt.add_argument("--since"); pt.add_argument("--log", default=DEFAULT_LOG)
    pb = sub.add_parser("backtest"); pb.add_argument("--from-date"); pb.add_argument("--to-date")
    pb.add_argument("--rating", choices=RATINGS); pb.add_argument("--log", default=DEFAULT_LOG)
    p.add_argument("--schema", action="store_true")
    args = p.parse_args()
    if args.schema:
        print(json.dumps({"name":"decision_log","version":VERSION,"subcommands":["record","resolve","auto-resolve","list","context","stats","backtest"],
                          "default_log_path":DEFAULT_LOG}, ensure_ascii=False, indent=2)); return 0
    if args.cmd == "record": return cmd_record(args)
    if args.cmd == "resolve": return cmd_resolve(args)
    if args.cmd == "auto-resolve": return cmd_auto_resolve(args)
    if args.cmd == "list": return cmd_list(args)
    if args.cmd == "context": return cmd_context(args)
    if args.cmd == "stats": return cmd_stats(args)
    if args.cmd == "backtest": return cmd_backtest(args)
    _emit_err(3, "需要子命令"); return 3


if __name__ == "__main__":
    sys.exit(main())
