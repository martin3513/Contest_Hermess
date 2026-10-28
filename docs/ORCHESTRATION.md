# Orca 팀 실행 계약

WORKFLOW.md의 `orchestrated` 모드에서 적용한다. Claude와 Codex는 같은 계약을 사용하고
`--agent claude` / `--agent codex`만 다르다. 선택한 제공자로 코디네이터·워커를 통일한다.
혼합 팀은 사용자 요청 시 사용한다. 권한은 Orca 설정을 유지한다. 모델은 `docs/MODEL_POLICY.md`와 `kit/model-policy.json`을 따른다.

## 버전별 가이드

`ORCA_CLI_COMMAND`가 있으면 그 실행 파일, 없고 `ORCA_DEV_REPO_ROOT`가 있으면 `orca-dev`,
그 외 Windows에서는 `orca`를 쓴다. 아래 명령의 orca를 선택한 실행 파일로 바꾼다.
Linux의 Orca 외부 셸은 화면낭독기와 혼동하지 않도록 `orca-ide`를 쓴다. 중간에 실행 파일을 바꾸지 않는다.

```text
orca skills get orca-cli --json
orca skills get orchestration --json
orca status --json
```

실제 가이드와 `--help`가 예시보다 우선한다. 연결 불가 시 오류와 연결 방법을 알린다.
팀 실행은 실제 Orca Task/Dispatch를 사용한다. Claude Task나 Codex 내장 subagent로 대체하지 않는다.

## 분할과 소유권

기존 `_workspace/orchestration.json`을 확인한다. 실행 중·상태 불명 Dispatch가 있으면
새 Run/워커를 중복 생성하지 않고 복구 가이드를 따른다. 모든 워커 정리가 확인되면 새 구간을 시작한다.

```text
orca orchestration run-create --objective "대회명: 공고 분석부터 목차 승인까지" --json
orca orchestration worker-start --spec "자기완결 작업 명세" --worktree current --agent codex --model <MODEL_ID> --json
```

spec에는 다음을 실제 값으로 넣는다. 셸 문자열 결합 대신 안전한 인자 배열을 사용한다.

- Target: 대회 절대 경로, `agents/<역할>.md`, 읽어도 되는 파일 목록.
- Change: 이번 산출물과 필수 내용.
- Constraints: 원본 읽기 전용, 사실 조작 금지, Git commit/push 금지.
- Ownership: 이 워커만 쓰는 출력 절대 경로. state.json·다른 워커 파일 수정 금지.
- Acceptance: 배점 합계·출처·필수 항목 등 확인할 내용.
- 완료 보고는 주입된 preamble의 Task/Dispatch/handle과 worker_done 명령을 그대로 따른다.

분석 완료 → 필요한 조사 → 목차 순서다. 관련 없는 조사 파일에는 생략 이유를 남긴다. 단순 조사는 한 워커에 묶어 맡기며 동시 워커는 기본 2개로 제한한다.
사용자 요청과 사용량 여유가 있으면 최대 4개로 늘린다. 범위별·섹션별 출력으로 동시 쓰기를 막는다.
심사는 새 워커로 실행하고 작성 과정·리서치 메모·이전 심사를 주지 않는다.
같은 폴더의 읽기 제한은 작업 계약이며 OS 수준 격리가 아니다.

## 감독과 종료

시작 영수증의 Task·Dispatch·handle을 저장하고 기대한 모든 작업이 정산될 때까지 감독한다.
한 번에 60초 이하로 기다리고 사용자에게 진행을 알린다.

```text
orca orchestration check --wait --types "worker_done,escalation,question" --timeout-ms 60000 --json
orca orchestration reply --id <질문ID> --body "답변" --json
orca orchestration worker-release --dispatch <정산된DispatchID> --json
orca orchestration check --ack <처리한DeliveryID> --json
```

Delivery의 모든 메시지를 처리한 후 ack한다. 완료 Dispatch가 기대한 시도인지 확인하고 산출물을 검사한다.
accepted settlement가 확인된 워커만 release한다. 실패 보고도 실패로 기록하고 정리한다.
유효한 worker_done이 Task를 자동 정산하므로 별도 completed 갱신을 하지 않는다.
빈 대기 3회 후 worker-list --include-remote --json의 attention/nextAction과 모든 페이지를 확인한다.
timeout·연결 끊김은 종료 증거가 아니다. live/unverifiable/exited를 구분한다.

worker-start 실패·복구·중단·불명확한 release는 아래 가이드를 읽고 정확한 후속 명령을 따른다.
자동 재시작이나 terminal close로 대체하지 않는다.

```text
orca skills get orchestration --reference references/recovery-and-cleanup.md --json
```

사용자 승인 대기 전 모든 기대 Dispatch를 정산하고 워커를 정리한다.
worker-list --run <RunID> --terminal-state reclaimable --json에 남은 항목이 없어야 한다.
작업별 성공/실패·근거·남은 문제를 기록하고 다음 승인 후 새 구간을 실행한다.

모델 배정·승격 이유·요청/확인 모델은 orchestration.json에 기록한다. 작업 시작·완료·실패·승인 대기 때 state.json의 progress를 갱신한다. 읽기 전용 모니터는 `python start.py status "대회명" --watch`다. 기록 시각은 워커 생존 증거가 아니다. 오래된 기록은 기존 감독 루프에서 worker-list/worker-show로 확인한다.
