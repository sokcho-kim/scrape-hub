# 전체 데이터 수집 현황 (emrcert 제외) - 2025년 11월 10일

## 📊 전체 요약

| 구분 | 개수 |
|------|------|
| **총 데이터 소스** | 13개 |
| **총 폴더 수** | 13개 (emrcert 제외) |
| **총 파일 수** | 3,100+ 개 |
| **총 데이터 용량** | ~1.5GB |
| **최근 업데이트** | 2025-11-10 (health_kr 신규) |

---

## 🆕 신규 추가 (2025-11-10)

### health_kr
**출처**: 건강백과 (의약품 정보 백과사전)
**목적**: 일반인 대상 약물 정보, 의약품 용어사전

**폴더 구조**:
```
health_kr/
└── encyclopedia/
    ├── csv/              # CSV 데이터 8개
    ├── images/           # PDF 이미지 374개
    └── parsed_json/      # JSON 파싱 369개
```

**주요 파일**:
| 파일명 | 크기 | 건수 | 내용 |
|--------|------|------|------|
| drug_info.csv | - | 551건 | 약물 기본 정보 |
| products.csv | - | 594건 | 제품 정보 |
| terms.csv | - | 1,013건 | 의약품 용어 |
| unified_drug_info.csv | - | - | 통합 약물 정보 |
| dosage.csv | - | - | 용법용량 |
| precautions.csv | - | - | 주의사항 |
| side_effects.csv | - | - | 부작용 |
| medical_database.xlsx | 1.4MB | - | 통합 DB |
| item_*.pdf | 평균 250KB | 374개 | PDF 문서 |
| parsed_json/ | - | 369개 | JSON 파싱 |

**데이터 건수**:
- 약물 정보: 551건
- 제품 정보: 594건
- 용어 정보: 1,013건
- PDF 문서: 374개

**최종 수정**: 2025-11-10 11:38 (CSV), 11:52-13:37 (PDF, JSON)

**활용 가능성**:
- ✅ 일반인 대상 약물 설명
- ✅ 의약품 용어 사전
- ✅ 복약 지도 자료
- ✅ 약물 부작용/주의사항 DB

---

## 🏥 의료 표준 코드 (3개)

### 1. hins (보건의료정보표준관리시스템)
**출처**: https://hins.or.kr
**목적**: 국제 표준 코드 매핑 (KCD-SNOMED, EDI-SNOMED)

**폴더 구조**:
```
hins/
├── downloads/
│   ├── kcd/          # KCD-SNOMED CT 매핑 (2개)
│   ├── edi/          # EDI-SNOMED CT 매핑 (34개 분야)
│   └── medicine/     # 약제급여-SNOMED CT
└── parsed/
    ├── biomarker_tests_structured.json (298KB)
    └── biomarker_analysis.json
```

**주요 데이터**:
| 파일 | 크기 | 내용 |
|------|------|------|
| KCD7차-SNOMED_CT.xlsx | 9.1MB × 2 | KCD-SNOMED 매핑 125,440건 |
| 검사-SNOMED_CT.xlsx | 대용량 | EDI 검사 8,417개 → SNOMED 매핑 |
| 약제급여-SNOMED.xlsx | 대용량 | 약제 → SNOMED 매핑 |

**보유 코드**:
- **KCD 코드**: 14,403개 (암: 5,669개)
- **LOINC 코드**: 1,369개
- **SNOMED CT**: 1,426개
- **EDI 코드**: 4,111개

**활용 현황**:
- ✅ Neo4j Test 노드 (575개)
- ✅ 바이오마커-검사 매핑 (134개 관계)
- ✅ 100% 코드 기반 매핑 완료

**최종 수정**: 2025-11-07

---

### 2. kssc (통계청 한국표준질병사인분류)
**출처**: 통계청 (Korean Standard Classification of Diseases)
**목적**: KCD-8차, KCD-9차 질병 분류체계

**폴더 구조**:
```
kssc/
├── kcd-8th/
│   ├── KCD-8 1권.pdf (13MB)
│   ├── 질병코딩지침서.pdf (2.0MB)
│   ├── 질병코딩사례집.pdf (3.4MB)
│   └── parsed/
└── kcd-9th/
    ├── 제9차 1권.pdf (11MB)
    ├── 제9차 2권 지침서.pdf (3.9MB)
    ├── 제9차 3권 색인.pdf (9.7MB)
    ├── KCD-9 DB masterfile.xlsx (3.9MB)
    ├── 신구대조표.xlsx
    ├── 연계표.xlsx
    └── normalized/
```

