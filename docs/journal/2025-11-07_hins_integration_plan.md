# 2025-11-07 업무 일지: HINS 통합 및 Week 2 실행 계획

**프로젝트**: medi-claim 지식그래프 구축 (Week 2)
**작업자**: Claude Code + 지민
**작업 일시**: 2025-11-07

---

## 📋 오늘 작업 요약

### 완료 작업
- ✅ HINS 데이터 수집 (KCD, EDI 매핑 파일 36개, 14.59 MB)
- ✅ HINS 바이오마커 분석 (9개 주요 바이오마커 39건 검출)
- ✅ HINS 통합 전략 수립
- ✅ Week 2 실행 계획 수립 (진행 중)

### 다음 작업
- [ ] 4개 Phase 스크립트 설계
- [ ] 스크립트 구현 및 실행
- [ ] Neo4j 통합

---

## 🎯 Week 2 목표 (수정)

### 기존 목표
```
Week 2: Cancer + Biomarker 노드 구축
- 바이오마커 50-70개 추출
- 암종 100개 매핑
- Neo4j 관계 생성
```

### 수정 목표 (HINS 통합 추가)
```
Week 2: Cancer + Biomarker + BiomarkerTest 노드 구축
- 바이오마커 50-70개 추출
- 바이오마커 검사 39+α개 (HINS 데이터)
- EDI 코드 + SNOMED CT 매핑
- 암종 100개 매핑
- Neo4j 3-hop 관계 구축 (Drug → Biomarker → Test)
```

---

## 📊 HINS 데이터 분석 결과

### 수집 데이터
- **KCD-SNOMED CT**: 2개 파일 (9.15 MB)
- **EDI-SNOMED CT**: 34개 파일 (5.44 MB)
- **총 데이터**: 36개 파일, 14.59 MB

### 바이오마커 검출 (EDI 검사 데이터)

| 바이오마커 | 검출 건수 | SNOMED CT | 주요 암종 |
|----------|---------|-----------|----------|
| HER2 | 6건 | 414464004 | 유방암, 위암 |
| EGFR | 10건 | - | 폐암 |
| PD-L1 | 2건 | 117617002 | 면역항암제 적용 |
| BRCA1/2 | 2건 | 405823003, 405826006 | 유방암, 난소암 |
| ALK | 11건 | 117617002 | 폐암 |
| ROS1 | 2건 | 9718006 | 폐암 |
| KRAS | 3건 | - | 대장암, 폐암 |
| BRAF | 2건 | - | 흑색종, 대장암 |
| NTRK | 1건 | - | 범종양 |

**총 39건** (2020년 기준)

### 데이터 품질
- EDI 코드: 100% (건강보험 청구 코드)
- SNOMED CT: ~40% (국제 표준 코드)
- 검사명 (한글): 100%
- 검사 방법: 체세포/생식세포 유전자검사, 면역조직화학검사 등

---

## 🔄 통합 전략: 4단계 프로세스

### 전체 플로우

```
[Phase 1]           [Phase 2]            [Phase 3]           [Phase 4]
항암제 사전      →  HINS 검사 파싱    →  매핑 및 검증    →  Neo4j 통합
(154개)             (39건)              (자동+GPT)         (노드+관계)
    ↓                   ↓                    ↓                   ↓
바이오마커 추출   →  검사 구조화      →  관계 생성       →  쿼리 테스트
(50-70개)           (EDI+SNOMED)        (JSON)             (그래프)
```

### Phase별 상세 계획

---

## Phase 1: 바이오마커 추출

### 목표
항암제 사전 154개에서 바이오마커 50-70개 추출

### 입력 데이터
- `bridges/anticancer_master_classified.json`
- 154개 항암제
- mechanism_of_action: 113개 (73.4%)

### 처리 로직

