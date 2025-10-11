# scrape-hub

각종 스크래핑 프로젝트를 관리하는 통합 저장소입니다.

## 프로젝트 목록

### 1. EMR 인증 정보 크롤러

보건복지부 EMR 인증 현황 페이지에서 제품인증 및 사용인증 정보를 수집하는 크롤러입니다.

**📋 작업 계획서**: [docs/plans/emrcert.md](docs/plans/emrcert.md)

### 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 사용법

```bash
# 모든 인증 정보 크롤링 (제품인증 + 사용인증)
python main.py

# 제품인증만 크롤링
python main.py --type product

# 사용인증만 크롤링
python main.py --type usage

# 브라우저를 보면서 크롤링 (디버깅용)
python main.py --visible
```

### 주요 기능

- **자동 페이지네이션**: 모든 페이지를 자동으로 순회
- **체크포인트**: 중단 시 마지막 위치부터 재시작
- **중복 방지**: 인증번호 기준으로 중복 데이터 제거
- **일정 단위 저장**: 10개 데이터마다 자동 저장
- **에러 핸들링**: 오류 발생 시에도 수집된 데이터 보존

### 출력 파일

`data/` 폴더에 다음 CSV 파일들이 생성됩니다:

- `product_certifications.csv`: 제품인증 정보
- `product_certification_history.csv`: 제품인증 이력
- `usage_certifications.csv`: 사용인증 정보
- `usage_certification_history.csv`: 사용인증 이력

### 체크포인트

`checkpoint.json` 파일에 진행 상황이 저장됩니다.
처음부터 다시 시작하려면 이 파일을 삭제하세요.

### 로그

`logs/` 폴더에 실행 로그가 저장됩니다.

### 문서

`docs/` 폴더에 프로젝트 문서가 저장됩니다:
- `docs/plans/emrcert.md`: EMR 크롤링 작업 계획서
- `docs/guides/`: 사용 가이드 (향후 추가)
- `docs/api/`: API 문서 (향후 추가)

## 프로젝트 구조

```
scrape-hub/
├── emrcert/                      # EMR 크롤러 패키지
│   ├── scrapers/                 # 스크래퍼 모듈
│   │   ├── product_certification.py    # 제품인증 크롤러
│   │   └── usage_certification.py      # 사용인증 크롤러
│   └── utils/                    # 유틸리티 함수
│       ├── logger.py             # 로깅 설정
│       ├── checkpoint.py         # 체크포인트 관리
│       └── csv_handler.py        # CSV 저장/중복제거
│
├── data/                         # 수집된 데이터 (CSV)
│   ├── product_certifications.csv
│   ├── product_certification_history.csv
│   ├── usage_certifications.csv
│   └── usage_certification_history.csv
│
├── logs/                         # 실행 로그 (타임스탬프별)
│
├── docs/                         # 📚 프로젝트 문서
│   ├── plans/                    # 작업 계획서
│   │   └── emrcert.md           # EMR 크롤링 계획
│   ├── guides/                   # 사용 가이드 (향후)
│   └── api/                      # API 문서 (향후)
│
├── main.py                       # 메인 실행 스크립트
├── requirements.txt              # 의존성 패키지
├── checkpoint.json               # 크롤링 진행 상황
└── README.md                     # 프로젝트 설명서
```

## 폴더별 설명

### 📦 `emrcert/`
EMR 인증 크롤러의 핵심 코드가 있는 패키지입니다.
- `scrapers/`: 각 인증 타입별 크롤러 구현
- `utils/`: 로깅, 체크포인트, CSV 처리 등 공통 유틸리티

### 💾 `data/`
크롤링으로 수집된 CSV 데이터가 저장됩니다.
- 10개 항목마다 자동 저장
- 인증번호 기준 중복 제거

### 📝 `logs/`
실행 로그가 타임스탬프와 함께 저장됩니다.
- 형식: `{scraper_name}_YYYYMMDD_HHMMSS.log`

### 📚 `docs/`
프로젝트 관련 문서를 체계적으로 관리합니다.
- `plans/`: 각 프로젝트의 작업 계획 및 요구사항
- `guides/`: 사용 가이드 및 트러블슈팅
- `api/`: API 문서 및 모듈 레퍼런스

### 💾 `checkpoint.json`
크롤링 진행 상황을 저장하여 중단 시 재시작을 지원합니다.
- 마지막 처리 페이지 번호
- 처리 완료된 인증번호 목록