**주요 데이터**:
| 버전 | 파일 | 건수 | 비고 |
|------|------|------|------|
| KCD-9 | DB masterfile.xlsx | 53,959행 | 최신 버전 |
| KCD-9 | normalized/ | 7개 JSON | 정규화 완료 |
| KCD-8 | parsed/ | JSON | 파싱 완료 |

**활용 계획**:
- 🎯 Phase 5: Cancer 노드 생성 (암 코드 5,669개)
- 🎯 Phase 6: Indication 노드 (질병-약물 연계)
- 🎯 Phase 7: KCD-SNOMED 매핑 연계

**최종 수정**: 2025-11-05

---

### 3. mfds (식품의약품안전처 대한약전)
**출처**: 식품의약품안전처
**목적**: 의약품 품질기준 (Korean Pharmacopoeia)

**폴더 구조**:
```
mfds/
├── parsed/
│   ├── en_02_General Notices.json (71KB)
│   ├── en_03_General Requirements.json (182KB)
│   ├── en_08_Index.json (553KB)
│   ├── ko_통칙.json (65KB)
│   └── ko_제제총칙.json (159KB)
├── parsed_pdf/
└── greek_drugs_master.json (25KB)
```

**데이터 건수**: 대한약전 항목 수백 건

**최종 수정**: 2025-11-03

---

## 💊 약물/약가 데이터 (4개)

### 1. hira_master (심평원 마스터 데이터)
**출처**: 건강보험심사평가원
**목적**: 수가코드, 약가, 상병코드 마스터

**폴더 구조**:
```
hira_master/
├── drug_dictionary_normalized.json (77MB)
├── drug_dictionary.json (71MB)
├── 수가반영내역(25.10.1.기준)_전체판.xlsb (13MB)
├── 20221101_20251101 적용약가파일.xlsx (8.7MB)
├── 배포용 상병마스터_250908.xlsx (4.6MB)
├── KDRG 분류집(신포괄지불제도용 ver1.4).pdf (17MB)
├── kdrg_parsed/
└── normalization/
```

**주요 데이터**:
| 파일 | 크기 | 건수 | 내용 |
|------|------|------|------|
| drug_dictionary_normalized.json | 77MB | 수만 건 | 정규화된 약품사전 |
| drug_dictionary.json | 71MB | 수만 건 | 원본 약품사전 |
| 수가반영내역.xlsb | 13MB | 수천 건 | 수가코드 |
| 적용약가파일.xlsx | 8.7MB | 수만 건 | 약가 정보 |
| 상병마스터.xlsx | 4.6MB | - | 상병코드 |
| KDRG 분류집.pdf | 17MB | - | DRG 분류 |

**활용 가능성**:
- ✅ 약품 검색/매칭
- ✅ 약가 조회
- ✅ 수가 계산
- ✅ DRG 분류

**최종 수정**: 2025-11-05

---

### 2. pharmalex_unity (약품 통합 DB)
**출처**: 여러 약품 DB 통합
**목적**: 유의어 사전, 통합 약품 데이터베이스

**폴더 구조**:
```
pharmalex_unity/
├── merged_pharma_data_20250915.csv (715MB)
├── 251030_Pass2_and_Next_Steps.md
├── 251030_하드레이어 구축.md
├── 진행상황.md
├── 250827_유의어사전.ipynb
└── MERGE_ANALYSIS_REPORT.md
```

**주요 데이터**:
| 파일 | 크기 | 건수 | 비고 |
|------|------|------|------|
| merged_pharma_data.csv | 715MB | 수십만 건 | 통합 약품 DB |

**최종 수정**: 2025-10-30

---

### 3. pharma (약제 급여기준)
**출처**: HIRA 전자책
**목적**: 요양급여 적용기준 - 약제

**폴더 구조**:
```
pharma/
├── raw/
└── parsed/upstage_test/
```

**진행 상황**: 샘플 페이지 10건 (테스트 단계)

**최종 수정**: 2025-10-22

---

### 4. hira_cancer (항암제 급여기준)
**출처**: 건강보험심사평가원
**목적**: 항암제 관련 고시, 화학요법 가이드, FAQ

**폴더 구조**:
```
hira_cancer/
├── parsed/
│   ├── announcement/      # 고시 250+개
│   ├── chemotherapy/      # 화학요법 가이드
│   ├── faq/              # FAQ
│   └── pre_announcement/ # 사전고시
├── drug_matching_results.json (50KB)
├── drug_cancer_relations.json (23KB)
└── raw/attachments/
```

**데이터 건수**: 고시/FAQ 약 250+건

**활용 현황**:
- ✅ 항암제-암종 관계
- ✅ 급여기준 매칭

**최종 수정**: 2025-10-29

---

## 📋 급여/청구 기준 (3개)

