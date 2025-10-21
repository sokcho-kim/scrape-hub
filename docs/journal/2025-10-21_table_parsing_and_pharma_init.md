# 표 파싱 시스템 개발 및 Pharma 프로젝트 초기화

**작업일**: 2025-10-21
**작업자**: Claude Code + 지민
**상태**: 🔄 진행 중

---

## 📋 작업 개요

건강보험 규제 문서(법령-고시-수가)의 표 파싱 시스템 개발 및 약제 데이터 수집 프로젝트 신규 생성

### 핵심 목표
- HIRA 전자책 PDF에서 표 자동 추출 및 구조화
- 파싱 도구 성능 비교 (Camelot vs pdfplumber vs Upstage)
- 약제 관련 데이터 수집을 위한 별도 프로젝트 구성

---

## 🎯 오늘의 작업

### 1. HIRA 표 파서 MVP 개발 ✅

**목적**: 수가표 PDF에서 표 감지 및 파싱

**작업 내용**:
- `scrape` 가상환경 생성 (uv)
- 라이브러리 설치: camelot-py, pdfplumber, opencv-python-headless
- MVP 파서 구현: `hira/table_parser/mvp_parser.py`

**테스트 결과**:

| 도구 | 표 감지율 | 평균 행/표 | 문제점 |
|------|----------|----------|--------|
| **Camelot lattice** | 60% (6/10p) | 1.0 rows | 텍스트 앵커 0%, 병합셀 미처리 |
| **pdfplumber** | 70% (7/10p) | 2.2 rows | 병합셀 미처리 (84.6% 손실) |

**핵심 발견**:
1. **pdfplumber > Camelot** (70% vs 60% 감지율)
2. **병합셀 문제**: 13개 행이 1개 셀로 병합 (`\n`으로 구분)
   - 예: `AA253\nAA254\n...` (13개 코드가 한 셀에)
   - 84.6% 행 손실 (13 actual → 2 detected)
3. **텍스트 앵커 실패**: 수가표에는 "표 N" 라벨 없음

**상세 문서**: `docs/journal/hira/2025-10-21_table_parser_mvp.md`

---

### 2. Pharma 프로젝트 생성 ✅

**목적**: 약제 관련 데이터 수집 및 파싱 전용 프로젝트

**생성된 구조**:
```
pharma/
├── scrapers/           # 약제급여목록, 약가정보 수집
├── parsers/
│   └── upstage_test.py  # Upstage API 테스트 스크립트
└── README.md

data/pharma/
├── raw/
│   ├── pdf/
│   └── excel/
├── parsed/
│   └── upstage_test/
└── README.md

docs/journal/pharma/
└── 2025-10-21_project_init.md
```

**테스트 대상 PDF**:
- 파일: `요양급여의 적용기준 및 방법에 관한 세부사항(약제) - 2025년 7월판.pdf`
- 페이지: 858p
- 특징: 병합셀, 중첩 테이블 다수
- 출처: HIRA 전자책 (이미 수집됨)

**Upstage 테스트 계획**:
- 샘플 페이지: 10개 (p10, 50, 100, 200, 300, 400, 500, 600, 700, 800)
- 예상 비용: $0.10 (10p) / $8.58 (전체 858p)
- 목적: pdfplumber 대비 병합셀 처리 성능 비교

**상세 문서**: `docs/journal/pharma/2025-10-21_project_init.md`

---

### 3. 메인 README 업데이트 ✅

- Pharma를 프로젝트 #5로 추가
- LIKMS 법령 수집 현황 업데이트 (35개 → 7개 법령)
- 전체 프로젝트 구조도 갱신

---

## 🔍 발견된 문제점

### 1. 병합셀 처리 실패 (Critical)

**증상**:
```
감지된 행: 2 rows
실제 행: 13 rows
손실률: 84.6%
```

**원인**:
- PDF에서 세로 병합된 셀을 `\n`으로 구분된 단일 문자열로 추출
- Camelot/pdfplumber 모두 이를 1개 행으로 처리

**예시** (Page 105):
```
감지: Row 1 | 가-2 | AA253\nAA254\n...\n10203 | ... | 134.47\n139.85\n...\n124.27

실제: Row 1 | 가-2 | AA253 | ... | 134.47
      Row 2 | 가-2 | AA254 | ... | 139.85
      ...
      Row 13 | 가-2 | 10203 | ... | 124.27
```