#### 1단계: 패턴 기반 자동 추출
```python
# mechanism_of_action에서 바이오마커 추출
BIOMARKER_PATTERNS = {
    'HER2': ['HER2', 'ERBB2'],
    'EGFR': ['EGFR'],
    'PD-L1': ['PD-L1', 'PDL1'],
    'BRCA': ['BRCA1', 'BRCA2'],
    'ALK': ['ALK'],
    'VEGF': ['VEGF', 'VEGFR'],
    'BRAF': ['BRAF'],
    # ... 50+ 패턴
}

for drug in anticancer_drugs:
    moa = drug['mechanism_of_action']
    for biomarker, patterns in BIOMARKER_PATTERNS.items():
        if any(pattern in moa for pattern in patterns):
            extract_biomarker(drug, biomarker)
```

#### 2단계: ATC Level 3 기반 추출
```python
# ATC Level 3 카테고리 → 바이오마커 매핑
ATC_TO_BIOMARKER = {
    'L01EA': ['BCR-ABL'],      # BCR-ABL 티로신 키나제 억제제
    'L01EB': ['EGFR'],         # EGFR 티로신 키나제 억제제
    'L01FC': ['HER2'],         # HER2 억제제
    'L01FF': ['PD-1', 'PD-L1'], # 면역관문 억제제
    # ...
}
```

#### 3단계: GPT 보완
```python
# 애매한 경우 GPT로 확인
for drug in unmatched_drugs:
    prompt = f"""
    항암제: {drug['ingredient_ko']}
    작용기전: {drug['mechanism_of_action']}

    이 약물의 타겟 바이오마커를 JSON으로 반환:
    {{
        "biomarkers": ["바이오마커1", "바이오마커2"],
        "confidence": 0.9
    }}
    """
    result = call_gpt(prompt)
```

### 출력 데이터

**파일**: `bridges/biomarkers_extracted.json`

```json
[
  {
    "biomarker_id": "BIOMARKER_001",
    "biomarker_name_en": "HER2",
    "biomarker_name_ko": "HER2 수용체",
    "biomarker_type": "protein",
    "protein_gene": "ERBB2",
    "related_drugs": [
      {
        "atc_code": "L01FD01",
        "ingredient_ko": "트라스투주맙",
        "relationship": "targets"
      }
    ],
    "cancer_types": ["유방암", "위암"],
    "source": "anticancer_dictionary",
    "extraction_method": "pattern_match",
    "confidence": 0.95
  }
]
```

### 예상 결과
- 바이오마커 수: 50-70개
- 자동 추출 성공률: 80%
- GPT 보완 필요: 20% (10-14개)
- 소요 시간: 2-3시간
- 비용: $5-7 (GPT API)

---

## Phase 2: HINS 검사 데이터 파싱

### 목표
HINS EDI 검사 파일에서 바이오마커 검사 정보 구조화

### 입력 데이터
- `data/hins/downloads/edi/2장_19_20용어매핑테이블(검사).xlsx`
- 8,417개 검사 항목

### 처리 로직

#### 1단계: Excel 파일 읽기
```python
import pandas as pd

df = pd.read_excel(file_path)

# 컬럼 확인
# ['term_ty', 'term_cd', 'term_kr', 'term_en',
#  'pre_ct_id', 'pre_ct_cn', 'snmd_ct_exp', ...]
```

#### 2단계: 바이오마커 관련 검사 필터링
```python
BIOMARKER_KEYWORDS = [
    'HER2', 'EGFR', 'PD-L1', 'BRCA', 'ALK', 'ROS1',
    'KRAS', 'BRAF', 'NTRK', 'MSI', 'TMB',
    '유전자검사', '면역조직화학검사'
]

biomarker_tests = []
for idx, row in df.iterrows():
    term_kr = str(row['term_kr'])

    for keyword in BIOMARKER_KEYWORDS:
        if keyword in term_kr:
            biomarker_tests.append({
                'edi_code': row['term_cd'],
                'test_name_ko': term_kr,
                'test_name_en': row.get('term_en', ''),
                'snomed_ct_id': row.get('pre_ct_id', ''),
                'snomed_ct_name': row.get('pre_ct_cn', ''),
                'biomarker_keyword': keyword
            })
            break
```