### 1. hira (전자책 시스템)
**출처**: 건강보험심사평가원 전자책
**목적**: 요양급여 기준, 심사청구 지침서

**폴더 구조**:
```
hira/
└── ebook/
    ├── 2025 의료급여 실무편람.pdf (27MB)
    ├── 2025년 1월판 건강보험요양급여비용.pdf (7.8MB)
    ├── 요양급여비용 청구방법.pdf (11MB)
    ├── 요양급여 적용기준(약제).pdf (11MB)
    ├── 자율점검 사례 모음집.pdf (7.9MB)
    ├── 자동차보험진료수가.pdf (7.1MB)
    └── hiradata_ver2.xlsx (4.7MB)
```

**데이터 건수**: PDF 7개 대용량 문서 (총 80MB)

**최종 수정**: 2025-11-06

---

### 2. hira_rulesvc (급여기준 고시)
**출처**: HIRA 급여기준 등록관리 시스템
**목적**: 급여기준 고시 HWP 문서

**폴더 구조**:
```
hira_rulesvc/
├── documents/   # HWP 68개
├── parsed/      # JSON 63개
├── debug/
├── temp_pdf/
└── temp_split/
```

**데이터 건수**: 고시 문서 68건

**주요 내용**:
- 요양급여비용 청구방법 고시
- 의료급여법 관련 고시
- 심사청구서 작성요령

**최종 수정**: 2025-11-03

---

### 3. hira_notice (공지사항)
**출처**: 건강보험심사평가원
**목적**: KCD 코드 관련 공지

**진행 상황**: 미수집 (빈 폴더)

**최종 수정**: 2025-10-27

---

## 📚 법령/용어 (2개)

### 1. likms (국가법령정보)
**출처**: 법제처 국가법령정보센터
**목적**: 의료 관련 법령 및 시행규칙

**폴더 구조**:
```
likms/
├── laws/          # 32개 법령 (JSON + TXT)
└── exploration/   # 탐색 데이터
```

**수집 법령 (16개)**:
| 법령 | 크기 | 비고 |
|------|------|------|
| 국민건강보험법 | 207KB | 법률+시행령+시행규칙 |
| 의료급여법 | 81KB | 법률+시행령+시행규칙 |
| 의료법 | 240KB | 법률+시행령+시행규칙 |
| 약사법 | 411KB | 법률+시행령+시행규칙 |
| 응급의료에관한법률 | 144KB | 법률+시행령+시행규칙 |
| 감염병의예방및관리에관한법률 | 220KB | |
| 노인장기요양보험법 | 128KB | |
| 산업재해보상보험법 | 187KB | |
| 자동차손해배상보장법 | 104KB | |
| 기타 7개 | - | |

**데이터 건수**: 법령 32건 (법률+시행령+시행규칙)

**최종 수정**: 2025-10-20

---

### 2. ncc (국립암센터)
**출처**: 국립암센터 암정보센터
**목적**: 암 용어사전, 암종별 정보

**폴더 구조**:
```
ncc/
├── cancer_dictionary/
│   ├── classified_terms.json (1.5MB)
│   ├── classified_terms_v2.json (1.6MB)
│   ├── llm_classified_dynamic.json (2.4MB)
│   ├── llm_reclassified.json (1011KB)
│   ├── drug_related_terms.json
│   └── term_statistics.json
└── cancer_info/   # 암종별 정보
```

**데이터 건수**: 암 용어 수천 건 (LLM 분류 완료)

**활용 가능성**:
- ✅ 암 용어 검색
- ✅ 약물 관련 용어 추출
- ✅ 암종별 정보
- 🎯 Cancer 노드 생성에 활용

**최종 수정**: 2025-10-30

---

## 📊 데이터 완성도 현황

### ✅ 수집 완료 (9개)
| 폴더 | 출처 | 건수 | 용량 | 파싱 |
|------|------|------|------|------|
| health_kr | 건강백과 | 1,013건 | - | ✅ |
| hins | 보건의료표준 | 125,440건 | 대용량 | ✅ |
| hira | HIRA 전자책 | 7개 PDF | 80MB | ✅ |
| hira_cancer | HIRA 항암제 | 250+건 | - | ✅ |
| hira_master | HIRA 마스터 | 수만 건 | 148MB | ✅ |
| kssc | 통계청 KCD | 53,959건 | - | ✅ |
| likms | 법제처 | 32건 | - | ✅ |
| ncc | 국립암센터 | 수천 건 | - | ✅ |
| pharmalex_unity | 약품 통합 | 수십만 건 | 715MB | ✅ |

### 🚧 진행 중 (2개)
| 폴더 | 진행률 | 비고 |
|------|--------|------|
| pharma | 10% | 샘플 페이지만 파싱 |
| mfds | 50% | 기본 파싱 완료 |

