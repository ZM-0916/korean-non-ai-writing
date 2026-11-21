# korean-non-ai-writing

한국어 글을 AI 티 없이 쓰고, AI가 쓴 한국어를 자연스럽게 고치는 Claude 스킬.

```
결론적으로, 이번 프로젝트는 우리 조직에 있어서 매우 중요한 의미를 지닌다고 할 수 있습니다.
→ 이번 프로젝트로 고객 데이터를 분석하는 체계가 생겼습니다.
```

## 다른 한국어 humanizer와 다른 점

| | 이 스킬 | 기존 한국어 humanizer 대부분 |
|---|---|---|
| 용도 | 새로 쓰기 + 고치기 + 진단 | 고치기 위주 |
| 장르 | 8개 장르별 적용 강도 표(슬라이드, 광고 카피, 자소서 포함) | 산문 위주 |
| 카피 기법 | 대비 훅, 셋 묶음 같은 카피 정석 기법은 1회 허용 | 일괄 AI 티로 처리 |
| Claude 말버릇 | "~를 먼저 본다", "축" 비유 등 Claude 출력 특유 표현을 별도 범주로 관리 | 없음 |
| 규제 업종 | 의료, 화장품, 금융 카피의 과장 표현에 `[규정 확인]` 표시 | 없음 |
| 표현 사전 | 대상과 어울리는 국내 표현을 매일 조사해 보강(`references/lexicon.md`) | 없음 |
| 회귀 테스트 | 스캔 스크립트 + 오탐 방지 테스트 | 일부만 |

## 설치

**claude.ai / Claude 데스크톱**
1. 이 저장소에서 `skills/korean-non-ai-writing` 폴더를 ZIP으로 압축한다.
2. Customize > Skills에서 업로드한다.

**Claude Code**
```
git clone https://github.com/<owner>/korean-non-ai-writing.git
cp -r korean-non-ai-writing/skills/korean-non-ai-writing ~/.claude/skills/
```

## 사용

- 고치기: "이 글 AI 티 빼줘" + 글
- 진단만: "AI 흔적만 찾아줘, 고치지 말고"
- 새로 쓰기: "팀장님께 보낼 일정 변경 메일 써줘"
- 금지어 지정: "금지=활용,매우 / 선호=유용하다→쓸만하다"
- 내 말투로: 자기 글 2~3단락을 같이 붙인다

스캔 스크립트만 따로 쓸 수도 있다.
```
python3 skills/korean-non-ai-writing/scripts/scan.py 글.txt
```

## 하지 않는 것

- AI 탐지기 우회. 오타 넣기나 번역기 왕복처럼 글을 망치는 기법은 쓰지 않는다.
- 표절, 대필 은폐, 학업, 채용, 심사 절차 우회.
- 사실 확인과 출처 보강. 문체만 다룬다.

## 구조

```
skills/korean-non-ai-writing/
  SKILL.md          스킬 본체 (패턴 카탈로그 A~L, 장르 규칙, 절차)
  scripts/scan.py   정규식 1차 스캔 (표현 사전도 읽음)
  references/lexicon.md  표현 사전
examples/           장르별 원문 → 결과 예시
tests/              스캔 회귀 테스트 (python3 tests/run_tests.py)
docs/daily-research.md  매일 표현 조사 절차
```

## 기여

새 패턴, 오탐 사례, Claude 말버릇 제보는 이슈로 받는다. 절차는 [CONTRIBUTING.md](CONTRIBUTING.md).

## 참고한 프로젝트

패턴 체계는 아래 공개 프로젝트를 참고해 새로 정리했다. 문장을 옮기지 않고 기준과 아이디어를 참고했다.

- [blader/humanizer](https://github.com/blader/humanizer): Wikipedia "Signs of AI writing" 기반 26개 패턴
- [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai): 한글 AI 티 분류 체계, 심각도, 변경률 가드
- [IsaacEryn/humanizer-ko](https://github.com/IsaacEryn/humanizer-ko): 한국어 정상 관습 오탐 방지
- [calintzy/hangeul-deai](https://github.com/calintzy/hangeul-deai): 화자, 독자 관계, 탐지 회피 배제 원칙
- [dotoridot/korean-humanizer](https://github.com/dotoridot/korean-humanizer): 금지어, 선호어 지정
- [hjongc/humanizer-kr](https://github.com/hjongc/humanizer-kr): 장르별 처리
- [DaleSeo/korean-skills](https://github.com/DaleSeo/korean-skills): 쉼표 패턴 근거

## 라이선스

MIT
