# 유지보수·검증

완성된 실행 지침과 런처를 포함한다. 과거 Claude 전용 생성 절차 대신 `시작.cmd`로 바로 작업한다.
myharness 다운로드·인터뷰·재생성이 필요 없다.

## 수정할 곳

- 메뉴·재개 기록: `start.py`
- 작성 흐름: `WORKFLOW.md`
- Orca 팀 계약: `docs/ORCHESTRATION.md`
- 역할: `agents/*.md`
- 문체·심사·출력: `kit/skills/`
- 유형: `kit/profiles/*.yaml`
- Claude 명령: `kit/commands/`

변경 후 `python scripts/sync_adapters.py`로 `.claude/`와 `.agents/` 어댑터를 동기화한다.
기존 `agents/` 계약은 덮어쓰지 않는다. 새 역할은 스크립트 ROLES와 팀 설계서에도 등록한다.

## 검증

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 start.py doctor
python -X utf8 start.py launch _smoke --agent claude --preview
python -X utf8 start.py launch _smoke --agent codex --preview
python -X utf8 kit/skills/hwpx-formatter/scripts/md2hwpx.py examples/sample-notice.md contests/_smoke/output/sample.hwpx
```

기존 출력이 있으면 새 이름을 사용한다. 테스트 자료도 Git 제외다.
실제 팀 검증은 작은 읽기 전용 작업으로 완료 보고·release까지 확인한다.
보고서 전 과정·각 제공자의 실행·한글 서식은 별도 검증이다. 실행하지 않은 항목을 통과로 기록하지 않는다.
완료 기준은 `spec/acceptance-checklist.md`, 검증 기록은 `docs/build/결과서.md`다.
