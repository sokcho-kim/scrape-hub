# 의료 지식그래프 구축 전략 (Neo4j + RAG)

**작성일**: 2025-11-06
**목표**: 전체 의료 데이터를 통합한 Neo4j 지식그래프 구축 및 RAG 시스템 개발

---

## 📊 1. 데이터 소스 요약 (emrcert 제외)

| 데이터 소스 | 크기 | 핵심 엔티티 | 우선순위 |
|-----------|------|-----------|---------|
| **hira_master** | 226 MB | 약제, KDRG코드, 약가 | ⭐⭐⭐⭐⭐ |
| **pharmalex_unity** | 715 MB | 통합 약제정보 | ⭐⭐⭐⭐⭐ |
| **hira_cancer** | 150 MB | 항암제, 암종, 요법 | ⭐⭐⭐⭐⭐ |
| **hira** | 114 MB | 급여기준, 고시 | ⭐⭐⭐⭐ |
| **hira_rulesvc** | 26 MB | 법령, 고시, 행정해석 | ⭐⭐⭐⭐ |
| **ncc** | 9.9 MB | 암정보, 치료법 | ⭐⭐⭐⭐ |
| **kssc** | 105 MB | KCD 8/9차 질병코드 | ⭐⭐⭐⭐ |
| **mfds** | 273 MB | 한국약전 | ⭐⭐⭐ |
| **likms** | 9.2 MB | 의료급여법 | ⭐⭐⭐ |
| **hira_notice** | 880 KB | KCD 개정안내 | ⭐⭐ |
| **pharma** | 3.6 MB | 테스트 데이터 | ⭐ |

**총 데이터**: 약 1.6 GB

---

## 🎯 2. 핵심 엔티티 타입 정의

### 2.1 Primary Entities (핵심 노드)

#### 💊 Drug (약제)
```cypher
(:Drug {
  code: String,              // 약제코드
  name_kor: String,          // 한글명
  name_eng: String,          // 영문명
  generic_name: String,      // 성분명
  brand_names: [String],     // 상품명 리스트
  category: String,          // 분류 (항암제, 항생제 등)
  price: Float,              // 약가
  unit: String,              // 단위
  manufacturer: String,      // 제조사
  atc_code: String          // ATC 코드
})
```
**데이터 소스**:
- hira_master/drug_dictionary.json (500만 라인)
- pharmalex_unity/merged_pharma_data.csv (715 MB)
- hira_cancer (항암제 67개)
- ncc (항암제)

---

#### 🏥 Disease (질병)
```cypher
(:Disease {
  kcd_code: String,          // KCD 코드 (A00.0)
  name_kor: String,          // 한글 질병명
  name_eng: String,          // 영문 질병명
  chapter: String,           // 대분류 (01-22)
  category: String,          // 중분류
  subcategory: String,       // 소분류
  is_usable: Boolean,        // 사용가능 코드 여부
  version: String            // KCD 8차/9차
})
```
**데이터 소스**:
- kssc/kcd-9th/normalized/kcd9_full.json (54,125개)
- kssc/kcd-8th (기존 코드)
- hira_master/배포용 상병마스터.xlsx

---

#### 🔬 Procedure (수술/처치)
```cypher
(:Procedure {
  code_kor: String,          // 한글 코드 (자751)
  code_eng: String,          // 영문 코드 (Q7511)
  name: String,              // 명칭
  category: String,          // 분류
  mdc: String               // MDC 분류 (01-22)
})
```
**데이터 소스**:
- hira_master/kdrg_parsed/kdrg_procedures_full.json (1,487개)
- hira_master/KDRG 분류집 (11 MDC, 1,274페이지)

---

#### 🎗️ Cancer (암종)
```cypher
(:Cancer {
  name: String,              // 암종명 (위암, 폐암 등)
  type: String,              // 유형 (주요암, 성인암, 소아청소년암)
  tags: [String],            // 태그
  kcd_codes: [String],       // 관련 KCD 코드
  description: String       // 설명
})
```
**데이터 소스**:
- ncc/cancer_info (100개 암종)
- hira_cancer (16개 추출된 암종)

---