#### 3단계: 검사 방법 분류
```python
TEST_CATEGORY_PATTERNS = {
    '면역조직화학검사': ['면역조직', '면역세포화학'],
    '유전자염기서열검사': ['염기서열분석', '염기서열검사'],
    '형광동소부합법': ['형광동소부합법', 'FISH'],
    '교잡법': ['교잡법', 'Hybridization'],
}

for test in biomarker_tests:
    for category, patterns in TEST_CATEGORY_PATTERNS.items():
        if any(p in test['test_name_ko'] for p in patterns):
            test['test_category'] = category
            break
```

#### 4단계: 바이오마커명 정규화
```python
# "체세포 유전자검사-기타[HER2 Gene]" → "HER2"
import re

def extract_biomarker_name(test_name):
    # 대괄호 안 추출
    match = re.search(r'\[([A-Z0-9-]+)', test_name)
    if match:
        return match.group(1).replace(' Gene', '')

    # 언더스코어 뒤 추출
    if '_' in test_name:
        return test_name.split('_')[-1]

    return None

for test in biomarker_tests:
    biomarker = extract_biomarker_name(test['test_name_ko'])
    if biomarker:
        test['biomarker_name'] = biomarker
```

### 출력 데이터

**파일**: `data/hins/parsed/biomarker_tests_structured.json`

```json
[
  {
    "test_id": "HINS_TEST_001",
    "edi_code": "C5674010",
    "test_name_ko": "면역조직(세포)화학검사[고형암]-Level Ⅱ_PD-L1",
    "test_name_en": "",
    "biomarker_name": "PD-L1",
    "test_category": "면역조직화학검사",
    "test_method": "면역조직(세포)화학검사",
    "snomed_ct_id": "117617002",
    "snomed_ct_name": "Immunohistochemistry",
    "reference_year": 2020,
    "data_source": "HINS_EDI"
  }
]
```

### 예상 결과
- 검사 항목: 39+α개 (50개 목표)
- EDI 코드 커버리지: 100%
- SNOMED CT 매핑: ~40%
- 소요 시간: 1-2시간

---

## Phase 3: 바이오마커-검사 매핑

### 목표
Phase 1 바이오마커와 Phase 2 검사를 자동 매핑 + GPT 검증

### 입력 데이터
- `bridges/biomarkers_extracted.json` (Phase 1 결과)
- `data/hins/parsed/biomarker_tests_structured.json` (Phase 2 결과)

### 처리 로직

#### 1단계: 이름 기반 자동 매칭
```python
def match_biomarker_to_tests(biomarker, tests):
    """
    바이오마커명으로 검사 매칭
    """
    biomarker_variants = get_variants(biomarker['biomarker_name_en'])
    # 예: HER2 → ["HER2", "HER-2", "ERBB2", "HER2 Gene"]

    matched_tests = []
    for test in tests:
        if any(variant in test['biomarker_name'] for variant in biomarker_variants):
            matched_tests.append({
                'test': test,
                'match_method': 'name_match',
                'confidence': 0.9
            })

    return matched_tests
```

#### 2단계: GPT 검증
```python
def verify_match_with_gpt(biomarker, test):
    """
    애매한 매칭은 GPT로 검증
    """
    prompt = f"""
    바이오마커: {biomarker['biomarker_name_ko']} ({biomarker['biomarker_name_en']})
    검사: {test['test_name_ko']} (EDI: {test['edi_code']})

    이 검사가 이 바이오마커를 측정하는가?
    {{
        "is_match": true/false,
        "confidence": 0.0-1.0,
        "reason": "설명"
    }}
    """

    result = call_gpt(prompt)
    return result['is_match'] and result['confidence'] > 0.7
```

