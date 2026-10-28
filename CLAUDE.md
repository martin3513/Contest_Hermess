# Contest Hermess — Claude Code

Orca에서 반복 사용하는 공모전 보고서 작업 공간이다. 한국어로 설명한다.
보고서 요청은 `WORKFLOW.md`를 읽고 실행한다. 개발 키트 빌드를 다시 할 필요가 없다.
공통 스킬은 `kit/skills/`, 프로필은 `kit/profiles/`, 역할은 `agents/`다.
Claude 진입점은 `.claude/skills/contest-report/SKILL.md`, 역할 어댑터는 `.claude/agents/`다.
Orca 팀 모드는 `docs/ORCHESTRATION.md`를 따른다. Claude 내장 Task로 대체하지 않는다.
원본은 `contests/<대회명>/input/`, 결과는 `output/`, 상태는 `_workspace/state.json`이다.
원본을 변경하지 않는다. 대회 파일은 기본 Git 제외다. 제출·메일은 사람이 직접 한다.
코드·사용법 수정에는 보고서 승인 절차를 적용하지 않는다.

네이밍은 `WORKFLOW.md`의 네이밍 절차와 `agents/naming-specialist.md`를 따른다.
모델 배정·토큰 절약은 `docs/MODEL_POLICY.md`, 배정값은 `kit/model-policy.json`을 따른다.
변경 이력: 2026-10-28 — 네이밍 역할, 역할별 모델 배정, 상태 자동 조회 추가(사용자 요청).
