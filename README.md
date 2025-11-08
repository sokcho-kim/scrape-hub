# Scrape Hub

각종 의료 데이터 수집 및 통합 프로젝트를 관리하는 통합 저장소입니다.

---

## 📋 프로젝트 목록

### 1. [EMR 인증 정보 크롤러](emrcert/README.md)

보건복지부 EMR 인증센터의 제품인증 및 사용인증 데이터 수집

**데이터 출처**: https://emrcert.mohw.go.kr

**수집 현황**:
- 제품인증: 155개
- 사용인증: 4,059개
- 총 수집: 4,214개
- 상태: ✅ 완료 (100%)

**상세 정보**: [emrcert/README.md](emrcert/README.md)

---

### 2. [HIRA 급여기준 시스템](hira_rulesvc/README.md)

건강보험심사평가원 급여기준 등록관리 시스템의 법령, 고시, 행정해석 문서 수집

**데이터 출처**: https://rulesvc.hira.or.kr

**수집 현황**:
- 법령 문서: 4개
- 고시기준: 13개
- 행정해석: 39개
- 총 수집: 56개 (HWP)
- 상태: ✅ 완료 (100%)

**상세 정보**: [hira_rulesvc/README.md](hira_rulesvc/README.md)

---

### 3. [HIRA 전자책](hira/README.md)

건강보험심사평가원 공식 전자책 (수가표, 청구지침, 급여기준)

**데이터 출처**: https://www.hira.or.kr/ra/ebook

**수집 현황**:
- 건강보험요양급여비용 (1,470p)
- 요양급여 적용기준(약제) (858p)
- 청구방법 및 작성요령 (848p)
- 의료급여 실무편람 (680p)
- 기타 실무 가이드 (419p)
- 총 수집: 8개 PDF (4,275p)
- 상태: ✅ 수집 완료, 파싱 진행 중

**상세 정보**: [hira/README.md](hira/README.md)

---

### 4. [LIKMS 법령 크롤러](likms/README.md)

대법원 사법정보공개포털에서 법령 텍스트 수집

**데이터 출처**: https://portal.scourt.go.kr/pgp

**수집 현황**:
- 의료급여법 3종 ✅
- 국민건강보험법 4종 ✅
- 총 수집: 7개 법령
- 상태: ✅ 완료 (100%)

**상세 정보**: [likms/README.md](likms/README.md)

---

### 5. [HIRA 암질환 사용약제 및 요법](hira_cancer/README.md)

건강보험심사평가원 암질환 게시판 데이터 수집 및 파싱

**데이터 출처**: https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030069000000

**수집 현황**:
- 공고 (announcement): 217개 게시글, 471개 첨부파일
- 공고예고 (pre_announcement): 232개 게시글, 299개 첨부파일
- FAQ: 117개 게시글, 58개 첨부파일
- 항암화학요법 (chemotherapy): 2개 게시글
- **총 수집**: 484개 게시글 + 828개 첨부파일 (4,948페이지)
- **상태**: ✅ 수집 완료, 파싱 완료 (99.4%)

**파싱 현황**:
- 파싱 성공: 823개 (99.4%)
- 파싱 실패: 4개 (timeout 2개, 413 error 2개)
- 출력 형식: Markdown + HTML
- 출력 크기: 19.2 MB (JSON)

**항암제 사전 구축** (Phase 1/4 완료):
- **접근법 전환**: 음차 유사도 → 코드 기반 매칭 (ATC 코드)
- **Ground Truth**: 약가 마스터 1.8M 레코드 → L01/L02 필터링
- **Phase 1 완료** (브랜드명/성분명 정제):
  - 항암제 추출: 154개 성분, 939개 브랜드명
  - 브랜드명 정제: 939/939 성공 (100%)
  - 한글 성분명 추출: 148/154 성공 (96.1%)
  - ATC 분류: L01.A-X 상세 분류 완료
  - 출력: `bridges/anticancer_master_classified.json`

**상세 정보**: [hira_cancer/README.md](hira_cancer/README.md)

---

### 6. [Pharma 프로젝트](pharma/README.md)

약제 관련 데이터 수집 및 파싱

**데이터 소스**:
- HIRA 약제급여목록
- 약가정보
- 약제 사용 기준 (PDF 표 파싱)

**현재 작업**:
- Upstage Document Parse API 테스트
- 복잡한 표 구조 파싱 (병합셀, 중첩)
- pdfplumber vs Upstage 비교 평가

**상태**: 🔄 초기 설정 완료, 테스트 준비 중

