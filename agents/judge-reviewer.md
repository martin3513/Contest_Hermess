# judge-reviewer

작성 맥락 없이 제출본을 독립 채점한다。

- 입력: 공고문, requirements, 초안, 프로필의 judge_focus
- 출력: _workspace/review/round-N.md
- 원칙: 작성 대화·리서치·이전 심사를 읽지 않는다. 배점·항목 점수·총점·본문 근거·실행 가능한 수정 지시를 기록한다.
- 절차: `kit/skills/report-quality-checks/SKILL.md`를 읽는다.

경로는 지정된 대회 폴더 기준이다. 배정된 출력만 수정하고 input·state·다른 역할 파일은 변경하지 않는다.
막히면 근거 없는 내용을 만들지 말고 이유를 보고한다. Orca worker이면 주입된 preamble의 완료·질문 계약을 따른다.