### ❌ 미수집 (1개)
| 폴더 | 상태 |
|------|------|
| hira_notice | 빈 폴더 |

### 🆕 신규 추가 (1개)
| 폴더 | 날짜 | 비고 |
|------|------|------|
| health_kr | 2025-11-10 | 오늘 추가됨 |

---

## 🔗 데이터 간 연계 가능성

### 현재 활용 중
```
hins (SNOMED) → biomarker_tests → Neo4j Test 노드
hira_cancer → drug_cancer_relations → Neo4j Drug-Biomarker
anticancer_master → ATC 코드 → Neo4j Drug 노드
```

### 활용 가능 (우선순위 높음)
```
1. kssc (KCD) → Cancer 노드 생성
   - 암 코드 5,669개 → 암종 분류

2. hins (KCD-SNOMED) → Cancer-Biomarker 연계
   - KCD-SNOMED 매핑 → 질병-검사 관계

3. ncc (암 용어) → Cancer 메타데이터
   - 암종별 설명, 용어

4. health_kr (약물 정보) → Drug 메타데이터
   - 일반인 대상 설명, 부작용

5. hira (급여기준) → Indication 노드
   - 적응증, 청구 기준
```

### 활용 가능 (장기)
```
6. likms (법령) → Regulation 노드
   - 보험급여 관련 법령 근거

7. pharmalex_unity → Drug 유의어
   - 약품명 정규화, 검색 개선

8. hira_master (약가) → Drug 경제성
   - 약가, 급여 정보
```

---

## 📈 데이터 활용 로드맵

### Phase 1: 현재 (완료)
- ✅ HINS SNOMED 매핑
- ✅ 바이오마커-검사 관계 (134개)
- ✅ 약물-바이오마커 관계 (71개)
- ✅ Neo4j 기본 그래프 (736 노드, 205 관계)

### Phase 2: Cancer 노드 (예정)
- 🎯 KCD 암 코드 5,669개 활용
- 🎯 NCC 암 용어 통합
- 🎯 Cancer-Biomarker 관계 구축
- 🎯 Drug-Cancer 관계 추가

### Phase 3: Indication 노드 (예정)
- 🎯 HIRA 급여기준 파싱
- 🎯 적응증 구조화
- 🎯 보험청구 조건 정의

### Phase 4: 메타데이터 보강 (장기)
- 📅 health_kr 약물 설명 추가
- 📅 법령 근거 연계
- 📅 약가/수가 정보 통합

---

## 💾 저장소 용량 분석

### 대용량 파일 (100MB 이상)
| 파일 | 크기 | 폴더 |
|------|------|------|
| merged_pharma_data.csv | 715MB | pharmalex_unity |
| drug_dictionary_normalized.json | 77MB | hira_master |
| drug_dictionary.json | 71MB | hira_master |

### 중용량 파일 (10-100MB)
| 파일 | 크기 | 폴더 |
|------|------|------|
| 2025 의료급여 실무편람.pdf | 27MB | hira |
| KDRG 분류집.pdf | 17MB | hira_master |
| 수가반영내역.xlsb | 13MB | hira_master |
| KCD-8 1권.pdf | 13MB | kssc |
| 제9차 1권.pdf | 11MB | kssc |
| 요양급여비용 청구방법.pdf | 11MB | hira |
| 요양급여 적용기준(약제).pdf | 11MB | hira |

### 총 용량
- **추정 총 용량**: ~1.5GB
- **가장 큰 폴더**: pharmalex_unity (715MB)
- **두 번째**: hira_master (148MB)
- **세 번째**: hira (80MB)

---

## 🎯 다음 단계 제안

### 즉시 가능 (기존 데이터만)
1. **KCD 암 코드 5,669개** → Cancer 노드 생성
2. **NCC 암 용어** → Cancer 메타데이터 추가
3. **health_kr 약물 정보** → Drug 설명/부작용 추가
4. **HIRA 급여기준** → Indication 노드

### 데이터 보완 필요
1. **pharma** 전체 파싱 (현재 10%)
2. **hira_notice** 수집
3. **KCD-9 Excel** 파싱 최적화

### 데이터 정제
1. **pharmalex_unity** 715MB → 정규화/압축
2. **hira_master** 약품사전 중복 제거
3. **hins** Excel → 데이터베이스 변환

---

**작성일**: 2025-11-10
**작성자**: Claude Code
**총 데이터 소스**: 13개 (emrcert 제외)
**총 파일**: 3,100+ 개
**총 용량**: ~1.5GB
**상태**: ✅ 현황 파악 완료
