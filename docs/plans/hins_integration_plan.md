# HINS 데이터 통합 계획

**작성일**: 2025-11-07
**목적**: HINS의 EDI-SNOMED CT 매핑 체계를 벤치마킹하여 우리의 최신 데이터에 통합

---

## 📊 현황 분석

### 우리가 가진 최신 데이터

**1. Anticancer Dictionary (2025년 최신)**
- 154개 항암제 (Neo4j 저장 완료)
- mechanism_of_action: 113개 (73.4%)
- 표적치료제 70개 (바이오마커 포함 가능성 높음)
- 출처: 약가 데이터 + ATC 분류

**2. Week 2 목표**
- 바이오마커 50-70개 추출 예정
- 항암제 → 바이오마커 역추출 방식
- GPT로 상세 정보 보완

### HINS 데이터 (2020년 기준)

**강점**:
- EDI 코드 ↔ SNOMED CT 국제 표준 매핑
- 바이오마커 검사 39건 (실제 검사 코드)
- 8,417개 검사 항목 (체계적 분류)
- 보험 급여 코드 (실제 의료 현장 사용)

**바이오마커 검출**:
- HER2: 6건
- EGFR: 10건
- PD-L1: 2건
- BRCA1/2: 2건
- ALK: 11건
- ROS1: 2건
- KRAS: 3건
- BRAF: 2건
- NTRK: 1건

**한계**:
- 2020년 기준 (5년 전)
- 최신 바이오마커 미포함 가능성

---

## 🎯 통합 전략

### 핵심 아이디어

```
[우리 데이터]                    [HINS 체계]                  [통합 결과]

항암제 (154개)                 검사 코드 체계          약물-바이오마커-검사 트리플
    ↓                              ↓                          ↓
바이오마커 추출         ←─→    EDI ↔ SNOMED CT    →    국제 표준 + 보험 코드
(50-70개, 2025)              (39건, 2020)              (완전한 지식 그래프)
```

### 통합 효과

**Before (Week 2 기존 계획)**:
```cypher
(:AnticancerDrug)-[:TARGETS]->(:Biomarker)
```

**After (HINS 통합)**:
```cypher
(:AnticancerDrug)-[:TARGETS]->(:Biomarker)
                                   ↓
                             [:TESTED_BY]
                                   ↓
                            (:BiomarkerTest {
                              edi_code: "C5674010",
                              snomed_ct: "117617002",
                              test_name_ko: "면역조직화학검사-PD-L1",
                              test_method: "면역조직(세포)화학검사"
                            })
```

---

## 🔄 4단계 통합 프로세스

### Phase 1: 바이오마커 추출 (기존 계획 유지)

**출처**: 항암제 사전 154개
**목표**: 바이오마커 50-70개 추출
**방법**: mechanism_of_action → GPT 보완

**예시**:
```json
{
  "biomarker_name_en": "HER2",
  "biomarker_name_ko": "HER2 수용체",
  "biomarker_type": "protein",
  "related_drugs": ["트라스투주맙", "퍼투주맙"],
  "cancer_types": ["유방암", "위암"]
}
```

### Phase 2: HINS 검사 데이터 파싱 (NEW)

**출처**: `data/hins/downloads/edi/2장_19_20용어매핑테이블(검사).xlsx`
**목표**: 바이오마커 검사 정보 구조화

**스크립트**: `scripts/parse_hins_biomarker_tests.py`

**추출 정보**:
```json
{
  "edi_code": "C5674010",
  "test_name_ko": "면역조직(세포)화학검사[고형암]-Level Ⅱ_PD-L1",
  "snomed_ct_id": "117617002",
  "snomed_ct_name": "Immunohistochemistry",
  "test_category": "면역조직화학검사",
  "biomarker_detected": "PD-L1"
}
```

**처리 로직**:
1. Excel 파일 읽기 (pandas)
2. 바이오마커 키워드 매칭 (HER2, EGFR, PD-L1 등)
3. EDI 코드 + SNOMED CT 추출
4. 검사 방법 분류
5. JSON 출력

### Phase 3: 바이오마커-검사 매핑 (NEW)

