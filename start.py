"""Contest Hermess: standard-library-only launcher for Orca on Windows."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
PROFILES = ("idea_proposal", "data_analysis", "research_report")


def now():
    return datetime.now(timezone.utc).isoformat()


def ensure_local(path):
    """Disallow junctions/symlinks on every component we may write through."""
    path = Path(os.path.abspath(path))
    if not path.is_relative_to(ROOT):
        raise ValueError("작업 폴더 밖에는 쓸 수 없습니다.")
    for part in (path, *path.parents):
        if part == ROOT:
            break
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024):
            raise ValueError(f"연결된 파일·폴더에는 쓰지 않습니다: {part}")


def write_json(path, data):
    ensure_local(path)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def create_json(path, data):
    ensure_local(path)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def contest_path(name):
    if (not name or name in {".", ".."} or name[-1:] in {" ", "."}
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
            or name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]}):
        raise ValueError("대회명은 경로가 아닌 폴더 이름이어야 합니다. 특수문자·예약 이름은 사용할 수 없습니다.")
    ensure_local(ROOT / "contests")
    base = (ROOT / "contests").resolve()
    path = base / name
    ensure_local(path)
    if not path.resolve().is_relative_to(base):
        raise ValueError("대회 폴더가 contests 밖을 가리킵니다.")
    # Reject redirected descendants too: input/result must stay in this contest.
    for sub in ("input", "output", "docs", "_workspace"):
        ensure_local(path / sub)
        if not (path / sub).resolve().is_relative_to(path.resolve()):
            raise ValueError(f"외부 폴더 연결은 지원하지 않습니다: {sub}")
    return path


def initialize(name, profile):
    path = contest_path(name)
    state_file = path / "_workspace/state.json"
    ensure_local(state_file)
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8-sig"))
        if state["profile"] != profile:
            raise ValueError(f"기존 유형은 {state['profile']}입니다. 다른 유형은 새 대회명으로 시작하세요.")
    for folder in ("input", "output", "docs/working_history", "_workspace/research", "_workspace/draft", "_workspace/review", "_workspace/launches"):
        ensure_local(path / folder)
        (path / folder).mkdir(parents=True, exist_ok=True)
    if not state_file.exists():
        try:
            create_json(state_file, {"schema_version": 1, "profile": profile, "stage": "ready", "round": 0, "scores": [], "approvals": {}, "updated": now()})
        except FileExistsError:
            raise ValueError("동시에 대회를 준비하고 있습니다. 잠시 후 다시 확인하세요.")
    return path


def orca_command():
    return os.environ.get("ORCA_CLI_COMMAND") or ("orca-dev" if os.environ.get("ORCA_DEV_REPO_ROOT") else "orca")


def call_orca(args):
    executable = shutil.which(orca_command())
    if not executable:
        raise RuntimeError(f"{orca_command()} 명령을 찾지 못했습니다. Orca의 CLI 설치와 PATH를 확인하세요.")
    # Never send user text through cmd.exe / shell=True. Windows npm shims are
    # executed through their Node entry point instead of batch interpolation.
    prefix = [executable]
    if Path(executable).suffix.lower() in {".cmd", ".bat"}:
        sibling = Path(executable).with_suffix("")
        if not sibling.exists():
            raise RuntimeError("배치 형식 Orca CLI만 발견했습니다. Orca 공식 CLI를 다시 설치하세요.")
        content = sibling.read_text(encoding="utf-8")
        match = re.search(r'"\$basedir/([^"\n]+\.(?:mjs|cjs|js))"', content)
        node = shutil.which("node")
        if not match or not node:
            raise RuntimeError("Orca Node 진입점을 확인하지 못했습니다. Orca CLI 설치를 확인하세요.")
        prefix = [node, str(sibling.parent / match.group(1))]
    result = subprocess.run(prefix + list(args), cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False)
    try:
        payload = json.loads(result.stdout.lstrip("\ufeff"))
    except ValueError:
        raise RuntimeError(result.stderr or result.stdout or f"Orca 종료 코드: {result.returncode}")
    if result.returncode or payload.get("ok") is False:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def make_prompt(name, profile, agent, mode):
    return (f"이 저장소의 WORKFLOW.md를 읽고 보고서 작업을 진행하세요. 대회명은 JSON 문자열 {json.dumps(name, ensure_ascii=False)}, "
            f"프로필은 {profile}, 실행 제공자는 {agent}, 모드는 {mode}입니다. "
            "contests/<대회명>/input 원본을 읽고 output에 최종 파일을 저장하세요. "
            "state.json과 최근 작업 이력을 확인해 이어서 진행하고 기존 결과를 덮어쓰지 마세요. "
            "새 세션 실행은 승인이나 처음부터 다시 작성하라는 뜻이 아닙니다. "
            "orchestrated 모드는 docs/ORCHESTRATION.md에 따라 실제 Orca worker를 감독하세요. "
            "single 모드는 역할별 순차 작업이며 독립 심사가 아님을 표시하세요. "
            "승인 대기 단계이면 해당 결과를 보여주고 사용자 응답을 기다리세요. 자동 제출하지 마세요.")


def launch(name, profile, agent, mode, preview=False):
    path = initialize(name, profile)
    prompt = make_prompt(name, profile, agent, mode)
    args = ["agent", "launch", "--agent", agent, "--worktree", f"path:{ROOT}", "--prompt", prompt, "--json"]
    if preview:
        print(json.dumps({"executable": orca_command(), "argv": args}, ensure_ascii=False, indent=2))
        return
    if not any(p.is_file() for p in (path / "input").rglob("*")):
        raise ValueError(f"자료가 없습니다. 이 폴더에 공고문을 넣은 뒤 다시 실행하세요: {path / 'input'}")
    pending = path / "_workspace/launch-pending.json"
    if pending.exists():
        raise ValueError(f"이전 실행 기록이 있습니다: {pending}\nOrca의 기존 대화를 먼저 확인하세요. 종료·대기 중인 워커를 확인한 후 메뉴 7로 새 세션 실행을 허용할 수 있습니다.")
    status = call_orca(["status", "--json"])
    if not status.get("result", {}).get("app", {}).get("running"):
        raise RuntimeError("Orca를 먼저 실행하고 이 폴더를 여세요.")
    call_orca(["skills", "get", "orca-cli", "--json"])
    if mode == "orchestrated":
        call_orca(["skills", "get", "orchestration", "--json"])
    attempt = uuid.uuid4().hex
    try:
        create_json(pending, {"attempt": attempt, "agent": agent, "mode": mode, "created": now(), "argv": args, "status": "launching"})
    except FileExistsError:
        raise ValueError("다른 실행이 먼저 시작됐습니다. 기존 Orca 대화를 확인하세요.")
    try:
        receipt = call_orca(args)
    except (RuntimeError, OSError) as error:
        write_json(path / f"_workspace/launches/{attempt}.json", {"error": str(error), "argv": args, "status": "unknown"})
        raise RuntimeError(f"실행 결과를 확정하지 못했습니다. 자동 재실행하지 않습니다.\n{error}\n기록: {pending}") from error
    write_json(path / f"_workspace/launches/{attempt}.json", receipt)
    write_json(pending, {"attempt": attempt, "agent": agent, "mode": mode, "created": now(), "status": "receipt-saved"})
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    print("Orca에 실행 요청을 보냈습니다. 위 영수증과 Orca 대화를 확인하세요. 이후 '진행'은 같은 대화에서 입력합니다.")


def show_status(name=None):
    paths = [contest_path(name)] if name else sorted((ROOT / "contests").glob("*"))
    for path in paths:
        state = path / "_workspace/state.json"
        if state.exists():
            print(f"\n[{path.name}]\n{state.read_text(encoding='utf-8-sig')}\n결과: {path / 'output'}")
    if name and not (contest_path(name) / "_workspace/state.json").exists():
        print("아직 작업 기록이 없습니다. 먼저 대회 폴더를 만드세요.")


def reset_launch(name):
    path = contest_path(name)
    pending = path / "_workspace/launch-pending.json"
    ensure_local(pending)
    if pending.exists():
        dest = path / "_workspace/launches" / f"reset-{uuid.uuid4().hex}.json"
        ensure_local(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        pending.replace(dest)
    print("실행 잠금만 해제했습니다. 보고서·승인·작업 이력은 보존했습니다.")


def doctor():
    print(f"작업 폴더: {ROOT}\nPython: {sys.version.split()[0]}\nOrca 명령: {orca_command()}")
    print(f"HWPX 라이브러리: {'설치됨' if importlib.util.find_spec('hwpx') else '없음 (MD 작업은 가능)'}")
    result = call_orca(["status", "--json"]).get("result", {})
    print(json.dumps({"app": result.get("app"), "runtime_state": result.get("runtime", {}).get("state")}, ensure_ascii=False, indent=2))


def menu():
    while True:
        print("\n경진대회 보고서 — Claude Code / Codex + Orca\n1. 대회 폴더 만들기\n2. Claude Code로 시작/이어가기\n3. Codex로 시작/이어가기\n4. 진행 상황\n5. 자료 입력 폴더 열기\n6. 결과 폴더 열기\n7. 이전 실행 확인 후 새 세션 허용\n8. 환경 점검\n0. 종료")
        choice = input("선택: ").strip()
        try:
            if choice == "0":
                return
            if choice == "8":
                doctor()
                continue
            if choice == "4":
                show_status()
                continue
            if choice not in {"1", "2", "3", "5", "6", "7"}:
                continue
            existing = [p.name for p in (ROOT / "contests").glob("*") if p.is_dir()]
            print("기존 대회: " + (", ".join(existing) or "없음"))
            name = input("대회명 (예: 2026_정책공모전): ").strip()
            path = contest_path(name)
            if choice in {"5", "6"}:
                target = path / ("input" if choice == "5" else "output")
                if not target.exists():
                    raise ValueError("먼저 메뉴 1에서 대회 폴더를 만드세요.")
                os.startfile(target)
            elif choice == "7":
                print("기존 Orca 대화를 확인하세요. 실행 중·상태 불명 워커가 있으면 해제하지 마세요.")
                if input("기존 작업이 끝났고 새 세션이 필요하면 '확인' 입력: ").strip() == "확인":
                    reset_launch(name)
            else:
                state_file = path / "_workspace/state.json"
                if state_file.exists():
                    profile = json.loads(state_file.read_text(encoding="utf-8-sig"))["profile"]
                else:
                    print("유형: 1 아이디어 제안서 / 2 데이터 분석 / 3 연구 보고서")
                    value = input("선택 [1]: ").strip() or "1"
                    if value not in {"1", "2", "3"}:
                        raise ValueError("유형은 1~3 중 선택하세요.")
                    profile = PROFILES[int(value) - 1]
                if choice == "1":
                    initialize(name, profile)
                    print(f"자료 넣기: {path / 'input'}\n결과 받기: {path / 'output'}")
                else:
                    value = input("실행 방식: 1 Orca 팀 작업 / 2 단독 작업 [1]: ").strip() or "1"
                    if value not in {"1", "2"}:
                        raise ValueError("실행 방식은 1 또는 2입니다.")
                    launch(name, profile, "claude" if choice == "2" else "codex", "orchestrated" if value == "1" else "single")
        except (ValueError, RuntimeError, OSError) as error:
            print(f"\n확인 필요: {error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command")
    for command in ("init", "launch"):
        p = subs.add_parser(command)
        p.add_argument("name")
        p.add_argument("--profile", choices=PROFILES, default="idea_proposal")
        if command == "launch":
            p.add_argument("--agent", choices=("claude", "codex"), default="codex")
            p.add_argument("--mode", choices=("orchestrated", "single"), default="orchestrated")
            p.add_argument("--preview", action="store_true", help="폴더와 실행 인자만 준비 (AI 실행 없음)")
    subs.add_parser("doctor")
    p = subs.add_parser("status")
    p.add_argument("name", nargs="?")
    p = subs.add_parser("reset-launch")
    p.add_argument("name")
    p.add_argument("--confirmed-idle", action="store_true", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            print(initialize(args.name, args.profile))
        elif args.command == "launch":
            launch(args.name, args.profile, args.agent, args.mode, args.preview)
        elif args.command == "status":
            show_status(args.name)
        elif args.command == "doctor":
            doctor()
        elif args.command == "reset-launch":
            reset_launch(args.name)
        else:
            menu()
    except (ValueError, RuntimeError, OSError) as error:
        print(f"확인 필요: {error}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\n종료합니다. 기존 자료는 그대로 보존됩니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
