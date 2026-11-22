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
    for rid, mn in exp.get("min_count", {}).items():
        if counts.get(rid, 0) < mn:
            errs.append(f"{rid} {counts.get(rid, 0)}건 < 최소 {mn}")
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
# 버전 일치 검사: SKILL.md, plugin.json, marketplace.json, CHANGELOG 최상단
import re as _re
repo = ROOT.parent
skill_ver = _re.search(r"버전 (\d+\.\d+\.\d+)", (repo / "skills/korean-non-ai-writing/SKILL.md").read_text(encoding="utf-8")).group(1)
plugin_ver = json.loads((repo / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
market_ver = json.loads((repo / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))["plugins"][0]["version"]
log_ver = _re.search(r"^## (\d+\.\d+\.\d+)", (repo / "CHANGELOG.md").read_text(encoding="utf-8"), _re.M).group(1)
vers = {"SKILL.md": skill_ver, "plugin.json": plugin_ver, "marketplace.json": market_ver, "CHANGELOG": log_ver}
if len(set(vers.values())) != 1:
    fails += 1
    print("FAIL 버전 불일치", vers)
else:
    print("PASS 버전 일치", skill_ver)

# 금지 기호 검사: 스킬 문서와 사전에 엠대시, 엔대시, 중앙점이 없어야 한다(J3 정의 줄 제외)
for f in [repo / "skills/korean-non-ai-writing/SKILL.md", repo / "skills/korean-non-ai-writing/references/lexicon.md"]:
    bad = [i + 1 for i, line in enumerate(f.read_text(encoding="utf-8").splitlines())
           if _re.search(r"[—–·]", line) and "| J3 |" not in line]
    if bad:
        fails += 1
        print(f"FAIL 금지 기호 {f.name} 줄 {bad}")
    else:
        print(f"PASS 금지 기호 없음 {f.name}")

sys.exit(1 if fails else 0)
