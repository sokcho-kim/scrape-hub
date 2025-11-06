# 바이오마커 추출 전략 분석 리포트

**작성일**: 2025-11-06
**작성자**: Claude Code
**프로젝트**: medi-claim 지식그래프 구축
**Phase**: Week 2 - 암종 및 바이오마커 구축

---

## 📋 Executive Summary

Week 2의 목표는 **암종(Cancer)과 바이오마커(Biomarker) 노드를 Neo4j에 구축**하는 것입니다. 이를 위해 수집된 데이터 소스(NCC, HIRA)를 분석한 결과, **직접 추출 방식보다 항암제 사전 기반 역추출 + GPT 보완 방식이 더 효과적**이라는 결론에 도달했습니다.

### 핵심 결론

```
✅ 권장 방법: 항암제 사전(154개) → 바이오마커 역추출 + GPT 보완
❌ 비권장: NCC/HIRA 데이터 직접 파싱
```

**예상 성과**:
- 바이오마커: **50-70개** (높은 정확도)
- 암종: **100개** (NCC 데이터 활용)
- 작업 시간: **2일** (vs 직접 파싱 5-7일)
- 비용: **$5-10** (GPT API)

---

## 1. 데이터 소스 분석

### 1.1 NCC 암정보 (107개 파일)

**위치**: `data/ncc/cancer_info/parsed/*.json`

**분석 결과**:
```
✅ 장점:
  - 100개 암종 정보 완비
  - 구조화된 JSON 형식
  - 한글 설명 풍부

❌ 단점:
  - 일반인 대상 → 바이오마커 상세 정보 부족
  - "HER2 수용체", "유전적 요인" 등 일반적 언급만 존재
  - 검사 방법, 양성 기준 등 임상 정보 미포함
```

**샘플 (유방암)**:
```json
{
  "name": "유방암",
  "content": {
    "sections": [
      {
        "heading": "치료방법",
        "content": "항호르몬치료는 조직검사 결과 여성 호르몬에 반응하는 유방암으로
                   진단되는 경우에 시행하고... 허투 수용체 (HER2 receptor)와 같은
                   표적치료에 대한 수용체가 발달되어 있는 환자의 경우..."
      }
    ]
  }
}
```

**바이오마커 추출 시도**:
- "HER2 receptor" 언급 → 하지만 검사 방법, 양성 기준 없음
- "여성 호르몬에 반응" → 구체적 마커명 없음 (HR, ER, PR)

### 1.2 HIRA 항암제 공고 (823개)

**위치**: `data/hira_cancer/parsed/chemotherapy/공고책자_20251001.json`

**분석 결과**:
```
✅ 장점:
  - 급여 기준에 바이오마커 명시 가능성 높음
  - 정책 문서 → 정확한 의학 용어 사용
  - 823개 공고 = 방대한 데이터

❌ 단점:
  - 한글 인코딩 문제 (CP949 vs UTF-8)
  - 2,069개 elements = 복잡한 구조
  - 테이블, HTML 혼재 → 파싱 난이도 높음
  - 바이오마커만 추출하기 어려움 (약제명, 암종, 급여 기준 혼재)
```

**인코딩 문제 샘플**:
```
원본: "의약품 급여목록 및 급여 상한금액표"
출력: "�ǰ�����ɻ��򰡿� ���� ��2025-210ȣ"
```

**구조 복잡도**:
- heading1, paragraph, table 등 다양한 category
- 페이지별 coordinates 정보
- HTML + Markdown + Text 중복 저장

### 1.3 항암제 사전 (154개) ✅

**위치**: `bridges/anticancer_master_classified.json`

**분석 결과**:
```
✅✅✅ 최적의 소스
  - 이미 구조화 완료
  - mechanism_of_action 필드에 바이오마커 정보 포함
  - ATC 분류로 약리학적 타겟 명확
  - 113개(73.4%) 작용기전 태깅 완료
```

**샘플 데이터**:
```json
{
  "ingredient_ko": "트라스투주맙",
  "atc_code": "L01FC01",
  "atc_level3": "L01FC",
  "atc_level3_name": "HER2 억제제",
  "mechanism_of_action": "HER2 표적",
  "therapeutic_category": "표적치료제"
}
```