**해결 방안** (설계됨, 미구현):
```python
def split_merged_cells(row: list) -> list[list]:
    # 1. \n 개수 확인하여 병합 여부 판단
    # 2. 각 셀을 \n으로 분할
    # 3. 짧은 열은 forward-fill
    # 4. 확장된 행 리스트 반환
```

---

### 2. 표 감지율 낮음 (70%)

**현황**:
- pdfplumber: 70% (7/10 pages)
- 목표: 90%+

**원인**:
- 텍스트 앵커 방식 실패 (수가표에 "표 N" 없음)
- bbox 기반 감지만 의존

**차기 테스트**:
- Upstage Document Parse API (OCR + 레이아웃 분석)
- 기대 성능: 95%+

---

## 📊 프로젝트 현황 요약

| 프로젝트 | 데이터 수집 | 파싱 | 상태 |
|---------|-----------|------|------|
| **EMR 인증** | ✅ 4,214개 | N/A | 완료 |
| **HIRA RULESVC** | ✅ 56개 (HWP) | ⏸️ 보류 | 수집 완료 |
| **HIRA 전자책** | ✅ 8개 (4,275p) | 🔄 진행 중 | 표 파싱 개발 |
| **LIKMS 법령** | ✅ 7개 법령 | N/A | 완료 |
| **Pharma** | ⏸️ 계획 중 | 🔄 Upstage 테스트 | 초기화 완료 |

---

## 🚀 다음 작업 계획

### Phase 1: Upstage API 성능 평가

**목적**: pdfplumber 대비 Upstage의 병합셀 처리 능력 검증

**작업 순서**:
1. ✅ Upstage 테스트 스크립트 작성 (`pharma/parsers/upstage_test.py`)
2. ⏸️ 환경 설정
   - `requests` 라이브러리 설치
   - `UPSTAGE_API_KEY` 환경변수 설정
3. ⏸️ 10페이지 샘플 테스트 실행
4. ⏸️ 결과 분석
   - 표 감지율 (목표: 90%+)
   - 병합셀 처리 품질
   - 행/열 추출 완전성
5. ⏸️ pdfplumber vs Upstage 비교 리포트 작성

**예산**: $0.10 (10페이지 테스트)

---

### Phase 2: 병합셀 분할 로직 구현

**전제 조건**: Upstage 테스트 완료 후 도구 선택

**Option A: pdfplumber + 후처리**
- 비용: $0 (무료)
- 병합셀 분할 함수 구현 필요
- 예상 정확도: 85%

**Option B: Upstage API**
- 비용: ~$8.58/문서
- API 응답 그대로 사용
- 예상 정확도: 95%+

**Option C: 하이브리드**
- 간단한 표: pdfplumber
- 복잡한 표: Upstage
- 비용 최적화 + 정확도 확보

**구현 계획**:
1. `split_merged_cells()` 함수 작성
2. 헤더 정규화 (null 문자 제거, 빈 헤더 채우기)
3. 행 단위 JSONL 출력 (`tables.jsonl`)
4. 메트릭 계산 (`tables_report.json`)

---

### Phase 3: Ground Truth 생성 및 평가

**샘플링 전략** (30 pages):
- 무표: 6p (20%)
- 단순표 (1개): 12p (40%)
- 중간 (2개): 6p (20%)
- 복잡 (3+개): 6p (20%)

**평가 메트릭**:
| 메트릭 | 목표치 | 현재 |
|--------|--------|------|
| 표 감지 Precision | ≥ 0.90 | ? |
| 표 감지 Recall | ≥ 0.85 | ~0.70 |
| 헤더 매핑 (단순/중간) | ≥ 0.95 | ? |
| 헤더 매핑 (복잡) | ≥ 0.90 | ? |
| Auto-ok 비율 | ≥ 80% | ? |

**작업**:
1. 30페이지 수동 라벨링 (표 bbox, 행/열 수)
2. 자동 파싱 결과와 비교
3. 정확도 계산 및 리포트

---

### Phase 4: 전체 문서 파싱 및 데이터 적재

**대상 문서**:
1. 건강보험요양급여비용 (1,470p)
2. 요양급여 적용기준(약제) (858p)
3. 청구방법 및 작성요령 (848p)
4. 의료급여 실무편람 (680p)
5. 기타 가이드 (419p)

