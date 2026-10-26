#!/usr/bin/env python3
"""대회가 준 한글(HWPX) 양식의 표 칸을 라벨 기준으로 채운다.

사용법:
    python3 fill_hwpx_form.py map  <양식.hwpx>                       # 양식의 표 구조 보기
    python3 fill_hwpx_form.py fill <양식.hwpx> <값.json> <출력.hwpx>  # 칸 채우기

값.json 예시 (키 = "라벨 > 방향", 방향은 right 또는 down):
    {
      "과제명 > right": "AI 기반 전통시장 수요 예측",
      "팀명 > right": "경주데이터랩",
      "대표자 > right": "홍길동"
    }

원본 양식은 건드리지 않고 항상 새 파일로 저장한다.
필요: pip install python-hwpx  (HWP(구형)는 지원하지 않음 → 한글에서 HWPX로 저장 후 사용)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from hwpx import HwpxDocument
except ImportError:  # pragma: no cover
    sys.exit("python-hwpx 가 없습니다. 먼저 실행하세요: pip install python-hwpx")


def show_map(form: Path) -> None:
    doc = HwpxDocument.open(form)
    # python-hwpx 6.x 새 이름을 먼저 쓰고, 옛 버전이면 예전 이름으로
    table_map = doc.tables.map() if hasattr(doc, "tables") and hasattr(doc.tables, "map") else doc.get_table_map()
    text = doc.text.plain() if hasattr(doc, "text") and hasattr(doc.text, "plain") else doc.export_text()
    for t in table_map.get("tables", []) if isinstance(table_map, dict) else []:
        print(f"[표 {t['table_index']}] {t['rows']}행 x {t['cols']}열 · 첫 줄: {t['first_row_preview']}")
        for cell in t["cells"]:
            if cell["text"]:
                print(f"    ({cell['row']},{cell['col']}) {cell['text']}")
    print("\n--- 문서 글자 (앞부분) ---")
    print(text[:3000])


def fill(form: Path, values: Path, out: Path) -> None:
    if out.resolve() == form.resolve():
        sys.exit("출력 파일은 원본 양식과 다른 이름이어야 합니다.")
    if out.exists() or out.resolve() == values.resolve():
        sys.exit("기존 파일을 덮어쓰지 않습니다. 새 출력 이름을 지정하세요.")
    mapping = json.loads(values.read_text(encoding="utf-8"))
    doc = HwpxDocument.open(form)
    tables = getattr(doc, "tables", None)
    result = tables.fill_by_path(mapping) if hasattr(tables, "fill_by_path") else doc.fill_by_path(mapping)
    if isinstance(result, dict) and result.get("failed_count"):
        sys.exit(f"찾지 못한 라벨 {result['failed_count']}개 → {result.get('failed')}. 결과를 저장하지 않았습니다.")
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save_to_path(out)
    report = HwpxDocument.open(out).validate()
    if not report.ok:
        sys.exit(f"검증 실패: {report}")
    print(f"저장 완료: {out}")
    print(f"채우기 결과: {result}")


def main() -> None:
    if len(sys.argv) >= 3 and sys.argv[1] == "map":
        show_map(Path(sys.argv[2]))
    elif len(sys.argv) == 5 and sys.argv[1] == "fill":
        fill(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
