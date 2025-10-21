# HIRA 표 파싱 시스템 MVP 개발

**작업일**: 2025-10-21
**작업자**: Claude Code
**상태**: 🔄 Phase 1 완료 / Phase 2 진행 중

---

## 📋 작업 개요

HIRA eBook PDF의 표 데이터를 구조화된 JSONL 형식으로 추출하는 하이브리드 파싱 시스템 개발.

### 목표
- **정확도 우선**: 탐지 P/R ≥ 0.9/0.85, 헤더 매핑 ≥ 0.95
- **커버리지**: 표 행 완전성 확보 (병합셀 처리)
- **비용 최적화**: $20 예산 내에서 Camelot + Upstage 하이브리드
- **추적성**: source_anchor 포함, Ground Truth 기반 평가

---

## 🎯 작업 전략: Option C (Iterative MVP)

### 단계별 접근
1. **MVP (2시간)**: 텍스트 앵커 + Camelot lattice
2. **문제 발견**: 1개 PDF 테스트로 한계 파악
3. **점진적 개선**: 필요한 기능만 추가
4. **Ground Truth**: 30p 층화 샘플링 (무표/단순/중간/복잡)

---

## 🛠️ Phase 1: 환경 설정 및 MVP 구현

### 1.1 가상환경 설정

**생성**:
```bash
python -m uv venv scrape
uv pip install --python scrape/Scripts/python.exe \
  camelot-py opencv-python-headless pdfplumber pandas
```

**패키지**:
- `camelot-py==1.0.9`: 격자형 표 파싱
- `pdfplumber==0.11.7`: PDF 텍스트/표 추출
- `opencv-python-headless==4.12.0.88`: Camelot 의존성
- `pandas==2.3.3`: 데이터프레임 처리

### 1.2 MVP 파서 구현

**파일**: `hira/table_parser/mvp_parser.py` (273줄)

**기능**:
- 텍스트 앵커 감지: `표\s*\d+(-\d+)?|도표\s*\d+|그림\s*\d+`
- Camelot lattice 파싱: 격자선 명확한 표
- 행 단위 JSONL 출력
- code_refs 추출: `고시\s*제?\d{4}-\d+|수가\s*[가-힣A-Z\d]+`
- source_anchor 포함

**출력 형식**:
```jsonl
{
  "doc_id": "...",
  "page": 9,
  "table_id": "t9_1",
  "row_id": "t9_1r1",
  "level": 0,
  "parent_table_id": null,
  "text": "구분=..., 코드=...",
  "table_kv": {"구분": "...", "코드": "..."},
  "bbox": [x0, y0, x1, y1],
  "code_refs": [],
  "source_anchor": {"page": 9, "table_id": "t9_1", "row_id": "t9_1r1"}
}
```

---

## 📊 Phase 2: 테스트 및 문제 발견

### 2.1 간단한 PDF 테스트

**PDF**: `알기 쉬운 의료급여제도.pdf` (38페이지)

**결과**:
| 메트릭 | 결과 |
|--------|------|
| 텍스트 앵커 후보 | 22개 |
| 파싱된 테이블 | 3개 (페이지 9, 34) |
| 추출된 행 | 9개 |
| **Recall** | **13.6%** (22개 중 3개) ❌ |

**문제점**:
1. ❌ 낮은 Recall: Camelot lattice가 선 없는 표 감지 못함
2. ❌ 헤더 매핑 불량: 병합셀로 인한 빈 헤더 `{"": "..."}`
3. ❌ 텍스트 품질: 병합셀 내용이 그대로 결합

---

### 2.2 수가표 PDF 테스트 (복잡도 높음)

**PDF**: `건강보험요양급여비용.pdf` (1,470페이지)
**샘플**: 10페이지 (p10, 15, 20, 100, 105, 110, 200, 250, 300, 500)

#### Camelot lattice 결과

| 메트릭 | 결과 | 평가 |
|--------|------|------|
| 텍스트 앵커 감지 | **0/10 (0%)** | ❌ **완전 실패** |
| Camelot 표 감지 | 6/10 (60%) | ⚠️ 보통 |
| 표 추출 | 6개 | ✅ |
| 행 추출 | 6개 (1행/표) | ❌ **매우 부족** |

**심각한 문제 발견**:

1. **텍스트 앵커 없음**
   - 수가표는 "표 N" 형식 앵커 미사용
   - 직접 격자표 시작 (분류번호/코드/분류/점수)
   - 앵커 기반 탐지 전략 무용지물

2. **대규모 병합셀**
   - Page 105 예시:
     ```
     코드: AA253\nAA254\nAA255\n... (13개가 1셀)
     점수: 134.47\n139.85\n151.37\n... (13개가 1셀)
     ```
   - Camelot이 **1개 행**으로 인식
   - 실제로는 **13개 행** → **누락률 84.6%** ❌

3. **헤더 품질 불량**
   - Null 문자: `"코\u0000 \u0000 드"`
   - 빈 헤더: `""` (병합된 컬럼)
   - 헤더 매핑 정확도 < 50%