**스크립트**: `scripts/map_biomarkers_to_tests.py`

**매핑 로직**:
```python
# 1. 우리가 추출한 바이오마커
biomarkers = load_json('biomarkers_extracted.json')  # Phase 1 결과

# 2. HINS 검사 데이터
hins_tests = load_json('hins_biomarker_tests.json')  # Phase 2 결과

# 3. 자동 매칭
for biomarker in biomarkers:
    # 키워드 기반 매칭
    matched_tests = find_tests_by_keyword(
        biomarker['biomarker_name_en'],
        hins_tests
    )

    # GPT로 검증 (optional)
    verified = verify_with_gpt(biomarker, matched_tests)

    # 관계 생성
    create_relationship(biomarker, verified)
```

**출력 예시**:
```json
{
  "biomarker": "HER2",
  "tests": [
    {
      "edi_code": "C5839046",
      "test_name": "체세포 유전자검사-형광법[HER2 Gene]",
      "snomed_ct": null,
      "match_confidence": 0.95
    },
    {
      "edi_code": "D4430",
      "test_name": "HER2 단백질",
      "snomed_ct": "414464004",
      "match_confidence": 1.0
    }
  ]
}
```

### Phase 4: Neo4j 통합 임포트 (NEW)

**스크립트**: `scripts/neo4j/import_biomarker_tests.py`

**노드 생성**:
```cypher
// 1. BiomarkerTest 노드 생성
CREATE (:BiomarkerTest {
  test_id: "EDI_C5674010",
  edi_code: "C5674010",
  test_name_ko: "면역조직화학검사-PD-L1",
  test_category: "면역조직화학검사",
  snomed_ct_id: "117617002",
  snomed_ct_name: "Immunohistochemistry",
  data_source: "HINS_2020",
  created_at: datetime()
})

// 2. 인덱스 생성
CREATE INDEX test_edi_code FOR (t:BiomarkerTest) ON (t.edi_code);
CREATE INDEX test_snomed FOR (t:BiomarkerTest) ON (t.snomed_ct_id);
```

**관계 생성**:
```cypher
// 바이오마커 → 검사
MATCH (b:Biomarker {biomarker_name_en: "PD-L1"})
MATCH (t:BiomarkerTest {edi_code: "C5674010"})
CREATE (b)-[:TESTED_BY {
  confidence: 1.0,
  source: "HINS_mapping"
}]->(t)

// 약물 → 바이오마커 → 검사 (3-hop)
MATCH (d:AnticancerDrug {ingredient_ko: "펨브롤리주맙"})
MATCH (b:Biomarker {biomarker_name_en: "PD-L1"})
MATCH (t:BiomarkerTest {edi_code: "C5674010"})
CREATE (d)-[:TARGETS]->(b)
CREATE (b)-[:TESTED_BY]->(t)
```

---

## 📐 Neo4j 스키마 확장

### 기존 스키마 (Week 1)

```
(:AnticancerDrug {
  atc_code, ingredient_ko, ingredient_en,
  mechanism_of_action, therapeutic_category
})
```

### 확장 스키마 (Week 2 + HINS)

```
(:AnticancerDrug)
       ↓ [:TARGETS]
(:Biomarker {
  biomarker_name_en, biomarker_name_ko,
  biomarker_type, protein_gene
})
       ↓ [:TESTED_BY]
(:BiomarkerTest {
  edi_code,                    # 건강보험 청구 코드
  snomed_ct_id,                # 국제 표준 코드
  test_name_ko, test_name_en,
  test_category, test_method,
  data_source, reference_year
})
       ↓ [:USED_FOR_DIAGNOSIS]
(:Cancer {
  cancer_name_ko, cancer_name_en,
  kcd_code
})
```

### 쿼리 예시

**1. 약물 → 검사 경로 찾기**:
```cypher
MATCH path = (d:AnticancerDrug {ingredient_ko: "트라스투주맙"})
             -[:TARGETS]->(b:Biomarker)
             -[:TESTED_BY]->(t:BiomarkerTest)
RETURN d.ingredient_ko, b.biomarker_name_ko,
       t.edi_code, t.test_name_ko, t.snomed_ct_id
```

