#!/usr/bin/env python3
"""한국어 AI 티 1차 스캔.

정규식으로 표현 후보와 리듬 지표만 뽑는다. 판정은 SKILL.md §3 원칙으로 한다.
사용: python3 scan.py 파일.txt [--json]
      cat 파일.txt | python3 scan.py - [--json]
"""
import json
import pathlib
import re
import statistics
import sys

# (ID, 심각도, 설명, 정규식)
RULES = [
    ("A1", "S2", "~에 대해", r"에\s?대(해|한|하여)"),
    ("A2", "S2", "~를 통해", r"[을를]\s?통(해|하여|한)"),
    ("A3", "S1", "~에 있어(서)", r"에\s?있어(서)?(?=[\s,.])"),
    ("A4", "S2", "~와 관련하여/~에 기반하여", r"(와|과)\s?관련(하여|해서|된|한)|에\s?기반(하여|한|해)"),
    ("A5", "S1", "가지고 있다", r"[을를]\s?가지고\s?있"),
    ("A6", "S1", "이중 피동", r"되어(지|진|져)"),
    ("A7", "S2", "~에 의해", r"에\s?의(해|하여|한)\s"),
    ("A8", "S2", "이루어지다/만들어지다", r"(이루어|만들어)(지|졌|진|져)"),
    ("A13", "S2", "~되고 있다", r"되고\s?있(다|습니다|는|어)"),
    ("A14", "S2", "단순한 X를 넘어", r"단순(한|히)\s?\S+\s?넘어"),
    ("A15", "S3", "더 이상 ~않다", r"더\s?이상\s?\S+\s?(않|없|아니)"),
    ("B2", "S2", "과시용 영어", r"시너지|레버리지|인사이트|임팩트|퍼포먼스"),
    ("C1", "S1", "A가 아니라 B 대비", r"아니라\s|아니다\.\s"),
    ("C5", "S2", "섹션 안내", r"(이\s?글|본\s?글|이번\s?(장|글|섹션|슬라이드))에서는"),
    ("C7", "S2", "연결어미 뒤 쉼표", r"[가-힣](?<!그리)(고|며|지만|는데|면서|으나|므로),"),
    ("D1", "S1", "결산 어휘", r"결론적으로|요약하자면|종합하면|정리하자면"),
    ("D2", "S1", "의의 과장", r"주목할\s?만|시사하는\s?바|중요한\s?의미|의미가\s?크"),
    ("D3", "S1", "열거 도입구", r"(두|세|네|다섯)\s?가지(로)?\s?(나눌|정리할|살펴볼|요약할)\s?수"),
    ("D4", "S1", "과장 어휘", r"혁신적|획기적|압도적|차별화된|완벽한|최적의|극대화"),
    ("D5", "S2", "의인화 추상 주어", r"(시장|데이터|숫자|역사|현실|시대)(이|가|은|는)\s?(묻|말해|보여|증명)"),
    ("D6", "S2", "~할 때입니다", r"할\s?때(입니다|이다)"),
    ("D7", "S2", "X에서 Y로 공식", r"(시대|경쟁|패러다임)에서\s?\S+\s?(시대|경쟁|패러다임)?(으로|로)"),
    ("D8", "S2", "분열문 중요한 것은", r"(중요한|필요한)\s?(것은|건)|핵심은\s"),
    ("D9", "S2", "결국 ~로 이어진다/~하는 이유다", r"결국\s?\S+\s?(으로|로)\s?이어|이유(다|입니다)\."),
    ("D10", "S2", "막연한 시간 지평", r"향후|앞으로의\s?시대"),
    ("D11", "S2", "내용 없는 과제 문단", r"과제(도|가)\s?(남아|있다|존재)"),
    ("D12", "S2", "생성형 은유", r"새로운\s?지평|퍼즐의\s?(마지막\s)?조각|게임\s?체인저|패러다임"),
    ("D14", "S2", "출처 없는 권위", r"전문가들(은|에\s?따르면)|(많은|여러)\s?연구(에\s?따르면|에서)"),
    ("F1", "S2", "정도부사", r"(매우|정말|굉장히|상당히|대단히)\s"),
    ("F3", "S2", "-적 연쇄", r"\S+적[,·\s]+\S+적[,·\s]+\S+적"),
    ("F4", "S2", "범용 정책 동사", r"(강화|확대|개선|구축|고도화)(하|해|할|한|합|을|를|\s|\.)"),
    ("G2", "S2", "다중 완곡", r"수\s?있을\s?것으로|할\s?수\s?있을\s?것|가능성이\s?있을\s?수|라고\s?할\s?수\s?있"),
    ("G3", "S2", "~할 수 있다 반복", r"수\s?있(다|습니다|어요)"),
    ("H1", "S2", "문두 접속사", r"(^|[.!?]\s+)(또한|따라서|나아가|더불어|게다가|아울러|한편)"),
    ("H2", "S2", "이는 ~ 반복", r"(^|[.!?]\s+)이는\s"),
    ("H3", "S2", "즉 남발", r"(^|\s)즉,?\s"),
    ("H4", "S2", "끊고 접속부사로 잇기", r"[.!?]\s+(그래서|그러므로|그러니까|그렇기\s?때문에|그\s?결과로?)\s"),
    ("I2", "S2", "점, 바 형식명사", r"(주목할|중요한|눈여겨볼)\s?점은|바와\s?같이"),
    ("I3", "S2", "~라는 것이다", r"라는\s?것(이다|입니다)"),
    ("I4", "S2", "~것이 중요하다/필요하다", r"것이\s?(중요|필요)"),
    ("I5", "S2", "무주체 판정", r"다는\s?(분석|평가|전망|지적)(이다|입니다)"),
    ("J1", "S2", "볼드", r"\*\*[^*\n]+\*\*"),
    ("J3", "S1", "엠대시, 엔대시, 중앙점(절대 금지)", r"[—–·‧・]"),
    ("J5", "S1", "이모지, 화살표 장식", r"[\U0001F300-\U0001FAFF☀-➿]|[→⇒➡]"),
    ("K1", "S1", "챗봇 인사, 마무리", r"좋은\s?질문|도움이\s?(되셨|되었)(기를|길|으면)|궁금한\s?(점|사항)(이|은)"),
    ("K2", "S1", "지식 한계 면책", r"최신\s?정보(와|는)\s?다를|학습\s?데이터\s?기준"),
    ("K3", "S1", "아부하는 톤", r"(훌륭한|멋진)\s?(아이디어|계획|생각|질문)"),
    ("K4", "S1", "예고, 연출된 솔직함", r"지금부터|솔직히\s?말하면|자,\s?이제|알아보겠습니다|살펴보겠습니다"),
    ("K5", "S1", "변경 이력 서술", r"(수정|개선|다듬은)\s?(한\s)?(버전|글)입니다"),
    ("L1", "S1", "~를 먼저 본다", r"[을를]\s?먼저\s?(본다|봅니다|보자|보겠|살펴)|부터\s?(본다|봅니다|보자)(?=[\s.,]|$)|먼저\s?(\S+\s){0,3}?\S*[을를]\s?(본다|봅니다|보자|보겠|살펴)|[을를]\s?먼저\s?(합니다|해요|한다|하고|하는|했|할|드립니다|드려요|진행)"),
    ("L2", "S1", "축 비유", r"(핵심|중심|주요|하나의|두|세|네|다섯)\s?(가지\s?)?축|[을를]\s?축으로"),
    ("L3", "S2", "짚어보면", r"짚어\s?(보면|보자|보겠)|짚고\s?넘어"),
    ("L4", "S2", "결이 다르다", r"결이\s?(다르|같)"),
    ("L5", "S2", "지점", r"(이|그|흥미로운|중요한)\s?지점"),
    ("L6", "S2", "결론부터 말하면", r"결론부터\s?말하면|한\s?줄로\s?(요약|정리)"),
    ("L7", "S2", "~하는 셈이다", r"셈(이다|입니다)"),
    ("L8", "S2", "레이어, 프레임", r"레이어|프레임"),
    ("L10", "S1", "~하는 자리", r"(는|은|던)\s자리(입니다|이다|예요|에요|였|가\s?되|가\s?될|로\s|를\s?(마련|가지|가졌|만들))"),
    ("L11", "S1", "같이 하는 사람 없는 함께", r"[을를]\s?함께\s?(합니다|해요|하는|할|하겠|하며|나누|나눠|나눕|만들|고민|걸어|성장)|(^|[\s.,])함께\s?(나누|나눠|나눕|고민|만들어\s?가|걸어\s?가|성장)|함께(합니다|해요|하는|할게|하겠|하며)"),
    ("L9", "S1", "절차나 일을 닫는다", r"(절차|단계|과정|작업|업무|논의|이야기|대화|질문|루프|고리|사이클|프로세스|세션|챕터|건)(을|를|은|는|도)?\s(\S+\s){0,3}?닫(는|고|았|자|아|으며|을|기|습)"),
]

