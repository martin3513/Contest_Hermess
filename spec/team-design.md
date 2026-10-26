# 공통 역할과 파일 규약

실행 순서·승인·재개 규칙의 단일 원본은 `WORKFLOW.md`다.
역할 계약은 `agents/<역할>.md`, 런타임 계약은 `docs/ORCHESTRATION.md`다.

| 역할 | 입력 | 출력 (대회 폴더 기준) |
|---|---|---|
| requirements-analyst | input, 프로필 | docs/requirements.md |
| researcher | requirements, 지정 범위 | _workspace/research/<범위>.md |
| outline-designer | requirements, research, 프로필 | docs/outline.md |
| writer | outline, research, 수정 지시 | _workspace/draft/NN_<섹션>.md |
| judge-reviewer | 공고, requirements, 초안, 프로필 | _workspace/review/round-N.md |
| consistency-checker | requirements, outline, draft, research | _workspace/review/consistency.md |

조사는 official/cases/market/policy 4종이며 내용은 프로필에서 읽는다.
동시 워커 기본 2개, 사용자 요청 시 최대 4개다. 같은 파일을 여러 워커에게 맡기지 않는다.
작성·목차는 korean-report-style, 심사·정합성은 report-quality-checks를 사용한다.
심사는 새 워커로 실행하고 작성 대화·리서치 메모·이전 심사를 주지 않는다.
단독 모드의 심사는 자체 검토로 표시한다.

## 파일 규약

`contests/<대회명>/input/` 원본 / `output/` 최종 / `docs/` 요구사항·목차·이력 / `_workspace/` 중간물.
코디네이터만 state.json을 갱신하고 워커는 지정 출력만 쓴다.
모델은 Orca 설정을 따른다. 제공자 전환 시 파일을 그대로 재사용한다.

```json
{"schema_version":1,"profile":"idea_proposal","stage":"approval_1","round":0,"scores":[],"approvals":{},"updated":"2026-10-27T00:00:00+09:00"}
```

작업 이력의 `## 다음 단계 참조`에 미해결·핵심 결정·다음 단계와 입력을 기록한다.
공고문 배점이 프로필보다 우선하며 분량 배분은 korean-report-style을 따른다.