**바이오마커 매핑 예시**:
| 항암제 | mechanism_of_action | → 바이오마커 |
|--------|---------------------|------------|
| 트라스투주맙 | HER2 표적 | HER2 |
| 오시머티닙 | EGFR 억제 | EGFR |
| 크리조티닙 | ALK 억제 | ALK |
| 펨브롤리주맙 | PD-1/PD-L1 억제 | PD-L1 |
| 올라파립 | PARP 억제 | BRCA1/2 |

---

## 2. 추출 방법론 비교

### 2.1 방법 A: NCC/HIRA 직접 파싱 ❌

**프로세스**:
```
NCC 100개 암종 파일 → GPT 분석 → 바이오마커 추출
HIRA 823개 공고 → 인코딩 수정 → 파싱 → 바이오마커 추출
```

**장점**:
- 원천 데이터 직접 활용
- 암종별 컨텍스트 보존

**단점**:
- ❌ 인코딩 문제 해결 필요 (1일 소요)
- ❌ 복잡한 구조 파싱 (2-3일 소요)
- ❌ 바이오마커 정보 불완전 (NCC)
- ❌ GPT 호출 비용 높음 (923개 문서 → $30-50)
- ❌ 정확도 낮음 (일반 설명문에서 추출)

**예상 결과**:
- 바이오마커: 20-30개 (불완전)
- 작업 시간: 5-7일
- 비용: $30-50
- 정확도: 60-70%

### 2.2 방법 B: 항암제 사전 역추출 + GPT 보완 ✅

**프로세스**:
```
Step 1: 항암제 154개 → mechanism_of_action 분석 → 바이오마커 추출
  예: "HER2 표적" → Biomarker: HER2

Step 2: GPT로 바이오마커 상세 정보 생성
  입력: HER2
  출력: {
    "name": "HER2",
    "full_name": "Human Epidermal growth factor Receptor 2",
    "type": "단백질",
    "test_methods": ["IHC", "FISH"],
    "positive_criteria": "IHC 3+ 또는 FISH 양성",
    "cancers": ["유방암", "위암"],
    "prognostic": true,
    "predictive": true
  }

Step 3: 암종별 바이오마커 빈도 GPT 보강
  예: 유방암 → HER2(20%), HR(70%), BRCA1/2(5-10%)
```

**장점**:
- ✅ 높은 정확도 (약제 사전 = 신뢰 가능한 소스)
- ✅ 이미 구조화된 데이터 활용
- ✅ 빠른 구현 (2일)
- ✅ 낮은 비용 ($5-10)
- ✅ 완전한 정보 (GPT 의학 지식 활용)

**단점**:
- GPT 생성 정보 검증 필요 (10% 샘플링)

**예상 결과**:
- 바이오마커: 50-70개 (높은 정확도)
- 작업 시간: 2일
- 비용: $5-10
- 정확도: 90%+

---

## 3. 추천 전략: 방법 B 상세

### 3.1 Phase 1: 바이오마커 자동 추출

**소스**: `anticancer_master_classified.json`

**추출 로직**:
```python
biomarkers = {}

for drug in anticancer_drugs:
    mechanism = drug['mechanism_of_action']
    atc_level3_name = drug['atc_level3_name']

    # 패턴 매칭
    if 'HER2' in mechanism or 'HER2' in atc_level3_name:
        biomarkers['HER2'] = {
            'source': 'mechanism',
            'drugs': [drug['ingredient_ko']]
        }

    if 'EGFR' in mechanism:
        biomarkers['EGFR'] = {...}

    # ... 50+ 바이오마커
```

**예상 추출 (주요 바이오마커)**:
```
표적치료제 타겟:
  - HER2, EGFR, ALK, ROS1, MET, RET, NTRK
  - BRAF, MEK, mTOR, BTK, JAK
  - VEGF/VEGFR, FGFR

면역 관문:
  - PD-1, PD-L1, CTLA-4

유전자 변이:
  - BRCA1/2, KRAS, NRAS, PIK3CA
  - dMMR, MSI-H

호르몬 수용체:
  - ER, PR, AR
```