#### 3단계: 관계 데이터 생성
```python
relationships = []

for biomarker in biomarkers:
    matched_tests = match_biomarker_to_tests(biomarker, tests)

    for match in matched_tests:
        if match['confidence'] > 0.7:
            relationships.append({
                'biomarker_id': biomarker['biomarker_id'],
                'test_id': match['test']['test_id'],
                'relationship_type': 'TESTED_BY',
                'confidence': match['confidence'],
                'verified_by': match['match_method']
            })
```

### 출력 데이터

**파일**: `bridges/biomarker_test_mappings.json`

```json
{
  "mappings": [
    {
      "biomarker_id": "BIOMARKER_001",
      "biomarker_name": "HER2",
      "tests": [
        {
          "test_id": "HINS_TEST_015",
          "edi_code": "D4430",
          "test_name_ko": "HER2 단백질",
          "snomed_ct_id": "414464004",
          "confidence": 1.0,
          "match_method": "name_match"
        },
        {
          "test_id": "HINS_TEST_042",
          "edi_code": "C5839046",
          "test_name_ko": "체세포 유전자검사-형광법[HER2 Gene]",
          "confidence": 0.95,
          "match_method": "name_match"
        }
      ]
    }
  ],
  "statistics": {
    "total_biomarkers": 65,
    "biomarkers_with_tests": 52,
    "coverage": 0.80,
    "total_relationships": 89,
    "verified_by_gpt": 12
  }
}
```

### 예상 결과
- 매핑 성공률: 80%
- 바이오마커-검사 관계: 80-100개
- GPT 검증 필요: 10-15개
- 소요 시간: 2-3시간
- 비용: $2-3 (GPT API)

---

## Phase 4: Neo4j 통합

### 목표
Biomarker, BiomarkerTest 노드 생성 및 관계 구축

### 입력 데이터
- `bridges/biomarkers_extracted.json`
- `data/hins/parsed/biomarker_tests_structured.json`
- `bridges/biomarker_test_mappings.json`

### Neo4j 스키마

#### 노드 생성

**1. Biomarker 노드**
```cypher
CREATE (b:Biomarker {
  biomarker_id: "BIOMARKER_001",
  biomarker_name_en: "HER2",
  biomarker_name_ko: "HER2 수용체",
  biomarker_type: "protein",
  protein_gene: "ERBB2",
  cancer_types: ["유방암", "위암"],
  source: "anticancer_dictionary",
  created_at: datetime()
})
```

**2. BiomarkerTest 노드**
```cypher
CREATE (t:BiomarkerTest {
  test_id: "HINS_TEST_001",
  edi_code: "C5674010",
  test_name_ko: "면역조직화학검사-PD-L1",
  test_category: "면역조직화학검사",
  snomed_ct_id: "117617002",
  snomed_ct_name: "Immunohistochemistry",
  reference_year: 2020,
  data_source: "HINS_EDI",
  created_at: datetime()
})
```

#### 관계 생성

**1. Drug → Biomarker ([:TARGETS])**
```cypher
MATCH (d:AnticancerDrug {atc_code: "L01FD01"})
MATCH (b:Biomarker {biomarker_name_en: "HER2"})
CREATE (d)-[:TARGETS {
  relationship_source: "mechanism_of_action",
  confidence: 0.95
}]->(b)
```

**2. Biomarker → Test ([:TESTED_BY])**
```cypher
MATCH (b:Biomarker {biomarker_id: "BIOMARKER_001"})
MATCH (t:BiomarkerTest {test_id: "HINS_TEST_015"})
CREATE (b)-[:TESTED_BY {
  confidence: 1.0,
  match_method: "name_match",
  verified_by: "gpt"
}]->(t)
```

**3. Test → Cancer ([:USED_FOR_DIAGNOSIS])**
```cypher
MATCH (t:BiomarkerTest {edi_code: "D4430"})
MATCH (c:Cancer {cancer_name_ko: "유방암"})
CREATE (t)-[:USED_FOR_DIAGNOSIS {
  indication: "HER2 양성 확인"
}]->(c)
```