LEXICON = pathlib.Path(__file__).resolve().parent.parent / "references" / "lexicon.md"


def load_lexicon():
    """references/lexicon.md 표에서 탐지 정규식을 읽는다. 확정은 S1, 후보는 S2."""
    rules = []
    if not LEXICON.exists():
        return rules
    for line in LEXICON.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| M"):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]]
        if len(cells) < 6:
            continue
        rid, status, target, bad, good, pat = cells[:6]
        pat = pat.strip("`").replace("\\|", "|")
        if not pat:
            continue
        sev = "S1" if status == "확정" else "S2"
        rules.append((rid, sev, f"{target}: {bad} → {good}", pat))
    return rules


RULES += load_lexicon()

# 실제로 닫는 대상이 "닫" 바로 앞에 오면 L9에서 제외
CLOSE_EXCEPT = re.compile(r"(문|창|창문|탭|앱|창구|가게|매장|점포|계좌|이슈|PR|뚜껑|입)(을|를|은|는|도)?\s?닫")

# 학술 용어로서의 축은 L2에서 제외
AXIS_EXCEPT = re.compile(r"(HPA|장-?뇌|좌표|[xyzXYZ]|시상하부|뇌하수체|부신|세로|가로|회전)\s?축")

S2_PARA_LIMIT = 3   # 한 문단 3회 이상
S2_DOC_LIMIT = 4    # 문서 전체 4회 이상
G3_DOC_LIMIT = 4


