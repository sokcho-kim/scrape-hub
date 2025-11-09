# Neo4j 100% 코드 기반 매핑 완성 - 2025년 11월 9일

## 📋 작업 개요

문자열 매칭을 완전히 배제하고 LOINC/SNOMED CT 표준 코드만을 사용한 순수 코드 기반 매핑 구현

---

## ✅ 완료 사항

### 1. 범용 SNOMED CT 코드 필터링

**문제**: HER2가 1,101개 검사에 매칭 (잘못된 매칭)
- 원인: `414464004` (Immunohistochemistry procedure) - 모든 IHC 검사에 사용되는 범용 코드

**해결**:
```python
GENERIC_SNOMED_CODES = {
    '414464004',  # Immunohistochemistry procedure (범용 IHC)
    '117617002',  # Immunohistochemistry staining method (범용 IHC 염색)
    '127798001',  # Laboratory procedure (범용 검사 procedure)
}
```

**결과**: HER2 1,101개 → 4개 (정확한 매칭)

### 2. 키워드 매칭 완전 제거

**변경 전**:
```python
def match_by_keyword(self, biomarker_name, test_row):
    variants = {'IDH1': ['IDH1'], 'IDH2': ['IDH2'], ...}
    # 키워드 매칭 로직
```

**변경 후**:
```python
def match_by_keyword(self, biomarker_name, test_row):
    """키워드 매칭 비활성화 - 100% 순수 코드 기반 매핑만 사용"""
    return None
```

**결과**: 137개 관계 (LOINC 31개 + SNOMED 106개) - 100% 코드 기반

### 3. EDI 코드 기반 Test 노드 매칭

**문제**: Excel 행 번호로 test_id 생성 → Neo4j Test 노드와 불일치
- 매핑 파일: HINS_TEST_0451 (8,417개 중 하나)
- Neo4j 노드: HINS_TEST_001~575 (575개만 존재)

**해결**:
```python
# 기존 Test 노드 로드
with open(INPUT_EXISTING_TESTS, 'r', encoding='utf-8') as f:
    tests_data = json.load(f)
    self.existing_tests = tests_data['tests']
    # EDI 코드로 인덱싱
    for test in self.existing_tests:
        edi_code = test.get('edi_code')
        if edi_code:
            self.edi_to_test_id[edi_code] = test['test_id']

# EDI 코드로 test_id 찾기
edi_code = str(test_row.get('term_cd', ''))
test_id = self.edi_to_test_id.get(edi_code)
if not test_id:
    continue  # Neo4j에 없는 Test는 스킵
```

**결과**: 134개 TESTED_BY 관계 정상 생성

---

## 📊 최종 결과

### Neo4j 그래프 현황
```
총 노드: 736개
├── Biomarker: 23개 (v2.0)
├── Test: 575개
└── Drug: 138개

총 관계: 205개
├── TESTED_BY: 134개 (100% 코드 기반!)
└── TARGETS: 71개
```

### 100% 순수 코드 기반 매핑
```
매핑 통계:
├── SNOMED CT (snomed_code_pre): 104개 (77.6%)
├── LOINC (loinc_code): 30개 (22.4%)
└── 키워드 매칭: 0개 ✅
```

### 바이오마커별 검사 매핑 (Top 10)

| 순위 | 바이오마커 | 한글명 | 검사 수 |
|------|-----------|--------|---------|
| 1 | ROS1 | ROS1 융합 유전자 | 104개 |
| 2 | EGFR | EGFR 수용체 | 10개 |
| 3 | BCR-ABL | BCR-ABL 융합 유전자 | 6개 |
| 4 | HER2 | HER2 수용체 | 4개 |
| 5 | KRAS | KRAS 돌연변이 | 3개 |
| 6 | BRAF | BRAF 돌연변이 | 2개 |
| 7 | FLT3 | FLT3 | 2개 |
| 8 | ALK | ALK 융합 유전자 | 1개 |
| 9 | BRCA1 | BRCA1 돌연변이 | 1개 |
| 10 | BRCA2 | BRCA2 돌연변이 | 1개 |