#### 💉 Regimen (치료요법)
```cypher
(:Regimen {
  name: String,              // 요법명
  type: String,              // 단독/병용
  line: String,              // 1차/2차/3차
  purpose: String,           // 고식적/보조/신보조
  drugs: [String],           // 포함 약제 리스트
  dosage: String            // 용량 정보
})
```
**데이터 소스**:
- hira_cancer (38개 관계 추출)
- ncc (항암화학요법)

---

#### 📋 Guideline (고시/지침)
```cypher
(:Guideline {
  doc_id: String,            // 고시번호 (고시 제2025-169호)
  title: String,             // 제목
  type: String,              // 유형 (공고/법령/행정해석)
  published_date: Date,      // 발행일
  source: String,            // 발행기관 (HIRA/복지부)
  category: String,          // 분류 (약제/행위/재료)
  content: String,           // 전문
  summary: String           // 요약
})
```
**데이터 소스**:
- hira_cancer (217개 공고 + 232개 공고예고)
- hira_rulesvc (56개 법령/고시)
- hira/hiradata_ver2.xlsx (8,539개 고시)
- likms (의료급여법 3개)

---

#### 🔍 Test (검사)
```cypher
(:Test {
  name: String,              // 검사명 (HbA1C, eGFR 등)
  code: String,              // 검사 코드
  unit: String,              // 단위 (%, mg/dL 등)
  normal_range: String,      // 정상 범위
  category: String          // 분류
})
```
**데이터 소스**:
- hira (고시 내 기준 - HbA1C, eGFR, LVEF, BMI 등 19개)

---

#### 📖 MedicalTerm (의학용어)
```cypher
(:MedicalTerm {
  name: String,              // 용어명
  definition: String,        // 정의
  category: String,          // 분류
  synonyms: [String],        // 동의어
  related_terms: [String]   // 관련 용어
})
```
**데이터 소스**:
- ncc/cancer_dictionary (3,543개)
- mfds/한국약전 (약학 용어)

---

### 2.2 Secondary Entities (보조 노드)

#### 📄 Document (문서)
```cypher
(:Document {
  file_name: String,         // 파일명
  file_type: String,         // PDF/HWP/Excel
  file_path: String,         // 경로
  parsed: Boolean,           // 파싱 여부
  content: String,           // 내용 (텍스트)
  embeddings: [Float]       // 벡터 임베딩
})
```

#### 🏢 Organization (기관)
```cypher
(:Organization {
  name: String,              // 기관명
  type: String,              // 유형 (정부/병원/제약사)
  code: String              // 기관 코드
})
```

---

## 🔗 3. 관계 타입 정의

### 3.1 Core Relationships (핵심 관계)

#### 약제 ↔ 질병
```cypher
// 약제 → 질병 (치료)
(Drug)-[:TREATS {
  indication: String,        // 적응증
  dosage: String,           // 용량
  line: String,             // 치료 라인 (1차/2차)
  evidence_level: String    // 근거 수준
}]->(Disease)

// 약제 → 암종 (항암제)
(Drug)-[:TREATS_CANCER {
  line: String,             // 1차/2차/3차
  purpose: String,          // 고식적/보조
  combination: Boolean      // 병용 여부
}]->(Cancer)
```

---

#### 약제 ↔ 약제
```cypher
// 약제 병용
(Drug)-[:COMBINED_WITH {
  regimen_name: String,     // 요법명
  drug_order: Integer       // 투여 순서
}]->(Drug)

// 약제 대체
(Drug)-[:ALTERNATIVE_TO {
  reason: String            // 대체 이유
}]->(Drug)

// 약제 금기
(Drug)-[:CONTRAINDICATED_WITH {
  severity: String,         // 심각도
  reason: String           // 이유
}]->(Drug)
```

---

#### 약제 ↔ 요법
```cypher
(Drug)-[:PART_OF]->(Regimen)
(Regimen)-[:TREATS]->(Cancer)
```

---

#### 질병 ↔ 수술/처치
```cypher
(Procedure)-[:TREATS]->(Disease)
(Procedure)-[:USED_FOR]->(Cancer)
```

---

