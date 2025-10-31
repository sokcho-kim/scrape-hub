# Scrape Hub

각종 스크래핑 프로젝트를 관리하는 통합 저장소입니다.

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

### 5. [HIRA 암질환 사용약제 및 요법](hira_cancer/README.md) 🆕

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

**항암제 사전 구축** (2025-10-31 Phase 1/4 완료):
- **접근법 전환**: 음차 유사도 → 코드 기반 매칭 (ATC 코드)
- **Ground Truth**: 약가 마스터 1.8M 레코드 → L01/L02 필터링
- **Phase 1 완료** (브랜드명/성분명 정제):
  - 항암제 추출: 154개 성분, 939개 브랜드명
  - 브랜드명 정제: 939/939 성공 (100%)
  - 한글 성분명 추출: 148/154 성공 (96.1%)
  - 출력: `bridges/anticancer_master_clean.json`
- **다음 단계**: Phase 2 (한글명 보완 + 염/기본형 분리) → Phase 3 (ATC 세분류) → Phase 4 (코드 기반 매칭)
- **핵심 원칙**: 신뢰도 최우선, 정확 매칭만, 퍼지/유사도 금지

**항암요법 데이터 파싱** (2025-10-30):
- 공고책자 PDF: 264페이지 → 498KB 텍스트 (248개 테이블) ✅
- 사전신청요법 엑셀: 659개 승인 요법 (구조화) ✅
- 약제명 추출: 124개 영문 + 202개 한글
- 치료 레짐: FOLFOX, FOLFIRI, R-CHOP, ABVD 등

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

### 7. [NCC 암정보 사전](ncc/README.md) 🆕

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
├── shared/                       # 공유 모듈
│   └── parsers.py                # 공통 파서 (Upstage API)
│
├── data/                         # 수집된 데이터 (프로젝트별)
│   ├── emrcert/                  # EMR 데이터 (CSV)
│   ├── hira_rulesvc/             # HIRA RULESVC 데이터 (HWP/PDF)
│   ├── hira/                     # HIRA 전자책 (PDF)
│   ├── hira_cancer/              # HIRA 암질환 데이터
│   │   ├── raw/                  # 원본 게시글 + 첨부파일 (HWP/PDF)
│   │   ├── parsed/               # 파싱된 Markdown + HTML (JSON)
│   │   └── parsed_preview/       # 텍스트 미리보기
│   ├── likms/                    # LIKMS 데이터 (TXT/JSON)
│   └── pharma/                   # Pharma 데이터
│
├── logs/                         # 실행 로그 (프로젝트별)
│   ├── emrcert/
│   ├── hira_rulesvc/
│   ├── hira/
│   ├── hira_cancer/
│   └── likms/
│
├── docs/                         # 프로젝트 문서
│   ├── plans/                    # 작업 계획서
│   ├── journal/                  # 작업 일지 (프로젝트별)
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
uv pip install playwright beautifulsoup4

# Playwright 브라우저 설치
playwright install chromium
```

### 2. 크롤러 실행

#### EMR 인증 크롤러
```bash
# 제품인증 수집
python -m emrcert.scrapers.product_certification

# 사용인증 수집
python -m emrcert.scrapers.usage_certification
```

#### HIRA 고시 문서 크롤러
```bash
# 전체 문서 수집
python -m hira_rulesvc.scrapers.law_scraper_v3
```

#### HIRA 전자책 크롤러
```bash
# PDF 품질 분석 (Phase 1)
python hira/analyze_ebooks.py
```

#### LIKMS 법령 크롤러
```bash
# 대법원 포털에서 법령 수집
python likms/scrapers/scourt_direct.py
```

#### HIRA 암질환 사용약제 크롤러
```bash
# 게시글 + 첨부파일 수집
python hira_cancer/scraper.py

# 첨부파일 파싱 (Upstage API)
python hira_cancer/parse_attachments.py --all

# 샘플 확인
python hira_cancer/view_parsed_samples.py
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
| **합계** | - | **9,991개** | - | ✅ 수집 완료 |

---

## 📚 문서

### 프로젝트별 문서
- [EMR 인증 크롤러](emrcert/README.md)
- [HIRA 급여기준 시스템](hira_rulesvc/README.md)
- [HIRA 전자책](hira/README.md)
- [HIRA 암질환 사용약제](hira_cancer/README.md)
- [LIKMS 법령 크롤러](likms/README.md)
- [NCC 암정보 사전](ncc/README.md)

### 작업 계획서
- [EMR 인증 계획](docs/plans/emrcert.md)
- [HIRA 고시 계획](docs/plans/hira_rulesvc.md)
- [항암제 사전 4-Phase 계획](docs/plans/anticancer_dictionary_phases.md) 🆕
- [약물 매칭 마스터 플랜](docs/plans/drug_matching_master_plan.md)

