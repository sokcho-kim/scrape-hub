# HIRA 급여기준 문서 수집 및 파싱

건강보험심사평가원(HIRA)의 의료급여 법령, 고시, 행정해석 문서를 수집하고 파싱한 프로젝트입니다.

---

## 프로젝트 개요

**목적**: 의료급여 관련 법령 및 급여기준 문서를 구조화된 데이터로 변환하여 검색 및 분석을 용이하게 합니다.

**데이터 소스**:
- HIRA 의료급여 법령/규정 페이지
- HWP 및 PDF 문서 56개

**최종 상태**: ✅ 55/55 완료 (100%)

---

## 주요 결과

| 항목 | 내용 |
|------|------|
| 수집 문서 | 55개 |
| 파싱 성공률 | 100% |
| 데이터 형식 | JSON (Markdown + HTML + 메타데이터) |
| 총 데이터 크기 | 4.13MB |
| 작업 기간 | 2025-10-17 ~ 2025-11-03 |

---

## 디렉토리 구조

```
hira_rulesvc/
├── scrapers/
│   └── law_crawler.py              # 법령/고시 크롤러
├── parsers/
│   ├── parse_hwp_documents.py      # HWP 직접 파싱
│   ├── parse_manual_pdf.py         # PDF 파싱
│   ├── split_and_parse_pdf.py      # 대용량 PDF 분할 파싱
│   └── retry_failed_hwp.py         # 실패 파일 재시도
├── tools/
│   └── verify_pdf_files.py         # 변환 파일 검증
└── data/
    ├── raw/                        # 원본 HWP/PDF
    ├── documents/                  # 수동 변환 PDF
    └── parsed/                     # 파싱 결과 JSON
```

---

## 파싱 방법

### 1단계: HWP 직접 파싱 (43개)

```bash
scraphub/Scripts/python hira_rulesvc/parse_hwp_documents.py --all
```

**결과**: 43개 성공, 12개 실패 (API 500/413 에러)

### 2단계: 수동 PDF 변환 + 파싱 (11개)

```bash
# 수동 변환: HWP → PDF (한컴오피스 사용)
# 파싱
scraphub/Scripts/python hira_rulesvc/parse_manual_pdf.py
```

**결과**: 11개 성공, 2개 실패 (페이지 제한)

### 3단계: 대용량 PDF 분할 파싱 (2개)

```bash
scraphub/Scripts/python hira_rulesvc/split_and_parse_pdf.py
```

**결과**: 2개 성공 (370p, 112p → 청크 분할)

---

## 데이터 형식

### JSON 구조

```json
{
  "file_name": "요양급여비용 심사청구서.pdf",
  "page_count": 0,
  "content": "Markdown 텍스트",
  "elements": [
    {
      "category": "heading1",
      "content": {"html": "<h1>제목</h1>", "text": "제목"},
      "coordinates": [...],
      "page": 1
    }
  ],
  "metadata": {
    "parsed_at": "2025-11-03T18:13:37",
    "api": "upstage-document-parse",
    "method": "split_and_merge"
  }
}
```

### 카테고리

- 법령: 의료급여법, 시행령, 시행규칙
- 고시: 급여기준, 수가, 작성요령
- 행정해석: ~30개 (부당이득금, 시설수용자 등)

---

## 기술 스택

### 파싱 API
- **Upstage Document Parse API**
  - 지원 형식: HWP, PDF, DOCX
  - 최대 페이지: 100p (동기)
  - 출력: Markdown + HTML + 요소 좌표

### 라이브러리
- **PyMuPDF (fitz)**: PDF 분할
- **requests**: API 호출
- **pathlib**: 파일 경로 처리

---

## 주요 스크립트

### 1. HWP 직접 파싱
```bash
scraphub/Scripts/python hira_rulesvc/parse_hwp_documents.py --all
```

### 2. 실패 파일 재시도
```bash
scraphub/Scripts/python hira_rulesvc/retry_failed_hwp.py
```

### 3. 수동 PDF 파싱
```bash
scraphub/Scripts/python hira_rulesvc/parse_manual_pdf.py \
  --pdf-dir data/hira_rulesvc/documents \
  --output-dir data/hira_rulesvc/parsed
```

### 4. 대용량 PDF 분할 파싱
```bash
scraphub/Scripts/python hira_rulesvc/split_and_parse_pdf.py
```

### 5. 변환 파일 검증
```bash
scraphub/Scripts/python hira_rulesvc/verify_pdf_files.py
```

---

## 트러블슈팅

### 문제 1: HWP 직접 파싱 실패 (500/413 에러)

**원인**: Upstage API 서버 문제 또는 페이지 제한

**해결**:
1. 한컴오피스로 PDF 수동 변환
2. `parse_manual_pdf.py` 실행

### 문제 2: PDF 페이지 제한 초과

**원인**: 100페이지 초과 (370p, 112p)

**해결**:
1. `split_and_parse_pdf.py` 사용
2. 자동으로 100페이지씩 분할
3. 병합된 JSON 출력

### 문제 3: 자동 변환 실패

**시도**:
- COM Automation (hwp_to_pdf.py) → 실패
- pyhwp 라이브러리 (hwp_extract_pyhwp.py) → 실패

**결론**: 수동 변환만 가능

---

## 성능 지표

### 파싱 속도
- **일반 HWP**: ~5초/파일
- **PDF (100페이지 미만)**: ~10초/파일
- **대용량 PDF 분할**: 0.42초/페이지

### 비용 (Upstage API)
- 총 페이지: ~300페이지
- 예상 비용: ~$3 USD

---

## 작업 히스토리

### 2025-10-17: 초기 파싱
- HWP 직접 파싱: 44/56
- 실패: 12개 (500/413 에러)
- 상세: [2025-10-17_document_parsing.md](../docs/journal/hira_rulesvc/2025-10-17_document_parsing.md)

### 2025-11-03: 파싱 완료
- 수동 PDF 변환: 13개
- 분할 파싱: 2개 대용량 파일
- 최종: 55/55 (100%)
- 상세: [2025-11-03_hwp_parsing_complete.md](../docs/journal/hira_rulesvc/2025-11-03_hwp_parsing_complete.md)

---

## 활용 방안

### 1. 급여기준 검색
```python
# 특정 키워드 검색
search_docs("부당이득금")
```

### 2. 법령 조회
```python
# 의료급여법 관련 조항 조회
get_law_section("의료급여법", "제9조")
```

### 3. 고시 비교
```python
# 고시 개정 내역 비교
compare_notifications("2024-171호", "2025-171호")
```

---

## 참고 자료

- Upstage Document Parse API: https://console.upstage.ai
- 작업 일지: `docs/journal/hira_rulesvc/`
- 파싱 요약: `data/hira_rulesvc/parsed/manual_pdf_summary.json`

---

**최종 업데이트**: 2025-11-03
**상태**: ✅ 완료
