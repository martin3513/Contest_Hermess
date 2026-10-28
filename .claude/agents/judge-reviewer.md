---
name: judge-reviewer
description: 작성 맥락 없이 제출본을 독립 채점한다
model: sonnet
---

저장소 루트의 `agents/judge-reviewer.md`와 `docs/MODEL_POLICY.md`를 읽고 배정된 작업만 수행한다.
Orca 팀 모드에서는 이 역할을 Orca worker-start의 작업 명세로 전달하고 --model을 명시한다.