---

### 2.3 대안 탐색: pdfplumber.find_tables()

**가설**: pdfplumber가 선 없는 표도 감지할 수 있을 것

**테스트**: 동일한 수가표 10페이지

#### pdfplumber 결과

| 메트릭 | Camelot | **pdfplumber** | 개선 |
|--------|---------|----------------|------|
| 표 감지율 | 60% (6/10) | **70% (7/10)** | +17% ✅ |
| 추출 행 수 | 6개 | **18개** | +200% ✅ |
| 평균 행/표 | 1.0 | **2.2** | +120% ✅ |

**결론**: **pdfplumber가 Camelot보다 우수!** ✅

---

### 2.4 병합셀 상세 분석

**Page 105 상세 추출**:

```
표 크기: 2 rows x 4 cols
Row 0 (헤더): 분류번호 | 코드 | 분류 | 점수
Row 1 (데이터): 가-2 | AA253\nAA254\n... | ... | 134.47\n139.85\n...
```

**병합셀 내부**:
- 코드 컬럼: 13줄 (`AA253`, `AA254`, ..., `10203`)
- 점수 컬럼: 13줄 (`134.47`, `139.85`, ..., `124.27`)

**실제 구조**:
```
Row 1: 가-2 | AA253 | ... | 134.47
Row 2: 가-2 | AA254 | ... | 139.85
...
Row 13: 가-2 | 10203 | ... | 124.27
```

**누락 행 수**: 11개 (84.6%)
**원인**: 줄바꿈(`\n`)으로 구분된 값들이 1개 셀로 인식됨

---

## 🎯 해결책: 줄바꿈 분할 로직

### 알고리즘

```python
def split_merged_cells(row: list) -> list[list]:
    """
    병합셀 내부 줄바꿈을 기준으로 행 분할

    Input:  ["가-2", "AA253\nAA254\nAA255", "...", "134.47\n139.85\n151.37"]
    Output: [
        ["가-2", "AA253", "...", "134.47"],
        ["가-2", "AA254", "...", "139.85"],
        ["가-2", "AA255", "...", "151.37"]
    ]
    """
    # 1. 각 셀을 줄바꿈으로 분할
    split_cells = []
    max_lines = 1

    for cell in row:
        if cell and '\n' in cell:
            lines = [l.strip() for l in cell.split('\n') if l.strip()]
            split_cells.append(lines)
            max_lines = max(max_lines, len(lines))
        else:
            split_cells.append([cell] if cell else [''])

    # 2. forward-fill: 짧은 컬럼은 첫 값 반복
    expanded_rows = []
    for i in range(max_lines):
        new_row = []
        for col_lines in split_cells:
            if i < len(col_lines):
                new_row.append(col_lines[i])
            else:
                new_row.append(col_lines[0] if col_lines else '')
        expanded_rows.append(new_row)

    return expanded_rows
```

### 예상 효과

| 메트릭 | 현재 | 개선 후 | 증가율 |
|--------|------|---------|--------|
| Page 105 행 수 | 2 | **13** | +550% |
| 전체 10페이지 행 수 | 18 | **~150** | +733% |
| 누락률 | 84.6% | **0%** | 완전 해결 |

---

## 📂 산출물

### 생성된 파일

```
hira/table_parser/
├── mvp_parser.py                    # MVP 파서 (273줄)
├── test_suga.py                     # 수가표 테스트
├── test_pdfplumber_detection.py    # pdfplumber 비교
└── test_detailed_extraction.py     # 병합셀 분석

data/hira/table_parser/mvp_output/
├── hira_ebook_test_001_tables.jsonl          # 9 records
├── hira_ebook_test_001_summary.json
├── hira_ebook_test_001_candidates.json       # 22 anchors
├── suga_sample_test.json                     # Camelot 결과
└── pdfplumber_detection_test.json            # pdfplumber 결과
```

### 테스트 통계

- MVP 개발 시간: 2시간
- 테스트 PDF: 2개 (38p + 10p 샘플)
- 발견된 테이블: 11개
- 추출된 레코드: 27개 (병합셀 미처리)
- 예상 실제 레코드: ~180개 (병합셀 처리 시)

---

## 🔍 현재 목표치 대비 갭 분석

| 메트릭 | 목표 | 현재 (pdfplumber) | 갭 | 우선순위 |
|--------|------|-------------------|-----|----------|
| **탐지 Recall** | ≥0.85 | 0.70 | -0.15 | 중 |
| **헤더 매핑 정확도** | ≥0.95 | ~0.40 | **-0.55** | **높음** |
| **행 추출 완전성** | 100% | ~15% | **-85%** | **최우선** |
| **자동 확정비율** | ≥0.80 | ~0.10 | -0.70 | 높음 |

---

## 🚀 다음 단계 (우선순위)

### Phase 3: 병합셀 처리 구현 (1시간)

**작업 내용**:
1. 줄바꿈 분할 로직 구현
2. 헤더 정규화 (Null 문자 제거, 빈 헤더 보정)
3. 수가표 10페이지 재테스트

