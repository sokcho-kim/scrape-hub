# LIKMS 법령 크롤러

**Legislative Information Knowledge Management System Scraper**

국회 법률정보시스템(https://likms.assembly.go.kr/law)에서 법령 데이터를 수집하는 크롤러입니다.

---

## 📋 프로젝트 개요

### 목적
- 의료급여법 등 법령 텍스트를 국회 법률정보시스템에서 직접 수집
- HWP 파일 파싱 문제를 우회하여 깨끗한 텍스트 형식으로 확보
- RAG 시스템에 사용할 법령 데이터 구축

### 데이터 출처
- **사이트**: 국회 법률정보시스템
- **URL**: https://likms.assembly.go.kr/law
- **제공 형식**: HTML (웹 페이지)

---

## 🎯 수집 목표

### 우선순위 1: 의료급여 관련 법령 3종
- [x] 의료급여법 (법률) ✅
- [x] 의료급여법 시행령 (대통령령) ✅
- [x] 의료급여법 시행규칙 (보건복지부령) ✅

**상태**: ✅ 100% 완료 (3/3)

### 향후 확장
- [ ] 국민건강보험법
- [ ] 기타 의료 관련 법령

---

## 📂 프로젝트 구조

```
likms/
├── scrapers/
│   ├── __init__.py
│   ├── explore_likms.py          # 사이트 탐색 스크립트
│   └── law_scraper.py            # 법령 수집 크롤러 (TODO)
├── __init__.py
└── README.md

data/likms/
├── exploration/                   # 탐색 결과
│   ├── screenshots/               # 스크린샷
│   └── *.txt                      # 추출 테스트 파일
└── laws/                          # 수집된 법령 (TODO)
    ├── 의료급여법.txt
    ├── 의료급여법_시행령.txt
    └── 의료급여법_시행규칙.txt

logs/likms/
└── likms_*.log                    # 실행 로그
```

---

## 🚀 사용법

### 1. 사이트 탐색 (초기 단계)

```bash
python likms/scrapers/explore_likms.py
```

**기능**:
- 국회 법률정보시스템 접속
- "의료급여법" 검색 테스트
- 검색 결과 구조 분석
- 법령 상세 페이지 분석
- 텍스트 추출 방법 파악

**결과**:
- `data/likms/exploration/screenshots/` - 페이지 스크린샷
- `data/likms/exploration/*.txt` - 추출 테스트 텍스트
- `logs/likms/` - 상세 로그

### 2. 법령 수집 (개발 예정)

```bash
# TODO: 탐색 완료 후 구현
python likms/scrapers/law_scraper.py --law "의료급여법"
```

---

## 🛠️ 기술 스택

| 항목 | 기술 |
|------|------|
| 브라우저 자동화 | Playwright |
| 로깅 | shared.utils.logger |
| 저장 형식 | TXT, JSON (예정) |

---

## 📝 개발 진행 상황

### ✅ 완료
- [x] 프로젝트 구조 생성
- [x] 탐색 스크립트 구현 (`explore_likms.py`)

### 🚧 진행 중
- [ ] 사이트 탐색 실행 및 분석
- [ ] 검색/추출 메커니즘 파악

### 📋 예정
- [ ] 법령 수집 크롤러 구현
- [ ] 의료급여법 3종 수집
- [ ] 메타데이터 자동 태깅
- [ ] JSON 형식으로 저장

---

## 🔍 탐색 체크리스트

사이트 구조 파악을 위한 확인 항목:

- [ ] 검색 기능 작동 방식
  - [ ] 검색창 위치 및 selector
  - [ ] 검색 API 엔드포인트 (있는 경우)
  - [ ] 검색 결과 표시 형식

- [ ] 법령 상세 페이지
  - [ ] URL 패턴
  - [ ] 법령 텍스트 위치
  - [ ] HTML 구조

- [ ] 데이터 추출
  - [ ] 법령 제목
  - [ ] 법령 번호
  - [ ] 시행일
  - [ ] 본문 텍스트
  - [ ] 조문 구조

---

## 📊 예상 데이터 형식

```json
{
  "title": "의료급여법",
  "law_number": "법률 제20309호",
  "enacted_date": "2024-05-17",
  "law_type": "법률",
  "ministry": "보건복지부",
  "content": "제1조 (목적) 이 법은...",
  "articles": [
    {
      "number": "제1조",
      "title": "목적",
      "content": "이 법은..."
    }
  ],
  "scraped_at": "2025-10-18T12:00:00",
  "source_url": "https://likms.assembly.go.kr/law/..."
}
```

---

## 🤝 기여

HIRA 고시 문서 크롤러와 연계하여 의료 법령 데이터 통합 구축

---

**작성일**: 2025-10-18
**상태**: 🚧 개발 중 (탐색 단계)
