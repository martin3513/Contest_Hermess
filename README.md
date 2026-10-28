# Contest Hermess — Orca 보고서 작업 공간

**`시작.cmd` 하나를 열어 Claude Code 또는 Codex를 선택하면 됩니다.**
이 폴더에서 공고 분석 → 조사 → 목차 → 작성·심사 → HWPX 출력을 반복합니다.

## 바로 시작

1. Orca에서 이 폴더를 열고 사용할 Claude Code/Codex 계정에 로그인합니다.
2. `시작.cmd`를 더블클릭합니다. Python 3.10 이상이 필요합니다.
3. **1번**으로 대회 폴더를 만들고 **5번**으로 자료 폴더를 엽니다.
4. 공고·양식·참고자료를 `contests/<대회명>/input/`에 넣습니다.
5. **2번 Claude Code / 3번 Codex**를 고르고 **1 팀 작업 / 2 단독 작업**을 선택합니다.
6. Orca 대화에서 목차·초안·최종 파일을 확인합니다. 결과는 **6번** 또는 `output/`에서 봅니다.

HWPX 출력 패키지 설치: `python -m pip install -r requirements-hwpx.txt`

## 사용법과 구성

네이밍도 지원합니다. 시작 메뉴에서 제공자·실행 방식 선택 후 **2 네이밍**을 고르세요.
input에 대상·고객·원하는 느낌·금지어를 적은 브리프를 넣으면 후보 12개와 추천 3개를 만듭니다.

모델은 [배정 파일](kit/model-policy.json)에서 바꿉니다. 기본은 경량/일반 모델이며 Astra·Opus는 어려운 판단에만 제한적으로 사용합니다. [모델 운영 규칙](docs/MODEL_POLICY.md)을 참고하세요. 이미 열린 대화의 모델은 변경되지 않습니다.

진행 상황은 **메뉴 9 자동 조회**를 권합니다. 기존 대회가 번호로 표시되므로 번호를 선택하면 해당 대회만 5초마다 확인합니다. 별도 터미널에서도 다음 명령으로 볼 수 있으며 AI 호출은 없습니다.

```powershell
python start.py status "대회명" --watch
```

현재 단계·역할별 모델·상태·다음 작업·차단 요인·최근 기록 시각을 표시합니다. 종료는 Ctrl+C입니다. 파일에 저장된 상태이므로 워커의 실시간 생존 여부와는 다르며, 토큰 실측이 없으면 미수집으로 표시합니다.

```powershell
python start.py launch "대회명" --agent codex --task naming --preview
```

`--preview`를 빼면 실행합니다. 코디네이터만 바꾸려면 `--model <모델ID>`를 추가합니다. 역할별 워커 배정은 팀 모드에 적용됩니다.

- **[자세한 한국어 사용법](docs/USAGE.md)** — 설치, 매일 사용, 재개, 제공자 변경, 문제 해결
- [공통 작업 절차](WORKFLOW.md) — 두 제공자의 실행 규칙
- [Orca 오케스트레이션](docs/ORCHESTRATION.md) — 워커 분업·감독·정리
- [검증 결과](docs/build/결과서.md) — 확인한 범위와 한계
- [유지보수 방법](BUILD.md) — 변경·동기화·테스트

| 위치 | 용도 |
|---|---|
| `시작.cmd`, `start.py` | 메뉴 실행 및 Orca 연결 |
| `contests/<대회명>/input/` | 사용자가 넣는 원본 |
| `contests/<대회명>/output/` | 최종 보고서 |
| `contests/<대회명>/docs/` | 목차·요구사항·작업 이력 |
| `contests/<대회명>/_workspace/` | 조사·초안·심사·상태 |
| `agents/`, `kit/` | 공통 역할·문체·채점·프로필·출력 코드 |
| `CLAUDE.md`, `.claude/` | Claude Code 진입점 |
| `AGENTS.md`, `.agents/` | Codex 진입점 |

`시작.cmd`는 하나의 진입점이며 저장소 전체가 필요합니다.
대회 자료·결과는 Git 제외이므로 별도로 백업하세요.
팀 모드는 실제 Orca 워커를 사용합니다. 단독 모드는 같은 에이전트의 자체 검토입니다.
기존 실행은 같은 Orca 대화에서 재개하고 새 대화가 필요할 때만 메뉴 7의 안내를 따릅니다.
한글 파일은 제출 전 한글에서 서식을 확인하고 제출은 직접 합니다.

## 참고

- [Codex 프로젝트 지침](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex 스킬](https://learn.chatgpt.com/docs/build-skills)
- Orca 계약: `orca skills get orca-cli --json`, `orca skills get orchestration --json`
- [HWPX 처리](https://github.com/airmang/python-hwpx)
- [초기 키트 설계 참고 myharness](https://github.com/cookyman74/my_harness) — 현재 실행에는 설치 불필요
