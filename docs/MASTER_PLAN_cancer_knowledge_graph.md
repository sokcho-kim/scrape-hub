# 암질환 지식그래프 구축 마스터 플랜

**프로젝트명**: 암질환 약제 및 요법 지식그래프 구축
**작성일**: 2025-11-06
**버전**: 2.0 (업데이트)
**작성자**: 지민 + Claude Code
**이전 버전**: docs/knowledge_graph_roadmap.md (2025-10-29)

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [현황 분석](#2-현황-분석)
3. [목표 및 범위](#3-목표-및-범위)
4. [Neo4j 스키마 설계](#4-neo4j-스키마-설계)
5. [LLM 자동화 전략](#5-llm-자동화-전략)
6. [구현 로드맵](#6-구현-로드맵)
7. [비용 분석](#7-비용-분석)
8. [법령 지식그래프와의 통합](#8-법령-지식그래프와의-통합)
9. [성공 지표](#9-성공-지표)
10. [부록](#10-부록)

---

## 1. 프로젝트 개요

### 1.1 배경

한국의 암질환 치료는 복잡한 급여 기준과 빠른 정책 변화로 인해 의료진도 최신 정보를 파악하기 어려움. 특히:
- 항암제 급여 기준이 암종·라인·바이오마커별로 세분화
- 병용요법·단독요법 급여 여부 상이
- 월 단위로 새로운 약제 급여 결정 또는 변경

### 1.2 목표

**"암질환 약제·요법 지식그래프 + 하이브리드 RAG 시스템 구축"**

#### 핵심 질문 해결
```
✅ "HER2 양성 유방암 1차 치료에 쓸 수 있는 급여 약제는?"
✅ "Pembrolizumab과 병용 가능한 항암제는?"
✅ "폐암 EGFR 변이 환자의 급여 기준은?"
✅ "Atezolizumab이 최근 급여 확대된 암종은?"
✅ "Dostarlimab + Paclitaxel + Carboplatin 병용요법의 급여 조건은?"
```

### 1.3 데이터 범위

| 데이터 소스 | 크기 | 핵심 내용 | 완성도 |
|-----------|------|----------|--------|
| **hira_cancer** | 150 MB | 항암제 급여 공고 (823개) | ✅ 99.4% |
| **ncc** | 9.9 MB | 암정보 (100개 암종) | ✅ 100% |
| **hira_master** | 226 MB | 약제 사전 (항암제 포함) | ✅ 100% |
| **pharmalex_unity** | 715 MB | 항암제 154개 성분 | ✅ 100% |

**총 데이터**: 약 1.1 GB

---

## 2. 현황 분석

### 2.1 기 수행 작업

#### Phase 1 완료 (2025-10-29)
```
✅ HIRA 암질환 공고 수집 (484개 게시글, 828개 첨부파일)
   - 공고: 217개 (471개 파일)
   - 공고예고: 232개 (299개 파일)
   - FAQ: 117개 (58개 파일)

✅ 엔티티 추출 (38개 관계)
   - 16개 암종
   - 67개 항암제
   - 14개 병용요법, 12개 단독요법

✅ NCC 암정보 수집 (100개 암종)
   - 934개 섹션
   - 8개 표
   - 91개 이미지

✅ NCC 암정보 사전 (3,543개 용어)
   - 약제명: ~500개
   - 치료법: ~300개
   - 암종: ~200개
```

**산출물 위치**:
- `data/hira_cancer/parsed/` (823개 JSON)
- `data/ncc/cancer_info/` (100개 암종 JSON)
- `dictionary/ncc/` (3,543개 용어)

#### 항암제 사전 구축 Phase 1 완료 (2025-10-31)
```
✅ 약가 마스터에서 항암제 추출
   - L01/L02 ATC 코드 필터링
   - 154개 성분, 939개 브랜드명

✅ 브랜드명/성분명 정제
   - 제형 제거 ("버제니오정" → "버제니오")
   - 한글 성분명 추출 (96.1% 성공)
   - ATC 코드 매핑

출력: bridges/anticancer_master_clean.json
```

### 2.2 미완료 작업

```
🔄 Phase 2: 한글 성분명 보완 (6개 누락)
🔄 Phase 3: ATC 세분류 (L01EA, L01EB 등)
🔄 Phase 4: 코드 기반 매칭 (브랜드명 → ATC)
```

### 2.3 당일(11-06) 발견사항

#### HIRA 고시 패턴 분석
```
8,539개 고시 분석 결과:
- 항암제 언급: 67개 고유 약제
- 암종 언급: 16개 암종
- 요법 패턴: "병용요법", "단독요법", "1차", "2차"
```

---

## 3. 목표 및 범위

### 3.1 최종 목표

**"암질환 특화 지식그래프 기반 RAG 시스템"**

#### 3.1.1 기능적 목표

```
✅ 항암제 검색
   - 암종별 급여 약제 조회
   - 바이오마커별 약제 검색
   - 라인별(1차/2차/3차) 급여 조건

✅ 병용요법 조회
   - 특정 약제와 병용 가능한 약제
   - 병용요법 급여 기준
   - 요법별 암종 적응증

✅ 급여 기준 추적
   - 최신 급여 기준 조회
   - 급여 변경 이력
   - 제한사항 및 예외

✅ 임상 정보 통합
   - NCC 암정보 연계
   - 치료 가이드라인
   - 부작용 정보
```

### 3.2 범위

#### 포함 (In Scope)
```
✅ 항암제 (154개 성분, 939개 브랜드)
✅ 암종 (100개)
✅ 병용요법 (26개 이상)
✅ 급여 공고 (823개)
✅ 바이오마커 (HER2, EGFR, ALK, PD-L1 등)
✅ 치료 라인 (1차, 2차, 3차)
✅ 치료 목적 (고식적, 보조, 신보조)
```

#### 제외 (Out of Scope)
```
❌ 비암질환 약제 (별도 프로젝트)
❌ 의료기기
❌ 임상시험 정보 (향후 확장)
❌ 해외 미승인 약물
```

---

## 4. Neo4j 스키마 설계

### 4.1 노드 타입 (10개)

#### 4.1.1 Core Entities (핵심)

##### AnticancerDrug (항암제)
```cypher
(:AnticancerDrug {
  atc_code: String,              // L01EF03
  ingredient_ko: String,         // 아베마시클립
  ingredient_en: String,         // abemaciclib
  ingredient_base_ko: String,    // 아베마시클립 (염 제거)
  ingredient_base_en: String,    // abemaciclib
  salt_form: String,             // null (염 없음)
  brand_names: [String],         // ["버제니오"]
  brand_name_primary: String,    // 버제니오
  manufacturers: [String],       // ["한국릴리(유)"]

  // ATC 분류
  atc_level1: String,            // L01
  atc_level1_name: String,       // 항종양제
  atc_level2: String,            // L01E
  atc_level2_name: String,       // 단백질 키나제 억제제
  atc_level3: String,            // L01EF
  atc_level3_name: String,       // CDK4/6 억제제

  // 약리학적 정보
  mechanism_of_action: String,   // CDK4/6 억제
  therapeutic_category: String,  // 표적치료제
  drug_class: String,            // 키나제 억제제

  // 약가 정보
  prices: [Object],              // [{dose: "50mg", price: 12345}]

  // 메타데이터
  is_recombinant: Boolean,       // false
  approval_date: Date           // 최초 허가일
})
```

##### Cancer (암종)
```cypher
(:Cancer {
  name_ko: String,               // 유방암
  name_en: String,               // Breast Cancer
  kcd_codes: [String],           // ["C50", "C50.0", ...]

  // 분류
  category: String,              // 성인암/소아청소년암
  is_major_cancer: Boolean,      // 12대 암 여부

  // 임상 정보 (NCC 데이터)
  incidence_rank: Integer,       // 발생 순위
  survival_rate_5yr: Float,      // 5년 생존율
  description: String,           // 설명
  symptoms: [String],            // 증상
  diagnosis_methods: [String],   // 진단 방법

  // 바이오마커
  common_biomarkers: [String],   // ["HER2", "HR", "BRCA"]

  // 메타데이터
  ncc_url: String,               // NCC 페이지 URL
  last_updated: Date
})
```

##### CancerSubtype (암 아형)
```cypher
(:CancerSubtype {
  name_ko: String,               // HER2 양성 유방암
  name_en: String,               // HER2-positive Breast Cancer
  parent_cancer: String,         // 유방암

  // 바이오마커
  biomarkers: Object,            // {"HER2": "positive", "HR": "any"}

  // 임상 특성
  prevalence: Float,             // 유병률 (20%)
  prognosis: String,             // 예후
  description: String
})
```

##### Regimen (요법)
```cypher
(:Regimen {
  id: String,                    // regimen_001
  name_ko: String,               // Dostarlimab+Paclitaxel+Carboplatin
  name_en: String,

  // 구성
  drugs: [String],               // ["Dostarlimab", "Paclitaxel", "Carboplatin"]
  drug_atc_codes: [String],      // ATC 코드 리스트

  // 요법 정보
  type: String,                  // 병용요법/단독요법
  line: String,                  // 1차/2차/3차
  purpose: String,               // 고식적/보조/신보조

  // 투여 정보
  dosage_schedule: String,       // 투여 용량 및 일정
  cycle_length: String,          // 주기 (21일 등)

  // 임상 근거
  clinical_trial: String,        // 임상시험명
  evidence_level: String         // 근거 수준
})
```

##### Biomarker (바이오마커)
```cypher
(:Biomarker {
  name: String,                  // HER2
  full_name: String,             // Human Epidermal growth factor Receptor 2
  type: String,                  // 단백질/유전자/기타

  // 검사 정보
  test_methods: [String],        // ["IHC", "FISH"]
  positive_criteria: String,     // 양성 기준

  // 임상 의의
  prognostic: Boolean,           // 예후 인자 여부
  predictive: Boolean,           // 예측 인자 여부

  description: String
})
```

#### 4.1.2 Guideline Entities

##### AnticancerGuideline (항암제 급여 공고)
```cypher
(:AnticancerGuideline {
  id: String,                    // guideline_20251024_001
  guideline_number: String,      // 고시 제2025-169호
  title: String,                 // 제목

  // 분류
  type: String,                  // 공고/공고예고/FAQ
  category: String,              // 신설/개정/삭제

  // 내용
  content: String,               // 전문
  summary: String,               // 요약
  changes: [Object],             // 변경 내역

  // 날짜
  published_date: Date,          // 발행일
  effective_date: Date,          // 시행일

  // 첨부파일
  attachments: [Object],         // [{filename, path, type}]

  // 메타데이터
  source: String,                // HIRA
  url: String
})
```

##### ReimbursementCriteria (급여 기준)
```cypher
(:ReimbursementCriteria {
  id: String,                    // criteria_001

  // 기준 내용
  indication: String,            // 적응증
  restrictions: String,          // 제한사항

  // 조건
  required_biomarkers: Object,   // {"HER2": "positive"}
  prior_treatments: [String],    // 선행 치료 요구사항
  exclusion_criteria: String,    // 제외 기준

  // 기타
  special_notes: String,         // 특이사항
  monitoring_requirements: String // 모니터링 요구사항
})
```

#### 4.1.3 Others

##### ClinicalTrial (임상시험)
```cypher
(:ClinicalTrial {
  trial_id: String,              // NCT12345678
  name: String,                  // 임상시험명
  phase: String,                 // Phase 1/2/3
  status: String,                // 진행중/완료

  primary_endpoint: String,      // 주요 평가변수
  results_summary: String       // 결과 요약
})
```

##### MedicalTerm (의학용어)
```cypher
(:MedicalTerm {
  name_ko: String,               // 표적치료제
  name_en: String,               // Targeted Therapy
  category: String,              // 치료법
  definition: String,            // 정의
  synonyms: [String]            // 동의어
})
```

##### Document (문서)
```cypher
(:Document {
  file_name: String,
  file_type: String,             // PDF/HWP
  content: String,
  embedding: [Float]            // 768차원 벡터
})
```

---

### 4.2 관계 타입 (15개)

#### 4.2.1 Drug ↔ Cancer 관계

```cypher
// 항암제 → 암종 (단독요법)
(AnticancerDrug)-[:TREATS_CANCER {
  line: String,                  // "1차", "2차", "3차 이상"
  purpose: String,               // "고식적", "보조", "신보조"
  biomarker_required: Object,    // {"HER2": "positive"}
  evidence_level: String,        // "1A", "1B", "2A" 등
  response_rate: Float,          // 반응률 (선택)
  survival_benefit: String      // 생존 이익 (선택)
}]->(Cancer)

// 항암제 → 암 아형
(AnticancerDrug)-[:TREATS_SUBTYPE {
  line: String,
  purpose: String,
  reimbursed: Boolean           // 급여 여부
}]->(CancerSubtype)

// 항암제 → 요법 (병용요법)
(AnticancerDrug)-[:PART_OF_REGIMEN {
  role: String,                  // "주약", "병용약"
  dose: String                   // 용량
}]->(Regimen)

// 요법 → 암종
(Regimen)-[:APPROVED_FOR {
  line: String,
  purpose: String,
  biomarker_criteria: Object
}]->(Cancer)

// 항암제 → 항암제 (병용)
(AnticancerDrug)-[:COMBINED_WITH {
  regimen_name: String,          // 요법명
  synergy: String,               // 시너지 효과
  common_combinations: [String] // 흔한 조합
}]->(AnticancerDrug)

// 항암제 → 항암제 (금기)
(AnticancerDrug)-[:CONTRAINDICATED_WITH {
  reason: String,                // 금기 이유
  severity: String              // 심각도
}]->(AnticancerDrug)
```

#### 4.2.2 Biomarker 관계

```cypher
// 암종 → 바이오마커
(Cancer)-[:HAS_BIOMARKER {
  frequency: Float,              // 빈도 (20%)
  prognostic_value: String,      // 예후 가치
  predictive_value: String      // 예측 가치
}]->(Biomarker)

// 암 아형 → 바이오마커 (정의)
(CancerSubtype)-[:DEFINED_BY]->(Biomarker)

// 약제 → 바이오마커 (표적)
(AnticancerDrug)-[:TARGETS]->(Biomarker)

// 급여 기준 → 바이오마커 (요구사항)
(ReimbursementCriteria)-[:REQUIRES_BIOMARKER {
  status: String                 // "positive", "negative", "high", "low"
}]->(Biomarker)
```

#### 4.2.3 Guideline 관계

```cypher
// 공고 → 약제 (급여 승인)
(AnticancerGuideline)-[:APPROVES {
  change_type: String,           // "신설", "확대", "변경", "삭제"
  effective_date: Date
}]->(AnticancerDrug)

// 공고 → 요법
(AnticancerGuideline)-[:APPROVES]->(Regimen)

// 공고 → 급여 기준
(AnticancerGuideline)-[:ESTABLISHES]->(ReimbursementCriteria)

// 급여 기준 → 약제
(ReimbursementCriteria)-[:APPLIES_TO]->(AnticancerDrug)

// 급여 기준 → 요법
(ReimbursementCriteria)-[:APPLIES_TO]->(Regimen)

// 급여 기준 → 암종
(ReimbursementCriteria)-[:FOR_CANCER]->(Cancer)

// 공고 개정
(AnticancerGuideline)-[:SUPERSEDES {
  changes: [String]              // 변경 내용
}]->(AnticancerGuideline)
```

#### 4.2.4 Clinical 관계

```cypher
// 임상시험 → 약제
(ClinicalTrial)-[:EVALUATED]->(AnticancerDrug)

// 임상시험 → 요법
(ClinicalTrial)-[:EVALUATED]->(Regimen)

// 임상시험 → 암종
(ClinicalTrial)-[:FOR_CANCER]->(Cancer)
```

#### 4.2.5 Document 관계

```cypher
// 문서 → 엔티티
(Document)-[:MENTIONS]->(AnticancerDrug)
(Document)-[:MENTIONS]->(Cancer)
(Document)-[:MENTIONS]->(Regimen)

// 문서 → 공고 (원본)
(Document)-[:SOURCE_OF]->(AnticancerGuideline)
```

---

### 4.3 스키마 시각화 (암질환 중심)

```
                    ┌──────────────┐
                    │  Biomarker   │
                    │   (50+)      │
                    └──────┬───────┘
                           │
              HAS_BIOMARKER│DEFINED_BY
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     ┌────▼────┐      ┌────▼─────┐    ┌────▼─────┐
     │ Cancer  │      │Cancer    │    │Anticancer│
     │ (100)   │      │Subtype   │    │  Drug    │
     └────┬────┘      │  (50+)   │    │  (154)   │
          │           └────┬─────┘    └────┬─────┘
          │                │               │
    TREATS│          TREATS_SUBTYPE        │PART_OF
          │                │               │
          └────────────────┼───────────────┘
                           │
                      ┌────▼─────┐
                      │ Regimen  │
                      │  (26+)   │
                      └────┬─────┘
                           │
                     APPROVED_FOR
                           │
                           ▼
                  ┌─────────────────┐
                  │Reimbursement    │
                  │  Criteria       │
                  │   (100+)        │
                  └────┬────────────┘
                       │
                 ESTABLISHES
                       │
                  ┌────▼────────┐
                  │Anticancer   │
                  │ Guideline   │
                  │   (823)     │
                  └─────────────┘
```

---

## 5. LLM 자동화 전략

### 5.1 자동화 대상

| 작업 | 수동 (예상) | LLM 자동화 | 절감 |
|-----|-----------|-----------|------|
| **공고 엔티티 추출** | 2주, $2,400 | 2일, $10-15 | 99.4% |
| **병용요법 구조화** | 1주, $1,200 | 1일, $5-10 | 99.6% |
| **급여 기준 파싱** | 2주, $2,400 | 2일, $10-15 | 99.4% |
| **바이오마커 추출** | 1주, $1,200 | 1일, $5-10 | 99.6% |
| **관계 추출** | 1주, $1,200 | 1일, $5-10 | 99.6% |
| **총계** | **7주, $8,400** | **7일, $35-60** | **99.4%** |

### 5.2 Claude API 활용

#### 5.2.1 HIRA 공고 엔티티 추출
```python
def extract_anticancer_entities(guideline_content: str) -> dict:
    """
    HIRA 공고에서 항암제, 암종, 요법 정보 추출
    """

    prompt = f"""
다음은 HIRA 항암제 급여 공고입니다. 다음 정보를 JSON으로 추출하세요:

공고 내용:
{guideline_content}

추출 정보:
1. 공고 메타데이터
   - 고시번호
   - 발행일
   - 변경 유형 (신설/확대/변경/삭제)

2. 항암제
   - 약제명 (한글, 영문)
   - 품명 (브랜드명)

3. 암종
   - 암종명
   - 암 아형 (있는 경우)

4. 바이오마커
   - 바이오마커명
   - 양성/음성 여부

5. 요법 정보
   - 병용요법/단독요법
   - 구성 약제 (병용요법인 경우)
   - 치료 라인 (1차/2차/3차)
   - 치료 목적 (고식적/보조/신보조)

6. 급여 기준
   - 적응증
   - 제한사항
   - 바이오마커 요구사항

출력 형식:
{{
  "metadata": {{
    "guideline_number": "고시 제2025-169호",
    "published_date": "2025-10-24",
    "change_type": "신설"
  }},
  "drugs": [
    {{
      "name_ko": "도스탈리맙",
      "name_en": "Dostarlimab",
      "brand_name": "젬퍼리"
    }}
  ],
  "cancers": [
    {{
      "name": "자궁암",
      "subtype": "dMMR 자궁내막암"
    }}
  ],
  "biomarkers": [
    {{
      "name": "dMMR",
      "status": "positive",
      "full_name": "deficient mismatch repair"
    }}
  ],
  "regimen": {{
    "name": "Dostarlimab + Paclitaxel + Carboplatin",
    "type": "병용요법",
    "drugs": ["Dostarlimab", "Paclitaxel", "Carboplatin"],
    "line": "1차",
    "purpose": "고식적요법"
  }},
  "reimbursement_criteria": {{
    "indication": "dMMR 또는 MSI-H 자궁내막암",
    "biomarker_requirements": {{"dMMR": "positive"}},
    "restrictions": "1차 치료에 한함"
  }}
}}

JSON만 출력하세요.
"""

    # Claude API 호출
    client = anthropic.Anthropic(api_key=API_KEY)
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.content[0].text)
```

#### 5.2.2 병용요법 구조화
```python
def structure_regimen(regimen_text: str, drug_index: dict) -> dict:
    """
    병용요법 텍스트 → 구조화 JSON
    """

    prompt = f"""
다음 병용요법 정보를 구조화하세요:

{regimen_text}

약제 데이터베이스:
{json.dumps(drug_index, ensure_ascii=False)}

출력 형식:
{{
  "regimen": {{
    "name_ko": "도스탈리맙+파클리탁셀+카보플라틴",
    "name_en": "Dostarlimab+Paclitaxel+Carboplatin",
    "drugs": [
      {{
        "name": "Dostarlimab",
        "atc_code": "L01FF05",
        "role": "주약",
        "dose": "500mg"
      }},
      {{
        "name": "Paclitaxel",
        "atc_code": "L01CD01",
        "role": "병용약",
        "dose": "175mg/m²"
      }},
      {{
        "name": "Carboplatin",
        "atc_code": "L01XA02",
        "role": "병용약",
        "dose": "AUC 5"
      }}
    ],
    "type": "병용요법",
    "line": "1차",
    "purpose": "고식적",
    "cycle_length": "21일",
    "administration_schedule": "Day 1, Day 8, Day 15"
  }}
}}

JSON만 출력하세요.
"""

    # ... (Claude API 호출)
```

#### 5.2.3 바이오마커 추출
```python
def extract_biomarkers(cancer_info: str) -> list:
    """
    암정보에서 바이오마커 추출
    """

    prompt = f"""
다음 암정보에서 바이오마커를 추출하세요:

{cancer_info}

출력 형식:
{{
  "biomarkers": [
    {{
      "name": "HER2",
      "full_name": "Human Epidermal growth factor Receptor 2",
      "type": "단백질",
      "test_methods": ["IHC", "FISH"],
      "positive_criteria": "IHC 3+ 또는 FISH 양성",
      "prognostic": true,
      "predictive": true,
      "clinical_significance": "HER2 표적치료 대상 선별"
    }}
  ]
}}

JSON만 출력하세요.
"""

    # ... (Claude API 호출)
```

---

### 5.3 자동화 파이프라인

```
[1단계: HIRA 공고 파싱]
823개 JSON → Claude API → 엔티티 추출
비용: $10-15 (약 2M 토큰)
시간: 1시간

[2단계: NCC 암정보 파싱]
100개 암종 → Claude API → 바이오마커 추출
비용: $5-10 (약 1M 토큰)
시간: 30분

[3단계: 병용요법 구조화]
26개 요법 → Claude API → 구조화
비용: $1-2
시간: 10분

[4단계: 관계 추출]
모든 엔티티 → Claude API → 관계 추출
비용: $5-10
시간: 30분

[5단계: Neo4j 임포트]
JSON → Python ETL → Neo4j
비용: 없음
시간: 1시간

총 비용: $21-37
총 시간: 3시간 10분
```

---

## 6. 구현 로드맵

### 6.1 Week 1: 항암제 사전 완성

#### Day 1-2: Phase 2-4 완료 (anticancer_dictionary_phases.md)
```
□ Phase 2: 한글 성분명 보완 (6개)
  - MFDS API 조회
  - 수동 매핑

□ Phase 2: 염/기본형 분리
  - "아비라테론아세테이트" → "아비라테론" + "아세테이트"

□ Phase 3: ATC 세분류
  - L01EA, L01EB, L01EC 등 세분류
  - 작용기전 태깅

□ Phase 4: 브랜드 인덱스 구축
  - 브랜드명 → ATC 매핑 테이블
  - 정확 매칭 함수 구현

산출물:
- bridges/anticancer_master_enhanced.json
- bridges/anticancer_master_classified.json
- bridges/brand_index.json
```

#### Day 3: 항암제 Neo4j 임포트
```
□ AnticancerDrug 노드 생성 (154개)
□ 브랜드명, ATC 분류 포함
□ 인덱스 생성

예상 시간: 4시간
```

---

### 6.2 Week 2: 암종 및 바이오마커 구축

#### Day 1-2: NCC 암정보 파싱
```
□ 100개 암종 JSON 읽기
□ Claude API로 바이오마커 추출
□ 임상 정보 구조화

예상 비용: $5-10
예상 시간: 1일
산출물: data/ncc/structured/*.json
```

#### Day 3-4: Cancer 및 Biomarker 노드 생성
```
□ Cancer 노드 (100개)
□ CancerSubtype 노드 (50개 예상)
  - HER2 양성 유방암
  - EGFR 변이 폐암 등
□ Biomarker 노드 (50개 예상)
  - HER2, EGFR, ALK, PD-L1 등

□ HAS_BIOMARKER 관계
□ DEFINED_BY 관계

예상 시간: 1.5일
산출물: scripts/neo4j/build_cancer_nodes.py
```

---

### 6.3 Week 3: HIRA 공고 및 급여 기준

#### Day 1-3: HIRA 공고 엔티티 추출
```
□ 823개 공고 Claude API 일괄 처리
□ 항암제, 암종, 요법 추출
□ 급여 기준 추출

예상 비용: $10-15
예상 시간: 2일
산출물: data/hira_cancer/structured_entities.json
```

#### Day 4-5: AnticancerGuideline 및 ReimbursementCriteria 노드
```
□ AnticancerGuideline 노드 (823개)
□ ReimbursementCriteria 노드 (100개 예상)
□ Regimen 노드 (26개 이상)

□ APPROVES 관계
□ ESTABLISHES 관계
□ APPLIES_TO 관계

예상 시간: 1.5일
산출물: scripts/neo4j/build_guideline_nodes.py
```

---

### 6.4 Week 4: 관계 구축

#### Day 1-3: Drug ↔ Cancer 관계
```
□ TREATS_CANCER 관계 (단독요법)
  - 라인, 목적, 바이오마커 조건

□ PART_OF_REGIMEN 관계 (병용요법)
  - 역할, 용량

□ APPROVED_FOR 관계 (요법 → 암종)

예상 관계: 200~500개
예상 시간: 2일
산출물: scripts/neo4j/build_anticancer_relations.py
```

#### Day 4-5: Biomarker 관계
```
□ TARGETS 관계 (약제 → 바이오마커)
□ REQUIRES_BIOMARKER 관계 (급여 기준 → 바이오마커)

예상 관계: 100~200개
예상 시간: 1일
```

---

### 6.5 Week 5: 문서 임베딩 및 RAG

#### Day 1-2: Document 노드 + 임베딩
```
□ Document 노드 (823개 공고)
□ Sentence Transformers 임베딩 (768차원)
□ Neo4j embedding 속성 저장

예상 시간: 1일
산출물: scripts/neo4j/build_anticancer_embeddings.py
```

#### Day 3-5: 하이브리드 RAG 파이프라인
```
□ 엔티티 추출 (암종, 약제, 바이오마커)
□ Neo4j 그래프 탐색
□ 벡터 유사도 검색
□ 컨텍스트 융합
□ Claude API 답변 생성

예상 시간: 2일
산출물: scripts/rag/anticancer_rag.py
```

---

### 6.6 Week 6: 테스트 및 문서화

#### Day 1-3: 통합 테스트
```
□ 샘플 질문 100개 테스트
  - "HER2 양성 유방암 1차 치료 급여 약제는?"
  - "Pembrolizumab과 병용 가능한 항암제는?"
  - "폐암 EGFR 변이 급여 기준은?"

□ 정확도 검증 (목표: 90% 이상)
□ 응답 시간 측정 (목표: < 3초)

예상 시간: 2일
```

#### Day 4-5: 문서화
```
□ 사용자 가이드
□ API 문서
□ 샘플 쿼리 모음

산출물:
- docs/ANTICANCER_USER_GUIDE.md
- docs/ANTICANCER_API_REFERENCE.md
```

---

### 6.7 타임라인 요약

```
Week 1: 항암제 사전 완성
├─ Day 1-2: Phase 2-4 완료
└─ Day 3: Neo4j 임포트

Week 2: 암종 및 바이오마커
├─ Day 1-2: NCC 파싱
└─ Day 3-4: Cancer/Biomarker 노드

Week 3: HIRA 공고 및 급여 기준
├─ Day 1-3: 엔티티 추출
└─ Day 4-5: Guideline 노드

Week 4: 관계 구축
├─ Day 1-3: Drug ↔ Cancer 관계
└─ Day 4-5: Biomarker 관계

Week 5: RAG 파이프라인
├─ Day 1-2: 문서 임베딩
└─ Day 3-5: Hybrid RAG

Week 6: 테스트 및 문서화
├─ Day 1-3: 통합 테스트
└─ Day 4-5: 문서화

──────────────────────────────
총 소요: 6주 (약 30일)
```

---

## 7. 비용 분석

### 7.1 개발 비용

| 항목 | 비용 | 비고 |
|-----|------|------|
| **LLM API (Claude)** |  |  |
| - HIRA 공고 엔티티 추출 (823개) | $10-15 | 2M 토큰 |
| - NCC 바이오마커 추출 (100개) | $5-10 | 1M 토큰 |
| - 병용요법 구조화 (26개) | $1-2 | 0.2M 토큰 |
| - 관계 추출 | $5-10 | 1M 토큰 |
| **Sentence Transformers** | $0 | 오픈소스 |
| **Neo4j** | $0 | Community Edition |
| **총 개발 비용** | **$21-37** |  |

### 7.2 수동 작업 대비 절감

| 작업 | 수동 | LLM 자동화 | 절감액 |
|-----|------|-----------|--------|
| 공고 엔티티 추출 | $2,400 (2주) | $15 (2일) | $2,385 (99.4%) |
| 병용요법 구조화 | $1,200 (1주) | $2 (1일) | $1,198 (99.8%) |
| 급여 기준 파싱 | $2,400 (2주) | $15 (2일) | $2,385 (99.4%) |
| 바이오마커 추출 | $1,200 (1주) | $10 (1일) | $1,190 (99.2%) |
| 관계 추출 | $1,200 (1주) | $10 (1일) | $1,190 (99.2%) |
| **총계** | **$8,400 (7주)** | **$52 (7일)** | **$8,348 (99.4%)** |

---

## 8. 법령 지식그래프와의 통합

### 8.1 통합 지점

#### 8.1.1 급여 기준 연결
```cypher
// 암질환 급여 기준 → 법령
(ReimbursementCriteria)-[:BASED_ON]->(Article)

// 예시
(ReimbursementCriteria {
  indication: "HER2 양성 유방암"
})-[:BASED_ON]->(Article {
  id: "제10조",
  title: "급여의 범위"
})
```

#### 8.1.2 고시 연결
```cypher
// 항암제 공고 → 일반 고시
(AnticancerGuideline)-[:REFERENCED_BY]->(Guideline)

// 항암제 공고 → 법령
(AnticancerGuideline)-[:GOVERNED_BY]->(Legislation)
```

#### 8.1.3 통합 쿼리 예시
```cypher
// 약제 → 급여 기준 → 법적 근거 추적
MATCH (drug:AnticancerDrug {name: "Pembrolizumab"})
      -[:TREATS_CANCER]->(cancer:Cancer {name: "폐암"})
MATCH (guideline:AnticancerGuideline)-[:APPROVES]->(drug)
MATCH (criteria:ReimbursementCriteria)-[:APPLIES_TO]->(drug)
OPTIONAL MATCH (criteria)-[:BASED_ON]->(article:Article)
                          <-[:CONTAINS]-(law:Legislation)
RETURN drug, cancer, guideline, criteria, article, law
```

### 8.2 통합 시너지

```
암질환 그래프 (상세)  +  법령 그래프 (근거)
         │                      │
         └──────────┬───────────┘
                    │
            ┌───────▼────────┐
            │  통합 RAG      │
            │  시스템        │
            └───────┬────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   약제 정보   법적 근거   절차 안내
```

---

## 9. 성공 지표

### 9.1 Phase별 완료 기준

#### Week 1: 항암제 사전
```
✅ 154개 성분 모두 한글명 존재
✅ ATC 세분류 완료
✅ 브랜드 인덱스 생성
✅ Neo4j AnticancerDrug 노드 154개
```

#### Week 2: 암종/바이오마커
```
✅ Cancer 노드 100개
✅ CancerSubtype 노드 50개
✅ Biomarker 노드 50개
✅ HAS_BIOMARKER 관계 100개
```

#### Week 3: 공고/급여 기준
```
✅ AnticancerGuideline 노드 823개
✅ ReimbursementCriteria 노드 100개
✅ Regimen 노드 26개 이상
✅ 엔티티 추출 정확도 95% 이상
```

#### Week 4: 관계 구축
```
✅ TREATS_CANCER 관계 200개 이상
✅ PART_OF_REGIMEN 관계 50개 이상
✅ APPROVED_FOR 관계 26개 이상
✅ TARGETS 관계 100개 이상
```

#### Week 5: RAG 파이프라인
```
✅ Document 임베딩 823개
✅ Hybrid RAG 동작
✅ 샘플 쿼리 테스트 통과
```

#### Week 6: 테스트
```
✅ 질의응답 정확도 90% 이상
✅ 응답 시간 < 3초
✅ 문서화 완료
```

### 9.2 최종 성공 지표

| 지표 | 목표 | 측정 방법 |
|-----|------|----------|
| **항암제 정확도** | 100% | 154개 모두 매핑 |
| **암종 커버리지** | 100% | 100개 모두 임포트 |
| **공고 파싱 정확도** | 95%+ | 샘플 100개 검증 |
| **병용요법 추출** | 90%+ | 수동 검증 |
| **질의응답 정확도** | 90%+ | 100개 질문 평가 |
| **바이오마커 인식** | 95%+ | 주요 마커 검증 |
| **응답 시간** | < 3초 | 평균 쿼리 시간 |

---

## 10. 부록

### 10.1 참조 문서

- `docs/knowledge_graph_roadmap.md` - 이전 버전 (2025-10-29)
- `docs/plans/anticancer_dictionary_phases.md` - 항암제 사전 4단계
- `docs/reports/hira_cancer_analysis_20251023.md` - 데이터 수집 분석
- `docs/journal/hira_cancer/2025-10-31_code_based_pivot.md` - 코드 기반 매칭

### 10.2 데이터 파일 위치

```
data/
├── hira_cancer/
│   ├── raw/attachments/       # 828개 원본 파일
│   └── parsed/                # 823개 JSON
├── ncc/
│   ├── cancer_info/           # 100개 암종 JSON
│   └── cancer_dictionary/     # 3,543개 용어
├── hira_master/
│   └── drug_dictionary_normalized.json  # 약제 포함
└── pharmalex_unity/
    └── merged_pharma_data.csv # 항암제 원본

bridges/
├── anticancer_master_clean.json      # Phase 1 완료
├── anticancer_master_enhanced.json   # Phase 2 (예정)
├── anticancer_master_classified.json # Phase 3 (예정)
└── brand_index.json                  # Phase 4 (예정)
```

### 10.3 Cypher 쿼리 예제

```cypher
// 1. HER2 양성 유방암 1차 치료 급여 약제
MATCH (drug:AnticancerDrug)-[r:TREATS_SUBTYPE {line: "1차"}]
      ->(subtype:CancerSubtype)-[:DEFINED_BY]->(bio:Biomarker {name: "HER2"})
WHERE subtype.parent_cancer = "유방암"
  AND r.biomarker_required.HER2 = "positive"
  AND r.reimbursed = true
RETURN drug.ingredient_ko, drug.brand_name_primary, r

// 2. Pembrolizumab과 병용 가능한 항암제
MATCH (drug1:AnticancerDrug {ingredient_en: "pembrolizumab"})
      -[:COMBINED_WITH]->(drug2:AnticancerDrug)
RETURN drug2.ingredient_ko, drug2.brand_name_primary

// 또는
MATCH (drug1:AnticancerDrug {ingredient_en: "pembrolizumab"})
      -[:PART_OF_REGIMEN]->(regimen:Regimen)
      <-[:PART_OF_REGIMEN]-(drug2:AnticancerDrug)
WHERE drug1 <> drug2
RETURN regimen.name_ko, collect(drug2.ingredient_ko)

// 3. 폐암 EGFR 변이 급여 기준
MATCH (cancer:Cancer {name_ko: "폐암"})
      -[:HAS_BIOMARKER]->(bio:Biomarker {name: "EGFR"})
MATCH (criteria:ReimbursementCriteria)-[:FOR_CANCER]->(cancer)
WHERE criteria.required_biomarkers.EGFR IS NOT NULL
RETURN criteria

// 4. 최근 급여 확대된 항암제
MATCH (guideline:AnticancerGuideline)
      -[r:APPROVES {change_type: "확대"}]->(drug:AnticancerDrug)
WHERE guideline.published_date >= date('2025-01-01')
RETURN drug.ingredient_ko, guideline.title, guideline.published_date
ORDER BY guideline.published_date DESC

// 5. 특정 요법의 상세 정보
MATCH (regimen:Regimen {name_ko: "Dostarlimab+Paclitaxel+Carboplatin"})
      -[:APPROVED_FOR]->(cancer:Cancer)
MATCH (regimen)<-[:PART_OF_REGIMEN]-(drug:AnticancerDrug)
OPTIONAL MATCH (guideline:AnticancerGuideline)-[:APPROVES]->(regimen)
OPTIONAL MATCH (criteria:ReimbursementCriteria)-[:APPLIES_TO]->(regimen)
RETURN regimen, cancer, collect(drug), guideline, criteria
```

### 10.4 샘플 질문 100개

**Category 1: 암종별 약제 조회 (30개)**
1. HER2 양성 유방암 1차 치료 급여 약제는?
2. 폐암 EGFR 변이 양성 환자에게 쓸 수 있는 약제는?
3. 대장암 3차 치료 옵션은?
... (27개 더)

**Category 2: 병용요법 (25개)**
31. Pembrolizumab과 병용 가능한 항암제는?
32. Atezolizumab + Bevacizumab + 화학요법 병용이 가능한 암종은?
... (23개 더)

**Category 3: 급여 기준 (25개)**
56. Osimertinib 급여 조건은?
57. Trastuzumab deruxtecan 급여 제한사항은?
... (23개 더)

**Category 4: 바이오마커 (10개)**
81. PD-L1 TPS ≥50% 환자에게 단독요법 가능한 약제는?
82. ALK 융합 양성 폐암 표적치료제는?
... (8개 더)

**Category 5: 변경 이력 (10개)**
91. 2025년 신규 급여된 항암제는?
92. Pembrolizumab 급여 확대 이력은?
... (8개 더)

---

**문서 버전**: 2.0
**최종 수정**: 2025-11-06
**이전 버전**: docs/knowledge_graph_roadmap.md (v1.0, 2025-10-29)
**관련 문서**: docs/MASTER_PLAN_knowledge_graph_construction.md (법령)

**Status**: ✅ 작성 완료, ⏳ 승인 대기

---
