---
name: hwpx-formatter
description: 완성된 Markdown 보고서를 한글(HWPX) 파일로 만들거나, 대회가 준 한글 양식(.hwpx)의 표 칸을 채울 때 사용한다. 보고서 출력, 한글 파일 변환, 양식 채우기, /export hwpx 요청에 사용한다. DOCX·PDF 출력 요청도 여기서 안내한다.
---

# 한글(HWPX) 출력

한컴오피스 없이 Python 라이브러리 `python-hwpx` 로 HWPX 를 만든다. 스크립트 두 개가 `scripts/` 에 있다.
(이 스킬 폴더 기준 경로: `kit/skills/hwpx-formatter/scripts/`)

## 0. 준비

```bash
python -m pip install -r requirements-hwpx.txt
```

Windows 에서 `python3` 명령이 없으면 아래 모든 명령의 `python3` 를 `python` 으로 바꿔 실행한다.
구형 `.hwp` 는 다루지 못한다. 양식이 .hwp 면 사용자에게 "한글에서 다른 이름으로 저장 → HWPX"를 부탁한다.

## 1. 경우 A — 양식 없이 새 문서로 출력 (기본)

```bash
python3 kit/skills/hwpx-formatter/scripts/md2hwpx.py \
  contests/<대회명>/output/<대회명>_보고서.md \
  contests/<대회명>/output/<대회명>_보고서.hwpx
```

- 제목(# ~ ####) → 한글 개요 1~4 수준, 글머리(- 들여쓰기) → ○ / - / · , 파이프 표 → 한글 표, `![설명](그림.png)` → 그림.
- 그림 경로는 Markdown 파일 위치 기준이다. 다른 곳이면 `--base-dir` 로 지정한다.
- 굵게·기울임은 글자만 남는다. 강조가 꼭 필요하면 한글에서 직접 지정하도록 안내한다.
- 기존 출력은 덮어쓰지 않는다. 새 날짜시각을 파일명에 넣는다.
- 스키마 검증 실패 시 비정상 종료한다. 오류를 그대로 알리고 한글에서의 외형 검증과 구분한다.

## 2. 경우 B — 대회 제공 양식(.hwpx)의 표 칸 채우기

표지·신청서처럼 "라벨 칸 옆 빈칸"을 채우는 양식에 쓴다.

1. 양식 구조 보기:
   ```bash
   python3 kit/skills/hwpx-formatter/scripts/fill_hwpx_form.py map contests/<대회명>/input/<양식>.hwpx
   ```
2. 출력에서 라벨(예: "과제명", "팀명")을 찾아 값 파일을 만든다 — `_workspace/form_values.json`:
   ```json
   { "과제명 > right": "AI 기반 전통시장 수요 예측", "팀명 > right": "경주데이터랩" }
   ```
   방향은 `right`(오른쪽 칸) 또는 `down`(아래 칸).
3. 채우기 (원본은 그대로 두고 새 파일로):
   ```bash
   python3 kit/skills/hwpx-formatter/scripts/fill_hwpx_form.py fill \
     contests/<대회명>/input/<양식>.hwpx _workspace/form_values.json \
     contests/<대회명>/output/<양식>_작성.hwpx
   ```
4. "찾지 못한 라벨"이 나오면 map 출력을 다시 보고 라벨 글자를 정확히 맞춘다.

본문이 긴 양식(제안서 본문 칸이 표 안에 있는 경우)은 칸 채우기에 한계가 있다.
그때는 경우 A 로 본문 파일을 따로 만들고, 사용자에게 "한글에서 양식 칸에 붙여 넣기"를 안내한다.

## 3. 다른 형식

- **DOCX:** `pandoc` 이 있으면 `pandoc 입력.md -o 출력.docx`. 없으면 설치 필요를 알리고 MD를 제공한다.
- **PDF:** 한글에서 HWPX 를 열어 PDF 로 저장하도록 안내한다 (서식이 가장 정확하다).
- **MD:** 그대로 둔다.

## 4. 끝난 뒤

- 만든 파일 경로를 사용자에게 알리고, **한글에서 직접 열어 확인**하라고 안내한다 (자동 변환은 글꼴·간격이 양식과 다를 수 있다).
- 제출은 사람이 한다. 업로드·메일 발송을 대신하지 않는다.
