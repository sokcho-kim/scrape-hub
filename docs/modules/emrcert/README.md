# EMR 인증 정보 크롤러 (emrcert)

보건복지부 EMR 인증센터의 제품인증 및 사용인증 데이터 수집 프로젝트

---

## 📋 프로젝트 개요

**목적**: 보건복지부 EMR 인증센터의 제품인증 및 사용인증 정보 자동 수집

**데이터 출처**: https://emrcert.mohw.go.kr

**수집 완료일**: 2025-10-13

**총 수집 건수**: 4,214개 (제품인증 155개 + 사용인증 4,059개)

---

## 📊 수집 데이터 통계

| 구분 | 수집 건수 | 페이지 수 | 소요 시간 | 형식 |
|------|----------|----------|----------|------|
| **제품인증** | 155개 | 16페이지 | 약 4분 | CSV |
| **사용인증** | 4,059개 | 406페이지 | 약 2시간 4분 | CSV |
| **합계** | **4,214개** | **422페이지** | **약 2시간 8분** | CSV |

---

## 📂 프로젝트 구조

```
emrcert/
├── scrapers/                           # 크롤러 모듈
│   ├── __init__.py
│   ├── product_certification.py       # 제품인증 크롤러
│   └── usage_certification.py         # 사용인증 크롤러
├── utils/                              # 유틸리티
│   ├── checkpoint.py                  # 체크포인트 관리
│   └── csv_handler.py                 # CSV 파일 처리
└── README.md                           # 이 파일

data/emrcert/
├── product_certifications.csv          # 제품인증 메인 데이터 (155건)
├── product_certification_history.csv   # 제품인증 이력 데이터 (155건)
├── usage_certifications.csv            # 사용인증 메인 데이터 (4,059건)
└── usage_certification_history.csv     # 사용인증 이력 데이터 (4,058건)
```

---

## 📋 수집 데이터 필드

### 1. 제품인증 (Product Certification)

**메인 데이터 필드** (`product_certifications.csv`):
| 필드명 | 설명 | 예시 |
|--------|------|------|
| 인증번호 | 제품인증 고유번호 | 제-2025-00006 |
| 인증기간 | 인증 유효기간 | 2026-06-14 ~ 2029-06-13 |
| 인증제품명 | EMR 제품명 | PHIS |
| 버전 | 제품 버전 | 1.0 |
| 기관정보 | 인증 받은 기관 | 고려대학교의료원 |
| 제조업체 | 제품 제조업체 | (주)케이시스 |
| 인증기관 | 인증 수행 기관 | 한국보건의료정보원 |

**이력 데이터** (`product_certification_history.csv`):
- 제품인증의 변경 이력 정보
- 동일 구조, 시간별 변경 사항 추적

### 2. 사용인증 (Usage Certification)

**메인 데이터 필드** (`usage_certifications.csv`):
| 필드명 | 설명 | 예시 |
|--------|------|------|
| 인증번호 | 사용인증 고유번호 | 사-2024-00123 |
| 인증기간 | 인증 유효기간 | 2024-01-01 ~ 2027-12-31 |
| 인증제품명 | 사용 중인 EMR 제품명 | BestCare EMR |
| 버전 | 제품 버전 | 2.5 |
| 기관정보 | 사용 기관명 | 서울대학교병원 |
| 제조업체 | 제품 제조업체 | (주)메디케어솔루션 |
| 인증기관 | 인증 수행 기관 | 한국보건의료정보원 |

**이력 데이터** (`usage_certification_history.csv`):
- 사용인증의 변경 이력 정보
- 동일 구조, 시간별 변경 사항 추적

---

## 🔧 사용 방법

### 1. 환경 설정

```bash
# Python 가상환경 생성 및 활성화 (uv 사용)
uv venv scraphub
. scraphub/Scripts/activate  # Windows
# source scraphub/bin/activate  # Linux/Mac

# 패키지 설치
uv pip install playwright beautifulsoup4

# Playwright 브라우저 설치
playwright install chromium
```

### 2. 크롤러 실행

```bash
# 가상환경 활성화 (이미 활성화된 경우 생략)
. scraphub/Scripts/activate

# 제품인증 크롤러 실행
python -m emrcert.scrapers.product_certification

# 사용인증 크롤러 실행
python -m emrcert.scrapers.usage_certification
```

### 3. 실행 결과 확인

```bash
# CSV 파일 확인
ls data/emrcert/

# 데이터 건수 확인
wc -l data/emrcert/*.csv
```

---

## 🛠️ 주요 기능

### 1. 자동 페이지네이션
- 전체 페이지 자동 탐색
- 마지막 페이지까지 순회

### 2. 체크포인트 시스템
- 페이지 단위로 진행 상황 저장 (`checkpoint.json`)
- 중단 시 이어서 실행 가능
- 중복 데이터 자동 제거