**상세 정보**: [pharma/README.md](pharma/README.md)

---

### 7. [NCC 암정보 사전](ncc/README.md)

국립암센터(NCC) 암정보 사전 수집 및 LLM 분류

**데이터 출처**: https://www.cancer.go.kr/lay1/program/S1T523C837/dictionaryworks/list.do

**수집 현황**:
- 암 용어 사전: 3,543개
- 수집 방식: Ajax 기반 동적 콘텐츠 추출
- 상태: ✅ 완료 (100%)

**분류 현황**:
- LLM 기반 자동 분류: 3,543개 (100%)
- 분류 카테고리: 9개 (약제, 암종, 치료법, 검사/진단, 증상/부작용, 유전자/분자, 임상시험/연구, 해부/생리, 기타)
- 평균 신뢰도: **0.928** (매우 높음)
- 사용 모델: GPT-4o-mini (Dynamic Few-shot)
- 비용: $1.06
- 상태: ✅ 분류 완료 (100%)

**상세 정보**: [ncc/README.md](ncc/README.md)

---

### 8. [HINS 바이오마커-검사 통합](docs/journal/) 🆕✨

**한국보건의료정보원(HINS) SNOMED CT 매핑 데이터를 활용한 항암제-바이오마커-검사 통합 시스템**

**데이터 출처**: https://hins.or.kr

**프로젝트 개요**:
- HINS EDI 검사 데이터와 항암제 사전 통합
- LOINC/SNOMED CT 국제 표준 코드 기반 매칭
- Neo4j 그래프 데이터베이스 통합 준비

**데이터 현황** (2025-11-07 완료):
- **바이오마커**: 23개 (v2.0, 항암제 + HINS 통합)
  - 항암제 기반: 17개
  - HINS 추가 발견: 6개 (KRAS, FLT3, IDH1/2, BRCA1/2)
- **검사**: 575개 (SNOMED CT 93.9% 매칭)
- **항암제**: 154개
- **바이오마커-검사 관계**: 996개
- **약물-바이오마커 관계**: 55개

**핵심 성과**:
- ✅ **LOINC/SNOMED CT 코드 기반 매칭** (업계 모범 사례)
- ✅ **3단계 매칭 전략**: LOINC (1순위) → SNOMED CT (2순위) → 키워드 (백업)
- ✅ **다층 데이터 소스 통합**: 항암제 사전 + HINS 검사
- ✅ **표준 코드 커버리지**: SNOMED CT 94.4%, LOINC 44.9%

**4-Phase 파이프라인**:

| Phase | 작업 | 출력 | 상태 |
|-------|------|------|------|
| **Phase 1** | 바이오마커 추출 (v2.0) | 23개 바이오마커 | ✅ 완료 |
| **Phase 2** | HINS 검사 파싱 (코드 기반) | 575개 검사 | ✅ 완료 |
| **Phase 3** | 바이오마커-검사 매핑 | 996개 관계 | ✅ 완료 |
| **Phase 4** | Neo4j 통합 | 그래프 DB | ✅ 스크립트 준비 |

**스크립트**:
```
scripts/
├── extract_biomarkers_from_drugs.py      # Phase 1 v1.0 (항암제만, 17개)
├── extract_biomarkers_from_drugs_v2.py   # Phase 1 v2.0 (통합, 23개) ⭐
├── parse_hins_biomarker_tests.py         # Phase 2 (LOINC/SNOMED CT) ⭐
├── map_biomarkers_to_tests.py            # Phase 3
└── (integrate_to_neo4j.py → neo4j/)      # Phase 4 (이동됨)
```

**Neo4j 구조**:
```
neo4j/
├── scripts/
│   └── integrate_to_neo4j.py            # 통합 스크립트
├── queries/
│   └── sample_queries.cypher            # 샘플 쿼리 모음
└── README.md                            # Neo4j 가이드
```

**데이터 파일**:
```
bridges/
├── biomarkers_extracted.json            # 17개 (v1.0)
├── biomarkers_extracted_v2.json         # 23개 (v2.0) ⭐
└── biomarker_test_mappings.json         # 996개 관계

data/hins/parsed/
└── biomarker_tests_structured.json      # 575개 검사
```

**문서**:
- [통합 계획서](docs/journal/2025-11-07_hins_integration_plan.md)
- [Phase 1-2 실행 보고서](docs/journal/2025-11-07_phase1-2_execution_report.md)
- [최종 완료 보고서](docs/journal/2025-11-07_hins_integration_complete.md)
- [Phase 1 버전 비교](docs/journal/2025-11-07_phase1_version_comparison.md)
- [작업 일지](docs/journal/2025-11-07_daily_report.md)

