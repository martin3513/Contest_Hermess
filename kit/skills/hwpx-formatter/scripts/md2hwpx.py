#!/usr/bin/env python3
"""Markdown 보고서를 한글(HWPX) 파일로 변환한다.

사용법:
    python3 md2hwpx.py <입력.md> <출력.hwpx> [--base-dir <이미지 기준 폴더>]

지원하는 Markdown:
    # / ## / ### / ####  제목 (개요 1~4 수준)
    일반 문단            (줄바꿈으로 이어진 줄은 한 문단으로 합침)
    - 항목 / * 항목       개조식 글머리 (들여쓰기 2칸마다 한 단계 아래: ○ → - → ·)
    1. 항목              번호 목록
    | 표 | 형식 |          파이프 표 (두 번째 줄의 구분선 |---| 필요)
    ![설명](그림.png)     그림 (png, jpg, gif, bmp)
    > 인용               '※ ' 로 시작하는 참고 문단
    ---                  쪽 나눔 없이 빈 줄로 처리

필요: pip install python-hwpx  (Python 3.10 이상, 한컴오피스 설치 불필요)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from hwpx import HwpxDocument
except ImportError:  # pragma: no cover
    sys.exit("python-hwpx 가 없습니다. 먼저 실행하세요: pip install python-hwpx")

BULLET_MARKS = ["○", "-", "·"]
IMAGE_RE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)\)\s*$")
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.+?)\s*#*\s*$")
BULLET_RE = re.compile(r"^(?P<indent>\s*)[-*+]\s+(?P<text>.+)$")
NUMBER_RE = re.compile(r"^(?P<indent>\s*)(?P<num>\d+)[.)]\s+(?P<text>.+)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def strip_inline(text: str) -> str:
    """굵게·기울임·코드·링크 표기를 걷어 내고 글자만 남긴다."""
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1(\2)", text)
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text)
    text = re.sub(r"(?<![\w*])([*_])(.+?)\1(?![\w*])", r"\2", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [strip_inline(cell) for cell in line.split("|")]


def add_table(doc: HwpxDocument, rows: list[list[str]]) -> None:
    cols = max(len(r) for r in rows)
    table = doc.add_table(len(rows), cols)
    for r, row in enumerate(rows):
        for c in range(cols):
            table.set_cell_text(r, c, row[c] if c < len(row) else "")


def add_image(doc: HwpxDocument, src: str, alt: str, base_dir: Path) -> None:
    path = (base_dir / src) if not Path(src).is_absolute() else Path(src)
    fmt = path.suffix.lower().lstrip(".").replace("jpeg", "jpg")
    if not path.exists() or fmt not in {"png", "jpg", "gif", "bmp"}:
        doc.add_paragraph(f"[그림 누락: {src}]")
        print(f"경고: 그림을 넣지 못했습니다 → {path}", file=sys.stderr)
        return
    doc.add_picture(path.read_bytes(), fmt, width_mm=150, align="CENTER")
    if alt:
        doc.add_paragraph(f"<그림> {alt}")


def convert(md_text: str, base_dir: Path) -> HwpxDocument:
    doc = HwpxDocument.new()
    lines = md_text.splitlines()
    para_buf: list[str] = []
    i = 0

    def flush_para() -> None:
        if para_buf:
            doc.add_paragraph(strip_inline(" ".join(s.strip() for s in para_buf)))
            para_buf.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or re.fullmatch(r"-{3,}|\*{3,}", stripped):
            flush_para()
            i += 1
            continue

        if stripped.startswith("```"):  # 코드 블록은 글자 그대로 넣는다
            flush_para()
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                doc.add_paragraph(lines[i])
                i += 1
            i += 1
            continue

        m = HEADING_RE.match(stripped)
        if m:
            flush_para()
            level = min(len(m.group("hashes")), 4)
            doc.add_heading(strip_inline(m.group("text")), level=level)
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1]):
            flush_para()
            rows = [split_row(stripped)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            add_table(doc, rows)
            continue

        m = IMAGE_RE.match(stripped)
        if m:
            flush_para()
            add_image(doc, m.group("src"), m.group("alt"), base_dir)
            i += 1
            continue

        m = BULLET_RE.match(line)
        if m:
            flush_para()
            depth = min(len(m.group("indent").replace("\t", "  ")) // 2, len(BULLET_MARKS) - 1)
            doc.add_paragraph(f"{'  ' * depth}{BULLET_MARKS[depth]} {strip_inline(m.group('text'))}")
            i += 1
            continue

        m = NUMBER_RE.match(line)
        if m:
            flush_para()
            depth = len(m.group("indent").replace("\t", "  ")) // 2
            doc.add_paragraph(f"{'  ' * depth}{m.group('num')}. {strip_inline(m.group('text'))}")
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            doc.add_paragraph("※ " + strip_inline(stripped.lstrip("> ")))
            i += 1
            continue

        para_buf.append(line)
        i += 1

    flush_para()
    return doc


def main() -> None:
    parser = argparse.ArgumentParser(description="Markdown → HWPX 변환")
    parser.add_argument("src", type=Path, help="입력 Markdown 파일")
    parser.add_argument("dst", type=Path, help="출력 HWPX 파일")
    parser.add_argument("--base-dir", type=Path, default=None, help="그림 경로의 기준 폴더 (기본: 입력 파일 폴더)")
    args = parser.parse_args()

    if args.dst.resolve() == args.src.resolve() or args.dst.exists():
        parser.error("원본 또는 기존 결과를 덮어쓰지 않습니다. 새 출력 이름을 지정하세요.")

    md_text = args.src.read_text(encoding="utf-8")
    doc = convert(md_text, args.base_dir or args.src.parent)
    args.dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save_to_path(args.dst)

    report = HwpxDocument.open(args.dst).validate()
    ok = getattr(report, "ok", None)
    print(f"저장 완료: {args.dst}")
    if ok is False:
        print(f"검증 경고: {report}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
