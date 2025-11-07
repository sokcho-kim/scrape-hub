// Neo4j 샘플 Cypher 쿼리
// 항암제-바이오마커-검사 데이터베이스

// =============================================================================
// 1. 데이터 확인 쿼리
// =============================================================================

// 전체 노드 수 확인
MATCH (n)
RETURN labels(n) as NodeType, count(n) as Count
ORDER BY Count DESC;

// 전체 관계 수 확인
MATCH ()-[r]->()
RETURN type(r) as RelationType, count(r) as Count
ORDER BY Count DESC;

// =============================================================================
// 2. 바이오마커 조회
// =============================================================================

// 모든 바이오마커 목록
MATCH (b:Biomarker)
RETURN b.name_ko, b.name_en, b.type, b.cancer_types
ORDER BY b.name_ko;

// 특정 타입의 바이오마커
MATCH (b:Biomarker {type: 'mutation'})
RETURN b.name_ko, b.name_en, b.cancer_types;

// 가장 많은 검사를 가진 바이오마커 TOP 10
MATCH (b:Biomarker)-[:TESTED_BY]->(t:Test)
RETURN b.name_ko, b.name_en, count(t) as test_count
ORDER BY test_count DESC
LIMIT 10;

// =============================================================================
// 3. HER2 바이오마커 분석
// =============================================================================

// HER2 관련 모든 검사
MATCH (b:Biomarker {name_en: 'HER2'})-[:TESTED_BY]->(t:Test)
RETURN b.name_ko, t.name_ko, t.edi_code, t.category
LIMIT 20;

// HER2 검사 카테고리별 통계
MATCH (b:Biomarker {name_en: 'HER2'})-[:TESTED_BY]->(t:Test)
RETURN t.category, count(t) as count
ORDER BY count DESC;

// =============================================================================
// 4. 약물 조회
// =============================================================================

// 모든 항암제 목록
MATCH (d:Drug)
RETURN d.ingredient_ko, d.therapeutic_category, d.atc_code
ORDER BY d.ingredient_ko
LIMIT 20;

// EGFR을 표적하는 모든 항암제
MATCH (d:Drug)-[:TARGETS]->(b:Biomarker {name_en: 'EGFR'})
RETURN d.ingredient_ko, d.mechanism_of_action, d.therapeutic_category;

// 가장 많은 바이오마커를 표적하는 약물 TOP 10
MATCH (d:Drug)-[:TARGETS]->(b:Biomarker)
RETURN d.ingredient_ko, count(b) as biomarker_count
ORDER BY biomarker_count DESC
LIMIT 10;

// =============================================================================
// 5. 경로 쿼리 (약물 → 바이오마커 → 검사)
// =============================================================================

// 특정 약물의 전체 경로
MATCH path = (d:Drug {ingredient_ko: '게피티니브'})
             -[:TARGETS]->(b:Biomarker)
             -[:TESTED_BY]->(t:Test)
RETURN path
LIMIT 10;

// 모든 약물-바이오마커-검사 연결
MATCH path = (d:Drug)-[:TARGETS]->(b:Biomarker)-[:TESTED_BY]->(t:Test)
RETURN d.ingredient_ko, b.name_ko, t.name_ko, t.edi_code
LIMIT 50;

// 특정 암종에 대한 전체 치료 경로
MATCH (b:Biomarker)
WHERE '폐암' IN b.cancer_types
MATCH (d:Drug)-[:TARGETS]->(b)-[:TESTED_BY]->(t:Test)
RETURN d.ingredient_ko, b.name_ko, t.name_ko
LIMIT 30;

// =============================================================================
// 6. 검사 조회
// =============================================================================

// 모든 검사 카테고리별 통계
MATCH (t:Test)
RETURN t.category, count(t) as count
ORDER BY count DESC;

// EDI 코드로 검사 조회
MATCH (t:Test {edi_code: 'C5674020'})
RETURN t;