#### 인덱스 생성
```cypher
-- Biomarker 인덱스
CREATE INDEX biomarker_id FOR (b:Biomarker) ON (b.biomarker_id);
CREATE INDEX biomarker_name_en FOR (b:Biomarker) ON (b.biomarker_name_en);
CREATE INDEX biomarker_name_ko FOR (b:Biomarker) ON (b.biomarker_name_ko);

-- BiomarkerTest 인덱스
CREATE INDEX test_id FOR (t:BiomarkerTest) ON (t.test_id);
CREATE INDEX test_edi FOR (t:BiomarkerTest) ON (t.edi_code);
CREATE INDEX test_snomed FOR (t:BiomarkerTest) ON (t.snomed_ct_id);
```

### 스크립트 구조

**파일**: `scripts/neo4j/import_biomarkers_and_tests.py`

```python
class BiomarkerTestImporter:
    def __init__(self, neo4j_uri, user, password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(user, password))

    def import_biomarkers(self, biomarkers_file):
        """Biomarker 노드 임포트"""
        with self.driver.session() as session:
            for biomarker in load_json(biomarkers_file):
                session.execute_write(self._create_biomarker, biomarker)

    def import_tests(self, tests_file):
        """BiomarkerTest 노드 임포트"""
        # ...

    def create_relationships(self, mappings_file):
        """관계 생성"""
        # 1. Drug → Biomarker
        # 2. Biomarker → Test
        # 3. Test → Cancer (optional)

    def create_indexes(self):
        """인덱스 생성"""
        # ...

    def verify_import(self):
        """임포트 검증"""
        stats = {
            'biomarkers': count_nodes('Biomarker'),
            'tests': count_nodes('BiomarkerTest'),
            'targets_relationships': count_relationships('TARGETS'),
            'tested_by_relationships': count_relationships('TESTED_BY')
        }
        return stats
```

### 검증 쿼리

**1. 3-hop 경로 확인**
```cypher
MATCH path = (d:AnticancerDrug)-[:TARGETS]->(b:Biomarker)-[:TESTED_BY]->(t:BiomarkerTest)
WHERE d.ingredient_ko = "트라스투주맙"
RETURN d.ingredient_ko, b.biomarker_name_ko, t.test_name_ko, t.edi_code
```

**2. EDI 코드로 역추적**
```cypher
MATCH path = (d:AnticancerDrug)-[:TARGETS]->(b:Biomarker)-[:TESTED_BY]->(t:BiomarkerTest)
WHERE t.edi_code = "D4430"
RETURN d.ingredient_ko, d.brand_name_primary
```

**3. SNOMED CT 커버리지**
```cypher
MATCH (t:BiomarkerTest)
WHERE t.snomed_ct_id IS NOT NULL
RETURN count(*) as with_snomed,
       toFloat(count(*)) / toFloat((MATCH (t2:BiomarkerTest) RETURN count(t2))) as coverage
```

### 예상 결과
- Biomarker 노드: 50-70개
- BiomarkerTest 노드: 39-50개
- [:TARGETS] 관계: 100-150개
- [:TESTED_BY] 관계: 80-100개
- 소요 시간: 1-2시간

---

## 📊 전체 데이터 플로우

```
[입력]                    [처리]                   [출력]

anticancer_master     →  Phase 1: 추출        →  biomarkers_extracted.json
(154개)                  (패턴+GPT)               (50-70개)
                              ↓
                         관계 생성
                              ↓
HINS EDI 검사         →  Phase 2: 파싱        →  biomarker_tests.json
(8,417개)                (필터+정규화)            (39-50개)
                              ↓
                         Phase 3: 매핑
                        (자동+GPT 검증)
                              ↓
                         biomarker_test_mappings.json
                              ↓
                         Phase 4: Neo4j
                              ↓
                    [Neo4j 그래프 데이터베이스]

                    노드: 360개
                    - AnticancerDrug: 154
                    - Biomarker: 65
                    - BiomarkerTest: 45
                    - Cancer: 100

                    관계: 400개
                    - TARGETS: 120
                    - TESTED_BY: 85
                    - HAS_BIOMARKER: 200
```