**코드가 없어서 매핑되지 않은 바이오마커 (13개)**:
- AR, CD20, CD38, CDK4/6, ER, IDH1, IDH2, MEK, PARP, PD-1, PD-L1, VEGF, mTOR

---

## 🔧 수정된 파일

### 1. `scripts/map_biomarkers_to_tests_code_based.py`
- 범용 SNOMED 코드 블랙리스트 추가
- 키워드 매칭 완전 비활성화
- EDI 코드 기반 기존 Test 노드 매칭
- test_id 포맷 수정 (4자리 → EDI 기반)

### 2. `neo4j/scripts/integrate_to_neo4j.py`
- v2.0 코드 기반 매핑 파일 사용
- `'tests'` 키 호환성 추가 (v1: matched_tests, v2: tests)

---

## 💡 핵심 인사이트

### 1. 표준 코드의 중요성
- **LOINC/SNOMED CT 기반 매핑이 정확성의 핵심**
- 문자열 매칭은 false positive 양산

### 2. 범용 vs 특이적 코드
- 범용 코드 (414464004)는 수천 개 검사에 사용됨
- 특이적 코드만 사용해야 정확한 매핑 가능

### 3. 코드 커버리지 한계
- 23개 바이오마커 중 10개만 코드 보유 (43.5%)
- AR, ER, PD-L1 등 주요 바이오마커도 특이적 코드 없음

---

## ⚠️ 현재 그래프의 한계

### 구조적 빈약함
```
현재: Test ← Biomarker → Drug
```

**문제점**:
1. ❌ 암종(질병) 정보 없음
2. ❌ 적응증 정보 없음
3. ❌ 치료 경로 불명확
4. ❌ 임상적 컨텍스트 부족
5. ❌ KCD/보험청구 연계 없음

**예시**:
```cypher
// 현재: 단순 조회만 가능
MATCH (d:Drug)-[:TARGETS]->(b:Biomarker)-[:TESTED_BY]->(t:Test)
WHERE b.name_en = 'EGFR'
RETURN d.ingredient_ko, t.name_ko
// → "제피티니브, EGFR 검사" (치료 맥락 없음)
```

---

## 🚀 향후 계획: Neo4j 그래프 확장

### Phase 5: Cancer (암종) 노드 추가 ⭐ 최우선

**목표**: 바이오마커-암종-약물 삼각 관계 구축

**새로운 노드**:
```
Cancer {
  cancer_id: "CANCER_001"
  name_ko: "비소세포폐암"
  name_en: "Non-small cell lung cancer"
  kcd_code: "C34"  // 추후 연결
  stage: ["I", "II", "III", "IV"]
  prevalence: "폐암의 85%"
}
```

**새로운 관계**:
```cypher
(Cancer)-[:HAS_BIOMARKER]->(Biomarker)
(Drug)-[:TREATS]->(Cancer)
(Biomarker)-[:PREDICTS_RESPONSE_TO]->(Drug)
(Test)-[:DIAGNOSES]->(Cancer)
```

**데이터 소스**:
- ✅ 기존 약물 데이터의 `therapeutic_category`
- ✅ 기존 약물 데이터의 `approved_indications`
- ✅ 바이오마커별 암종 매핑 (문헌 기반)

**예상 효과**:
```cypher
// 확장 후: 완전한 치료 경로 조회
MATCH path = (cancer:Cancer {name_ko: "비소세포폐암"})
             -[:HAS_BIOMARKER]->(b:Biomarker)
             <-[:TARGETS]-(d:Drug)-[:TREATS]->(cancer)
WHERE b.name_en = 'EGFR'
RETURN cancer.name_ko, b.name_ko,
       d.ingredient_ko, d.approved_indications
// → "비소세포폐암 → EGFR 돌연변이 → 제피티니브 → EGFR 돌연변이 양성 NSCLC 1차 치료"
```