**2. EDI 코드로 검색**:
```cypher
MATCH (t:BiomarkerTest {edi_code: "C5674010"})
      <-[:TESTED_BY]-(b:Biomarker)
      <-[:TARGETS]-(d:AnticancerDrug)
RETURN d.ingredient_ko as drug,
       b.biomarker_name_ko as biomarker,
       t.test_name_ko as test
```

**3. SNOMED CT 기반 검색 (국제 표준)**:
```cypher
MATCH (t:BiomarkerTest)
WHERE t.snomed_ct_id IS NOT NULL
RETURN t.snomed_ct_id, t.snomed_ct_name,
       count(*) as test_count
ORDER BY test_count DESC
```

---

## 💡 벤치마킹 포인트

### HINS에서 배울 점

**1. 용어 매핑 체계**
- EDI (국내 보험 코드) ↔ SNOMED CT (국제 표준)
- 양방향 매핑으로 국내/국제 호환성 확보

**2. 계층적 분류**
- 대분류 (장) → 중분류 (field) → 소분류 (test)
- 우리도 적용 가능: ATC Level 1-3 → 바이오마커 → 검사

**3. 데이터 품질**
- 각 검사마다 고유 코드 (EDI)
- 표준화된 명명 규칙
- 검사 방법 상세 기술

### 우리의 강점

**1. 최신 데이터 (2025)**
- HINS는 2020년 기준
- 우리는 최신 약가 + ATC 분류 사용

**2. 약물 중심 접근**
- HINS: 검사 → 용어 매핑
- 우리: 약물 → 바이오마커 → 검사 (임상 흐름)

**3. LLM 활용**
- HINS: 수동 매핑
- 우리: GPT로 자동 보완 + 검증

---

## 🎯 예상 성과

### 데이터 규모

```
노드:
  - AnticancerDrug: 154개
  - Biomarker: 50-70개 (new)
  - BiomarkerTest: 39개 (HINS) + α (new)
  - Cancer: 100개 (NCC)

관계:
  - [:TARGETS] (Drug → Biomarker): 100-150개
  - [:TESTED_BY] (Biomarker → Test): 50-100개
  - [:USED_FOR_DIAGNOSIS] (Test → Cancer): 100-200개

총 노드: ~360개
총 관계: ~400개
```

### 활용 가치

**1. 임상 의사결정 지원**
```
질문: "유방암 환자에서 트라스투주맙 사용 전 필요한 검사는?"
답변: HER2 검사 (EDI: D4430, SNOMED CT: 414464004)
```

**2. 보험 청구 연계**
- EDI 코드로 실제 보험 청구 가능
- 검사 급여 기준 연결 (Week 3에서 추가)

**3. 국제 표준 호환**
- SNOMED CT로 해외 데이터와 연동
- 논문, 임상시험 데이터 통합 가능

**4. RAG 시스템 고도화**
```
질문: "PD-L1 검사 코드가 뭐야?"
→ 그래프 검색: Biomarker(PD-L1) → BiomarkerTest
→ 답변: "EDI 코드 C5674010, SNOMED CT 117617002입니다."
```

---

## 📅 타임라인

### Day 1 (오늘 저녁)

**시간**: 3-4시간

- [x] HINS 데이터 바이오마커 분석 완료
- [ ] 통합 계획 문서 작성 ← 현재
- [ ] Phase 2 스크립트 작성 (`parse_hins_biomarker_tests.py`)
- [ ] HINS 검사 데이터 파싱 실행

### Day 2 (내일)

**시간**: 6-8시간

**오전** (4시간):
- [ ] Phase 1: 바이오마커 추출 (기존 계획)
  - `extract_biomarkers_from_drugs.py` 실행
  - 50-70개 바이오마커 초안 생성
  - GPT로 상세 정보 보완

**오후** (4시간):
- [ ] Phase 3: 바이오마커-검사 매핑
  - `map_biomarkers_to_tests.py` 실행
  - 자동 매칭 + GPT 검증

- [ ] Phase 4: Neo4j 통합
  - BiomarkerTest 노드 임포트
  - [:TESTED_BY] 관계 생성
  - 쿼리 테스트

