# Contest Hermess — Codex

Orca에서 반복 사용하는 공모전 보고서 작업 공간이다. 한국어로 설명한다.
보고서 요청은 `WORKFLOW.md`를 읽고 실행한다. 코드 수정에는 보고서 승인 관문을 적용하지 않는다.
공통 스킬은 `kit/skills/`, 프로필은 `kit/profiles/`, 역할은 `agents/`다.
Codex 진입점은 `.agents/skills/contest-report/SKILL.md`다.
Orca 팀 모드는 `docs/ORCHESTRATION.md`에 따라 실제 Orca 워커를 사용한다.
원본은 `contests/<대회명>/input/`, 결과는 `output/`, 상태는 `_workspace/state.json`이다.
원본을 변경하지 않는다. 대회 파일은 기본 Git 제외다. 제출·메일은 사람이 직접 한다.
