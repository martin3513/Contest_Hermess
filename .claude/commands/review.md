---
description: 현재 초안을 심사위원 기준으로 다시 채점하고 정합성을 검사한다
argument-hint: "[대회명]"
---

현재 초안을 다시 채점한다. 인자: `$ARGUMENTS` (대회명, 생략 시 가장 최근에 작업한 대회)

1. 대회 폴더를 정한다. 생략됐으면 `contests/*/_workspace/state.json` 중 `updated` 가 가장 최근인 대회를 쓰고, 어느 대회인지 한 줄로 알린다.
2. `_workspace/draft/` 가 비어 있으면 "아직 초안이 없다"고 알리고 멈춘다.
3. `judge-reviewer` 에이전트로 채점한다. 입력은 `docs/requirements.md` 와 초안 파일만 준다 (리서치·대화 내용은 주지 않는다).
   결과는 다음 번호의 `_workspace/review/round-N.md`.
4. `consistency-checker` 에이전트로 정합성 검사를 한다 → `_workspace/review/consistency.md`.
5. `state.json` 의 `round`·`scores` 를 갱신한다.
6. 사용자에게: 총점(이전 라운드 대비 변화), 감점이 큰 항목 3개, 치명 정합성 문제 개수.
   그리고 "지적 사항을 반영할까요?"라고 묻는다. 반영은 사용자가 원할 때만 writer 로 한다 (반복 상한 3회 유지).