---

## 📅 실행 일정

### Day 1 (오늘, 2025-11-07)

**오후 3시간**:
- [x] HINS 데이터 분석 완료
- [ ] 실행 계획서 작성 ← 현재
- [ ] Phase 1 스크립트 작성
- [ ] Phase 2 스크립트 작성

### Day 2 (내일, 2025-11-08)

**오전 4시간**:
- [ ] Phase 1 실행 (바이오마커 추출)
- [ ] Phase 2 실행 (HINS 파싱)
- [ ] Phase 3 스크립트 작성

**오후 4시간**:
- [ ] Phase 3 실행 (매핑)
- [ ] Phase 4 스크립트 작성
- [ ] Phase 4 실행 (Neo4j 임포트)

### Day 3 (2025-11-09)

**오전 2시간**:
- [ ] 검증 및 테스트
- [ ] 샘플 쿼리 작성
- [ ] 문서화

**총 예상 시간**: 13시간
**예상 완료**: 2025-11-09 (토)

---

## 💰 비용 추정

### GPT API 사용

| Phase | 작업 | 호출 횟수 | 단가 | 비용 |
|-------|-----|---------|-----|------|
| Phase 1 | 바이오마커 상세 정보 | 10-15건 | $0.05 | $0.5-0.75 |
| Phase 1 | 바이오마커 GPT 추출 | 20건 | $0.10 | $2.0 |
| Phase 3 | 매핑 검증 | 10-15건 | $0.05 | $0.5-0.75 |
| **총계** | - | 40-50건 | - | **$3-4** |

> 예상보다 낮음: 자동 매칭 성공률이 높을 것으로 예상

---

## 🎯 성공 지표

### 정량 지표

- [ ] Biomarker 노드 50개 이상
- [ ] BiomarkerTest 노드 35개 이상
- [ ] [:TARGETS] 관계 100개 이상
- [ ] [:TESTED_BY] 관계 50개 이상
- [ ] EDI 코드 커버리지 80% 이상
- [ ] SNOMED CT 매핑 35% 이상

### 정성 지표

- [ ] 3-hop 쿼리 성공 (Drug → Biomarker → Test)
- [ ] EDI 코드 기반 검색 가능
- [ ] SNOMED CT 기반 국제 표준 연계 확인
- [ ] 주요 바이오마커 9개 모두 매핑 완료

---

## 🔍 검증 계획

### 자동 검증

**1. 데이터 무결성**
```python
def validate_data_integrity():
    # 모든 biomarker_id가 unique한지
    # 모든 EDI 코드가 유효한지
    # 관계의 양쪽 노드가 모두 존재하는지
    pass
```

**2. 매핑 일관성**
```python
def validate_mapping_consistency():
    # HER2 바이오마커가 HER2 억제제와 연결되었는지
    # 각 바이오마커가 최소 1개 이상의 약물과 연결되었는지
    pass
```

**3. Neo4j 데이터 검증**
```cypher
-- 고아 노드 확인 (관계 없는 노드)
MATCH (b:Biomarker)
WHERE NOT (b)-[:TARGETS]-()
  AND NOT (b)-[:TESTED_BY]-()
RETURN count(b) as orphan_biomarkers

-- 3-hop 경로 카운트
MATCH path = (d:AnticancerDrug)-[:TARGETS]->(:Biomarker)-[:TESTED_BY]->(:BiomarkerTest)
RETURN count(path) as complete_paths
```

### 수동 검증 (10% 샘플링)