### 3.2 Phase 2: GPT로 상세 정보 생성

**입력 (바이오마커명)**:
```
HER2
```

**GPT 프롬프트**:
```
다음 바이오마커에 대한 상세 정보를 JSON으로 생성하세요:

바이오마커: HER2

출력 형식:
{
  "name": "HER2",
  "full_name": "정식 명칭 (영문)",
  "full_name_ko": "정식 명칭 (한글)",
  "type": "단백질/유전자/기타",
  "test_methods": ["IHC", "FISH", ...],
  "positive_criteria": "양성 판정 기준",
  "negative_criteria": "음성 판정 기준",
  "cancers": ["유방암", "위암", ...],
  "frequency": {"유방암": "20%", "위암": "10-20%"},
  "prognostic": true/false,
  "predictive": true/false,
  "clinical_significance": "임상적 의의",
  "targeted_drugs": ["트라스투주맙", "페르투주맙", ...]
}
```

**출력 샘플**:
```json
{
  "name": "HER2",
  "full_name": "Human Epidermal growth factor Receptor 2",
  "full_name_ko": "인간 표피성장인자 수용체 2",
  "type": "단백질",
  "test_methods": ["IHC", "FISH", "ISH"],
  "positive_criteria": "IHC 3+ 또는 IHC 2+/FISH 양성",
  "negative_criteria": "IHC 0-1+ 또는 IHC 2+/FISH 음성",
  "cancers": ["유방암", "위암", "대장암", "방광암"],
  "frequency": {
    "유방암": "15-20%",
    "위암": "10-20%"
  },
  "prognostic": true,
  "predictive": true,
  "clinical_significance": "HER2 양성 환자는 항HER2 표적치료 대상",
  "targeted_drugs": ["트라스투주맙", "페르투주맙", "트라스투주맙 데룩스테칸"]
}
```

**비용 계산**:
- 바이오마커 50-70개
- GPT-4o: $2.50/1M input, $10/1M output
- 평균 입력: 200 tokens, 출력: 600 tokens
- 총 비용: (50 × 200 × $2.50 + 50 × 600 × $10) / 1,000,000 = **$0.33**
- 여유 포함: **$5-10**

### 3.3 Phase 3: 암종별 바이오마커 매핑

**소스**: NCC 100개 암종 + GPT 보완

**프로세스**:
```python
for cancer in ncc_cancers:
    cancer_name = cancer['name']  # "유방암"

    # GPT 프롬프트
    prompt = f"""
    {cancer_name}에서 임상적으로 중요한 바이오마커를 나열하고 빈도를 제시하세요.

    출력 형식:
    {{
      "cancer": "{cancer_name}",
      "biomarkers": [
        {{"name": "HER2", "frequency": "15-20%", "significance": "표적치료 대상"}},
        ...
      ]
    }}
    """
```

**예상 출력 (유방암)**:
```json
{
  "cancer": "유방암",
  "biomarkers": [
    {"name": "HER2", "frequency": "15-20%", "significance": "항HER2 치료 대상"},
    {"name": "ER", "frequency": "70-80%", "significance": "호르몬 치료 대상"},
    {"name": "PR", "frequency": "65-70%", "significance": "호르몬 치료 반응 예측"},
    {"name": "BRCA1", "frequency": "3-5%", "significance": "PARP 억제제 대상"},
    {"name": "BRCA2", "frequency": "2-3%", "significance": "PARP 억제제 대상"},
    {"name": "Ki-67", "frequency": "100%", "significance": "증식 지표"}
  ]
}
```

---

## 4. 구현 계획

### 4.1 스크립트 구조

```
scripts/
├── extract_biomarkers_from_drugs.py    # Phase 1: 항암제 → 바이오마커
├── enrich_biomarkers_with_gpt.py      # Phase 2: GPT 상세 정보
├── map_cancer_biomarkers.py           # Phase 3: 암종별 매핑
└── neo4j/
    ├── import_cancer_nodes.py         # Cancer 노드 생성
    ├── import_biomarker_nodes.py      # Biomarker 노드 생성
    └── create_biomarker_relations.py  # HAS_BIOMARKER 관계
```

