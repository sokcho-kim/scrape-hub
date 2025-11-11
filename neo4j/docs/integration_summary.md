# 통합 의료 지식그래프 구축 완료

## 최종 통합 결과

### 노드 통계

| 노드 타입 | 개수 | 데이터 소스 | 설명 |
|---------|------|------------|------|
| Disease | 21,589 | KCD-9 | 한국 표준 질병 분류 |
| Procedure | 1,487 | KDRG v1.4 | 한국형 DRG 수가 체계 |
| Biomarker | 23 | 항암제 급여 기준 | 암 바이오마커 |
| Test | 575 | HINS EDI/LOINC/SNOMED | 진단검사 |
| Drug | 138 | ATC 분류 | 항암제 및 보조약물 |
| **Regimen** | **28** | **HIRA 급여 고시** | **화학요법 레지멘** |

### 관계 통계

| 관계 타입 | 개수 | 설명 |
|----------|------|------|
| HAS_BIOMARKER | 502 | Disease → Biomarker |
| TESTED_BY | 134 | Biomarker → Test |
| TARGETS | 71 | Drug → Biomarker |
| **TREATED_BY** | **618** | **Disease → Regimen** |
| **INCLUDES** | **88** | **Regimen → Drug** |

## HIRA Regimen 통합

### 정규화 결과

- **총 레지멘**: 38개 (원본 데이터)
- **KCD 매핑 성공률**: 100% (38/38)
- **약물 매핑 성공률**: 92.1% (35/38)
- **완전 매핑**: 92.1%

### 누락된 약물 (3개 레지멘, 7.9%)

1. **Platinum** (2회)
   - 일반 용어로 Carboplatin/Cisplatin 구분 불가
   - 원본 데이터 품질 이슈

2. **병용 약물 문자열** (1회)
   - "Gemcitabine   Cisplatin" 형태로 공백 구분
   - 개별 약물로 분리 필요

### Neo4j 통합 결과

- **Regimen 노드**: 28개 (중복 제거 후)
- **TREATED_BY 관계**: 618개
  - 질병(KCD) → 레지멘 매핑
  - 코드 기반 자동 확장 (C50 → C50.0, C50.1 등)
- **INCLUDES 관계**: 88개
  - 레지멘 → 약물(ATC) 매핑

## 데이터 경로

### 완전한 의료 의사결정 경로

```
질병(KCD)
  ↓ HAS_BIOMARKER
바이오마커
  ↓ TESTED_BY          ↑ TARGETS
진단검사(EDI)        약물(ATC)
                      ↑ INCLUDES
                   레지멘(HIRA)
                      ↑ TREATED_BY
                  질병(KCD)
```

## 주요 쿼리

### 1. 암종별 급여 인정 레지멘 조회

```cypher
MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)-[:INCLUDES]->(drug:Drug)
WHERE d.kcd_code STARTS WITH 'C50'  // 유방암
RETURN
    d.name_kr as 암종,
    r.regimen_type as 요법유형,
    tb.line as 치료라인,
    collect(drug.ingredient_ko) as 약물목록,
    r.announcement_no as 고시번호,
    r.announcement_date as 고시일자
```

### 2. 약물별 레지멘 사용 현황

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

### 3. 치료 라인별 통계

```cypher
MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)
WHERE d.is_cancer = true
RETURN
    d.name_kr as 암종,
    count(DISTINCT r) as 레지멘수,
    collect(DISTINCT tb.line) as 치료라인목록
ORDER BY 레지멘수 DESC
LIMIT 10
```

## 검증 결과

### 레지멘에 포함된 약물 TOP 10

| 약물 | 레지멘수 | 기전 |
|------|---------|------|
| 파클리탁셀 | 6 | 미세소관 안정화 |
| 시스플라틴 | 5 | DNA 손상 |
| 카르보플라틴 | 4 | DNA 손상 |
| 펨브롤리주맙 | 4 | PD-1/PD-L1 억제 |
| 카페시타빈 | 4 | 티미딜산 합성효소 억제 |
| 플루오로우라실 | 4 | 티미딜산 합성효소 억제 |

### 암종별 레지멘 수 TOP 5