// LOINC 코드가 있는 검사
MATCH (t:Test)
WHERE t.loinc_code IS NOT NULL
RETURN t.name_ko, t.loinc_code, t.edi_code
LIMIT 20;

// SNOMED CT 코드가 있는 검사
MATCH (t:Test)
WHERE t.snomed_ct_id IS NOT NULL
RETURN t.name_ko, t.snomed_ct_id, t.snomed_ct_name
LIMIT 20;

// =============================================================================
// 7. 통계 및 분석
// =============================================================================

// 바이오마커 타입별 분포
MATCH (b:Biomarker)
RETURN b.type, count(b) as count
ORDER BY count DESC;

// 암종별 바이오마커 수
MATCH (b:Biomarker)
UNWIND b.cancer_types as cancer_type
RETURN cancer_type, count(DISTINCT b) as biomarker_count
ORDER BY biomarker_count DESC;

// 검사가 가장 많은 바이오마커
MATCH (b:Biomarker)-[r:TESTED_BY]->(t:Test)
RETURN b.name_ko, count(t) as test_count,
       collect(DISTINCT t.category) as test_categories
ORDER BY test_count DESC
LIMIT 10;

// 약물이 가장 많은 바이오마커
MATCH (d:Drug)-[:TARGETS]->(b:Biomarker)
WITH b, count(d) as drug_count
RETURN b.name_ko, drug_count
ORDER BY drug_count DESC
LIMIT 10;

// =============================================================================
// 8. 고급 쿼리
// =============================================================================

// 약물과 검사가 모두 있는 바이오마커 (가장 완성도 높음)
MATCH (d:Drug)-[:TARGETS]->(b:Biomarker)-[:TESTED_BY]->(t:Test)
WITH b, count(DISTINCT d) as drug_count, count(DISTINCT t) as test_count
RETURN b.name_ko, b.name_en, drug_count, test_count
ORDER BY drug_count DESC, test_count DESC;

// 특정 검사 카테고리로 진단 가능한 바이오마커
MATCH (b:Biomarker)-[:TESTED_BY]->(t:Test {category: '면역조직화학검사'})
RETURN DISTINCT b.name_ko, b.cancer_types
ORDER BY b.name_ko;

// 유방암 관련 전체 생태계
MATCH (b:Biomarker)
WHERE '유방암' IN b.cancer_types
OPTIONAL MATCH (d:Drug)-[:TARGETS]->(b)
OPTIONAL MATCH (b)-[:TESTED_BY]->(t:Test)
RETURN b.name_ko,
       count(DISTINCT d) as drug_count,
       count(DISTINCT t) as test_count
ORDER BY drug_count DESC;

// =============================================================================
// 9. 데이터 품질 확인
// =============================================================================

// 검사가 없는 바이오마커 (약물만 있음)
MATCH (b:Biomarker)
WHERE NOT (b)-[:TESTED_BY]->()
RETURN b.name_ko, b.name_en, b.type;

// 약물이 없는 바이오마커 (검사만 있음)
MATCH (b:Biomarker)
WHERE NOT ()-[:TARGETS]->(b)
RETURN b.name_ko, b.name_en, b.type;

// LOINC 코드가 없는 검사
MATCH (t:Test)
WHERE t.loinc_code IS NULL
RETURN count(t) as tests_without_loinc;

// =============================================================================
// 10. 시각화 쿼리
// =============================================================================

// 특정 바이오마커의 전체 네트워크
MATCH path = (d:Drug)-[:TARGETS]->(b:Biomarker {name_en: 'EGFR'})-[:TESTED_BY]->(t:Test)
RETURN path
LIMIT 50;

// 폐암 관련 네트워크
MATCH (b:Biomarker)
WHERE '폐암' IN b.cancer_types
MATCH path = (d:Drug)-[:TARGETS]->(b)-[:TESTED_BY]->(t:Test)
RETURN path
LIMIT 100;

// 전체 그래프 (샘플)
MATCH path = (d:Drug)-[:TARGETS]->(b:Biomarker)-[:TESTED_BY]->(t:Test)
RETURN path
LIMIT 20;