**예상 비용** (Upstage 사용 시):
- 총 4,275 pages × $0.01 = **$42.75**

**출력 형식**:
```jsonl
# tables.jsonl
{"doc_id": "hira_fee_2025", "page": 105, "table_id": "t105_1", "row_id": "t105_1r1", "분류번호": "가-2", "코드": "AA253", "분류": "...", "점수": "134.47"}
{"doc_id": "hira_fee_2025", "page": 105, "table_id": "t105_1", "row_id": "t105_1r2", "분류번호": "가-2", "코드": "AA254", "분류": "...", "점수": "139.85"}
...
```

**벡터 DB 적재**:
- 행 단위로 임베딩
- 메타데이터: doc_id, page, table_id, row_id
- 법령/고시 참조 링크 추가

---

## 🔗 법령-고시-수가 연계 구조

```
법령 (LIKMS)
├─ 국민건강보험법
│  ├─ 제41조 (요양급여)
│  └─ 제45조 (요양급여비용)
│
├─ 고시 (HIRA RULESVC)
│  ├─ 요양급여의 적용기준 및 방법에 관한 세부사항 (보건복지부 고시)
│  └─ 행정해석 문서
│
└─ 세부기준 (HIRA 전자책 표 파싱)
   ├─ 수가표 (건강보험요양급여비용)
   ├─ 약제 기준 (요양급여 적용기준-약제)
   └─ 청구지침 (청구방법 및 작성요령)
```

**연계 방법**:
1. 표 행에서 `code_refs` 추출 (고시 제XXXX-XX호, 법 제XX조)
2. LIKMS/HIRA RULESVC 문서와 매칭
3. 벡터 DB에 참조 링크 저장
4. RAG 시 법적 근거 함께 제시

---

## 📝 작업 일지

### 오늘 작업 시간
- 표 파싱 MVP 개발: ~3시간
- Pharma 프로젝트 설정: ~1시간
- 문서 작성: ~1시간

### 성과
- pdfplumber가 Camelot보다 우수함을 실증
- 병합셀 문제 정확히 진단 (84.6% 손실)
- Pharma 프로젝트 구조 완성
- Upstage 테스트 준비 완료

### 블로커
- Upstage API 키 설정 필요
- `requests` 라이브러리 설치 필요 (pip 없는 uv 환경)
- 병합셀 분할 로직 미구현

### 학습 내용
- PDF 표 추출 도구별 장단점
- 병합셀의 `\n` 구분 구조
- 의료 문서의 특수성 (텍스트 앵커 없음)

---

## 🎯 우선순위 정리

**High Priority** (내일):
1. Upstage API 테스트 실행 (pharma PDF 10페이지)
2. pdfplumber vs Upstage 비교 리포트
3. 도구 선택 의사결정

**Medium Priority** (이번 주):
1. 병합셀 분할 로직 구현
2. 30페이지 Ground Truth 생성
3. 평가 메트릭 계산

**Low Priority** (다음 주):
1. 전체 문서 파싱 (4,275p)
2. 벡터 DB 적재
3. 법령-고시-수가 연계 구현

---

## 🔗 관련 문서

- [HIRA 표 파서 MVP](docs/journal/hira/2025-10-21_table_parser_mvp.md)
- [Pharma 프로젝트 초기화](docs/journal/pharma/2025-10-21_project_init.md)
- [HIRA 전자책 수집](docs/journal/hira/2025-10-20_ebook_collection_and_analysis.md)
- [LIKMS 법령 수집](docs/journal/likms/2025-10-20_medical_law_collection.md)

---

**작성 시각**: 2025-10-21 18:00
**다음 작업**: Upstage API 테스트 실행 (pharma/parsers/upstage_test.py)
**예상 소요**: 30분 (API 설정 10분 + 실행 20분)

---

## 💡 메모

- 업무일지 제목 후보: "건강보험 법령-고시 연계 데이터 구축"
- 전체 프로젝트 목표: 법령 → 고시 → 수가의 위계적 규제 체계를 데이터로 연결
- Upstage 예산: $20 내 (현재 $0 사용)
- pdfplumber 무료 대안을 최대한 활용, 복잡한 경우만 Upstage 사용 고려
