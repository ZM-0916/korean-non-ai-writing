#!/usr/bin/env python3
"""scan.py 회귀 테스트. 사용: python3 tests/run_tests.py"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "skills" / "korean-non-ai-writing" / "scripts"))
import scan  # noqa: E402

expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
fails = 0
for name, exp in expected.items():
    text = (ROOT / "fixtures" / name).read_text(encoding="utf-8")
    findings, _ = scan.scan(text)
    flagged = {f["id"] for f in findings if f["flag"]}
    counts = {f["id"]: f["count"] for f in findings}
    g, _, _ = scan.grade(findings)
    errs = []
    for rid in exp.get("must_flag", []):
        if rid not in flagged:
            errs.append(f"놓침 {rid}")
    for rid in exp.get("must_detect", []):
        if counts.get(rid, 0) == 0:
            errs.append(f"미검출 {rid}")
    for rid in exp.get("must_not_flag", []):
        if rid in flagged:
            errs.append(f"오탐 {rid}")
    for rid, mx in exp.get("max_count", {}).items():
        if counts.get(rid, 0) > mx:
            errs.append(f"{rid} {counts[rid]}건 > 허용 {mx}")
    if "grade_in" in exp and g not in exp["grade_in"]:
        errs.append(f"등급 {g} (기대 {exp['grade_in']})")
    status = "PASS" if not errs else "FAIL"
    fails += bool(errs)
    print(f"{status} {name} 등급 {g} 감지 {sorted(flagged)}")
    for e in errs:
        print("   -", e)
sys.exit(1 if fails else 0)