#### 고시 ↔ 엔티티
```cypher
// 고시 → 약제 (급여 승인)
(Guideline)-[:APPROVES {
  effective_date: Date,     // 적용일
  restriction: String,      // 제한사항
  reimbursement: String    // 급여 기준
}]->(Drug)

// 고시 → 요법 (급여 승인)
(Guideline)-[:APPROVES]->(Regimen)

// 고시 → 질병 (급여 대상)
(Guideline)-[:APPLIES_TO]->(Disease)

// 고시 → 수술 (급여 승인)
(Guideline)-[:APPROVES]->(Procedure)

// 고시 → 고시 (개정)
(Guideline)-[:AMENDS {
  change_type: String       // 신설/개정/삭제
}]->(Guideline)
```

---

#### 검사 ↔ 질병/약제
```cypher
// 검사 → 질병 (진단)
(Test)-[:DIAGNOSES {
  threshold: String,        // 기준치
  operator: String         // >=, <=, =
}]->(Disease)

// 약제 → 검사 (모니터링 필요)
(Drug)-[:REQUIRES_MONITORING]->(Test)
```

---

#### 문서 ↔ 엔티티
```cypher
(Document)-[:MENTIONS]->(Drug)
(Document)-[:MENTIONS]->(Disease)
(Document)-[:MENTIONS]->(Procedure)
(Document)-[:SOURCE_OF]->(Guideline)
```

---

### 3.2 Metadata Relationships

```cypher
// 데이터 출처
(Entity)-[:SOURCED_FROM {
  source: String,           // 데이터 소스
  date: Date,              // 수집일
  confidence: Float        // 신뢰도
}]->(Organization)

// 계층 구조
(Disease)-[:PARENT_OF]->(Disease)  // KCD 계층
(Procedure)-[:BELONGS_TO]->(MedicalTerm)  // MDC 분류
```

---

## 🏗️ 4. 지식그래프 구축 전략

### Phase 1: 핵심 노드 구축 (1주)

#### Week 1-1: 약제 노드 (Drug)
**우선순위**: ⭐⭐⭐⭐⭐

```python
# 데이터 소스 통합 순서
1. hira_master/drug_dictionary_normalized.json (500만 라인)
   → 기본 약제 노드 생성

2. pharmalex_unity/merged_pharma_data.csv (715 MB)
   → 제조사, 가격 정보 보강

3. hira_cancer (67개 항암제)
   → 항암제 플래그 추가

4. ncc 항암제 정보
   → 항암제 상세 정보 추가
```

**예상 노드 수**: 약 50만~100만개
**작업 시간**: 2-3일

**구현 스크립트**: `scripts/neo4j/build_drug_nodes.py`

---

#### Week 1-2: 질병 노드 (Disease)
**우선순위**: ⭐⭐⭐⭐⭐

```python
# 데이터 소스
1. kssc/kcd-9th/normalized/kcd9_full.json (54,125개)
   → KCD-9 질병 노드 생성

2. kssc/kcd-8th
   → KCD-8 노드 생성 (비교용)

3. hira_master/배포용 상병마스터.xlsx
   → 추가 정보 보강
```

**예상 노드 수**: 약 54,000개
**작업 시간**: 1-2일

**구현 스크립트**: `scripts/neo4j/build_disease_nodes.py`

---

#### Week 1-3: 수술/처치 노드 (Procedure)
**우선순위**: ⭐⭐⭐⭐

```python
# 데이터 소스
1. hira_master/kdrg_parsed/kdrg_procedures_full.json (1,487개)
   → 수술/처치 노드 생성

2. hira_master/kdrg_korean_to_english.json
   → 한영 매핑 추가
```

**예상 노드 수**: 약 1,500개
**작업 시간**: 0.5일

**구현 스크립트**: `scripts/neo4j/build_procedure_nodes.py`

---

#### Week 1-4: 암종 노드 (Cancer)
**우선순위**: ⭐⭐⭐⭐

```python
# 데이터 소스
1. ncc/cancer_info (100개)
   → 암종 노드 생성

2. hira_cancer (16개 추출)
   → 급여 관련 암종 추가
```

**예상 노드 수**: 약 100개
**작업 시간**: 0.5일

**구현 스크립트**: `scripts/neo4j/build_cancer_nodes.py`

---

### Phase 2: 관계 구축 (1주)

