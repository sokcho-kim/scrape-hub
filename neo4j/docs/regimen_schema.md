# HIRA Regimen 노드 스키마

## 개요

HIRA(건강보험심사평가원) 화학요법 급여 인정 기준 데이터를 Neo4j에 통합하기 위한 스키마입니다.

## 데이터 소스

- **원본**: `data/hira_cancer/parsed/drug_cancer_relations.json`
- **정규화된 데이터**: `bridges/hira_regimens_normalized.json`
- **총 레지멘**: 38개
- **매핑 성공률**: 92.1% (KCD 100%, 약물 92.1%)

## 노드: Regimen

### 속성

```cypher
(r:Regimen {
    regimen_id: String,           // UNIQUE - "REGIMEN_제2025_210호_3DRUG"
    cancer_name: String,          // "자궁암"
    regimen_type: String,         // "병용요법" | "단독요법"
    line: String,                 // "1차" | "2차" | "3차" | null
    purpose: String,              // "고식적요법" | "완치적요법" | null
    action: String,               // "신설" | "변경" | "삭제"
    announcement_no: String,      // "제2025-210호"
    announcement_date: String,    // "2025.10.1."
    source_text: String,          // 원본 텍스트
    drug_count: Integer,          // 약물 개수
    created_at: DateTime
})
```

### 제약조건

```cypher
CREATE CONSTRAINT regimen_id IF NOT EXISTS
FOR (r:Regimen) REQUIRE r.regimen_id IS UNIQUE
```

## 관계

### 1. Disease → TREATED_BY → Regimen

질병(KCD 코드)과 레지멘 간의 치료 관계

```cypher
(d:Disease)-[:TREATED_BY {
    line: String,                 // "1차" | "2차" | "3차"
    purpose: String,              // "고식적요법" | "완치적요법"
    announcement_no: String,      // "제2025-210호"
    announcement_date: String,    // "2025.10.1."
    mapping_method: "kcd_code",   // 매핑 방법
    created_at: DateTime
}]->(r:Regimen)
```

**매핑 로직**:
- Regimen의 `kcd_codes` 배열과 Disease의 `kcd_code`를 매칭
- STARTS WITH 패턴 사용 (예: C53 → C53.0, C53.1 등 포함)

### 2. Regimen → INCLUDES → Drug

레지멘에 포함된 약물

```cypher
(r:Regimen)-[:INCLUDES {
    drug_name: String,            // "Dostarlimab"
    normalized_name: String,      // "dostarlimab"
    order: Integer,               // 약물 순서 (옵션)
    created_at: DateTime
}]->(d:Drug)
```

**매핑 로직**:
- Regimen의 `drugs` 배열에서 `atc_code`로 Drug 노드와 매칭

## 통합 데이터 구조

```
Disease (KCD)
    ↓ TREATED_BY
Regimen (HIRA 급여)
    ↓ INCLUDES
Drug (ATC)
    ↓ TARGETS
Biomarker
    ↓ TESTED_BY
Test (EDI/LOINC/SNOMED)
```

## 쿼리 예시

### 1. HER2 양성 유방암 1차 급여 요법 조회

```cypher
// HER2 양성 유방암의 HIRA 급여 인정 요법 조회
MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)-[:INCLUDES]->(drug:Drug)
MATCH (d)-[:HAS_BIOMARKER]->(b:Biomarker {name_en: 'HER2'})<-[:TARGETS]-(drug)
WHERE d.kcd_code STARTS WITH 'C50'
  AND tb.line = '1차'
RETURN
    d.name_kr as 질병,
    r.regimen_type as 요법유형,
    tb.line as 치료라인,
    tb.purpose as 목적,
    collect(DISTINCT drug.ingredient_ko) as 약물목록,
    r.announcement_no as 고시번호,
    r.announcement_date as 고시일자
ORDER BY r.announcement_date DESC
```

### 2. 특정 약물이 포함된 모든 레지멘 조회

```cypher
MATCH (r:Regimen)-[:INCLUDES]->(d:Drug {ingredient_base_en: 'pembrolizumab'})
MATCH (disease:Disease)-[:TREATED_BY]->(r)
RETURN
    disease.name_kr as 암종,
    r.line as 치료라인,
    r.regimen_type as 요법유형,
    r.announcement_date as 고시일자
ORDER BY r.announcement_date DESC
```

### 3. 특정 암종의 치료 라인별 급여 요법 통계

```cypher
MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)
WHERE d.kcd_code STARTS WITH 'C34'  // 폐암
RETURN
    tb.line as 치료라인,
    count(DISTINCT r) as 요법수,
    collect(DISTINCT r.regimen_type) as 요법유형
ORDER BY tb.line
```

### 4. 바이오마커 검사 → 약물 → 급여 요법 전체 경로

```cypher
MATCH path = (t:Test)<-[:TESTED_BY]-(b:Biomarker)<-[:TARGETS]-(drug:Drug)<-[:INCLUDES]-(r:Regimen)<-[:TREATED_BY]-(d:Disease)
WHERE d.kcd_code STARTS WITH 'C50'  // 유방암
  AND b.name_en = 'HER2'
RETURN
    d.name_kr as 질병,
    b.name_ko as 바이오마커,
    t.edi_code as 검사코드,
    t.name_ko as 검사명,
    drug.ingredient_ko as 약물,
    r.regimen_type as 요법유형,
    r.line as 치료라인,
    r.announcement_no as 고시번호
LIMIT 10
```

## 데이터 정규화 상태

### 완전 매핑 (35개, 92.1%)

KCD 코드와 모든 약물의 ATC 코드가 매핑된 레지멘

### 부분 매핑 (3개, 7.9%)

- **Platinum** (2개) - 일반 용어, Carboplatin/Cisplatin 구분 불가
- **병용 약물 문자열** (1개) - 데이터 품질 이슈

### 누락 약물 처리

누락된 약물은 `missing_drugs` 배열에 기록되며, 해당 레지멘은 생성되지만 누락된 약물과의 관계는 생성되지 않습니다.

## 구현 계획

1. **Regimen 노드 생성**
   - `hira_regimens_normalized.json` 로드
   - Regimen 노드 MERGE (regimen_id 기준)

2. **Disease → TREATED_BY → Regimen 관계 생성**
   - kcd_codes 배열 순회
   - STARTS WITH 패턴으로 Disease 매칭
   - 관계 속성: line, purpose, announcement_no, announcement_date

3. **Regimen → INCLUDES → Drug 관계 생성**
   - drugs 배열 순회
   - atc_code로 Drug 매칭
   - 관계 속성: drug_name, normalized_name

4. **검증 쿼리**
   - 노드 카운트
   - 관계 카운트
   - 샘플 경로 쿼리

## 참고사항

- 모든 매핑은 **코드 기반**으로 진행 (텍스트 유사도 사용 안 함)
- KCD 코드는 공식 WHO ICD-10 분류 기반
- ATC 코드는 WHO Collaborating Centre for Drug Statistics Methodology 기준
- HIRA 고시 데이터는 정기적으로 업데이트됨 (최신성 확인 필요)
