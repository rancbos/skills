#!/usr/bin/env python3
"""
health_check.py — jw-investment-data 全源健康检查 v1.0
═══════════════════════════════════════════════════════

检测所有数据源的可用性。每个源独立测试，超时 10s。

用法:
  python health_check.py                  # JSON 输出
  python health_check.py --format markdown # 人读表格
  python health_check.py --schema          # 自描述

退出码: 0=全通, 1=部分故障, 4=全挂
"""

import argparse, json, os, sys, time, urllib.request, urllib.error
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

__version__ = "1.0.0"

_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

EASTMONEY_BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; jw-health-check/1.0)"}
TIMEOUT = 10


def _em_fetch(report_name: str) -> bool:
    """东方财富端点连通性测试"""
    url = (f"{EASTMONEY_BASE}?sortColumns=REPORT_DATE&sortTypes=-1"
           f"&pageSize=1&pageNumber=1&reportName={report_name}&columns=ALL")
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        return bool(data.get("success") and data["result"] and data["result"]["data"])
    except Exception as e:
        return False


def _check_lpr() -> bool:
    """中国货币网 LPR"""
    url = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHis?pageSize=1&pageNum=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        return bool(data.get("records"))
    except:
        return False


def _check_worldbank() -> bool:
    """世界银行 API"""
    url = "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json&per_page=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        return len(data) > 1 and bool(data[1])
    except:
        return False


def _check_baostock() -> dict:
    """Baostock 登录+货币查询"""
    try:
        import baostock as bs
        old = sys.stdout
        dn = open(os.devnull, 'w')
        sys.stdout = dn
        lg = bs.login()
        sys.stdout = old
        dn.close()
        if lg.error_code != '0':
            return {"login": False, "money": False}
        rs = bs.query_money_supply_data_month(start_date='2026-04', end_date='2026-05')
        money_ok = (rs.error_code == '0' and rs.next())
        sys.stdout = dn = open(os.devnull, 'w')
        bs.logout()
        sys.stdout = old
        dn.close()
        return {"login": True, "money": money_ok}
    except:
        return {"login": False, "money": False}


def run_checks() -> dict:
    """并行全源检查"""
    results = {}
    start = time.time()

    # 东方财富（串行即可，同一域名）
    results["eastmoney_cpi"] = _em_fetch("RPT_ECONOMY_CPI")
    results["eastmoney_pmi"] = _em_fetch("RPT_ECONOMY_PMI")
    results["eastmoney_gdp"] = _em_fetch("RPT_ECONOMY_GDP")
    results["eastmoney_ppi"] = _em_fetch("RPT_ECONOMY_PPI")
    results["eastmoney_m2"] = _em_fetch("RPT_ECONOMY_MONEY")

    # 外部源并行
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(_check_baostock): "baostock",
            ex.submit(_check_lpr): "chinamoney_lpr",
            ex.submit(_check_worldbank): "worldbank",
        }
        for f in as_completed(futures):
            name = futures[f]
            try:
                val = f.result()
                results[name] = val
            except:
                results[name] = False

    elapsed_ms = int((time.time() - start) * 1000)

    # 汇总
    def _count_ok(d):
        return sum(1 for v in d.values() if v is True)

    flat_results = {}
    for k, v in results.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                flat_results[f"{k}_{sub_k}"] = sub_v
        else:
            flat_results[k] = v

    ok_count = _count_ok(flat_results)
    total = len(flat_results)
    all_ok = ok_count == total
    all_fail = ok_count == 0

    return {
        "ok": not all_fail,
        "source": "health_check",
        "data": {
            "checks": results,
            "summary": {
                "ok": ok_count,
                "fail": total - ok_count,
                "total": total,
                "status": "✅ ALL GOOD" if all_ok else ("❌ ALL DOWN" if all_fail else "⚠️ PARTIAL"),
                "elapsed_ms": elapsed_ms,
            },
        },
        "ts": int(time.time()),
        "meta": {"version": __version__},
    }


def _format_markdown(result: dict) -> str:
    data = result["data"]
    summary = data["summary"]
    checks = data["checks"]

    lines = [
        "# 🏥 数据源健康检查",
        "",
        f"| 状态 | OK | 失败 | 总计 | 耗时 |",
        f"|:---|:--:|:--:|:--:|:--:|",
        f"| **{summary['status']}** | {summary['ok']} | {summary['fail']} | {summary['total']} | {summary['elapsed_ms']}ms |",
        "",
        "## 详细结果",
        "",
        "| 数据源 | 状态 |",
        "|:---|:--:|",
    ]

    for name, status in checks.items():
        if isinstance(status, dict):
            for sub, sub_ok in status.items():
                icon = "✅" if sub_ok else "❌"
                lines.append(f"| {name}.{sub} | {icon} |")
        else:
            icon = "✅" if status else "❌"
            lines.append(f"| {name} | {icon} |")

    lines += [
        "",
        "---",
        f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CST",
        f"🔧 health_check v{__version__}",
    ]
    return "\n".join(lines)


def _schema_json() -> str:
    return json.dumps({
        "name": "health_check", "version": __version__,
        "description": "jw-investment-data 全源健康检查",
        "sources": ["eastmoney(CPI/PMI/GDP/PPI/M2)", "baostock", "chinamoney(LPR)", "worldbank"],
        "output": {"ok": "bool", "data.checks": "{source: bool|dict}", "data.summary": "{ok,fail,total,status,elapsed_ms}"},
        "exit_codes": {"0": "全通", "1": "部分故障", "4": "全挂"},
    }, ensure_ascii=False, indent=2)


def main():
    p = argparse.ArgumentParser(f"health_check v{__version__}")
    p.add_argument("--format", default="json", choices=["json", "markdown"])
    p.add_argument("--schema", action="store_true")
    p.add_argument("--version", action="store_true")
    args = p.parse_args()

    if args.schema:
        print(_schema_json())
        return 0
    if args.version:
        print(f"health_check v1.0.0")
        return 0

    result = run_checks()
    summary = result["data"]["summary"]

    if args.format == "markdown":
        print(_format_markdown(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if summary["status"] == "✅ ALL GOOD":
        return 0
    elif summary["status"] == "❌ ALL DOWN":
        return 4
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