#### Week 2-1: Drug ↔ Disease 관계
**우선순위**: ⭐⭐⭐⭐⭐

```python
# 데이터 소스
1. hira (고시 8,539개)
   → 패턴 매칭으로 관계 추출

2. hira_cancer (38개 관계)
   → 항암제-암종 관계

3. ncc 암정보
   → 치료법 관계
```

**예상 관계 수**: 약 10,000~50,000개
**작업 시간**: 3일

**구현 스크립트**: `scripts/neo4j/build_drug_disease_relations.py`

---

#### Week 2-2: 고시 관계 (Guideline)
**우선순위**: ⭐⭐⭐⭐

```python
# 데이터 소스
1. hira/hiradata_ver2.xlsx (8,539개)
   → 고시 노드 + APPROVES 관계

2. hira_cancer (217+232개)
   → 암질환 고시

3. hira_rulesvc (56개)
   → 법령 노드
```

**예상 노드 수**: 약 9,000개
**예상 관계 수**: 약 20,000개
**작업 시간**: 2일

**구현 스크립트**: `scripts/neo4j/build_guideline_relations.py`

---

#### Week 2-3: 요법 관계 (Regimen)
**우선순위**: ⭐⭐⭐

```python
# 데이터 소스
1. hira_cancer (38개 관계)
   → 요법 노드 + PART_OF 관계

2. ncc 항암화학요법
   → 추가 요법 정보
```

**예상 노드 수**: 약 100개
**예상 관계 수**: 약 300개
**작업 시간**: 1일

---

### Phase 3: 고급 기능 (2주)

#### Week 3: 문서 임베딩 + 벡터 검색
**우선순위**: ⭐⭐⭐⭐

```python
# 1. 문서 노드 생성
- hira_rulesvc 법령 (56개)
- hira_cancer 공고 (449개)
- ncc 암정보 (100개)

# 2. 임베딩 생성
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

# 3. Neo4j Vector Index 생성
CREATE VECTOR INDEX document_embeddings
FOR (d:Document)
ON d.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}
```

**임베딩 대상**: 약 600개 문서
**작업 시간**: 3일

---

#### Week 4: RAG 파이프라인 통합

```python
# Hybrid RAG 구현
def hybrid_rag(query: str):
    # 1. 엔티티 추출 (NER)
    entities = extract_entities(query)
    # → "Paclitaxel", "유방암"

    # 2. Neo4j 그래프 탐색
    cypher = """
    MATCH (d:Drug {name: $drug})-[r:TREATS]->(c:Cancer {name: $cancer})
    OPTIONAL MATCH (d)-[:PART_OF]->(reg:Regimen)-[:APPROVED_BY]->(g:Guideline)
    RETURN d, r, c, reg, g
    """
    graph_context = session.run(cypher, drug="Paclitaxel", cancer="유방암")

    # 3. 벡터 유사도 검색
    vector_results = vector_search(query, top_k=5)

    # 4. 컨텍스트 융합
    context = merge(graph_context, vector_results)

    # 5. LLM 생성
    answer = llm(query, context)

    return answer, graph_context, vector_results
```

**작업 시간**: 4일

---

## 🚀 5. 구현 로드맵 (4주)

### Week 1: 핵심 노드 구축
- [Day 1-3] Drug 노드 (50만~100만개)
- [Day 4-5] Disease 노드 (54,000개)
- [Day 6] Procedure 노드 (1,500개)
- [Day 7] Cancer 노드 (100개)

**산출물**:
- Neo4j 데이터베이스 (노드 약 60만개)
- 인덱스 설정 완료
- 검증 스크립트

---

### Week 2: 관계 구축
- [Day 1-3] Drug ↔ Disease 관계 (10,000~50,000개)
- [Day 4-5] Guideline 관계 (20,000개)
- [Day 6-7] Regimen, Test 관계 (500개)

**산출물**:
- 관계 약 30,000~70,000개
- Cypher 쿼리 예제 10개
- 시각화 (Neo4j Browser)

---

### Week 3: 문서 임베딩
- [Day 1-2] 문서 노드 생성 (600개)
- [Day 3-4] 임베딩 생성 및 저장
- [Day 5-7] Vector Index 최적화