**상태**: ✅ Phase 1-4 완료, Neo4j 실행 대기

---

## 📂 레포지토리 구조

```
scrape-hub/
├── emrcert/                      # EMR 인증 크롤러
│   ├── scrapers/                 # 크롤러 모듈
│   ├── utils/                    # 유틸리티
│   └── README.md                 # 프로젝트 문서
│
├── hira_rulesvc/                 # HIRA 고시 문서 크롤러
│   ├── scrapers/                 # 크롤러 모듈
│   ├── config/                   # 설정 파일
│   ├── debug/                    # 디버깅 스크립트
│   └── README.md                 # 프로젝트 문서
│
├── hira/                         # HIRA 전자책 크롤러
│   ├── analyze_ebooks.py         # PDF 품질 분석
│   └── README.md                 # 프로젝트 문서
│
├── hira_cancer/                  # HIRA 암질환 사용약제 크롤러
│   ├── scraper.py                # 게시글 + 첨부파일 수집
│   ├── parse_attachments.py      # 첨부파일 파싱 (Upstage API)
│   ├── analyze_data.py           # 데이터 분석
│   ├── archive/                  # 구버전 스크립트
│   └── README.md                 # 프로젝트 문서
│
├── likms/                        # LIKMS 법령 크롤러
│   ├── scrapers/                 # 크롤러 모듈
│   └── README.md                 # 프로젝트 문서
│
├── pharma/                       # Pharma 프로젝트 (약제)
│   ├── scrapers/                 # 데이터 수집
│   ├── parsers/                  # PDF/Excel 파싱
│   └── README.md                 # 프로젝트 문서
│
├── ncc/                          # NCC 암정보 사전
│   ├── scraper.py                # 용어 사전 수집
│   ├── classify_llm.py           # LLM 기반 분류
│   └── README.md                 # 프로젝트 문서
│
├── scripts/                      # 통합 스크립트 ⭐
│   ├── extract_biomarkers_from_drugs.py        # Phase 1 v1.0
│   ├── extract_biomarkers_from_drugs_v2.py     # Phase 1 v2.0
│   ├── parse_hins_biomarker_tests.py           # Phase 2
│   └── map_biomarkers_to_tests.py              # Phase 3
│
├── neo4j/                        # Neo4j 그래프 DB ⭐
│   ├── scripts/
│   │   └── integrate_to_neo4j.py               # Phase 4 통합
│   ├── queries/
│   │   └── sample_queries.cypher               # 샘플 쿼리
│   └── README.md                               # Neo4j 가이드
│
├── bridges/                      # 통합 데이터 ⭐
│   ├── anticancer_master_classified.json       # 154개 항암제
│   ├── biomarkers_extracted.json               # 17개 (v1.0)
│   ├── biomarkers_extracted_v2.json            # 23개 (v2.0)
│   └── biomarker_test_mappings.json            # 996개 관계
│
├── data/                         # 수집된 데이터 (프로젝트별)
│   ├── emrcert/                  # EMR 데이터 (CSV)
│   ├── hira_rulesvc/             # HIRA RULESVC 데이터 (HWP/PDF)
│   ├── hira/                     # HIRA 전자책 (PDF)
│   ├── hira_cancer/              # HIRA 암질환 데이터
│   ├── hins/                     # HINS 데이터 ⭐
│   │   ├── downloads/            # 원본 Excel
│   │   └── parsed/               # 파싱된 JSON (575개 검사)
│   ├── likms/                    # LIKMS 데이터 (TXT/JSON)
│   ├── ncc/                      # NCC 데이터 (JSON)
│   └── pharma/                   # Pharma 데이터
│
├── docs/                         # 프로젝트 문서
│   ├── plans/                    # 작업 계획서
│   ├── journal/                  # 작업 일지 (프로젝트별)
│   │   ├── 2025-11-07_hins_integration_plan.md           ⭐
│   │   ├── 2025-11-07_phase1-2_execution_report.md       ⭐
│   │   ├── 2025-11-07_hins_integration_complete.md       ⭐
│   │   ├── 2025-11-07_phase1_version_comparison.md       ⭐
│   │   └── 2025-11-07_daily_report.md                    ⭐
│   └── samples/                  # 샘플 데이터
│
└── README.md                     # 이 파일
```

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# uv를 사용한 가상환경 생성
uv venv scraphub

# 가상환경 활성화
# Windows:
. scraphub/Scripts/activate
# Linux/Mac:
source scraphub/bin/activate

