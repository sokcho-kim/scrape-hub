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

### 5. [Pharma 프로젝트](pharma/README.md) 🆕

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
├── likms/                        # LIKMS 법령 크롤러
│   ├── scrapers/                 # 크롤러 모듈
│   └── README.md                 # 프로젝트 문서
│
├── pharma/                       # Pharma 프로젝트 (약제)
│   ├── scrapers/                 # 데이터 수집
│   ├── parsers/                  # PDF/Excel 파싱
│   └── README.md                 # 프로젝트 문서
│
├── data/                         # 수집된 데이터 (프로젝트별)
│   ├── emrcert/                  # EMR 데이터 (CSV)
│   ├── hira_rulesvc/             # HIRA RULESVC 데이터 (HWP/PDF)
│   ├── hira/                     # HIRA 전자책 (PDF)
│   └── likms/                    # LIKMS 데이터 (TXT/JSON)
│
├── logs/                         # 실행 로그 (프로젝트별)
│   ├── emrcert/
│   ├── hira_rulesvc/
│   ├── hira/
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
| **LIKMS** | 법령 텍스트 | 35개 | TXT/JSON | ✅ 완료 |
| **합계** | - | **4,313개** | - | ✅ 수집 완료 |

---

## 📚 문서

### 프로젝트별 문서
- [EMR 인증 크롤러](emrcert/README.md)
- [HIRA 급여기준 시스템](hira_rulesvc/README.md)
- [HIRA 전자책](hira/README.md)
- [LIKMS 법령 크롤러](likms/README.md)

### 작업 계획서
- [EMR 인증 계획](docs/plans/emrcert.md)
- [HIRA 고시 계획](docs/plans/hira_rulesvc.md)

### 작업 일지
- [EMR 인증 일지](docs/journal/emrcert/)
- [HIRA 급여기준 시스템 일지](docs/journal/hira_rulesvc/)
- [HIRA 전자책 일지](docs/journal/hira/)
- [LIKMS 법령 일지](docs/journal/likms/)

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

---

## 🚀 향후 계획

### 전처리 파이프라인
- [ ] Upstage Document Parse API 연동
- [ ] HWP/PDF → Markdown/JSON 변환
- [ ] 메타데이터 자동 태깅

### 데이터 활용
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
- LIKMS: 대법원 사법정보공개포털 (https://portal.scourt.go.kr/pgp)

---

**최종 업데이트**: 2025-10-20
**총 수집 데이터**: 4,313개 + 4,275페이지 (EMR 4,214개 + HIRA RULESVC 56개 + HIRA 전자책 8개/4,275p + LIKMS 35개)
**프로젝트 상태**: ✅ 수집 완료, 파싱 및 RAG 시스템 구축 진행 중