### 3. 안정적인 에러 처리
- 개별 항목 실패 시 건너뛰고 계속 진행
- 페이지 실패 시 재시도 로직
- 최종 정상 종료 보장

### 4. 효율적인 데이터 저장
- 10개 항목마다 버퍼링하여 CSV 파일에 저장
- I/O 최적화로 성능 향상
- 중복 제거 후 최종 저장

---

## 📈 성능 지표

### 처리 속도
- **제품인증**: 페이지당 약 15초 (16페이지 / 4분)
- **사용인증**: 페이지당 약 18초 (406페이지 / 124분)
- **평균**: 페이지당 약 18초

### 수집 타임라인 (사용인증 기준)
| 진행률 | 페이지 | 예상 소요 시간 |
|--------|--------|---------------|
| 25% | 100 페이지 | 약 25분 |
| 50% | 200 페이지 | 약 50분 |
| 75% | 300 페이지 | 약 75분 |
| 100% | 406 페이지 | 약 124분 |

---

## 🐛 트러블슈팅

### 1. HTML 파싱 버그 수정 (2025-10-11)

**문제**:
- "인증제품명"과 "버전" 필드가 비어있는 현상

**원인**:
- HTML 테이블의 TH-TD 쌍 단위 처리 로직 오류

**해결**:
```python
# 수정 전
for header, value in zip(headers, values):
    data[header] = value

# 수정 후
# TH-TD 쌍을 순서대로 매칭하도록 개선
```

**결과**:
- 모든 필드가 정상적으로 수집됨
- 2025-10-13 전체 데이터 재수집 완료

### 2. 모듈 실행 블록 누락 (2025-10-13)

**문제**:
- `python -m emrcert.scrapers.product_certification` 실행 시 아무것도 실행되지 않음

**원인**:
- `if __name__ == '__main__':` 블록 누락

**해결**:
```python
if __name__ == '__main__':
    scraper = ProductCertificationScraper(headless=True)
    scraper.run()
```

---

## 📊 데이터 품질

### 수집 완료율
- **제품인증**: 100% (155/155개)
- **사용인증**: 100% (4,059/4,059개)

### 필드 완성도
- ✅ 인증번호: 100%
- ✅ 인증기간: 100%
- ✅ 인증제품명: 100% (버그 수정 후)
- ✅ 버전: 100% (버그 수정 후)
- ✅ 기관정보: 100%
- ✅ 제조업체: 100%
- ✅ 인증기관: 100%

---

## 🚀 향후 계획

### 데이터 활용
- [ ] 수집된 데이터 분석
- [ ] 인증 트렌드 분석
- [ ] 제조업체별 통계
- [ ] 데이터베이스 저장

### 자동화
- [ ] 정기적인 데이터 업데이트 스케줄링
- [ ] 변경 사항 모니터링
- [ ] 신규 인증 알림 시스템

### 전처리
- [ ] CSV → JSON 변환
- [ ] 메타데이터 추가 (수집일, 버전 등)
- [ ] 데이터 검증 자동화

---

## 📚 관련 문서

### 작업 일지
- [2025-10-11: 버그 수정](../docs/journal/emrcert/2025-10-11_emrcert_bugfix.md)
- [2025-10-13: 전체 재수집](../docs/journal/emrcert/2025-10-13_emrcert_fullscrape.md)

---

## 🔗 데이터 출처

### 웹사이트
- **메인**: https://emrcert.mohw.go.kr
- **제품인증**: https://emrcert.mohw.go.kr/certifiState/productCertifiStateList.es?mid=a10106010000
- **사용인증**: https://emrcert.mohw.go.kr/certifiState/useCertifiStateList.es?mid=a10106020000

### 운영 기관
- **보건복지부 EMR 인증센터**
- 주관: 한국보건의료정보원

---

## 📝 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.x |
| 브라우저 자동화 | Playwright |
| HTML 파싱 | BeautifulSoup4 |
| 데이터 저장 | CSV (pandas) |
| 환경 관리 | uv (Python package manager) |

---

## 🤝 기여

버그 리포트나 개선 제안은 이슈로 등록해주세요.

---

## 📄 라이선스

이 프로젝트는 수집된 데이터의 2차 저작물 사용 권한을 포함하지 않습니다.
데이터 출처: 보건복지부 EMR 인증센터 (https://emrcert.mohw.go.kr)

---

## 📊 주요 통계 요약

| 항목 | 값 |
|------|-----|
| 총 수집 건수 | 4,214개 |
| 제품인증 | 155개 |
| 사용인증 | 4,059개 |
| 총 페이지 | 422페이지 |
| 총 소요 시간 | 약 2시간 8분 |
| 평균 처리 속도 | 페이지당 18초 |
| 데이터 형식 | CSV (4개 파일) |
| 수집 완료율 | 100% |
| 필드 완성도 | 100% |

---

**최종 업데이트**: 2025-10-13
**프로젝트 상태**: ✅ 완료 (100%)