# 패키지 설치
uv pip install playwright beautifulsoup4 pandas

# Playwright 브라우저 설치
playwright install chromium
```

### 2. Neo4j 그래프 데이터베이스 실행 ⭐ (추천)

**전체 과정 약 5분 소요**

```bash
# Step 1: Docker Desktop 실행 확인
docker ps

# Step 2: Neo4j 컨테이너 시작 (.env 파일의 비밀번호 사용)
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password_here neo4j:latest

# Step 3: Neo4j 시작 대기 (약 10초)
timeout 30 bash -c "until docker logs neo4j 2>&1 | grep -q 'Started'; do sleep 1; done"

# Step 4: Python 패키지 설치
pip install neo4j python-dotenv

# Step 5: 연결 테스트
python neo4j/scripts/test_connection.py

# Step 6: 데이터 통합 (약 15초)
python neo4j/scripts/integrate_to_neo4j.py --clear-db

# Step 7: 브라우저에서 확인
# http://localhost:7474 접속
# Username: neo4j, Password: .env 파일의 비밀번호
```

**결과**: 730개 노드, 1,067개 관계

**자세한 가이드**: [neo4j/README.md](neo4j/README.md)

---

### 3. 주요 스크립트 실행

#### Phase 1: 바이오마커 추출
```bash
# v1.0 (항암제만, 17개)
python scripts/extract_biomarkers_from_drugs.py

# v2.0 (항암제 + HINS, 23개) - 권장
python scripts/extract_biomarkers_from_drugs_v2.py
```

#### Phase 2: HINS 검사 파싱
```bash
# LOINC/SNOMED CT 코드 기반 (575개)
python scripts/parse_hins_biomarker_tests.py
```

#### Phase 3: 바이오마커-검사 매핑
```bash
# 996개 관계 생성
python scripts/map_biomarkers_to_tests.py
```

#### Phase 4: Neo4j 통합
```bash
# 데이터 검증 (Neo4j 없이)
python neo4j/scripts/integrate_to_neo4j.py --skip-neo4j

# Neo4j 통합 (기존 데이터 삭제)
python neo4j/scripts/integrate_to_neo4j.py --clear-db
```

#### HIRA 암질환 사용약제
```bash
# 게시글 + 첨부파일 수집
python hira_cancer/scraper.py