**산출물**:
- 문서 임베딩 완료 (600개)
- 벡터 검색 API

---

### Week 4: RAG 통합
- [Day 1-2] Hybrid RAG 파이프라인 구현
- [Day 3-4] 성능 최적화
- [Day 5-7] 테스트 및 문서화

**산출물**:
- RAG API 서버
- 데모 웹 인터페이스
- 사용 가이드

---

## 📐 6. Neo4j 스키마 시각화

```
            ┌──────────┐
            │ Disease  │
            │ (54K)    │
            └─────┬────┘
                  │
         TREATS   │   DIAGNOSES
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌────▼────┐   ┌───▼────┐
│ Drug  │    │  Test   │   │Procedure│
│(500K) │    │  (20)   │   │ (1.5K) │
└───┬───┘    └─────────┘   └────────┘
    │
    │ COMBINED_WITH
    │ PART_OF
    │
┌───▼───────┐       ┌──────────┐
│  Regimen  │──────▶│  Cancer  │
│   (100)   │TREATS │  (100)   │
└─────┬─────┘       └──────────┘
      │
      │ APPROVED_BY
      │
┌─────▼──────┐      ┌──────────┐
│ Guideline  │──────│ Document │
│  (9K)      │SOURCE│  (600)   │
└────────────┘      └──────────┘
```

---

## 💾 7. 예상 데이터베이스 크기

| 구성요소 | 개수 | 예상 크기 |
|---------|------|----------|
| **Nodes** |  |  |
| Drug | 500K~1M | 500 MB |
| Disease | 54K | 50 MB |
| Procedure | 1.5K | 1 MB |
| Cancer | 100 | < 1 MB |
| Guideline | 9K | 100 MB |
| Document | 600 | 50 MB |
| **Relationships** | 50K~100K | 100 MB |
| **Embeddings** | 600 × 768 | 10 MB |
| **합계** | | **~800 MB - 1.2 GB** |

---

## 🔧 8. 기술 스택

### 데이터베이스
- **Neo4j 5.x** (Graph Database)
- **Neo4j Vector Index** (벡터 검색)

### 임베딩
- **SentenceTransformers** (paraphrase-multilingual-mpnet-base-v2)
- 또는 **OpenAI Embeddings** (text-embedding-3-large)

### ETL
- **Python 3.10+**
- **pandas** (데이터 처리)
- **neo4j-driver** (Python Neo4j 드라이버)

### RAG
- **LangChain** (RAG 파이프라인)
- **OpenAI GPT-4** 또는 **Anthropic Claude**

### API/서버
- **FastAPI** (REST API)
- **Streamlit** (데모 UI)

---

## 📋 9. 즉시 실행 가능한 다음 단계

### 🥇 최우선 (이번 주)
1. **Neo4j 설치 및 설정** (1시간)
2. **Drug 노드 구축 스크립트 작성** (1일)
3. **Disease 노드 구축 스크립트 작성** (0.5일)
4. **기본 관계 구축 (Drug-Disease)** (1일)

### 🥈 다음 주
5. **Guideline 노드 + 관계** (2일)
6. **Procedure, Cancer 노드** (1일)
7. **Cypher 쿼리 예제 작성** (1일)

### 🥉 3주차 이후
8. **문서 임베딩**
9. **RAG 파이프라인**
10. **웹 인터페이스**

---

## 🎯 성공 지표

### Week 1 완료 기준
- ✅ Neo4j 데이터베이스 구축 완료
- ✅ Drug 노드 50만개 이상
- ✅ Disease 노드 54,000개
- ✅ 기본 인덱스 설정 완료

### Week 2 완료 기준
- ✅ Drug-Disease 관계 10,000개 이상
- ✅ Guideline 노드 8,000개 이상
- ✅ Cypher 쿼리 10개 작성
- ✅ 그래프 시각화 성공

### Week 4 완료 기준
- ✅ RAG 파이프라인 동작
- ✅ 하이브리드 검색 성능 테스트 통과
- ✅ 데모 웹 UI 완성
- ✅ API 문서화 완료

---

**다음 작업**: Neo4j 설치 및 첫 번째 ETL 스크립트 작성
**예상 완료일**: 2025-12-04 (4주 후)