### 4.2 Neo4j 스키마

#### Biomarker 노드
```cypher
(:Biomarker {
  name: String,                    // "HER2"
  full_name: String,               // "Human Epidermal growth factor Receptor 2"
  full_name_ko: String,            // "인간 표피성장인자 수용체 2"
  type: String,                    // "단백질"

  test_methods: [String],          // ["IHC", "FISH"]
  positive_criteria: String,
  negative_criteria: String,

  prognostic: Boolean,
  predictive: Boolean,
  clinical_significance: String,

  source: String                   // "drug_mechanism"
})
```

#### Cancer 노드 (NCC 기반)
```cypher
(:Cancer {
  name_ko: String,                 // "유방암"
  name_en: String,                 // "Breast Cancer"
  cancer_seq: String,              // "4757"

  category: String,                // "주요암"
  tags: [String],                  // ["주요암", "성인"]

  description: String,
  symptoms: [String],
  risk_factors: [String],

  ncc_url: String
})
```

#### HAS_BIOMARKER 관계
```cypher
(Cancer)-[:HAS_BIOMARKER {
  frequency: String,               // "15-20%"
  significance: String,            // "표적치료 대상"
  prognostic_value: String,
  predictive_value: String
}]->(Biomarker)
```

### 4.3 타임라인

**Day 1 (오늘 완료 가능)**:
- ✅ 전략 리포트 작성
- ⏳ Phase 1 스크립트 작성 및 실행
  - `extract_biomarkers_from_drugs.py`
  - 예상 출력: 50-70개 바이오마커 초안

**Day 2**:
- Phase 2: GPT로 바이오마커 상세 정보 생성
- Phase 3: 암종별 바이오마커 매핑
- Neo4j 임포트

---

## 5. 예상 결과

### 5.1 바이오마커 커버리지

```
예상 바이오마커: 50-70개

카테고리별 분포:
├─ 표적치료 타겟: 25-30개
│  └─ HER2, EGFR, ALK, ROS1, MET, RET, NTRK, BRAF, MEK, etc.
├─ 면역 관문: 3-5개
│  └─ PD-1, PD-L1, CTLA-4, LAG-3
├─ 유전자 변이: 10-15개
│  └─ BRCA1/2, KRAS, NRAS, PIK3CA, TP53, dMMR, MSI-H
├─ 호르몬 수용체: 3-5개
│  └─ ER, PR, AR
└─ 기타: 10-15개
   └─ Ki-67, PD-L1 TPS, TMB, etc.
```

### 5.2 암종 커버리지

```
암종: 100개 (NCC 데이터)

주요 12대 암 포함:
  ✅ 유방암, 폐암, 위암, 대장암, 간암, 췌장암
  ✅ 갑상선암, 전립선암, 신장암, 담낭/담도암
```

### 5.3 관계 (HAS_BIOMARKER)

```
예상 관계: 200-300개

예시:
  유방암 → HER2 (15-20%)
  유방암 → ER (70-80%)
  유방암 → BRCA1 (3-5%)
  폐암 → EGFR (40-50% in Asian)
  폐암 → ALK (3-5%)
  폐암 → PD-L1 (30-50%)
```

---

## 6. 검증 전략

### 6.1 자동 검증

**Cross-check**:
```python
# 항암제 → 바이오마커 → 항암제 순환 검증
for biomarker in biomarkers:
    # 이 바이오마커를 표적하는 약물 목록
    targeting_drugs = find_drugs_targeting(biomarker)

    # 원래 추출 소스 약물과 일치하는지 확인
    assert targeting_drugs == biomarker['source_drugs']
```

### 6.2 수동 샘플링 (10%)

**검증 항목**:
- [ ] 5개 바이오마커 의학 문헌 확인
- [ ] 10개 암종-바이오마커 매핑 확인
- [ ] GPT 생성 빈도 정보 검증