# 첨부파일 파싱 (Upstage API)
python hira_cancer/parse_attachments.py --all
```

---

## 📊 수집 데이터 현황

| 프로젝트 | 데이터 타입 | 수집 건수 | 형식 | 상태 |
|---------|-----------|----------|------|------|
| **EMR 인증** | 제품인증 | 155개 | CSV | ✅ 완료 |
| **EMR 인증** | 사용인증 | 4,059개 | CSV | ✅ 완료 |
| **HIRA RULESVC** | 법령 문서 | 4개 | HWP | ✅ 완료 |
| **HIRA RULESVC** | 고시기준 | 13개 | HWP | ✅ 완료 |
| **HIRA RULESVC** | 행정해석 | 39개 | HWP/PDF | ✅ 완료 |
| **HIRA 전자책** | 수가/청구 가이드 | 8개 (4,275p) | PDF | ✅ 수집 완료 |
| **HIRA 암질환** | 게시글 | 484개 | HTML/JSON | ✅ 완료 |
| **HIRA 암질환** | 첨부파일 (원본) | 828개 | HWP/PDF | ✅ 완료 |
| **HIRA 암질환** | 첨부파일 (파싱) | 823개 (4,948p) | Markdown/HTML | ✅ 완료 (99.4%) |
| **LIKMS** | 법령 텍스트 | 35개 | TXT/JSON | ✅ 완료 |
| **NCC** | 암 용어 사전 | 3,543개 | JSON | ✅ 수집 완료 |
| **NCC** | LLM 분류 | 3,543개 | JSON | ✅ 분류 완료 |
| **HINS** | 바이오마커 | 23개 | JSON | ✅ 완료 (v2.0) |
| **HINS** | 검사 | 575개 | JSON | ✅ 완료 |
| **HINS** | 바이오마커-검사 관계 | 996개 | JSON | ✅ 완료 |
| **합계** | - | **11,585개** | - | ✅ 수집 완료 |

---

## 📚 문서

### 프로젝트별 문서
- [EMR 인증 크롤러](emrcert/README.md)
- [HIRA 급여기준 시스템](hira_rulesvc/README.md)
- [HIRA 전자책](hira/README.md)
- [HIRA 암질환 사용약제](hira_cancer/README.md)
- [LIKMS 법령 크롤러](likms/README.md)
- [NCC 암정보 사전](ncc/README.md)
- [Neo4j 그래프 데이터베이스](neo4j/README.md) ⭐

### HINS 바이오마커-검사 통합
- [통합 계획서](docs/journal/2025-11-07_hins_integration_plan.md)
- [Phase 1-2 실행 보고서](docs/journal/2025-11-07_phase1-2_execution_report.md)
- [최종 완료 보고서](docs/journal/2025-11-07_hins_integration_complete.md)
- [Phase 1 버전 비교](docs/journal/2025-11-07_phase1_version_comparison.md)
- [작업 일지](docs/journal/2025-11-07_daily_report.md)

### 작업 계획서
- [EMR 인증 계획](docs/plans/emrcert.md)
- [HIRA 고시 계획](docs/plans/hira_rulesvc.md)
- [항암제 사전 4-Phase 계획](docs/plans/anticancer_dictionary_phases.md)
- [약물 매칭 마스터 플랜](docs/plans/drug_matching_master_plan.md)

---

## 🛠️ 기술 스택

| 항목 | 기술 |
|------|------|
| 언어 | Python 3.13 |
| 브라우저 자동화 | Playwright |
| HTML 파싱 | BeautifulSoup4 |
| 데이터 처리 | Pandas, JSON |
| 표준 코드 | LOINC, SNOMED CT, ATC |
| 그래프 DB | Neo4j |
| 패키지 관리 | uv |

---

## 🚀 향후 계획

### Neo4j 그래프 데이터베이스 ✅ 완료 (2025-11-08)
- [x] Neo4j 실행 및 데이터 통합 (730개 노드, 1,067개 관계)
- [x] 샘플 쿼리 테스트
- [x] 실행 가이드 문서화 완료
- [ ] 그래프 시각화 및 분석
- [ ] v2.0 바이오마커 (23개) 통합

### 데이터 확장
- [ ] 추가 바이오마커 패턴 정의
- [ ] HINS 다른 데이터셋 탐색
- [ ] 약가 데이터 연동

### 지식그래프 구축
- [ ] 약제-질환-레짐 관계 구축
- [ ] 벡터 데이터베이스 적재
- [ ] RAG 시스템 구축
- [ ] 검색 API 개발

### 자동화
- [ ] 정기적 데이터 업데이트 스케줄링
- [ ] 변경 사항 모니터링
- [ ] 신규 데이터 알림 시스템

---

## 🤝 기여

버그 리포트나 개선 제안은 이슈로 등록해주세요.

---

## 📄 라이선스

이 프로젝트는 수집된 데이터의 2차 저작물 사용 권한을 포함하지 않습니다.

**데이터 출처**:
- EMR 인증: 보건복지부 EMR 인증센터 (https://emrcert.mohw.go.kr)
- HIRA RULESVC: 건강보험심사평가원 급여기준 시스템 (https://rulesvc.hira.or.kr)
- HIRA 전자책: 건강보험심사평가원 전자책 (https://www.hira.or.kr/ra/ebook)
- HIRA 암질환: 건강보험심사평가원 암질환 게시판 (https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030069000000)
- LIKMS: 대법원 사법정보공개포털 (https://portal.scourt.go.kr/pgp)
- NCC: 국립암센터 암정보 사전 (https://www.cancer.go.kr)
- HINS: 한국보건의료정보원 (https://hins.or.kr) ⭐

---

**최종 업데이트**: 2025-11-08
**총 수집 데이터**: 11,585개 + 9,223페이지

**프로젝트 현황**:
- EMR 인증: 4,214개 ✅
- HIRA RULESVC: 56개 ✅
- HIRA 전자책: 8개 (4,275p) ✅
- HIRA 암질환: 484개 게시글 + 828개 첨부파일 (4,948p) ✅
- LIKMS: 35개 ✅
- NCC: 3,543개 (LLM 분류 완료, 평균 신뢰도 0.928) ✅
- **항암제 마스터**: 154개 성분 + 939개 브랜드명 ✅
- **HINS 바이오마커**: 23개 (v2.0, 항암제 + HINS 통합) ✅
- **HINS 검사**: 575개 (SNOMED CT 93.9% 매칭) ✅
- **바이오마커-검사 관계**: 996개 ✅
- **Neo4j 그래프 DB**: 730개 노드, 1,067개 관계 ✅ (2025-11-08 통합 완료)

**프로젝트 상태**: ✅ 데이터 수집 완료, HINS 통합 완료, **Neo4j 그래프 DB 통합 완료**