### Day 3 (검증)

**시간**: 2-3시간

- [ ] 데이터 검증 (10% 샘플링)
- [ ] 쿼리 성능 테스트
- [ ] Week 2 완료 리포트 작성

**총 예상 시간**: 11-15시간
**예상 완료**: 2025-11-08

---

## 💰 비용 추정

### GPT API 사용

**Phase 1: 바이오마커 상세 정보 생성**
- 50-70개 × $0.10/건 = $5-7

**Phase 3: 매핑 검증**
- 50개 매칭 × $0.05/건 = $2-3

**총 예상 비용**: $7-10

---

## 🚧 리스크 및 대응

### 리스크 1: HINS 데이터 구 버전 (2020)

**문제**: 최신 바이오마커 (예: TMB, MSI) 누락 가능

**대응**:
1. HINS 데이터는 기본 프레임워크로 사용
2. 최신 바이오마커는 GPT + 문헌 조사로 보완
3. 추후 HINS 최신 데이터 추가 수집 고려

### 리스크 2: 바이오마커 이름 불일치

**문제**:
- HINS: "HER2 Gene"
- 우리: "HER2 수용체"
- 매칭 실패 가능성

**대응**:
1. 키워드 변형 리스트 작성
   ```python
   BIOMARKER_VARIANTS = {
       "HER2": ["HER2", "HER-2", "ERBB2", "HER2 Gene", "HER2 수용체"],
       "PD-L1": ["PD-L1", "PDL1", "PD L1", "CD274"]
   }
   ```
2. GPT로 매칭 검증
3. 수동 검토 (10%)

### 리스크 3: EDI 코드 변경

**문제**: 2020 → 2025 사이 EDI 코드 변경 가능

**대응**:
1. `reference_year: 2020` 메타데이터 명시
2. 추후 최신 EDI 코드 업데이트 계획
3. SNOMED CT는 국제 표준이라 안정적

---

## 📊 성공 지표

### 정량 지표

- [ ] BiomarkerTest 노드 30개 이상 생성
- [ ] [:TESTED_BY] 관계 50개 이상
- [ ] EDI 코드 커버리지 80% 이상
- [ ] SNOMED CT 매핑 60% 이상

### 정성 지표

- [ ] 약물 → 검사 3-hop 쿼리 성공
- [ ] EDI 코드 기반 검색 가능
- [ ] SNOMED CT 기반 국제 표준 연계 확인

---

## 📚 참고 자료

### HINS 분석 결과
- `data/hins/BIOMARKER_ANALYSIS.md`
- `data/hins/parsed/biomarker_analysis.json`

### Week 2 기존 계획
- `docs/reports/biomarker_extraction_strategy_20251106.md`
- `docs/journal/2025-11-06_week1_complete_week2_strategy.md`

### 데이터 소스
- HINS EDI: `data/hins/downloads/edi/*.xlsx`
- Anticancer: `bridges/anticancer_master_classified.json`
- NCC Cancer: `data/ncc/cancer_info/parsed/*.json`

---

## ✅ 결론

### 통합 전략 요약

1. **HINS 체계 벤치마킹**: EDI ↔ SNOMED CT 매핑 구조
2. **우리 강점 활용**: 최신 약물 데이터 + LLM
3. **완전한 경로 구축**: 약물 → 바이오마커 → 검사 → 암종
4. **실용성 확보**: 보험 청구 코드 + 국제 표준

### 핵심 가치

> "HINS의 검증된 체계 + 우리의 최신 데이터 = 실전 활용 가능한 지식그래프"

- 임상 의사결정 지원
- 보험 청구 연계
- 국제 표준 호환
- RAG 시스템 고도화

### Next Step

1. **즉시**: HINS 검사 데이터 파싱 스크립트 작성
2. **내일**: 바이오마커 추출 + 검사 매핑
3. **모레**: Neo4j 통합 + 검증

**예상 완료**: 2025-11-08 (금)
**예상 비용**: $7-10 (GPT API)
**예상 성과**: 360+ 노드, 400+ 관계

---

**작성 완료**: 2025-11-07
**작성자**: Claude Code + 지민
**문서 버전**: 1.0