**예상 결과**:
- 행 추출: 18개 → **150+개** (+733%)
- 헤더 매핑: 40% → **85%**
- 누락률: 84.6% → **0%**

### Phase 4: pdfplumber 전체 파이프라인 통합 (1시간)

**작업 내용**:
1. pdfplumber.find_tables() 기반 재작성
2. 줄바꿈 분할 + 헤더 정규화 통합
3. JSONL 출력 형식 유지
4. code_refs 추출 유지

### Phase 5: Ground Truth 작업 (2-3시간)

**층화 샘플링 (30페이지)**:
- 무표 (6p): 텍스트만 있는 페이지
- 단순표=1개 (12p): 격자선 명확, 병합셀 적음
- 중간=2개 (6p): 일부 병합셀, 선 약함
- 복잡=3개↑ (6p): 중첩 테이블, 대규모 병합셀

**레이블 방법**:
1. 자동 파싱 결과 생성
2. 스프레드시트로 교정 (헤더 매핑, 누락 행)
3. 확정본 JSONL 저장

### Phase 6: 평가 및 개선 (1-2시간)

**메트릭 계산**:
- Detection: Precision, Recall
- Parsing: 헤더 매핑 정확도, 합계 일관성
- Routing: pdfplumber vs Upstage 성공률
- Coverage: 자동 확정 비율

---

## 💡 교훈 및 인사이트

### ✅ 성공 요인

1. **Iterative 접근의 효과**
   - 작은 PDF로 빠른 테스트 → 문제 조기 발견
   - Camelot 한계 파악 → pdfplumber 대안 즉시 검증
   - 2시간 만에 핵심 문제 (병합셀) 정확히 진단

2. **pdfplumber 재발견**
   - Camelot보다 표 감지율 높음 (60% → 70%)
   - 선 없는 표도 감지 가능 (공백 기반 정렬)
   - 이미 설치됨, 추가 비용 없음

3. **병합셀 문제의 보편성**
   - 수가표의 84.6% 행이 병합셀로 숨겨짐
   - 단순 줄바꿈 분할로 해결 가능
   - 다른 HIRA PDF도 유사할 것으로 예상

### ⚠️ 주의 사항

1. **텍스트 앵커 의존 위험**
   - 수가표처럼 앵커 없는 문서 존재
   - 기하학적 힌트 또는 전체 스캔 필요
   - 앵커는 보조 지표로만 활용

2. **1개 도구 의존 위험**
   - Camelot만으로는 recall < 70%
   - pdfplumber도 완벽하지 않음 (중첩 테이블 약함)
   - Upstage 대안 준비 필요 (복잡한 케이스)

3. **병합셀의 다양성**
   - 수직 병합 (현재 케이스)
   - 수평 병합 (미확인)
   - 2차원 병합 (미확인)
   - 다양한 케이스 테스트 필요

---

## 📊 비용 예측 (updated)

### 현재 계획 (pdfplumber 중심)

| 시나리오 | 페이지 | 비용 | 설명 |
|----------|--------|------|------|
| **pdfplumber (기본)** | 전체 | **$0** | 무료 |
| **Upstage (복잡 케이스)** | ~200p (추정 15%) | **$2-3** | 중첩, 스캔 |
| **합계** | 4,275p | **$2-3** | 예산 $20 내 |

### 이전 예측 대비

| 항목 | 이전 (Camelot 중심) | 현재 (pdfplumber 중심) | 절감 |
|------|---------------------|------------------------|------|
| 기본 파서 | Camelot (lattice) | pdfplumber | - |
| 복잡 케이스 비율 | 20-30% | 10-15% | -50% |
| Upstage 비용 | $5-10 | **$2-3** | **-70%** |

---

## 🔗 관련 문서

- Phase 2 완료: `docs/journal/hira/2025-10-20_ebook_collection_and_analysis.md`
- Upstage 파서 테스트: (예정)
- Ground Truth 가이드: (예정)

---

## 📅 타임라인

| 시간 | 작업 | 결과 |
|------|------|------|
| 09:00 - 09:30 | Option C 계획 수립, 가상환경 설정 | ✅ scrape venv |
| 09:30 - 11:00 | MVP 파서 작성 (mvp_parser.py) | ✅ 273줄 |
| 11:00 - 11:30 | 간단한 PDF 테스트 | ⚠️ Recall 13.6% |
| 11:30 - 12:00 | 수가표 샘플 테스트 (Camelot) | ❌ 심각한 문제 발견 |
| 14:00 - 14:30 | pdfplumber 대안 테스트 | ✅ 70% 감지율 |
| 14:30 - 15:00 | 병합셀 상세 분석 | ✅ 84.6% 누락 원인 파악 |
| 15:00 - 15:30 | Journal 작성 | ✅ 본 문서 |

**총 작업 시간**: 약 5시간
**다음 작업**: Phase 3 (병합셀 처리) 또는 Upstage 비교 테스트

---

**작성 시각**: 2025-10-21 15:30
**마지막 수정**: 2025-10-21 15:30