def split_paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in parts if len(s.strip()) > 1]


def scan(text):
    paras = split_paragraphs(text)
    findings = []
    for rid, sev, desc, pat in RULES:
        rx = re.compile(pat, re.MULTILINE)
        per_para = []
        samples = []
        for p in paras:
            hits = []
            for m in rx.finditer(p):
                if rid == "L9" and CLOSE_EXCEPT.search(p[m.start():m.end()]):
                    continue
                if rid == "L2":
                    window = p[max(0, m.start() - 8):m.end()]
                    if AXIS_EXCEPT.search(window):
                        continue
                hits.append(m)
            per_para.append(len(hits))
            for m in hits[:2]:
                s, e = max(0, m.start() - 12), min(len(p), m.end() + 12)
                samples.append(p[s:e].replace("\n", " "))
        total = sum(per_para)
        if total == 0:
            continue
        para_max = max(per_para)
        if sev == "S1":
            flag = True
        elif rid == "G3":
            flag = total >= G3_DOC_LIMIT
        elif sev == "S2":
            flag = para_max >= S2_PARA_LIMIT or total >= S2_DOC_LIMIT
        else:
            flag = False
        findings.append({
            "id": rid, "severity": sev, "desc": desc, "count": total,
            "para_max": para_max, "flag": flag, "samples": samples[:3],
        })

    # 리듬 지표
    sents = split_sentences(text)
    metrics = {"sentences": len(sents)}
    if len(sents) >= 6:
        lens = [len(s) for s in sents]
        mean = statistics.mean(lens)
        cv = statistics.pstdev(lens) / mean if mean else 0
        metrics["length_cv"] = round(cv, 2)
        comma_ratio = sum(1 for s in sents if "," in s) / len(sents)
        metrics["comma_sentence_ratio"] = round(comma_ratio, 2)
        endings = [re.sub(r"[.!?\s]+$", "", s)[-2:] for s in sents]
        run, best = 1, 1
        for a, b in zip(endings, endings[1:]):
            run = run + 1 if a == b else 1
            best = max(best, run)
        metrics["max_same_ending_run"] = best
        if cv < 0.25:
            findings.append({"id": "E1", "severity": "S2", "desc": "문장 길이 균일",
                             "count": 1, "para_max": 1, "flag": True,
                             "samples": [f"변동계수 {cv:.2f}"]})
        if comma_ratio > 0.5:
            findings.append({"id": "C8", "severity": "S2", "desc": "쉼표 문장 비율 과다",
                             "count": 1, "para_max": 1, "flag": True,
                             "samples": [f"{comma_ratio:.0%}"]})
        if best >= 3:
            findings.append({"id": "E2", "severity": "S2", "desc": "같은 종결 연속",
                             "count": best, "para_max": best, "flag": True,
                             "samples": [f"최대 {best}연속"]})
    return findings, metrics


def grade(findings):
    s1 = sum(1 for f in findings if f["flag"] and f["severity"] == "S1")
    s2 = sum(1 for f in findings if f["flag"] and f["severity"] == "S2")
    if s1 >= 3:
        g = "D"
    elif s1 >= 1 or s2 >= 5:
        g = "C"
    elif s2 >= 3:
        g = "B"
    else:
        g = "A"
    return g, s1, s2


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    src = args[0] if args else "-"
    text = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    findings, metrics = scan(text)
    g, s1, s2 = grade(findings)
    if as_json:
        print(json.dumps({"grade": g, "s1": s1, "s2": s2, "metrics": metrics,
                          "findings": findings}, ensure_ascii=False, indent=2))
        return
    print(f"예비 등급 {g} (S1 {s1}건, S2 {s2}건)  지표 {metrics}")
    print("후보일 뿐이다. 판정은 SKILL.md §3 원칙과 장르 예외로 한다.\n")
    for f in sorted(findings, key=lambda x: (not x["flag"], x["severity"], x["id"])):
        mark = "●" if f["flag"] else "○"
        ex = " | ".join(f["samples"])
        print(f"{mark} {f['id']:<4} {f['severity']} {f['desc']} ×{f['count']} (문단 최대 {f['para_max']})  {ex}")


if __name__ == "__main__":
    main()
