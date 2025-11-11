# 통합 의료 지식그래프 스키마 설계

**버전**: 2.0 (전체 코드 시스템 통합)
**작성일**: 2025-11-11
**목표**: 암 질환 중심에서 전체 질병 체계로 확장

---

## 📋 목차

1. [개요](#개요)
2. [노드 타입](#노드-타입)
3. [관계 타입](#관계-타입)
4. [데이터 소스 매핑](#데이터-소스-매핑)
5. [통합 전략](#통합-전략)
6. [쿼리 패턴](#쿼리-패턴)

---

## 개요

### 현재 상태 (Phase 1-4)
- **Biomarker**: 23개
- **Test**: 575개
- **Drug**: 138개
- **관계**: TESTED_BY (996개), TARGETS (71개)

### 확장 목표 (Phase 5-8)
- **Disease**: 54,125개 (KCD-9)
- **Procedure**: 1,487개 (KDRG v1.4)
- **Cancer**: 107개 (NCC 암종)
- **Term**: 3,543개 (NCC 암정보 용어사전)
- **표준 코드 시스템 매핑**: SNOMED CT, LOINC, ATC

---

## 노드 타입

### 1. Disease (질병) - KCD-9

**데이터 소스**: `data/kssc/kcd-9th/normalized/kcd9_full.json`
**총 개수**: 54,125개

```cypher
(:Disease {
  kcd_code: String,              // 고유 ID (예: "C50.0")
  name_kr: String,               // 한글명 (예: "유방의 젖꼭지 및 유륜의 악성 신생물")
  name_en: String,               // 영문명 (예: "Malignant neoplasm of nipple and areola")
  is_header: Boolean,            // 헤더 여부 (범위 코드)
  classification: String,        // 대/중/소/세분류
  symbol: String,                // † * 등 특수 기호
  is_lowest: Boolean,            // 최하위 코드 여부
  is_domestic: Boolean,          // 한국 고유 코드
  is_oriental: Boolean,          // 한방 코드
  is_additional: Boolean,        // 추가 코드
  note: String,                  // 비고
  created_at: DateTime
})
```

**제약조건**: `kcd_code` UNIQUE
**인덱스**: `name_kr`, `name_en`, `classification`

---

### 2. Procedure (수술/처치) - KDRG

**데이터 소스**: `data/hira_master/kdrg_parsed/codes/kdrg_procedures_full.json`
**총 개수**: 1,487개

```cypher
(:Procedure {
  kdrg_code_kr: String,          // 한글 코드 (고유 ID, 예: "자751")
  kdrg_code_en: String,          // 영문 코드 (예: "Q7511")
  name: String,                  // 수술/처치명 (예: "췌장수술")
  table_index: Integer,          // KDRG 테이블 인덱스
  created_at: DateTime
})
```

**제약조건**: `kdrg_code_kr` UNIQUE, `kdrg_code_en` UNIQUE
**인덱스**: `name`

---

### 3. Cancer (암종) - NCC

**데이터 소스**: `data/ncc/cancer_info/parsed/*.json`
**총 개수**: 107개

```cypher
(:Cancer {
  cancer_id: String,             // 고유 ID (예: "NCC_4757")
  cancer_seq: String,            // NCC 시퀀스 (예: "4757")
  name_kr: String,               // 한글명 (예: "유방암")
  category: String,              // 카테고리 (예: "주요암 > 성인")
  tags: [String],                // 태그 (예: ["주요암", "성인"])
  url: String,                   // NCC URL
  content_summary: String,       // 내용 요약
  created_at: DateTime
})
```

**제약조건**: `cancer_id` UNIQUE, `cancer_seq` UNIQUE
**인덱스**: `name_kr`, `category`

---

### 4. Biomarker (바이오마커) - 기존

**변경 없음** (현재 23개)

```cypher
(:Biomarker {
  biomarker_id: String,
  name_en: String,
  name_ko: String,
  type: String,
  protein_gene: String,
  cancer_types: [String],
  drug_count: Integer,
  source: String,
  confidence: Float,
  created_at: DateTime
})
```

---

### 5. Test (검사) - HINS EDI

**확장**: SNOMED CT, LOINC 매핑 추가

```cypher
(:Test {
  test_id: String,
  edi_code: String,
  name_ko: String,
  name_en: String,
  biomarker_name: String,
  category: String,
  loinc_code: String,           // LOINC 표준 코드
  snomed_ct_id: String,         // SNOMED CT ID
  snomed_ct_name: String,       // SNOMED CT 명칭
  reference_year: Integer,
  data_source: String,
  created_at: DateTime
})
```

---

### 6. Drug (약물) - ATC

**확장**: 적응증 추가

```cypher
(:Drug {
  atc_code: String,
  ingredient_ko: String,
  ingredient_en: String,
  mechanism_of_action: String,
  therapeutic_category: String,
  atc_level1: String,
  atc_level2: String,
  atc_level3: String,
  atc_level3_name: String,
  atc_level4: String,
  atc_level4_name: String,
  indications: [String],        // 적응증 목록 (추가)
  created_at: DateTime
})
```

---

### 7. SNOMED (SNOMED CT) - 신규

**데이터 소스**: HINS 매핑 테이블
**총 개수**: 1,426개 (고유)

```cypher
(:SNOMED {
  snomed_id: String,             // SNOMED CT ID (고유 ID)
  name_ko: String,               // 한글 명칭
  name_en: String,               // 영문 명칭
  concept_type: String,          // 개념 유형
  created_at: DateTime
})
```

**제약조건**: `snomed_id` UNIQUE

---

### 8. LOINC (검사 표준 코드) - 신규

**데이터 소스**: HINS 매핑 테이블
**총 개수**: 1,369개 (고유)

```cypher
(:LOINC {
  loinc_code: String,            // LOINC 코드 (고유 ID)
  name_ko: String,               // 한글 명칭
  name_en: String,               // 영문 명칭
  component: String,             // 검사 항목
  property: String,              // 속성
  time_aspect: String,           // 시간 측면
  system: String,                // 시스템
  scale: String,                 // 척도
  method: String,                // 방법
  created_at: DateTime
})
```

**제약조건**: `loinc_code` UNIQUE

---

## 관계 타입

### 기존 관계 (유지)

#### 1. TESTED_BY (바이오마커 → 검사)
```cypher
(b:Biomarker)-[:TESTED_BY {
  match_type: String,
  confidence: Float,
  created_at: DateTime
}]->(t:Test)
```

#### 2. TARGETS (약물 → 바이오마커)
```cypher
(d:Drug)-[:TARGETS {
  created_at: DateTime
}]->(b:Biomarker)
```

---

### 신규 관계

#### 3. IS_A (질병 계층 구조)
```cypher
(d1:Disease)-[:IS_A {
  hierarchy_level: String,       // "대→중", "중→소", "소→세"
  created_at: DateTime
}]->(d2:Disease)
```

**용도**: KCD 질병 분류 체계 표현
**예시**: `C50.0 (유방 젖꼭지 악성)` IS_A `C50 (유방 악성신생물)`

---

#### 4. CANCER_TYPE (질병 → 암종)
```cypher
(d:Disease)-[:CANCER_TYPE {
  match_type: String,            // "exact", "partial", "related"
  confidence: Float,
  created_at: DateTime
}]->(c:Cancer)
```

**용도**: KCD 암 코드와 NCC 암종 연결
**예시**: `C50.x (유방암 KCD)` CANCER_TYPE `NCC_4757 (유방암)`

---

#### 5. TREATED_BY (질병 → 수술/처치)
```cypher
(d:Disease)-[:TREATED_BY {
  drg_group: String,             // DRG 그룹 번호
  is_primary: Boolean,           // 주 처치 여부
  created_at: DateTime
}]->(p:Procedure)
```

**용도**: KDRG 그룹핑 규칙 반영
**예시**: `C50 (유방암)` TREATED_BY `자751 (췌장수술)`

---

#### 6. INDICATED_FOR (약물 → 암종)
```cypher
(drug:Drug)-[:INDICATED_FOR {
  line_of_therapy: String,       // "1차", "2차", "3차"
  biomarker_status: String,      // "HER2 양성", "EGFR 돌연변이"
  approval_status: String,       // "급여", "비급여"
  evidence_level: String,        // "1A", "1B", "2A" 등
  created_at: DateTime
}]->(c:Cancer)
```

**용도**: 약물-암종 적응증 관계
**예시**: `L01XE13 (라파티니브)` INDICATED_FOR `NCC_4757 (유방암)`

---

#### 7. HAS_BIOMARKER (암종 → 바이오마커)
```cypher
(c:Cancer)-[:HAS_BIOMARKER {
  biomarker_role: String,        // "진단", "예후", "표적"
  prevalence: String,            // "20-30%", "드물게"
  clinical_significance: String, // 임상적 의의
  created_at: DateTime
}]->(b:Biomarker)
```

**용도**: 암종별 관련 바이오마커 표현
**예시**: `NCC_4757 (유방암)` HAS_BIOMARKER `BIOMARKER_001 (HER2)`

---

#### 8. MAPS_TO_SNOMED (코드 → SNOMED)
```cypher
// Disease → SNOMED
(d:Disease)-[:MAPS_TO_SNOMED {
  mapping_quality: String,       // "exact", "approximate", "related"
  source: String,                // 매핑 출처
  created_at: DateTime
}]->(s:SNOMED)

// Test → SNOMED
(t:Test)-[:MAPS_TO_SNOMED {
  mapping_quality: String,
  source: String,
  created_at: DateTime
}]->(s:SNOMED)
```

**용도**: 국내 코드와 국제 표준 연결

---

#### 9. MAPS_TO_LOINC (검사 → LOINC)
```cypher
(t:Test)-[:MAPS_TO_LOINC {
  mapping_quality: String,
  source: String,
  created_at: DateTime
}]->(l:LOINC)
```

**용도**: EDI 검사와 LOINC 표준 연결

---

## 데이터 소스 매핑

| 노드 타입 | 데이터 소스 | 파일 경로 | 개수 |
|-----------|------------|-----------|------|
| **Disease** | KCD-9 | `data/kssc/kcd-9th/normalized/kcd9_full.json` | 54,125 |
| **Procedure** | KDRG v1.4 | `data/hira_master/kdrg_parsed/codes/kdrg_procedures_full.json` | 1,487 |
| **Cancer** | NCC | `data/ncc/cancer_info/parsed/*.json` | 107 |
| **Biomarker** | Bridges | `bridges/biomarkers_extracted_v2.json` | 23 |
| **Test** | HINS EDI | `data/hins/parsed/biomarker_tests_structured.json` | 575 |
| **Drug** | ATC | `bridges/anticancer_master_classified.json` | 138 |
| **SNOMED** | HINS | `data/hins/downloads/edi/2장_19_20용어매핑테이블(검사)_(심평원코드-SNOMED_CT).xlsx` | 1,426 |
| **LOINC** | HINS | 동일 매핑 테이블 | 1,369 |

---

## 통합 전략

### Phase 5: Disease 노드 생성
1. KCD-9 전체 54,125개 코드 로드
2. IS_A 계층 관계 생성 (대→중→소→세)
3. 암 코드(C00-D48) 식별 및 태깅

### Phase 6: Procedure 노드 생성
1. KDRG 1,487개 수술/처치 코드 로드
2. 한글↔영문 코드 양방향 인덱싱

### Phase 7: Cancer 노드 및 관계 생성
1. NCC 107개 암종 로드
2. CANCER_TYPE 관계: Disease ↔ Cancer 매핑
3. HAS_BIOMARKER 관계: Cancer → Biomarker
4. INDICATED_FOR 관계: Drug → Cancer

### Phase 8: 표준 코드 통합
1. SNOMED CT 노드 생성 및 MAPS_TO_SNOMED 관계
2. LOINC 노드 생성 및 MAPS_TO_LOINC 관계
3. TREATED_BY 관계: Disease → Procedure

---

## 쿼리 패턴

### 1. 암 진단 → 검사 → 약물 경로
```cypher
MATCH path = (d:Disease {kcd_code: 'C50.9'})-[:CANCER_TYPE]->(c:Cancer)
            -[:HAS_BIOMARKER]->(b:Biomarker)<-[:TARGETS]-(drug:Drug)
RETURN path
```

**용도**: 유방암(C50.9) 진단 시 필요한 바이오마커 검사와 표적치료제 조회

---

### 2. 약물 적응증 및 바이오마커 조건
```cypher
MATCH (drug:Drug)-[r:INDICATED_FOR]->(c:Cancer)-[:HAS_BIOMARKER]->(b:Biomarker)
WHERE drug.ingredient_ko = '트라스투주맙'
RETURN c.name_kr, b.name_ko, r.biomarker_status, r.line_of_therapy
```

**용도**: 트라스투주맙의 암종별 적응증 및 바이오마커 조건

---

### 3. 질병 계층 탐색
```cypher
MATCH path = (child:Disease)-[:IS_A*]->(parent:Disease {kcd_code: 'C00-D48'})
WHERE child.is_lowest = true
RETURN child.kcd_code, child.name_kr, length(path) as depth
ORDER BY depth DESC
LIMIT 20
```

**용도**: 신생물 대분류(C00-D48) 하위의 모든 최하위 질병 코드 조회

---

### 4. 국제 표준 코드 매핑
```cypher
MATCH (d:Disease {kcd_code: 'C50.9'})-[:MAPS_TO_SNOMED]->(s:SNOMED)
RETURN d.name_kr, s.snomed_id, s.name_en
```

**용도**: KCD 코드의 SNOMED CT 표준 코드 조회

---

### 5. 입원 수가 계산 (DRG Grouping)
```cypher
MATCH (d:Disease {kcd_code: 'C50.9'})-[r:TREATED_BY]->(p:Procedure)
WHERE r.is_primary = true
RETURN d.name_kr, p.name, r.drg_group
```

**용도**: 유방암 주 처치 시 DRG 그룹 조회

---

### 6. 통합 임상 의사결정 지원
```cypher
// "HER2 양성 유방암 1차 치료 급여 약제는?"
MATCH path = (d:Disease)-[:CANCER_TYPE]->(c:Cancer {name_kr: '유방암'})
            -[:HAS_BIOMARKER]->(b:Biomarker {name_en: 'HER2'})
            <-[:TARGETS]-(drug:Drug)<-[:INDICATED_FOR {
              biomarker_status: 'HER2 양성',
              line_of_therapy: '1차',
              approval_status: '급여'
            }]-(c)
            -[:HAS_BIOMARKER]->(b)-[:TESTED_BY]->(t:Test)
RETURN drug.ingredient_ko AS 약물,
       t.name_ko AS 필요검사,
       t.edi_code AS EDI코드
```

**용도**: 프로젝트 핵심 질문 해결

---

## 데이터 볼륨 예상

| 항목 | 현재 (Phase 4) | 확장 후 (Phase 8) | 증가율 |
|------|---------------|------------------|--------|
| **노드 수** | 730 | 61,445 | 84배 |
| **관계 수** | 1,067 | ~150,000 | 141배 |
| **데이터베이스 크기** | ~10 MB | ~500 MB | 50배 |
| **인덱스 수** | 6 | 24 | 4배 |

---

## 구현 순서

1. ✅ **Phase 1-4**: Biomarker-Test-Drug (완료)
2. **Phase 5**: Disease 노드 + IS_A 관계
3. **Phase 6**: Procedure 노드
4. **Phase 7**: Cancer 노드 + CANCER_TYPE, HAS_BIOMARKER, INDICATED_FOR
5. **Phase 8**: SNOMED/LOINC 노드 + 매핑 관계

---

## 제약조건 및 인덱스 정의

### 제약조건
```cypher
// 기존
CREATE CONSTRAINT biomarker_id IF NOT EXISTS FOR (b:Biomarker) REQUIRE b.biomarker_id IS UNIQUE;
CREATE CONSTRAINT test_id IF NOT EXISTS FOR (t:Test) REQUIRE t.test_id IS UNIQUE;
CREATE CONSTRAINT drug_atc IF NOT EXISTS FOR (d:Drug) REQUIRE d.atc_code IS UNIQUE;

// 신규
CREATE CONSTRAINT disease_kcd IF NOT EXISTS FOR (d:Disease) REQUIRE d.kcd_code IS UNIQUE;
CREATE CONSTRAINT procedure_kr IF NOT EXISTS FOR (p:Procedure) REQUIRE p.kdrg_code_kr IS UNIQUE;
CREATE CONSTRAINT procedure_en IF NOT EXISTS FOR (p:Procedure) REQUIRE p.kdrg_code_en IS UNIQUE;
CREATE CONSTRAINT cancer_id IF NOT EXISTS FOR (c:Cancer) REQUIRE c.cancer_id IS UNIQUE;
CREATE CONSTRAINT snomed_id IF NOT EXISTS FOR (s:SNOMED) REQUIRE s.snomed_id IS UNIQUE;
CREATE CONSTRAINT loinc_code IF NOT EXISTS FOR (l:LOINC) REQUIRE l.loinc_code IS UNIQUE;
```

### 인덱스
```cypher
// 기존
CREATE INDEX biomarker_name IF NOT EXISTS FOR (b:Biomarker) ON (b.name_en);
CREATE INDEX test_edi_code IF NOT EXISTS FOR (t:Test) ON (t.edi_code);
CREATE INDEX drug_ingredient IF NOT EXISTS FOR (d:Drug) ON (d.ingredient_ko);

// 신규
CREATE INDEX disease_name_kr IF NOT EXISTS FOR (d:Disease) ON (d.name_kr);
CREATE INDEX disease_name_en IF NOT EXISTS FOR (d:Disease) ON (d.name_en);
CREATE INDEX disease_classification IF NOT EXISTS FOR (d:Disease) ON (d.classification);
CREATE INDEX procedure_name IF NOT EXISTS FOR (p:Procedure) ON (p.name);
CREATE INDEX cancer_name IF NOT EXISTS FOR (c:Cancer) ON (c.name_kr);
CREATE INDEX cancer_category IF NOT EXISTS FOR (c:Cancer) ON (c.category);
CREATE INDEX snomed_name IF NOT EXISTS FOR (s:SNOMED) ON (s.name_ko);
CREATE INDEX loinc_component IF NOT EXISTS FOR (l:LOINC) ON (l.component);
```

---

**다음 단계**: Phase 5 Disease 노드 생성 스크립트 작성