**구현 난이도**: ⭐⭐ (중)
**소요 시간**: 1-2시간
**가치**: ⭐⭐⭐⭐⭐ (매우 높음)

---

### Phase 6: Indication (적응증) 노드 추가

**목표**: 약물 사용 조건의 구조화

**새로운 노드**:
```
Indication {
  indication_id: "IND_001"
  description: "HER2 양성 전이성 유방암 1차 치료"
  cancer_type: "유방암"
  biomarker_status: "HER2 양성"
  stage: "전이성"
  line: "1차"
  combination: true
}
```

**새로운 관계**:
```cypher
(Drug)-[:HAS_INDICATION]->(Indication)
(Indication)-[:REQUIRES_BIOMARKER]->(Biomarker)
(Indication)-[:FOR_CANCER]->(Cancer)
```

**데이터 소스**:
- ✅ 기존 약물 데이터의 `approved_indications` 파싱
- ✅ NLP를 통한 구조화

**구현 난이도**: ⭐⭐⭐ (중상)
**소요 시간**: 2-3시간
**가치**: ⭐⭐⭐⭐ (높음)

---

### Phase 7: KCD (한국표준질병사인분류) 노드 추가

**목표**: 보험청구 및 통계 연계

**새로운 노드**:
```
KCD {
  kcd_code: "C34.9"
  name_ko: "기관지 및 폐의 악성 신생물, 상세불명 부분"
  level: 4
  parent_code: "C34"
  icd10_code: "C34.9"
}
```

**새로운 관계**:
```cypher
(KCD)-[:MANIFESTS_AS]->(Cancer)
(KCD)-[:MAPS_TO_ICD10]->(ICD10)
```

**데이터 소스**:
- 📥 KCD 코드 파일 필요 (통계청/질병관리청)
- 📥 암종별 KCD 매핑 테이블

**구현 난이도**: ⭐⭐ (중)
**소요 시간**: 1-2시간 (KCD 데이터 있는 경우)
**가치**: ⭐⭐⭐ (중간 - 보험청구 활용)

---

### Phase 8: Gene/Mutation 분리

**목표**: 유전자-돌연변이 관계의 정밀화

**현재 문제**:
```
Biomarker {name_en: "EGFR"}  // Gene? Mutation? Protein?
```

**개선안**:
```
Gene {gene_id: "GENE_001", symbol: "EGFR", name: "표피성장인자수용체"}
  ↓ [:HAS_MUTATION]
Mutation {mutation_id: "MUT_001", name: "L858R", type: "missense"}
  ↓ [:IN_EXON]
Exon {exon_number: 21}
```

**새로운 관계**:
```cypher
(Gene)-[:HAS_MUTATION]->(Mutation)
(Mutation)-[:DETECTED_BY]->(Test)
(Drug)-[:TARGETS_MUTATION]->(Mutation)
```

**데이터 소스**:
- 📥 HGNC (Gene nomenclature)
- 📥 CIViC (Clinical Interpretations of Variants in Cancer)
- 📥 OncoKB

**구현 난이도**: ⭐⭐⭐⭐ (높음)
**소요 시간**: 4-6시간
**가치**: ⭐⭐⭐⭐⭐ (매우 높음 - 정밀의료)

---

### Phase 9: 추가 확장 (장기)

#### 9.1 ClinicalTrial (임상시험) 노드
```cypher
(Drug)-[:TESTED_IN]->(ClinicalTrial)
(ClinicalTrial)-[:ENROLLS]->(Cancer)
(ClinicalTrial)-[:REQUIRES_BIOMARKER]->(Biomarker)
```

**데이터 소스**: ClinicalTrials.gov API

