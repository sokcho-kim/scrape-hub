# HIRA 급여기준 HWP 파싱 완료

**작업일**: 2025-11-03
**상태**: ✅ 완료 (55/55)
**이전 상태**: 44/56 (2025-10-17)

---

## 작업 개요

2025-10-17에 부분 완료된 HIRA 급여기준 문서 파싱을 완료했습니다.
실패했던 12개 파일을 수동 PDF 변환 + 분할 파싱 방식으로 100% 완료했습니다.

---

## 파싱 결과

| 항목 | 결과 |
|------|------|
| 전체 파일 | 55개 |
| 기존 완료 (10-17) | 43개 HWP 직접 파싱 |
| 추가 완료 (11-03) | 12개 (수동 PDF 변환 + 파싱) |
| 성공률 | 100% |
| 총 저장 파일 | 57개 JSON (summary 포함) |

---

## 실패 파일 해결 과정

### 1단계: 실패 원인 분석

**기존 실패 (12개)**:
- 10개: API 500 Server Error
- 2개: API 413 Request Entity Too Large

**분석 결과**:
- HWP 직접 파싱 불가
- 자동 변환 시도 실패 (COM automation, pyhwp 모두 실패)

### 2단계: 수동 PDF 변환

**사용자 직접 변환**: 12개 HWP → 13개 PDF (보너스 1개 포함)
- 변환 도구: 한컴오피스
- 저장 위치: `data/hira_rulesvc/documents/`

**검증**:
```bash
scraphub/Scripts/python hira_rulesvc/verify_pdf_files.py
```
- ✅ 12개 매칭 확인
- +1개 추가 파일 발견 (의료급여 본인부담 정리)

### 3단계: PDF 파싱

**일반 PDF (11개)** - `hira_rulesvc/parse_manual_pdf.py`
- 성공: 11개
- 실패: 2개 (페이지 제한 초과)

**대용량 PDF (2개)** - `hira_rulesvc/split_and_parse_pdf.py`
- 370페이지 → 4청크 분할 파싱 (2.80분)
- 112페이지 → 2청크 분할 파싱 (0.78분)
- 총 소요 시간: 3.58분

---

## 파싱 통계

### 파일 크기 분포

| 범위 | 개수 |
|------|------|
| 1-10 페이지 | ~35개 |
| 11-50 페이지 | ~12개 |
| 51-100 페이지 | ~6개 |
| 100+ 페이지 | 2개 (370p, 112p) |

### 총 데이터 규모

- **파싱된 JSON 파일**: 57개
- **총 파일 크기**: 4.13 MB
- **최대 파일**: 요양급여비용 심사청구서 (370페이지)

---

## 기술적 해결책

### 1. PDF 분할 파싱 구현

**파일**: `hira_rulesvc/split_and_parse_pdf.py`

**알고리즘**:
```python
1. PyMuPDF로 PDF를 100페이지씩 분할
2. 각 청크를 Upstage API로 개별 파싱
3. 파싱 결과를 페이지 번호 기준으로 병합
4. 단일 JSON 파일로 저장
```

**성능**:
- 370페이지: 167.96초 (평균 0.45초/페이지)
- 112페이지: 46.79초 (평균 0.42초/페이지)
- API Rate Limit: 2초 대기

### 2. 자동 변환 시도 (실패)

**COM Automation** - `hira_rulesvc/hwp_to_pdf.py`
- 실패: 매개변수 타입 불일치 오류
- 한컴오피스 COM API 불안정

**pyhwp 라이브러리** - `hira_rulesvc/hwp_extract_pyhwp.py`
- 실패: "Not an OLE2 Compound Binary File"
- 구형 HWP 형식만 지원

---

## 생성된 파일

### 스크립트
```
hira_rulesvc/
├── parse_hwp_documents.py         # 기존 HWP 직접 파싱
├── retry_failed_hwp.py            # 실패 파일 재시도 (async 시도)
├── parse_manual_pdf.py            # 수동 변환 PDF 파싱
├── split_and_parse_pdf.py         # 대용량 PDF 분할 파싱
├── verify_pdf_files.py            # PDF 변환 검증
├── hwp_to_pdf.py                  # COM 자동변환 시도 (실패)
└── hwp_extract_pyhwp.py           # pyhwp 추출 시도 (실패)
```

### 데이터
```
data/hira_rulesvc/
├── parsed/
│   ├── *.json (55개 문서)
│   ├── manual_pdf_summary.json
│   └── retry_summary.json
├── documents/ (13개 PDF)
└── temp_split/ (임시 청크 파일)
```

### 로그
```
logs/
├── hira_hwp_parse.log
├── hira_hwp_parse_v2.log
└── hira_split_parse.log
```

---

## 트러블슈팅 가이드

### 문제 1: HWP 직접 파싱 실패 (500/413 에러)

**해결책**:
1. PDF로 수동 변환 (한컴오피스 사용)
2. `parse_manual_pdf.py` 실행

### 문제 2: PDF 페이지 제한 초과 (413)

**해결책**:
1. `split_and_parse_pdf.py` 사용
2. 자동 100페이지 청크 분할
3. 병합된 JSON 출력

### 문제 3: API Rate Limit

**해결책**:
- 청크 간 2초 대기 (`time.sleep(2)`)
- 파일 간 1초 대기

---

## 남은 작업

### 데이터 정제
- [ ] 43개 HWP 파싱 결과 재검증
- [ ] 13개 PDF 파싱 결과 통합 검증
- [ ] 중복 제거 (1개 추가 파일 확인)

### 데이터 활용
- [ ] 55개 문서 카테고리 분류
- [ ] 메타데이터 정규화
- [ ] 검색 인덱스 구축

---

## 참고 자료

- 기존 작업: [2025-10-17_document_parsing.md](./2025-10-17_document_parsing.md)
- 파싱 요약: `data/hira_rulesvc/parsed/manual_pdf_summary.json`
- 분할 파싱 로그: `logs/hira_split_parse.log`

---

**작업 완료**: 2025-11-03
**최종 상태**: ✅ 55/55 (100%)