### 작업 일지
- [EMR 인증 일지](docs/journal/emrcert/)
- [HIRA 급여기준 시스템 일지](docs/journal/hira_rulesvc/)
- [HIRA 전자책 일지](docs/journal/hira/)
- [HIRA 암질환 일지](docs/journal/hira_cancer/)
- [LIKMS 법령 일지](docs/journal/likms/)
- [NCC 암정보 사전 일지](docs/journal/ncc/)

---

## 🛠️ 기술 스택

| 항목 | 기술 |
|------|------|
| 언어 | Python 3.x |
| 브라우저 자동화 | Playwright |
| HTML 파싱 | BeautifulSoup4 |
| 데이터 저장 | CSV, HWP, PDF |
| 패키지 관리 | uv |

---

## 🔄 프로젝트 타임라인

### EMR 인증 크롤러
| 날짜 | 작업 | 결과 |
|------|------|------|
| 2025-10-11 | HTML 파싱 버그 수정 | 필드 누락 문제 해결 |
| 2025-10-13 | 전체 데이터 재수집 | 4,214개 수집 완료 |

### HIRA 급여기준 시스템
| 날짜 | 작업 | 결과 |
|------|------|------|
| 2025-10-13 | 초기 탐색 및 구조 분석 | 트리 구조 파싱 |
| 2025-10-14 | V2 개발 (SEQ 방식) | 실패, 재설계 |
| 2025-10-16 | V3 완성 (폴더 방식) | 53개 자동 수집 |
| 2025-10-17 | 최종 완료 | 56개 수집 완료 (100%) |

### HIRA 전자책
| 날짜 | 작업 | 결과 |
|------|------|------|
| 2025-10-20 | PDF 수집 및 품질 분석 계획 | 8개 PDF (4,275p) 수집 완료 |

### LIKMS 법령 크롤러
| 날짜 | 작업 | 결과 |
|------|------|------|
| 2025-10-20 | 의료 관련 법령 수집 | 35개 법령 수집 완료 |

### HIRA 암질환 사용약제
| 날짜 | 작업 | 결과 |
|------|------|------|
| 2025-10-22 | 초기 스크래핑 | 구조 분석 완료 |
| 2025-10-23 | 전체 수집 | 484개 게시글 + 828개 첨부파일 |
| 2025-10-24 | 첨부파일 파싱 | 823개 파싱 완료 (4,948p, $49.48) |
| 2025-10-30 | 항암요법 데이터 파싱 | 공고책자 264p + 엑셀 659요법 완료 |
| 2025-10-31 | **접근법 전환** | 음차 유사도 → 코드 기반 (ATC) |
| 2025-10-31 | 약가 마스터 분석 | 1.8M → 154개 항암제 추출 |
| 2025-10-31 | Phase 1 완료 | 브랜드/성분명 정제 (939/154개) |

### NCC 암정보 사전
| 날짜 | 작업 | 결과 |
|------|------|------|
| 2025-10-29 | 전체 수집 | 3,543개 용어 수집 완료 (9분) |
| 2025-10-30 | LLM 분류 | 3가지 방식 비교 및 완료 (2시간 15분, $1.06) |

---

## 🚀 향후 계획

### 항암제 사전 구축 (Phase 2-4)
- [x] **Phase 1**: 브랜드명/성분명 정제 (완료)
- [ ] **Phase 2**: 한글 성분명 보완 + 염/기본형 분리
  - 누락 6개 한글명 보완
  - "아비라테론아세테이트" → 기본형 "아비라테론" + 염 "아세테이트"
- [ ] **Phase 3**: ATC 기반 분류 강화
  - L01/L02 세분류 (L01EA, L01EB, L01EF 등)
  - 보조 약제 추가 (진토제, 골전이 치료제 등)
- [ ] **Phase 4**: 코드 기반 매칭 구현
  - 브랜드 인덱스 구축
  - HIRA 텍스트 → ATC 코드 매핑 (정확 매칭만)
  - 지식그래프 노드 생성

### 데이터 활용
- [ ] 지식그래프 구축 (약제-질환-레짐 관계)
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

---

**최종 업데이트**: 2025-10-31
**총 수집 데이터**: 9,991개 + 9,223페이지
- EMR 인증: 4,214개
- HIRA RULESVC: 56개
- HIRA 전자책: 8개 (4,275p)
- HIRA 암질환: 484개 게시글 + 828개 첨부파일 (4,948p 파싱 완료)
- LIKMS: 35개
- NCC: 3,543개 (LLM 분류 완료, 평균 신뢰도 0.928)
- **항암제 마스터**: 154개 성분 + 939개 브랜드명 (약가 마스터 정제 완료)

**프로젝트 상태**: ✅ 수집 완료, 파싱 완료, LLM 분류 완료, 항암제 사전 Phase 1/4 완료, 지식그래프 구축 준비 중

**관련 문서**:
- [항암제 사전 4-Phase 계획](docs/plans/anticancer_dictionary_phases.md)
- [2025-10-31 작업 일지: 코드 기반 전환](docs/journal/hira_cancer/2025-10-31_code_based_pivot.md)
- [지식그래프 로드맵](docs/knowledge_graph_roadmap.md)