**샘플**: 주요 바이오마커 6개
- HER2 (유방암)
- EGFR (폐암)
- PD-L1 (면역항암제)
- BRCA1/2 (유방암, 난소암)
- ALK (폐암)
- KRAS (대장암)

**검증 항목**:
1. 바이오마커명 정확성
2. 연결된 약물 적절성
3. 검사 코드 유효성
4. SNOMED CT 매핑 정확성

---

## 🚧 리스크 및 대응

### 리스크 1: 바이오마커 추출 실패율 높음

**시나리오**: mechanism_of_action 정보 부족으로 추출 실패

**영향도**: 중
**발생 가능성**: 중

**대응**:
1. ATC Level 3 카테고리 활용 (백업)
2. GPT로 전체 약물 재검토
3. 외부 데이터 소스 (OncoKB, CIViC) 활용

### 리스크 2: HINS-바이오마커 매칭 오류

**시나리오**: 이름 불일치로 자동 매칭 실패

**영향도**: 중
**발생 가능성**: 중

**대응**:
1. 바이오마커 변형 사전 구축
2. GPT 검증 강화
3. 수동 검토 (10%)

### 리스크 3: Neo4j 성능 문제

**시나리오**: 400개 관계에서 쿼리 속도 저하

**영향도**: 저
**발생 가능성**: 저

**대응**:
1. 인덱스 최적화
2. 쿼리 최적화 (WITH, LIMIT)
3. 필요시 캐싱

---

## 📁 생성될 파일 목록

### 데이터 파일 (bridges/)

```
bridges/
├── biomarkers_extracted.json           # Phase 1 출력
├── biomarker_test_mappings.json        # Phase 3 출력
└── integration_stats.json              # 통계

data/hins/parsed/
└── biomarker_tests_structured.json     # Phase 2 출력
```

### 스크립트 파일 (scripts/)

```
scripts/
├── extract_biomarkers_from_drugs.py    # Phase 1
├── parse_hins_biomarker_tests.py       # Phase 2
├── map_biomarkers_to_tests.py          # Phase 3
└── neo4j/
    ├── import_biomarkers_and_tests.py  # Phase 4
    ├── validate_graph.py               # 검증
    └── sample_queries.py               # 샘플 쿼리
```

### 문서 파일 (docs/)

```
docs/
├── journal/
│   └── 2025-11-07_hins_integration_plan.md  # 현재 파일
└── reports/
    └── week2_completion_report.md           # 완료 보고서
```

---

## 🎓 학습 및 개선 사항

### 새로운 접근법

1. **역방향 추론**: 약물 → 바이오마커 역추출
2. **표준 매핑**: EDI ↔ SNOMED CT 국제 표준 연계
3. **3-hop 그래프**: Drug → Biomarker → Test 완전 경로

### 벤치마킹

- HINS 체계: 용어 표준화 + 계층적 분류
- 우리 강점: 최신 데이터 + LLM 활용

### 다음 개선 사항

1. 검사 급여 기준 연결 (Week 3)
2. 암종별 바이오마커 프로파일 (Week 4)
3. 임상시험 데이터 통합 (Week 5)

---

## 📞 체크포인트

### 사용자 확인 필요 사항

1. [ ] 실행 계획 승인
2. [ ] 타임라인 조정 필요 여부
3. [ ] GPT 사용 승인 ($3-4)
4. [ ] Phase별 우선순위 확인

### 다음 논의 사항

1. Week 3 목표 (급여 기준 연결)
2. 외부 데이터 소스 활용 여부
3. 검증 기준 및 샘플링 비율

---

**작성 완료**: 2025-11-07
**다음 단계**: 사용자 승인 후 Phase 1-2 스크립트 작성 시작
**예상 완료**: 2025-11-09 (토)

---

## ✅ 승인 대기

**작업 시작 조건**:
- [x] 실행 계획서 작성 완료
- [ ] 사용자 계획 검토 및 승인
- [ ] 스크립트 작성 시작

**다음 작업**: Phase 1-2 스크립트 설계 및 작성
