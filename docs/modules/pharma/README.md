# Pharma 프로젝트

**목적**: 약제 관련 데이터 수집 및 파싱

---

## 프로젝트 개요

약제급여목록, 약가정보, 약제 사용 기준 등 의약품 관련 데이터를 수집하고 구조화합니다.

---

## 데이터 소스

### 1. HIRA 약제급여목록
- **출처**: 건강보험심사평가원
- **내용**: 요양급여 적용 약제 목록
- **형식**: PDF, Excel
- **주기**: 분기별 갱신

### 2. 약가정보
- **출처**: 건강보험심사평가원
- **내용**: 약제 코드, 제품명, 성분, 단가
- **형식**: Excel, CSV

### 3. 약제 사용 기준
- **출처**: HIRA 요양급여 적용기준
- **내용**: 약제별 급여 기준, 사전승인, 투여 용량
- **형식**: PDF (표 중심)

---

## 디렉토리 구조

```
pharma/
├── scrapers/           # 데이터 수집 스크립트
│   ├── hira_drug_list.py
│   └── drug_price.py
├── parsers/            # 데이터 파싱 스크립트
│   ├── pdf_parser.py
│   └── excel_parser.py
└── README.md

data/pharma/
├── raw/                # 원본 데이터
│   ├── pdf/
│   ├── excel/
│   └── README.md
├── parsed/             # 파싱된 데이터
│   ├── drug_list.jsonl
│   ├── drug_criteria.jsonl
│   └── README.md
└── README.md

docs/journal/pharma/    # 작업 일지
```

---

## 주요 기능

### 1. 약제급여목록 수집
- HIRA 공개 자료 다운로드
- 분기별 변경사항 추적

### 2. PDF 표 파싱
- Upstage Document Parse API 활용
- 약제 사용 기준 표 구조화
- 병합셀, 중첩 테이블 처리

### 3. 데이터 정규화
- 약제 코드 표준화
- 성분명, 제품명 매핑
- 용량, 용법 정규 표현

---

## 사용 예시

### 약제급여목록 수집
```bash
python pharma/scrapers/hira_drug_list.py
```

### PDF 파싱 (Upstage)
```bash
python pharma/parsers/pdf_parser.py \
  --input data/pharma/raw/pdf/drug_criteria.pdf \
  --output data/pharma/parsed/drug_criteria.jsonl
```

---

## 출력 형식

### drug_list.jsonl
```json
{
  "drug_code": "645900821",
  "product_name": "타이레놀정 500mg",
  "ingredient": "아세트아미노펜",
  "dosage": "500mg",
  "unit_price": 42.50,
  "manufacturer": "한국얀센",
  "benefit_type": "급여",
  "updated_at": "2025-01-01"
}
```

### drug_criteria.jsonl
```json
{
  "doc_id": "pharma_criteria_001",
  "page": 15,
  "table_id": "t15_1",
  "row_id": "t15_1r3",
  "drug_code": "645900821",
  "drug_name": "타이레놀정",
  "criteria": "1일 최대 4,000mg 이내 투여",
  "prior_approval": false,
  "source_anchor": {"page": 15, "table_id": "t15_1", "row_id": "t15_1r3"}
}
```

---

## 다음 단계

- [ ] Upstage API 테스트 (약제 사용 기준 PDF)
- [ ] 약제급여목록 스크레이퍼 작성
- [ ] 데이터 정규화 로직 구현
- [ ] Ground Truth 샘플 작성

---

**생성일**: 2025-10-21
**상태**: 초기 설정 완료
