# 의료 지식그래프 구축 마스터 플랜

**프로젝트명**: 의료 데이터 통합 지식그래프 및 하이브리드 RAG 시스템 구축
**작성일**: 2025-11-06
**버전**: 1.0
**작성자**: 지민 + Claude Code

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [현황 분석](#2-현황-분석)
3. [목표 및 범위](#3-목표-및-범위)
4. [기술 스택](#4-기술-스택)
5. [데이터 소스 맵핑](#5-데이터-소스-맵핑)
6. [Neo4j 스키마 설계](#6-neo4j-스키마-설계)
7. [LLM 자동화 전략](#7-llm-자동화-전략)
8. [구현 로드맵](#8-구현-로드맵)
9. [비용 분석](#9-비용-분석)
10. [성공 지표](#10-성공-지표)
11. [리스크 및 대응](#11-리스크-및-대응)

---

## 1. 프로젝트 개요

### 1.1 배경

현재 수집된 의료 데이터(약 1.6GB, 11개 소스)를 활용하여:
- 기존 RAG 시스템의 한계 극복 (단순 벡터 검색)
- 법령 간 계층 구조, 엔티티 관계를 명시적으로 표현
- 정확한 법적 근거 추적 및 절차 안내 가능

### 1.2 핵심 아이디어

**하이브리드 RAG = 그래프 DB (Neo4j) + 벡터 검색 + LLM**

```
사용자 질문
    ↓
1. 엔티티 추출 (NER)
    ↓
2. Neo4j 그래프 탐색 (구조화된 지식)
    ↓
3. 벡터 유사도 검색 (비구조화 지식)
    ↓
4. 컨텍스트 융합
    ↓
5. LLM 생성 (GPT-4/Claude)
    ↓
답변 + 근거
```

**차별점**:
- ✅ 정확한 관계 정보 (그래프)
- ✅ 최신 문서 검색 (벡터)
- ✅ 출처 추적 가능 (노드 링크)
- ✅ 복잡한 쿼리 지원 (Cypher)
- ✅ 법령 계층 추적 (법 > 시행령 > 고시)

---

## 2. 현황 분석

### 2.1 데이터 수집 현황

| 데이터 소스 | 크기 | 핵심 엔티티 | 완성도 | 우선순위 |
|-----------|------|-----------|--------|---------|
| **hira_master** | 226 MB | 약제(500만), KDRG코드(1,487) | ✅ 100% | ⭐⭐⭐⭐⭐ |
| **pharmalex_unity** | 715 MB | 통합 약제정보 | ✅ 100% | ⭐⭐⭐⭐⭐ |
| **hira_cancer** | 150 MB | 항암제(67), 암종(16) | ✅ 99.4% | ⭐⭐⭐⭐⭐ |
| **hira** (ebook) | 114 MB | 급여기준, 절차 | ✅ 100% | ⭐⭐⭐⭐⭐ |
| **hira_rulesvc** | 26 MB | 법령(56개), 행정해석(39) | ✅ 100% | ⭐⭐⭐⭐⭐ |
| **ncc** | 9.9 MB | 암정보(100개) | ✅ 100% | ⭐⭐⭐⭐ |
| **kssc** | 105 MB | KCD 8/9차(54,125개) | ✅ 100% | ⭐⭐⭐⭐ |
| **mfds** | 273 MB | 한국약전 | ⚠️ 42.9% | ⭐⭐⭐ |
| **likms** | 9.2 MB | 의료급여법 | 🔄 진행중 | ⭐⭐⭐ |
| **hira_notice** | 880 KB | KCD 개정안내 | 🔄 진행중 | ⭐⭐ |
| **pharma** | 3.6 MB | 테스트 데이터 | 🟡 테스트 | ⭐ |

**총 데이터**: 약 1.6 GB (emrcert 제외)

### 2.2 기 수행 작업 (2025-11-05)

#### ✅ 완료된 작업
```
1. KCD-9 Master File 정규화 (54,125개 코드)
   - 4개 JSON 파일 생성
   - 사용 가능 코드: 44,706개

2. KDRG 분류집 지능형 파싱 (1,216페이지)
   - 28개 청크로 분할
   - 5.2MB 텍스트, 16,329개 요소

3. KDRG 수술/처치 코드 추출 (1,487개)
   - 한글↔영문 매핑 테이블
   - 검색 인덱스 생성

4. 프로젝트 구조 정리
   - KCD 파일 재구성 (data/kssc/)
```

**산출물 위치**:
- `data/kssc/kcd-9th/normalized/`
- `data/hira_master/kdrg_parsed/`

### 2.3 당일 분석 작업 (2025-11-06)

#### ✅ 완료된 분석
```
1. HIRA 고시 데이터 패턴 분석 (8,539개)
   - 수술/처치 코드: 8,013개 (1,120개 고유)
   - 약제명: 3,352개 (447개 고유)
   - 질병코드: 1,606개 (391개 고유)
   - 검사명: 487개 (19개 고유)

2. 전체 프로젝트 데이터 소스 탐색
   - 11개 소스, 1.6GB
   - 각 소스별 엔티티 파악

3. 법령 계층 구조 Gap Analysis (tree.md)
   - 7가지 부족 사항 도출
   - 개선 스키마 설계

4. HIRA ebook 절차적 지식 분석
   - 4개 문서, 1,763페이지
   - 절차/단계/서식 구조 파악
```

**산출물**:
- `data/hira/hira_pattern_analysis.json`
- `docs/knowledge_graph_gap_analysis.md`
- `docs/knowledge_graph_procedural_knowledge_plan.md`

---

## 3. 목표 및 범위

### 3.1 최종 목표

**"의료 지식그래프 기반 하이브리드 RAG 시스템 구축"**

#### 3.1.1 기능적 목표
```
✅ 질의응답
   - "당뇨병 치료제 급여기준은?"
   - "노숙인의 의료급여 절차는?"
   - "Metformin과 Glucophage 중복 청구 가능?"

✅ 관계 탐색
   - 약제 → 질병 → 수술 연결
   - 법령 계층 추적 (법 > 시행령 > 고시)

✅ 절차 안내
   - 단계별 상세 가이드
   - 필수 서식 제공
   - 기한 안내

✅ 부당청구 예방
   - 사례 기반 경고
   - 법적 근거 제시
```

#### 3.1.2 기술적 목표
```
✅ Neo4j 지식그래프
   - 60만+ 노드
   - 10만+ 관계
   - 800MB~1.2GB

✅ 벡터 임베딩
   - 600개 문서
   - 768차원 벡터

✅ 하이브리드 검색
   - 그래프 + 벡터 융합
   - 정확도 90%+
```

### 3.2 범위

#### 포함 (In Scope)
```
✅ 약제 정보 (50만~100만개)
✅ 질병 코드 (KCD 54,125개)
✅ 수술/처치 (KDRG 1,487개)
✅ 법령/고시 (9,000개)
✅ 암정보 (100개)
✅ 절차/서식 (225개)
✅ 사례 (50개+)
```

#### 제외 (Out of Scope)
```
❌ emrcert 데이터 (명시적 제외)
❌ 실시간 업데이트 (v1.0에서)
❌ 다국어 지원 (한국어만)
❌ 외부 DB 연동 (DrugBank, PubMed)
❌ 웹 크롤링 자동화
```

---

## 4. 기술 스택

### 4.1 데이터베이스

#### Neo4j 5.x (Graph Database)
```
역할: 엔티티 및 관계 저장
노드: 약 60만개
관계: 약 10만개
크기: 800MB~1.2GB

주요 쿼리:
- Cypher (그래프 탐색)
- Full-text search (텍스트 검색)
- Vector index (벡터 유사도)
```

#### Neo4j Vector Index
```
역할: 문서 임베딩 검색
차원: 768 (Sentence Transformers)
문서: 600개
인덱스: cosine similarity
```

### 4.2 임베딩

#### Option 1: Sentence Transformers (추천)
```
모델: paraphrase-multilingual-mpnet-base-v2
차원: 768
속도: 빠름
비용: 무료
한국어: 지원
```

#### Option 2: OpenAI Embeddings
```
모델: text-embedding-3-large
차원: 1536 (or 768)
속도: API 의존
비용: $0.13/M tokens
한국어: 우수
```

### 4.3 LLM API

#### Claude API (1순위) ⭐⭐⭐⭐⭐
```
모델: claude-3-5-sonnet-20241022
컨텍스트: 200K 토큰
비용: $3/M input, $15/M output
장점: 긴 문서 처리, 한국어 법령 이해도

용도:
- 법령 구조화
- 관계 추출
- 엔티티 연결
- RAG 답변 생성
```

#### GPT-4 (2순위) ⭐⭐⭐⭐
```
모델: gpt-4-turbo
컨텍스트: 128K 토큰
비용: $10/M input, $30/M output
장점: 범용성, Function calling

용도:
- 대안 LLM
- 비교 검증
```

### 4.4 ETL 및 개발

#### Python 3.10+
```
라이브러리:
- neo4j-driver (Neo4j 연결)
- anthropic (Claude API)
- sentence-transformers (임베딩)
- pandas (데이터 처리)
- beautifulsoup4 (HTML 파싱)
```

#### 기타 도구
```
- Upstage Document Parse (PDF → 텍스트)
- PyMuPDF (PDF 처리)
- pdfplumber (표 추출)
```

### 4.5 API/서버

#### FastAPI
```
역할: REST API 서버
엔드포인트:
- POST /query (질의응답)
- GET /entity/{id} (엔티티 조회)
- GET /relationship/{type} (관계 조회)
```

#### Streamlit
```
역할: 데모 웹 UI
기능:
- 질의응답 인터페이스
- 그래프 시각화
- 검색 기록
```

---

## 5. 데이터 소스 맵핑

### 5.1 노드별 데이터 소스

| 노드 타입 | 주요 소스 | 보조 소스 | 예상 개수 |
|----------|----------|----------|----------|
| **Drug** | hira_master | pharmalex_unity, hira_cancer | 50만~100만 |
| **Disease** | kssc (KCD) | hira_master | 54,000 |
| **Procedure** | hira_master (KDRG) | hira | 1,500 |
| **Cancer** | ncc | hira_cancer | 100 |
| **Legislation** | hira_rulesvc | likms | 60 |
| **Article** | hira_rulesvc | - | 5,000 |
| **Guideline** | hira (hiradata) | hira_cancer | 9,000 |
| **Procedure_Doc** | hira ebook | hira_rulesvc | 10 |
| **Step** | hira ebook | - | 100 |
| **Form** | hira ebook | - | 30 |
| **Case** | hira ebook | hira_cancer | 50+ |
| **AdministrativeInterpretation** | hira_rulesvc | - | 39 |
| **Test** | hira (고시) | - | 19 |
| **MedicalTerm** | ncc | mfds | 3,543 |

### 5.2 데이터 흐름도

```
[원본 데이터]
    ↓
[Upstage API] → 텍스트 변환 (HWP/PDF → TXT)
    ↓
[Claude API] → 구조화 (TXT → JSON)
    ↓
[Python ETL] → 전처리 및 정규화
    ↓
[Neo4j Import] → 노드/관계 생성
    ↓
[Sentence Transformers] → 임베딩 생성
    ↓
[Neo4j Vector Index] → 벡터 저장
    ↓
[FastAPI] → RAG API
    ↓
[Streamlit] → 웹 UI
```

---

## 6. Neo4j 스키마 설계

### 6.1 노드 타입 (14개)

#### 6.1.1 Primary Entities (핵심)

##### Drug (약제)
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

##### Disease (질병)
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

##### Procedure (수술/처치)
```cypher
(:Procedure {
  code_kor: String,          // 한글 코드 (자751)
  code_eng: String,          // 영문 코드 (Q7511)
  name: String,              // 명칭
  category: String,          // 분류
  mdc: String               // MDC 분류 (01-22)
})
```

##### Cancer (암종)
```cypher
(:Cancer {
  name: String,              // 암종명 (위암, 폐암 등)
  type: String,              // 유형 (주요암, 성인암)
  tags: [String],            // 태그
  kcd_codes: [String],       // 관련 KCD 코드
  description: String       // 설명
})
```

#### 6.1.2 Legal Entities (법령)

##### Legislation (법령)
```cypher
(:Legislation {
  id: String,                // 법률 번호 (법률 제20309호)
  name: String,              // 법령명 (의료급여법)
  type: String,              // 법/시행령/시행규칙/고시
  level: Integer,            // 계층 (1: 법, 2: 시행령, 3: 고시)
  enacting_authority: String, // 발령 주체
  enacted_date: Date,        // 제정일
  effective_date: Date,      // 시행일
  amended_date: Date,        // 최종 개정일
  status: String,            // 상태 (시행중/폐지)
  content: String           // 전문
})
```

##### Article (법조문)
```cypher
(:Article {
  id: String,                // 조항 ID (제10조)
  number: String,            // 조 번호 (10)
  paragraph: Integer,        // 항 번호 (1, 2, 3...)
  item: Integer,             // 호 번호
  title: String,             // 조항 제목
  content: String,           // 조항 내용
  effective_date: Date,      // 시행일
  amended_date: Date        // 개정일
})
```

##### AdministrativeInterpretation (행정해석)
```cypher
(:AdministrativeInterpretation {
  id: String,                // 해석 ID
  title: String,             // 제목
  category: String,          // 8개 카테고리
  subcategory: String,       // 하위 카테고리
  content: String,           // 해석 내용
  issued_date: Date,         // 발행일
  issuer: String            // 발행 기관 (HIRA)
})
```

##### Guideline (고시)
```cypher
(:Guideline {
  doc_id: String,            // 고시번호
  title: String,             // 제목
  type: String,              // 유형 (공고/공고예고/FAQ)
  published_date: Date,      // 발행일
  source: String,            // 발행기관
  category: String,          // 분류 (약제/행위/재료)
  content: String,           // 전문
  summary: String           // 요약
})
```

#### 6.1.3 Procedural Entities (절차)

##### Procedure_Doc (절차)
```cypher
(:Procedure_Doc {
  id: String,                // 절차 ID
  name: String,              // 절차명
  category: String,          // 분류 (청구/심사/지급)
  description: String,       // 설명
  total_steps: Integer,      // 총 단계 수
  estimated_time: String,    // 예상 소요 시간
  responsible_party: String, // 담당자
  legal_basis: String       // 법적 근거 조항
})
```

##### Step (단계)
```cypher
(:Step {
  id: String,                // 단계 ID
  step_number: Integer,      // 단계 번호
  name: String,              // 단계명
  description: String,       // 상세 설명
  is_required: Boolean,      // 필수 여부
  estimated_time: String,    // 예상 소요 시간
  tips: String,             // 주의사항
  common_errors: [String]   // 흔한 오류
})
```

##### Form (서식)
```cypher
(:Form {
  id: String,                // 서식 ID
  name: String,              // 서식명
  version: String,           // 버전
  category: String,          // 분류
  file_path: String,         // 파일 경로
  file_format: String,       // 파일 형식
  instructions: String,      // 작성 요령
  effective_date: Date      // 적용일
})
```

##### Case (사례)
```cypher
(:Case {
  id: String,                // 사례 ID
  title: String,             // 사례 제목
  type: String,              // 유형 (올바른/부당청구)
  category: String,          // 분류
  description: String,       // 사례 설명
  issue: String,             // 문제점
  solution: String,          // 해결책
  legal_basis: String,       // 법적 근거
  penalty: String           // 제재
})
```

#### 6.1.4 Others

##### Test (검사)
```cypher
(:Test {
  name: String,              // 검사명
  code: String,              // 검사 코드
  unit: String,              // 단위
  normal_range: String,      // 정상 범위
  category: String          // 분류
})
```

##### Document (문서)
```cypher
(:Document {
  file_name: String,         // 파일명
  file_type: String,         // PDF/HWP/Excel
  file_path: String,         // 경로
  parsed: Boolean,           // 파싱 여부
  content: String,           // 내용
  embedding: [Float]        // 벡터 임베딩 (768차원)
})
```

### 6.2 관계 타입 (20개)

#### 6.2.1 Core Relationships

```cypher
// 약제 ↔ 질병
(Drug)-[:TREATS {
  indication: String,
  dosage: String,
  line: String,
  evidence_level: String
}]->(Disease)

(Drug)-[:TREATS_CANCER {
  line: String,
  purpose: String,
  combination: Boolean
}]->(Cancer)

// 약제 ↔ 약제
(Drug)-[:COMBINED_WITH {
  regimen_name: String,
  drug_order: Integer
}]->(Drug)

(Drug)-[:ALTERNATIVE_TO {
  reason: String
}]->(Drug)

(Drug)-[:CONTRAINDICATED_WITH {
  severity: String,
  reason: String
}]->(Drug)

// 질병 ↔ 수술/처치
(Procedure)-[:TREATS]->(Disease)
(Procedure)-[:USED_FOR]->(Cancer)

// 고시 ↔ 엔티티
(Guideline)-[:APPROVES {
  effective_date: Date,
  restriction: String,
  reimbursement: String
}]->(Drug)

(Guideline)-[:APPROVES]->(Procedure)
(Guideline)-[:APPLIES_TO]->(Disease)

// 고시 개정
(Guideline)-[:AMENDS {
  change_type: String
}]->(Guideline)
```

#### 6.2.2 Legal Relationships

```cypher
// 법령 계층
(Legislation)-[:BASED_ON {
  article_ref: String
}]->(Legislation)

// 법령 ↔ 조문
(Legislation)-[:CONTAINS]->(Article)

// 조문 간 참조
(Article)-[:REFERS_TO {
  reference_type: String
}]->(Article)

// 조문 개정
(Article)-[:AMENDS {
  change_type: String,
  effective_date: Date
}]->(Article)

// 행정해석 ↔ 법조문
(AdministrativeInterpretation)-[:INTERPRETS {
  interpretation_type: String
}]->(Article)

(AdministrativeInterpretation)-[:APPLIES_TO]->(Legislation)
```

#### 6.2.3 Procedural Relationships

```cypher
// 절차 ↔ 단계
(Procedure_Doc)-[:HAS_STEP {
  order: Integer
}]->(Step)

// 단계 순서
(Step)-[:NEXT_STEP {
  condition: String
}]->(Step)

// 단계 분기
(Step)-[:BRANCH_IF {
  condition: String
}]->(Step)

// 절차 ↔ 서식
(Procedure_Doc)-[:REQUIRES_FORM]->(Form)
(Step)-[:REQUIRES_FORM {
  is_mandatory: Boolean
}]->(Form)

// 사례 ↔ 절차
(Case)-[:DEMONSTRATES]->(Procedure_Doc)
(Case)-[:DEMONSTRATES]->(Step)

// 사례 ↔ 엔티티
(Case)-[:INVOLVES]->(Drug)
(Case)-[:INVOLVES]->(Disease)
(Case)-[:BASED_ON]->(Legislation)

// 절차 ↔ 법령
(Procedure_Doc)-[:GOVERNED_BY]->(Legislation)
(Procedure_Doc)-[:BASED_ON]->(Article)
```

#### 6.2.4 Test Relationships

```cypher
// 검사 ↔ 질병
(Test)-[:DIAGNOSES {
  threshold: String,
  operator: String
}]->(Disease)

// 약제 ↔ 검사
(Drug)-[:REQUIRES_MONITORING]->(Test)
```

#### 6.2.5 Document Relationships

```cypher
// 문서 ↔ 엔티티
(Document)-[:MENTIONS]->(Drug)
(Document)-[:MENTIONS]->(Disease)
(Document)-[:MENTIONS]->(Procedure)
(Document)-[:SOURCE_OF]->(Guideline)
```

### 6.3 스키마 시각화

```
                    ┌──────────┐
                    │Legislation│
                    │  (60)    │
                    └─────┬────┘
                          │
                   BASED_ON│CONTAINS
                          │
          ┌───────────────┼───────────────┐
          │               │               │
     ┌────▼────┐     ┌────▼────┐   ┌─────▼─────┐
     │ Article │     │Guideline│   │AdminInterp│
     │ (5,000) │     │ (9,000) │   │   (39)    │
     └─────────┘     └────┬────┘   └───────────┘
                          │
                     APPROVES
                          │
          ┌───────────────┼───────────────┐
          │               │               │
     ┌────▼────┐     ┌────▼────┐    ┌────▼─────┐
     │  Drug   │     │ Disease │    │Procedure │
     │(500K+)  │     │(54,000) │    │ (1,500)  │
     └────┬────┘     └────┬────┘    └──────────┘
          │               │
      TREATS│         TREATS
          │               │
          └───────┬───────┘
                  │
             ┌────▼────┐
             │ Cancer  │
             │  (100)  │
             └────┬────┘
                  │
          ┌───────┴───────┐
          │               │
   ┌──────▼──────┐  ┌────▼─────┐
   │Procedure_Doc│  │   Case   │
   │    (10)     │  │   (50+)  │
   └──────┬──────┘  └──────────┘
          │
      HAS_STEP
          │
     ┌────▼────┐
     │  Step   │
     │  (100)  │
     └────┬────┘
          │
    REQUIRES_FORM
          │
     ┌────▼────┐
     │  Form   │
     │   (30)  │
     └─────────┘
```

### 6.4 예상 DB 크기

| 구성요소 | 개수 | 예상 크기 |
|---------|------|----------|
| **Nodes** |  |  |
| Drug | 500K~1M | 500 MB |
| Disease | 54K | 50 MB |
| Procedure | 1.5K | 1 MB |
| Cancer | 100 | < 1 MB |
| Legislation | 60 | 5 MB |
| Article | 5K | 20 MB |
| Guideline | 9K | 100 MB |
| Procedure_Doc | 10 | < 1 MB |
| Step | 100 | 1 MB |
| Form | 30 | < 1 MB |
| Case | 50+ | 1 MB |
| AdminInterp | 39 | 2 MB |
| Test | 19 | < 1 MB |
| Document | 600 | 50 MB |
| **Relationships** | 50K~100K | 100 MB |
| **Embeddings** | 600 × 768 | 10 MB |
| **Total** | | **~840 MB - 1.2 GB** |

---

## 7. LLM 자동화 전략

### 7.1 자동화 대상 작업

| 작업 | 수동 (예상) | LLM 자동화 | 절감 |
|-----|-----------|-----------|------|
| **법령 구조화** | 6주, $7,200 | 3일, $20-26 | 99.6% |
| **절차 추출** | 4주, $4,800 | 2일, $3-4 | 99.9% |
| **관계 추출** | 3주, $3,600 | 1일, $5-10 | 99.7% |
| **엔티티 연결** | 2주, $2,400 | 1일, $5-10 | 99.5% |
| **총계** | **15주, $18,000** | **7일, $33-50** | **99.7%** |

### 7.2 Claude API 활용

#### 7.2.1 법령 구조화 프롬프트
```python
def parse_legislation_document(document_text: str) -> dict:
    """
    법령 문서 → 구조화 JSON
    """

    prompt = f"""
다음 한국 법령 문서를 분석하여 JSON 형식으로 추출하세요:

문서:
{document_text}

추출 정보:
1. 법령 메타데이터 (법령명, 번호, 발령주체, 시행일)
2. 법조문 (조, 항, 호)
3. 참조 관계 ("제X조에 따라...")
4. 엔티티 (약제명, 질병명, 수술명)
5. 요약

출력 형식:
{{
  "metadata": {{...}},
  "articles": [...],
  "references": [...],
  "entities": {{...}},
  "summary": "..."
}}

JSON만 출력하세요.
"""

    # Claude API 호출
    client = anthropic.Anthropic(api_key=API_KEY)
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.content[0].text)
```

#### 7.2.2 절차 구조화 프롬프트
```python
def extract_procedure_from_document(doc_text: str) -> dict:
    """
    절차 문서 → 구조화 JSON
    """

    prompt = f"""
다음 의료급여/요양급여 절차 문서를 분석하여 JSON으로 추출하세요:

문서:
{doc_text}

추출 정보:
1. 절차 기본 정보
2. 단계들 (순서, 설명, 소요시간, 주의사항)
3. 단계 간 순서/분기 (IF-THEN)
4. 필수 서식
5. 조건
6. 기한
7. 관련 사례

출력 형식:
{{
  "procedure": {{...}},
  "steps": [...],
  "step_flow": [...],
  "required_forms": [...],
  "conditions": [...],
  "deadlines": [...],
  "cases": [...]
}}

JSON만 출력하세요.
"""

    # ... (동일)
```

#### 7.2.3 관계 추출 프롬프트
```python
def extract_relationships(all_documents: list[dict]) -> dict:
    """
    여러 법령 문서 간 관계 추출
    """

    doc_summaries = "\n\n".join([
        f"- {doc['metadata']['name']} ({doc['metadata']['number']})"
        for doc in all_documents
    ])

    prompt = f"""
다음 법령들 간의 계층 관계와 참조 관계를 분석하세요:

{doc_summaries}

출력 형식:
{{
  "hierarchy": [
    {{
      "parent": "의료급여법",
      "child": "의료급여법 시행령",
      "relationship_type": "BASED_ON",
      "article_reference": "제3조"
    }}
  ],
  "cross_references": [...]
}}

JSON만 출력하세요.
"""

    # ... (동일)
```

### 7.3 자동화 파이프라인

```
[1단계: 문서 변환]
HWP/PDF → Upstage API → 텍스트
비용: $11.20 (1,120페이지)
시간: 10분

[2단계: 구조화]
텍스트 → Claude API → JSON
비용: $20-26 (56개 법령)
시간: 30분

[3단계: 관계 추출]
여러 JSON → Claude API → 관계 JSON
비용: $0.23
시간: 5분

[4단계: Neo4j 임포트]
JSON → Python ETL → Neo4j
비용: 없음
시간: 1시간

총 비용: $31.43~$37.43
총 시간: 1시간 45분
```

---

## 8. 구현 로드맵

### 8.1 Phase 1: 자동화 파이프라인 구축 (Week 1)

#### Day 1-2: LLM 자동화 스크립트 개발
```
□ Claude API 연동 스크립트
□ 법령 구조화 함수 (parse_legislation_document)
□ 절차 구조화 함수 (extract_procedure_from_document)
□ 관계 추출 함수 (extract_relationships)
□ 엔티티 연결 함수 (link_entities)

산출물:
- scripts/neo4j/auto_structure_legislation.py
- scripts/neo4j/auto_structure_procedures.py
- scripts/neo4j/extract_relationships.py
```

#### Day 3: 프로토타입 테스트
```
□ 1개 법령 문서 테스트 (의료급여법)
□ 1개 절차 문서 테스트 (의료급여 실무편람 일부)
□ 결과 검증 (샘플 10개 조문)
□ 비용/시간 측정
□ 오류 수정

검증 기준:
- 조문 추출 정확도 95% 이상
- 관계 추출 정확도 90% 이상
- 엔티티 인식 정확도 90% 이상
```

#### Day 4-5: 전체 데이터 자동 처리
```
□ 56개 법령 일괄 처리 (실행 시간: 30분)
□ 4개 절차 문서 일괄 처리 (실행 시간: 10분)
□ 8,539개 HIRA 고시 엔티티 추출 (실행 시간: 2시간)
□ 샘플 검증 (10% 무작위 샘플링)

산출물:
- data/hira_rulesvc/structured/*.json (56개)
- data/hira/procedures_structured/*.json (4개)
- data/hira/entities_extracted/*.json (8,539개)

예상 비용: $40-50
```

---

### 8.2 Phase 2: Neo4j 노드 구축 (Week 2)

#### Day 1-2: Drug 노드 구축
```
□ hira_master/drug_dictionary_normalized.json 읽기
□ pharmalex_unity/merged_pharma_data.csv 통합
□ 중복 제거 및 정규화
□ Neo4j Drug 노드 생성
□ 인덱스 생성 (name_kor, name_eng, code)

예상 노드: 500,000~1,000,000개
예상 시간: 2시간
산출물: scripts/neo4j/build_drug_nodes.py
```

#### Day 3: Disease 노드 구축
```
□ kssc/kcd-9th/normalized/kcd9_full.json 읽기
□ Neo4j Disease 노드 생성
□ 계층 관계 구축 (PARENT_OF)
□ 인덱스 생성 (kcd_code, name_kor)

예상 노드: 54,125개
예상 시간: 30분
산출물: scripts/neo4j/build_disease_nodes.py
```

#### Day 4: Procedure, Cancer, Test 노드 구축
```
□ KDRG Procedure 노드 (1,487개)
□ NCC Cancer 노드 (100개)
□ Test 노드 (19개)

예상 시간: 2시간
산출물: scripts/neo4j/build_other_nodes.py
```

#### Day 5: Legislation 및 Article 노드 구축
```
□ 자동 구조화된 법령 JSON 읽기
□ Legislation 노드 생성 (60개)
□ Article 노드 생성 (5,000개)
□ CONTAINS 관계 생성

예상 시간: 3시간
산출물: scripts/neo4j/build_legislation_nodes.py
```

---

### 8.3 Phase 3: 관계 구축 (Week 3)

#### Day 1-2: Drug ↔ Disease 관계
```
□ HIRA 고시 엔티티 매칭
□ TREATS 관계 생성
□ TREATS_CANCER 관계 생성 (hira_cancer 데이터)

예상 관계: 10,000~50,000개
예상 시간: 1일
산출물: scripts/neo4j/build_drug_disease_relations.py
```

#### Day 3-4: Guideline 관계
```
□ Guideline 노드 생성 (8,539개)
□ APPROVES 관계 (Guideline → Drug/Procedure)
□ AMENDS 관계 (Guideline → Guideline)
□ APPLIES_TO 관계 (Guideline → Disease)

예상 관계: 20,000개
예상 시간: 1일
산출물: scripts/neo4j/build_guideline_relations.py
```

#### Day 5: 법령 관계
```
□ BASED_ON 관계 (법령 계층)
□ REFERS_TO 관계 (조문 간 참조)
□ INTERPRETS 관계 (행정해석 → 조문)

예상 관계: 5,000개
예상 시간: 4시간
산출물: scripts/neo4j/build_legislation_relations.py
```

#### Day 6-7: 절차 관계
```
□ Procedure_Doc, Step, Form, Case 노드 생성
□ HAS_STEP, NEXT_STEP 관계
□ REQUIRES_FORM 관계
□ DEMONSTRATES 관계
□ GOVERNED_BY 관계

예상 노드: 225개
예상 관계: 335개
예상 시간: 1일
산출물: scripts/neo4j/build_procedure_relations.py
```

---

### 8.4 Phase 4: 문서 임베딩 및 벡터 검색 (Week 4)

#### Day 1-2: 문서 노드 생성 및 임베딩
```
□ Document 노드 생성 (600개)
  - hira_rulesvc 법령 (56개)
  - hira_cancer 공고 (449개)
  - ncc 암정보 (100개)

□ Sentence Transformers 임베딩 생성
  - 모델: paraphrase-multilingual-mpnet-base-v2
  - 차원: 768

□ Neo4j embedding 속성 저장

예상 시간: 1일
산출물: scripts/neo4j/build_document_embeddings.py
```

#### Day 3-4: Neo4j Vector Index 구축
```
□ Vector Index 생성
□ 인덱스 최적화
□ 벡터 유사도 검색 테스트

Cypher:
CREATE VECTOR INDEX document_embeddings
FOR (d:Document)
ON d.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}

예상 시간: 4시간
```

#### Day 5-7: 하이브리드 RAG 파이프라인 구현
```
□ 엔티티 추출 (NER)
□ Neo4j 그래프 탐색 함수
□ 벡터 유사도 검색 함수
□ 컨텍스트 융합 로직
□ Claude API 답변 생성

예상 시간: 2일
산출물: scripts/rag/hybrid_rag.py
```

---

### 8.5 Phase 5: API 및 웹 UI (Week 5)

#### Day 1-3: FastAPI 서버 개발
```
□ REST API 엔드포인트
  - POST /query (질의응답)
  - GET /entity/{id} (엔티티 조회)
  - GET /relationship/{type} (관계 조회)
  - GET /graph/visualize (그래프 시각화 데이터)

□ API 문서 자동 생성 (Swagger)
□ 에러 처리 및 로깅

예상 시간: 2일
산출물: api/main.py
```

#### Day 4-5: Streamlit 웹 UI
```
□ 질의응답 인터페이스
□ 그래프 시각화 (pyvis)
□ 검색 기록
□ 엔티티 브라우저

예상 시간: 1.5일
산출물: app/streamlit_app.py
```

---

### 8.6 Phase 6: 테스트 및 문서화 (Week 6)

#### Day 1-3: 통합 테스트
```
□ 단위 테스트 (pytest)
□ 통합 테스트
□ 성능 테스트 (쿼리 응답 시간)
□ 정확도 검증 (100개 샘플 질문)

성공 기준:
- 쿼리 응답 시간 < 3초
- 정확도 > 90%
- 법령 추적 정확도 > 95%
```

#### Day 4-5: 문서화
```
□ 사용자 가이드
□ API 문서
□ 아키텍처 문서
□ 배포 가이드

산출물:
- docs/USER_GUIDE.md
- docs/API_REFERENCE.md
- docs/ARCHITECTURE.md
- docs/DEPLOYMENT_GUIDE.md
```

---

### 8.7 타임라인 요약

```
Week 1: LLM 자동화 파이프라인 구축
├─ Day 1-2: 스크립트 개발
├─ Day 3: 프로토타입 테스트
└─ Day 4-5: 전체 데이터 처리

Week 2: Neo4j 노드 구축
├─ Day 1-2: Drug 노드 (500K+)
├─ Day 3: Disease 노드 (54K)
├─ Day 4: Procedure, Cancer, Test
└─ Day 5: Legislation, Article

Week 3: 관계 구축
├─ Day 1-2: Drug ↔ Disease 관계
├─ Day 3-4: Guideline 관계
├─ Day 5: 법령 관계
└─ Day 6-7: 절차 관계

Week 4: 문서 임베딩 및 RAG
├─ Day 1-2: Document 노드 + 임베딩
├─ Day 3-4: Vector Index
└─ Day 5-7: Hybrid RAG 파이프라인

Week 5: API 및 웹 UI
├─ Day 1-3: FastAPI 서버
└─ Day 4-5: Streamlit UI

Week 6: 테스트 및 문서화
├─ Day 1-3: 통합 테스트
└─ Day 4-5: 문서화

──────────────────────────────
총 소요: 6주 (약 30일)
```

---

## 9. 비용 분석

### 9.1 개발 비용

| 항목 | 비용 | 비고 |
|-----|------|------|
| **LLM API (Claude)** |  |  |
| - 법령 구조화 (56개) | $20-26 | 2.8M 토큰 |
| - 절차 구조화 (4개) | $3-4 | 0.7M 토큰 |
| - 고시 엔티티 추출 (8,539개) | $10-15 | 대규모 배치 |
| - 관계 추출 | $0.23 | 소량 |
| **문서 변환 (Upstage)** |  |  |
| - HWP/PDF → 텍스트 | $11.20 | 1,120페이지 |
| **Neo4j** | $0 | Community Edition |
| **Sentence Transformers** | $0 | 오픈소스 |
| **개발 환경** | $0 | 로컬 환경 |
| **총 개발 비용** | **$44.43~$56.43** |  |

### 9.2 운영 비용 (월간 예상)

| 항목 | 비용 | 비고 |
|-----|------|------|
| **Claude API (RAG 답변)** | $50-100 | 1,000회 질의 가정 |
| **Neo4j 서버** | $0-200 | Community / Cloud |
| **FastAPI 서버** | $0-20 | 로컬 / 클라우드 |
| **총 운영 비용** | **$50-320/월** |  |

### 9.3 수동 작업 대비 절감

| 작업 | 수동 | LLM 자동화 | 절감액 |
|-----|------|-----------|--------|
| 법령 구조화 | $7,200 (6주) | $26 (3일) | $7,174 (99.6%) |
| 절차 추출 | $4,800 (4주) | $4 (2일) | $4,796 (99.9%) |
| 관계 추출 | $3,600 (3주) | $10 (1일) | $3,590 (99.7%) |
| 엔티티 연결 | $2,400 (2주) | $10 (1일) | $2,390 (99.6%) |
| **총계** | **$18,000 (15주)** | **$50 (7일)** | **$17,950 (99.7%)** |

---

## 10. 성공 지표

### 10.1 Phase별 완료 기준

#### Phase 1: 자동화 파이프라인 (Week 1)
```
✅ 56개 법령 구조화 JSON 생성
✅ 4개 절차 구조화 JSON 생성
✅ 조문 추출 정확도 95% 이상
✅ 관계 추출 정확도 90% 이상
✅ 비용 < $60
```

#### Phase 2: 노드 구축 (Week 2)
```
✅ Drug 노드 500,000개 이상
✅ Disease 노드 54,125개
✅ Legislation 노드 60개
✅ Article 노드 5,000개 이상
✅ 인덱스 생성 완료
```

#### Phase 3: 관계 구축 (Week 3)
```
✅ Drug-Disease 관계 10,000개 이상
✅ Guideline 관계 20,000개 이상
✅ 법령 계층 관계 100개 이상
✅ 절차 관계 335개 이상
```

#### Phase 4: RAG 파이프라인 (Week 4)
```
✅ Document 노드 600개 + 임베딩
✅ Vector Index 구축 완료
✅ Hybrid RAG 동작 확인
✅ 샘플 쿼리 테스트 통과
```

#### Phase 5: API 및 UI (Week 5)
```
✅ FastAPI 서버 동작
✅ Streamlit UI 동작
✅ API 문서 생성
```

#### Phase 6: 테스트 및 문서화 (Week 6)
```
✅ 통합 테스트 통과
✅ 정확도 90% 이상
✅ 응답 시간 < 3초
✅ 문서화 완료
```

### 10.2 최종 성공 지표

| 지표 | 목표 | 측정 방법 |
|-----|------|----------|
| **데이터 완성도** | 100% | 모든 소스 임포트 완료 |
| **노드 수** | 600,000+ | Neo4j 노드 카운트 |
| **관계 수** | 50,000+ | Neo4j 관계 카운트 |
| **질의 응답 정확도** | 90%+ | 100개 샘플 질문 평가 |
| **법령 추적 정확도** | 95%+ | 법령 근거 검증 |
| **응답 시간** | < 3초 | 평균 쿼리 시간 |
| **그래프 탐색 성공률** | 95%+ | 엔티티 찾기 성공률 |
| **벡터 검색 정확도** | 85%+ | Top-5 정확도 |

### 10.3 비기능적 지표

| 지표 | 목표 |
|-----|------|
| **코드 커버리지** | 80%+ |
| **API 가용성** | 99%+ |
| **평균 부하** | 100 QPS |
| **메모리 사용량** | < 4GB |
| **디스크 사용량** | < 2GB |

---

## 11. 리스크 및 대응

### 11.1 기술적 리스크

#### 🔴 High Risk

##### Risk 1: LLM API 비용 초과
```
위험도: High
영향도: Medium

원인:
- 토큰 수 과다 예상
- API 호출 횟수 초과

대응:
✅ 프로토타입 단계에서 비용 정확히 측정
✅ 배치 크기 조정으로 비용 최적화
✅ 비용 모니터링 알림 설정
✅ 예산 초과 시 수동 검증으로 전환
```

##### Risk 2: 데이터 품질 문제
```
위험도: High
영향도: High

원인:
- LLM 추출 오류
- 데이터 불일치

대응:
✅ 10% 샘플 수동 검증
✅ 오류 패턴 분석 후 프롬프트 개선
✅ 검증 로직 추가 (정규식, 화이트리스트)
✅ 신뢰도 점수 부여
```

##### Risk 3: Neo4j 성능 문제
```
위험도: Medium
영향도: High

원인:
- 100만 노드 처리 시 성능 저하
- 복잡한 쿼리 타임아웃

대응:
✅ 인덱스 최적화
✅ 쿼리 최적화 (EXPLAIN 분석)
✅ 샤딩/파티셔닝 고려
✅ 캐싱 레이어 추가
```

#### 🟡 Medium Risk

##### Risk 4: HWP 파일 처리 실패
```
위험도: Medium
영향도: Medium

원인:
- Upstage API HWP 지원 제한
- 텍스트 추출 실패

대응:
✅ HWP → PDF 변환 후 재시도
✅ 수동 텍스트 추출 (최후 수단)
✅ hira_rulesvc에 중복 문서 확인
```

##### Risk 5: 임베딩 품질 저하
```
위험도: Medium
영향도: Medium

원인:
- 한국어 의료 용어 인식 부족
- 벡터 검색 부정확

대응:
✅ 여러 임베딩 모델 비교 테스트
✅ 파인튜닝 고려 (장기)
✅ 하이브리드 검색 가중치 조정
```

#### 🟢 Low Risk

##### Risk 6: 서버 배포 문제
```
위험도: Low
영향도: Low

원인:
- 클라우드 배포 복잡성

대응:
✅ Docker 컨테이너화
✅ 배포 문서 작성
✅ CI/CD 파이프라인 구축 (선택)
```

### 11.2 일정 리스크

| 리스크 | 확률 | 대응 |
|-------|------|------|
| **LLM 자동화 지연** | Medium | 수동 작업으로 임시 대응 |
| **Neo4j 임포트 지연** | Low | 배치 크기 축소, 병렬 처리 |
| **테스트 기간 부족** | Medium | 핵심 기능 우선 테스트 |
| **문서화 미완성** | Low | 최소 문서만 작성 |

### 11.3 비용 리스크

| 리스크 | 확률 | 대응 |
|-------|------|------|
| **Claude API 비용 초과** | Medium | 프로토타입 단계 비용 측정 |
| **운영 비용 증가** | Low | 캐싱으로 API 호출 감소 |

---

## 12. 다음 단계 (Immediate Actions)

### 12.1 오늘 (2-3시간)

```
□ Claude API 키 확인
□ Neo4j Desktop 설치 (또는 Docker)
□ 프로토타입 스크립트 작성
  - 1개 법령 문서 테스트 (의료급여법)
  - parse_legislation_document() 함수
  - JSON 출력 검증
□ 비용 측정
□ 결과 검토
```

**예상 결과**:
- 1개 법령 구조화 JSON
- 실제 비용: $0.3~0.5
- 조문 수: 약 100개
- 소요 시간: 30초

### 12.2 내일 (1일)

```
□ 전체 법령 자동화 (56개)
□ 절차 문서 자동화 (4개)
□ 샘플 검증 (10개 문서)
□ 오류 패턴 분석
□ 프롬프트 개선
```

**예상 결과**:
- 60개 구조화 JSON
- 실제 비용: $30-40
- 검증 완료

### 12.3 이번 주 (5일)

```
□ Neo4j 데이터베이스 구축
□ Drug, Disease, Procedure 노드 생성
□ 기본 관계 구축
□ 간단한 Cypher 쿼리 테스트
```

**마일스톤**: Week 1-2 완료

---

## 13. 부록

### 13.1 참조 문서

- `docs/knowledge_graph_neo4j_plan.md` - Neo4j 상세 설계
- `docs/knowledge_graph_gap_analysis.md` - tree.md Gap 분석
- `docs/knowledge_graph_procedural_knowledge_plan.md` - 절차 지식 설계
- `docs/knowledge_graph_llm_automation_strategy.md` - LLM 자동화 상세
- `work_log_20251105.md` - 전일 작업 로그

### 13.2 데이터 파일 위치

```
data/
├── hira/
│   ├── ebook/                    # 9개 PDF (절차 문서)
│   ├── parsed/                   # 파싱된 JSON
│   └── hiradata_ver2.xlsx        # 8,539개 고시
├── hira_cancer/
│   ├── raw/attachments/          # 828개 파일
│   └── parsed/                   # 823개 JSON
├── hira_master/
│   ├── drug_dictionary_normalized.json  # 약제 사전
│   ├── kdrg_parsed/              # KDRG 파싱 결과
│   └── 배포용 상병마스터.xlsx
├── hira_rulesvc/
│   ├── documents/                # 56개 HWP/PDF
│   └── config/document_tree.json # 법령 계층
├── kssc/
│   └── kcd-9th/normalized/       # KCD-9 정규화
├── ncc/
│   └── cancer_info/              # 100개 암정보 JSON
└── ... (기타)
```

### 13.3 Cypher 쿼리 예제

```cypher
// 1. 약제 → 질병 관계 조회
MATCH (d:Drug {name: "Metformin"})-[:TREATS]->(dis:Disease)
RETURN d, dis

// 2. 법령 계층 추적
MATCH path = (notice:Legislation {type: "고시"})
             -[:BASED_ON*]->(law:Legislation {type: "법"})
RETURN path

// 3. 절차 단계별 안내
MATCH (proc:Procedure_Doc {name: "요양급여비용 청구"})
      -[:HAS_STEP]->(step:Step)
OPTIONAL MATCH (step)-[:REQUIRES_FORM]->(form:Form)
RETURN proc, step, form
ORDER BY step.step_number

// 4. 부당청구 사례 검색
MATCH (case:Case {type: "부당청구"})-[:INVOLVES]->(drug:Drug)
WHERE drug.name CONTAINS "Metformin"
RETURN case, drug

// 5. 벡터 유사도 검색
CALL db.index.vector.queryNodes(
  'document_embeddings',
  5,
  $query_embedding
) YIELD node, score
RETURN node, score
```

---

## 14. 승인 및 시작

### 14.1 검토 사항

```
□ 프로젝트 목표 및 범위 확인
□ 기술 스택 승인
□ 예산 승인 ($50-60 개발 비용)
□ 일정 검토 (6주)
□ 리스크 인지
```

### 14.2 시작 준비

```
□ Claude API 키 발급
□ Neo4j 설치
□ Python 환경 설정
□ 프로토타입 코드 작성
```

### 14.3 시작 명령

```bash
# 프로토타입 실행
cd C:\Jimin\scrape-hub
python scripts/neo4j/prototype_legislation_parser.py

# 예상 출력:
# ✅ 의료급여법 파싱 완료
# ✅ 조문 수: 97개
# ✅ 관계: 15개
# ✅ 비용: $0.42
# ✅ 시간: 28초
```

---

**문서 버전**: 1.0
**최종 수정**: 2025-11-06
**다음 검토**: 프로토타입 완료 후
**승인자**: 지민

**Status**: ✅ 작성 완료, ⏳ 승인 대기

---
