# scrape-hub

각종 스크래핑 프로젝트를 관리하는 통합 저장소입니다.

## 프로젝트 목록

### 1. EMR 인증 정보 크롤러

보건복지부 EMR 인증 현황 페이지에서 제품인증 및 사용인증 정보를 수집하는 크롤러입니다.

**📋 작업 계획서**: [docs/plans/emrcert.md](docs/plans/emrcert.md)
**📖 작업 일지**: [docs/journal/](docs/journal/)

### 설치

```bash
# 가상환경 생성 (권장)
python -m venv scraphub

# 가상환경 활성화
# Windows:
scraphub\Scripts\activate
# Linux/Mac:
source scraphub/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 사용법

#### 방법 1: 메인 스크립트 실행 (권장)

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

#### 방법 2: 개별 모듈 실행

```bash
# 제품인증 크롤러만 실행
python -m emrcert.scrapers.product_certification

# 사용인증 크롤러만 실행
python -m emrcert.scrapers.usage_certification
```

### 주요 기능

- **자동 페이지네이션**: 모든 페이지를 자동으로 순회
- **체크포인트**: 중단 시 마지막 위치부터 재시작
- **중복 방지**: 인증번호 기준으로 중복 데이터 제거
- **일정 단위 저장**: 10개 데이터마다 자동 저장
- **에러 핸들링**: 오류 발생 시에도 수집된 데이터 보존
- **로깅**: 타임스탬프별 상세 실행 로그

### 출력 파일

`data/emrcert/` 폴더에 다음 CSV 파일들이 생성됩니다:

- `product_certifications.csv`: 제품인증 메인 정보 (~155개)
- `product_certification_history.csv`: 제품인증 이력 정보
- `usage_certifications.csv`: 사용인증 메인 정보 (~4,060개)
- `usage_certification_history.csv`: 사용인증 이력 정보

**총 수집 데이터**: 약 4,215개 인증 정보

### 데이터 구조

#### 제품인증/사용인증 메인 데이터
- 인증번호
- 인증기간
- 인증제품명
- 버전
- 기관정보
- 구분 (의료기관/제조업체)
- 대표자
- 주소
- 연락처
- 기타 정보

#### 인증 이력 데이터
- 인증번호
- 인증제품명
- 버전
- 인증일자
- 만료일자

### 체크포인트

`checkpoint_emrcert.json` 파일에 진행 상황이 저장됩니다.
처음부터 다시 시작하려면 이 파일을 삭제하세요.

```json
{
  "product_cert": {
    "last_page": 0,
    "processed_ids": []
  },
  "usage_cert": {
    "last_page": 0,
    "processed_ids": []
  }
}
```

### 로그

`logs/emrcert/` 폴더에 실행 로그가 저장됩니다.
- 형식: `{scraper_name}_YYYYMMDD_HHMMSS.log`
- 예시: `product_certification_20251013_090528.log`

### 문서

`docs/` 폴더에 프로젝트 문서가 저장됩니다:
- `docs/plans/emrcert.md`: EMR 크롤링 작업 계획서
- `docs/journal/emrcert/`: 작업 일지 및 버그 수정 기록
  - `2025-10-11_emrcert_bugfix.md`: HTML 테이블 파싱 버그 수정
  - `2025-10-13_emrcert_fullscrape.md`: 전체 데이터 재수집 작업

### 성능 지표

| 항목 | 제품인증 | 사용인증 |
|------|---------|---------|
| 총 페이지 | 16 | 406 |
| 수집 항목 | ~155개 | ~4,060개 |
| 소요 시간 | ~4분 | ~2시간 |
| 페이지당 속도 | ~15초 | ~18초 |

**총 소요 시간**: 약 2시간 8분

## 프로젝트 구조

```
scrape-hub/
├── emrcert/                      # EMR 크롤러 패키지
│   └── scrapers/                 # 스크래퍼 모듈
│       ├── product_certification.py    # 제품인증 크롤러
│       └── usage_certification.py      # 사용인증 크롤러
│
├── shared/                       # 공통 유틸리티
│   └── utils/                    # 유틸리티 함수
│       ├── logger.py             # 로깅 설정 (프로젝트별 경로 지원)
│       ├── checkpoint.py         # 체크포인트 관리
│       └── csv_handler.py        # CSV 저장/중복제거
│
├── data/                         # 수집된 데이터 (프로젝트별)
│   ├── emrcert/                  # EMR 크롤러 데이터
│   │   ├── product_certifications.csv
│   │   ├── product_certification_history.csv
│   │   ├── usage_certifications.csv
│   │   └── usage_certification_history.csv
│   └── hira_rulesvc/             # HIRA 규칙 서비스 데이터 (향후)
│
├── logs/                         # 실행 로그 (프로젝트별)
│   ├── emrcert/                  # EMR 크롤러 로그
│   └── hira_rulesvc/             # HIRA 규칙 서비스 로그 (향후)
│
├── docs/                         # 📚 프로젝트 문서
│   ├── plans/                    # 작업 계획서
│   │   └── emrcert.md           # EMR 크롤링 계획
│   └── journal/                  # 작업 일지 (프로젝트별)
│       ├── README.md            # 작업 일지 목록
│       └── emrcert/             # EMR 크롤러 작업 일지
│           ├── 2025-10-11_emrcert_bugfix.md
│           └── 2025-10-13_emrcert_fullscrape.md
│
├── main.py                       # 메인 실행 스크립트
├── requirements.txt              # 의존성 패키지
├── checkpoint_emrcert.json       # EMR 크롤링 진행 상황
└── README.md                     # 프로젝트 설명서
```

## 폴더별 설명

### 📦 `emrcert/`
EMR 인증 크롤러의 핵심 코드가 있는 패키지입니다.
- `scrapers/`: 각 인증 타입별 크롤러 구현

### 🔧 `shared/`
여러 프로젝트가 공유하는 유틸리티 모듈입니다.
- `utils/`: 로깅, 체크포인트, CSV 처리 등 공통 유틸리티
- 프로젝트별 경로를 지원하여 데이터와 로그를 분리 관리

### 💾 `data/`
크롤링으로 수집된 CSV 데이터가 프로젝트별로 저장됩니다.
- `emrcert/`: EMR 크롤러 데이터 (4개 CSV 파일)
- `hira_rulesvc/`: HIRA 규칙 서비스 데이터 (향후)
- 10개 항목마다 자동 저장, 인증번호 기준 중복 제거

### 📝 `logs/`
실행 로그가 프로젝트별로 타임스탬프와 함께 저장됩니다.
- `emrcert/`: EMR 크롤러 로그
- `hira_rulesvc/`: HIRA 규칙 서비스 로그 (향후)
- 형식: `{scraper_name}_YYYYMMDD_HHMMSS.log`
- 에러 및 진행 상황 추적 가능

### 📚 `docs/`
프로젝트 관련 문서를 체계적으로 관리합니다.
- `plans/`: 각 프로젝트의 작업 계획 및 요구사항
- `journal/`: 작업 일지 및 버그 수정 기록 (프로젝트별 하위 폴더)

### 💾 `checkpoint_emrcert.json`
EMR 크롤링 진행 상황을 저장하여 중단 시 재시작을 지원합니다.
- 마지막 처리 페이지 번호
- 처리 완료된 인증번호 목록

## 개발 히스토리

### 2025-10-13
- 제품인증 및 사용인증 크롤러에 `if __name__ == '__main__':` 블록 추가
- 전체 데이터 재수집 완료 (4,215개 항목)
- 작업 일지 작성: `docs/journal/2025-10-13_emrcert_fullscrape.md`

### 2025-10-11
- HTML 테이블 파싱 버그 수정
- "인증제품명"과 "버전" 필드가 비어있던 문제 해결
- TH-TD 쌍 단위 처리 로직 개선
- 작업 일지 작성: `docs/journal/2025-10-11_emrcert_bugfix.md`

## 트러블슈팅

### 크롤러가 실행되지 않을 때
1. 가상환경이 활성화되어 있는지 확인
2. `requirements.txt`의 패키지가 모두 설치되었는지 확인
3. Playwright 브라우저가 설치되었는지 확인: `playwright install chromium`

### 데이터가 비어있을 때
1. 로그 파일을 확인하여 에러 메시지 확인
2. 네트워크 연결 상태 확인
3. 웹사이트 접근 가능 여부 확인

### 중복 데이터가 발생할 때
1. `checkpoint.json` 파일을 삭제하고 재실행
2. 기존 CSV 파일을 백업 후 삭제하고 재실행

## 데이터 출처

- 웹사이트: https://emrcert.mohw.go.kr
- 제품인증: https://emrcert.mohw.go.kr/certifiState/productCertifiStateList.es?mid=a10106010000
- 사용인증: https://emrcert.mohw.go.kr/certifiState/useCertifiStateList.es?mid=a10106020000

## 라이선스

MIT License

## 기여

버그 리포트 및 개선 제안은 Issues를 통해 제출해주세요.