#### 9.2 Publication (논문) 노드
```cypher
(Biomarker)-[:CITED_IN]->(Publication)
(Drug)-[:EVIDENCE_FROM]->(Publication)
```

**데이터 소스**: PubMed API

#### 9.3 Pathway (신호전달경로) 노드
```cypher
(Gene)-[:PARTICIPATES_IN]->(Pathway)
(Drug)-[:INHIBITS]->(Pathway)
```

**데이터 소스**: KEGG, Reactome

#### 9.4 SideEffect (부작용) 노드
```cypher
(Drug)-[:CAUSES]->(SideEffect)
```

**데이터 소스**: SIDER, FDA Adverse Events

---

## 📅 단계별 구현 로드맵

### 즉시 구현 가능 (기존 데이터만 사용)

**Week 1: 핵심 노드 추가**
- [ ] Phase 5: Cancer 노드 (1-2일)
- [ ] Phase 6: Indication 노드 (1-2일)
- [ ] 관계 재구축 및 검증 (1일)

**예상 결과**:
```
노드: 736개 → ~800개
관계: 205개 → ~600개
실용성: ⭐⭐ → ⭐⭐⭐⭐⭐
```

### 중기 구현 (외부 데이터 필요)

**Week 2-3: 표준 코드 연계**
- [ ] Phase 7: KCD 노드 (KCD 데이터 확보)
- [ ] ICD-10 매핑
- [ ] 보험청구 시나리오 개발

### 장기 구현 (외부 API/대규모 데이터)

**Month 2-3: 정밀의료 그래프**
- [ ] Phase 8: Gene/Mutation 분리
- [ ] ClinicalTrial 연동
- [ ] Publication 연동
- [ ] Pathway 데이터베이스 통합

---

## 🎯 핵심 가치 제안

### 현재 (v2.0 코드 기반)
```
"EGFR 검사가 있고, 제피티니브라는 약이 EGFR을 타겟팅한다"
→ 데이터 조회는 가능하지만 임상 의사결정 지원 불가
```

### Phase 5-6 완료 후
```
"비소세포폐암 환자가 EGFR L858R 돌연변이 양성이면
 1차 치료로 제피티니브 사용 가능,
 C5831196 EDI 코드로 EGFR 검사 청구"
→ 완전한 임상 의사결정 지원 가능!
```

### Phase 8 완료 후
```
"EGFR 21번 엑손 L858R 돌연변이는
 제피티니브, 엘로티니브, 아파티니브에 반응하지만
 T790M 내성 돌연변이 발생 시 오시머티니브로 전환"
→ 정밀의료 치료 경로 제시!
```

---

## 💭 다음 단계 결정

### 옵션 A: 빠른 가치 실현 (권장)
- Phase 5 (Cancer) + Phase 6 (Indication)
- 소요: 3-4시간
- 효과: 실용성 즉시 확보

### 옵션 B: 완전한 확장
- Phase 5 → 6 → 7 → 8 순차 구현
- 소요: 2-3주
- 효과: 정밀의료 knowledge graph 완성

### 옵션 C: 선별적 확장
- Phase 5 (필수) + Phase 8 (Gene/Mutation)
- 소요: 1주
- 효과: 핵심 가치 + 정밀의료 기반

---

## 📝 작업 로그

**2025-11-09 오후**
- ✅ 범용 SNOMED 코드 필터링 구현
- ✅ 키워드 매칭 완전 제거
- ✅ EDI 코드 기반 Test 노드 매칭
- ✅ Neo4j 100% 코드 기반 매핑 통합 완료
- ✅ 그래프 확장 계획 수립

**시간 소요**: 약 3시간
**상태**: ✅ v2.0 코드 기반 매핑 완성

---

**작성일**: 2025-11-09
**작성자**: Claude Code
**Neo4j 버전**: 2025.10.1
**데이터 버전**: v2.0 (23 biomarkers, 100% code-based)