| 암종 | 레지멘수 | 치료라인 |
|------|---------|---------|
| 다발골수종 | 5 | 2차, 5차 |
| 림프종 | 3 | 1차, 3차 |
| 유방암 | 3 | 2차, 3차 |
| 위암 | 3 | 2차 |
| 담도암 | 3 | 2차 |

## 기술적 특징

### 100% 코드 기반 매핑

- **KCD 코드**: WHO ICD-10 기반 공식 분류
- **ATC 코드**: WHO Collaborating Centre 기준
- **텍스트 유사도 사용 안 함**: 모든 매핑은 표준 코드 체계 기반

### 약물명 정규화

- 괄호 제거: "Cisplatin (FP)" → "cisplatin"
- 약어 처리: "5-FU" → "fluorouracil"
- 별칭 매핑: "Leucovorin" → "folinic acid"

### 추가된 약물 (12개)

| 약물 | ATC | 분류 |
|------|-----|------|
| Dexamethasone | H02AB02 | 스테로이드 |
| Prednisolone | H02AB06 | 스테로이드 |
| Thalidomide | L04AX02 | 면역억제제 |
| Folinic acid | V03AF03 | 해독제 |
| Pirtobrutinib | L01EL05 | BTK 억제제 |
| Amivantamab | L01FX23 | EGFR/MET 이중항체 |
| Tislelizumab | L01FF09 | PD-1 억제제 |
| Sacituzumab govitecan | L01FX17 | Trop-2 ADC |
| Pemigatinib | L01EX15 | FGFR 억제제 |
| Lanreotide | H01CB03 | 소마토스타틴 유사체 |
| Octreotide | H01CB02 | 소마토스타틴 유사체 |
| Lutetium oxodotreotide | V10XX04 | 방사성의약품 |

## 파일 구조

```
C:\Jimin\scrape-hub\
├── data/
│   └── hira_cancer/parsed/
│       └── drug_cancer_relations.json          # 원본 HIRA 데이터
├── bridges/
│   ├── hira_regimens_normalized.json           # 정규화된 레지멘
│   ├── cancer_type_to_kcd_official.json        # KCD 매핑 (41개)
│   ├── anticancer_master_classified.json       # 약물 DB (166개)
│   └── biomarkers_with_kcd.json                # 바이오마커 (23개)
├── neo4j/
│   ├── scripts/
│   │   ├── import_all_code_based.py            # 전체 통합 스크립트
│   │   └── import_regimens.py                  # Regimen 통합 스크립트
│   └── docs/
│       ├── comprehensive_schema.md              # 전체 스키마
│       ├── regimen_schema.md                    # Regimen 스키마
│       └── integration_summary.md               # 본 문서
├── analyze_hira_regimens.py                     # 정규화 스크립트
├── add_missing_drugs.py                         # 약물 추가 스크립트
└── verify_regimen_integration.py                # 검증 스크립트
```

## 다음 단계 제안

### 1. 데이터 보완

- [ ] Platinum 약물 상세화 (Carboplatin/Cisplatin 구분)
- [ ] 병용 약물 문자열 파싱 개선
- [ ] 바이오마커-약물 관계 확장 (TARGETS)

### 2. 기능 확장

- [ ] 치료 가이드라인 통합 (NCCN, ASCO)
- [ ] 임상시험 데이터 연결
- [ ] 부작용 정보 추가

### 3. 쿼리 개선

- [ ] 그래프 알고리즘 적용 (최단 경로, 중심성 분석)
- [ ] 추천 시스템 구축 (유사 레지멘 찾기)
- [ ] 시각화 대시보드 개발

## 결론

HIRA 화학요법 급여 데이터가 성공적으로 Neo4j 지식그래프에 통합되었습니다.

- **92.1%** 완전 매핑 달성
- **100%** 코드 기반 매핑
- **618개** 질병-레지멘 관계 생성
- **88개** 레지멘-약물 관계 생성

이제 질병 진단부터 바이오마커 검사, 약물 선택, 급여 인정 레지멘까지 **완전한 의료 의사결정 경로**를 그래프로 표현할 수 있습니다.

---

**생성일**: 2025-11-11
**데이터 기준일**: 2025년 10월 HIRA 고시
**매핑 방법**: 100% 코드 기반 (WHO ICD-10, WHO ATC)
