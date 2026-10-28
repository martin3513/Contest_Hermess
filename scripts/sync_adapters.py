"""Regenerate thin runtime adapters; shared instructions stay in kit/ and agents/."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "naming-specialist": ("브랜드·서비스·사업·공모전 제안명과 슬로건을 제안하고 비교한다", "네이밍 브리프, 공고의 명칭 조건, 필요한 참고자료", "docs/naming.md", "WORKFLOW.md의 네이밍 절차를 따른다. 기본 후보 12개와 추천 3개에 의미·발음·적합성·중복 확인 상태를 기록한다. 미확인 중복이나 상표 사용 가능성을 단정하지 않는다.", None),
    "requirements-analyst": ("공고문·제출 양식에서 요구사항을 추출한다", "input/ 전체와 프로필", "docs/requirements.md", "마감·자격·분량·배점·필수 항목·제출 형식을 원문 위치와 함께 기록한다. 불명확한 내용은 질문 목록으로 분리한다.", None),
    "researcher": ("지정한 한 범위의 근거 자료를 조사한다", "docs/requirements.md와 지정 조사 범위", "_workspace/research/<범위>.md", "원문 URL·기관·날짜·확인한 수치·한계를 기록한다. 검색 실패를 숨기지 않는다. 범위는 official/cases/market/policy 중 배정받은 하나다.", None),
    "outline-designer": ("배점에 대응하는 목차와 분량을 설계한다", "requirements, research 4종, 프로필", "docs/outline.md", "심사 항목과 목차를 매핑하고 분량·핵심 주장·필요한 표를 정한다.", "korean-report-style"),
    "writer": ("담당 섹션 초안을 작성하거나 지적 사항을 수정한다", "outline, research, 프로필, 수정 지시", "_workspace/draft/NN_<섹션>.md", "배정된 섹션만 쓴다. 추정과 관측을 구분하고 출처 없는 수치는 [출처 필요]로 표시한다.", "korean-report-style"),
    "judge-reviewer": ("작성 맥락 없이 제출본을 독립 채점한다", "공고문, requirements, 초안, 프로필의 judge_focus", "_workspace/review/round-N.md", "작성 대화·리서치·이전 심사를 읽지 않는다. 배점·항목 점수·총점·본문 근거·실행 가능한 수정 지시를 기록한다.", "report-quality-checks"),
    "consistency-checker": ("목차·수치·요약·심사 항목의 정합성을 검사한다", "requirements, outline, draft, research", "_workspace/review/consistency.md", "4가지 교차 검사를 수행하고 치명/주의/정상을 근거 위치와 함께 기록한다.", "report-quality-checks"),
}


def put(relative, text):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main():
    policy = json.loads((ROOT / "kit/model-policy.json").read_text(encoding="utf-8"))
    for name, (description, inputs, output, rules, skill) in ROLES.items():
        # Role contracts are hand-maintained after initial generation.
        if not (ROOT / f"agents/{name}.md").exists():
            put(f"agents/{name}.md", f"# {name}\n\n{description}。\n\n- 입력: {inputs}\n- 출력: {output}\n- 원칙: {rules}\n" + (f"- 절차: `kit/skills/{skill}/SKILL.md`를 읽는다.\n" if skill else "") + "\n경로는 지정된 대회 폴더 기준이다. 배정된 출력만 수정하고 input·state·다른 역할 파일은 변경하지 않는다.\n막히면 근거 없는 내용을 만들지 말고 이유를 보고한다. Orca worker이면 주입된 preamble의 완료·질문 계약을 따른다.\n")
        model = policy["providers"]["claude"][policy["roles"][name]]
        put(f".claude/agents/{name}.md", f"---\nname: {name}\ndescription: {description}\nmodel: {model}\n---\n\n저장소 루트의 `agents/{name}.md`와 `docs/MODEL_POLICY.md`를 읽고 배정된 작업만 수행한다.\nOrca 팀 모드에서는 이 역할을 Orca worker-start의 작업 명세로 전달하고 --model을 명시한다.\n")
    for runtime in (".claude", ".agents"):
        put(f"{runtime}/skills/contest-report/SKILL.md", "---\nname: contest-report\ndescription: 이 저장소의 공모전 보고서 또는 네이밍(브랜드명·서비스명·사업명·제안명·슬로건)을 시작·재개·검토·출력할 때 사용한다.\n---\n\n저장소 루트의 `WORKFLOW.md`를 읽고 실행한다.\n대회명·유형·실행 모드가 있으면 그대로 사용하고, 없으면 필요한 정보만 확인한다.\n팀 모드는 `docs/ORCHESTRATION.md`, 역할은 `agents/`, 프로필은 `kit/profiles/`를 참조한다.\n")
        for skill in ("korean-report-style", "report-quality-checks", "hwpx-formatter"):
            source = (ROOT / f"kit/skills/{skill}/SKILL.md").read_text(encoding="utf-8")
            front = source.split("---", 2)[1].strip()
            put(f"{runtime}/skills/{skill}/SKILL.md", f"---\n{front}\n---\n\n저장소 루트의 `kit/skills/{skill}/SKILL.md`를 읽고 적용한다.\n스크립트는 원본 kit 경로에서 실행한다.\n")
    for path in (ROOT / "kit/commands").glob("*.md"):
        put(f".claude/commands/{path.name}", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