### 6.3 의학 전문가 리뷰 (선택)

Week 2 완료 후 샘플 검토 요청

---

## 7. 리스크 및 대응

| 리스크 | 확률 | 영향 | 대응 방안 |
|--------|------|------|----------|
| GPT 생성 정보 부정확 | 중 | 중 | 10% 샘플링 검증, 의학 문헌 참조 |
| 바이오마커 누락 | 중 | 중 | 수동 보완 (주요 마커 체크리스트) |
| 빈도 정보 과장 | 중 | 낮 | 범위로 표시 (예: "15-20%") |
| 암종별 매핑 불완전 | 낮 | 중 | NCC + 의학 지식 교차 검증 |

---

## 8. 대안 (Plan B)

만약 **방법 B가 불충분**하다면:

### Plan B1: 의학 온톨로지 활용
- **UMLS (Unified Medical Language System)** 활용
- **NCI Thesaurus** 바이오마커 데이터
- 라이선스: 무료 (계정 필요)

### Plan B2: 전문 데이터베이스
- **OncoKB**: 암 바이오마커 데이터베이스
- **CIViC**: Clinical Interpretations of Variants in Cancer
- 접근: API 또는 파일 다운로드

### Plan B3: 바이오마커 NER 모델
- **BioBERT** 또는 **PubMedBERT** 활용
- HIRA 공고 문서에서 NER 수행
- 예상 시간: 3-4일 추가

---

## 9. 결론 및 권고

### 최종 권고: 방법 B 채택

**이유**:
1. ✅ **높은 정확도**: 항암제 사전 = 신뢰 가능한 소스
2. ✅ **빠른 구현**: 2일 (vs 5-7일)
3. ✅ **낮은 비용**: $5-10 (vs $30-50)
4. ✅ **완전한 정보**: GPT 의학 지식 활용
5. ✅ **즉시 시작 가능**: 데이터 준비 완료

### 다음 단계

**오늘 (2025-11-06)**:
- [x] 전략 리포트 작성
- [ ] Phase 1 스크립트 작성
- [ ] 바이오마커 초안 생성 (50-70개)

**내일 (2025-11-07)**:
- [ ] Phase 2-3 실행
- [ ] Neo4j 임포트
- [ ] 검증 (10% 샘플링)

---

## 10. 부록

### 10.1 참고 자료

- WHO ATC/DDD Index: https://www.whocc.no/atc_ddd_index/
- NCI Thesaurus: https://ncithesaurus.nci.nih.gov/
- OncoKB: https://www.oncokb.org/
- CIViC: https://civicdb.org/

### 10.2 관련 문서

- `docs/MASTER_PLAN_cancer_knowledge_graph.md`
- `docs/journal/2025-11-06_anticancer_dictionary_complete.md`
- `bridges/anticancer_master_classified.json`

### 10.3 주요 바이오마커 체크리스트

**표적치료 (Targeted Therapy)**:
- [ ] HER2 (유방암, 위암)
- [ ] EGFR (폐암, 대장암)
- [ ] ALK (폐암)
- [ ] ROS1 (폐암)
- [ ] BRAF (흑색종, 대장암)
- [ ] KRAS (대장암, 폐암)
- [ ] NTRK (다양한 암종)
- [ ] MET (폐암, 위암)
- [ ] RET (갑상선암, 폐암)

**면역치료 (Immunotherapy)**:
- [ ] PD-L1 (폐암, 방광암 등)
- [ ] dMMR/MSI-H (대장암, 자궁내막암)
- [ ] TMB (Tumor Mutational Burden)

**호르몬 치료 (Hormone Therapy)**:
- [ ] ER (유방암)
- [ ] PR (유방암)
- [ ] AR (전립선암)

**유전성 암 (Hereditary Cancer)**:
- [ ] BRCA1/2 (유방암, 난소암)
- [ ] Lynch syndrome genes (대장암)

---

**문서 버전**: 1.0
**최종 수정일**: 2025-11-06
**승인 상태**: ⏳ 검토 대기

**다음 액션**: Phase 1 스크립트 작성 및 실행
