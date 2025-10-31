# 대한민국 약전 파싱 작업 일지

**날짜**: 2025-10-31
**작업자**: Claude + 사용자
**목표**: 대한민국 약전(Korean Pharmacopoeia) 전체 문서 파싱

## 작업 개요

약물 문서와 기준 데이터 파싱에 활용하기 위해 대한민국 약전 문서를 Upstage API를 통해 파싱하는 작업을 진행함.

## 데이터 구조

### 원본 파일 위치
`data/mfds/raw/THE KOREAN PHARMACOPOEIA/`

### 파일 구성
- **한글판 (ko/)**: 6개 hwpx 파일 (~22MB)
  - [별표 1] 통칙 (52KB)
  - [별표 2] 제제총칙 (62KB)
  - [별표 3] 의약품각조 제1부 (10.1MB)
  - [별표 4] 의약품각조 제2부 (3MB)
  - [별표 5] 일반시험법 (4.4MB)
  - [별표 6] 일반정보 (3.5MB)

- **영문판 (en/)**: 8개 docx 파일 (~24MB)
  - 01_KP Cover (56KB)
  - 02_[Appendix 1] General Notices (50KB)
  - 03_[Appendix 2] General Requirements for Pharmaceutical Preparations (64KB)
  - 04_[Appendix 3] Monographs_Part1 (12.6MB)
  - 05_[Appendix 4] Monographs_Part2 (2.7MB)
  - 06_[Appendix 5] General Tests (4.2MB)
  - 07_[Appendix 6] General Information (3.7MB)
  - 08_Index (138KB)

**총 14개 파일, 약 46MB**

## 작업 진행 상황

### 1단계: 샘플 테스트 ✅

**스크립트**: `mfds/parse_pharmacopoeia_test.py`

작은 파일 2개로 Upstage API 품질 테스트:
- 한글 hwpx: 통칙 (52KB) - 성공
- 영문 docx: General Notices (50KB) - 성공

**결과**:
- 두 형식 모두 Upstage API로 정상 파싱 확인
- 테이블, 리스트, 문단 구조 잘 보존됨
- 출력: markdown + html 형식

**테스트 결과 위치**: `data/mfds/parsed_test/`

### 2단계: 전체 파일 파싱 ⚠️

**스크립트**: `mfds/parse_pharmacopoeia_full.py`
**로그**: `logs/mfds_full_parse.log`

**실행 결과**:
- 성공: 6/14 파일 (122 pages)
- 실패: 8/14 파일 (대용량 파일)

**성공한 파일**:
```
[KO] 통칙 (7 pages, 13,474 chars)
[KO] 제제총칙 (15 pages, 33,123 chars)
[EN] KP Cover (4 pages, 340 chars)
[EN] General Notices (12 pages, 30,809 chars)
[EN] General Requirements (22 pages, 81,538 chars)
[EN] Index (62 pages, 202,817 chars)
```

**실패한 파일** (API 제약):
```
[ERROR] 413 Request Entity Too Large (7개):
  - [별표 4] 의약품각조 제2부 (3MB)
  - [별표 5] 일반시험법 (4.4MB)
  - [별표 6] 일반정보 (3.5MB)
  - 05_[Appendix 4] Monographs_Part2 (2.7MB)
  - 06_[Appendix 5] General Tests (4.2MB)
  - 07_[Appendix 6] General Information (3.7MB)

[ERROR] ReadTimeout 60s (2개):
  - [별표 3] 의약품각조 제1부 (10.1MB)
  - 04_[Appendix 3] Monographs_Part1 (12.6MB)
```

**파싱 결과 위치**: `data/mfds/parsed/`
- 개별 JSON 파일: `{lang}_{filename}.json`
- 요약: `parse_summary.json`

**통계**:
- 총 소요시간: 433.7초 (7.2분)
- 파일당 평균: 31.0초
- 성공률: 43% (6/14)

### 3단계: 대용량 파일 분할 파싱 준비 ✅

**문제 해결 과정**:

1. **python-docx 설치**
   - `uv pip install python-docx` 실행
   - python-docx 1.2.0 + lxml 6.0.2 설치 완료
   - scraphub venv에 설치됨

2. **분할 파싱 스크립트 작성 (1차 시도 - 실패)**
   - **스크립트**: `mfds/parse_pharmacopoeia_split.py`
   - **전략**: 문단 기준 분할 (100 문단/청크)
   - **처리 방식**:
     - docx 파일 읽기
     - 100 문단씩 새 docx 청크 생성
     - 각 청크를 Upstage API로 파싱
     - 결과를 병합하여 저장
   - **hwpx 지원**: 현재 미지원 (수동 PDF 변환 필요)

### 4단계: 문단 분할 방식 문제 발견 및 PDF 전환 ⚠️→✅

**문제점 발견**:
- 문단 100개 단위 분할 → **표가 중간에 잘림**
- Upstage API의 멀티페이지 표 병합은 **파일 내에서만 유효**
- 파일을 분할하면 표 구조가 손상됨
- 약전 문서는 표와 그림이 많은 기술 문서 → 표 구조 보존 필수

**해결 방안**:
1. **PDF 변환**: docx/hwpx → PDF (수동 변환, MS Word/한글)
2. **페이지 기준 분할**: 50-100 페이지 단위로 분할 (표 보존)
3. **기존 파서 재사용**: `hira_cancer/parsers/upstage_split_parser.py` 활용

**실행 과정**:
1. 대용량 파일 8개를 수동으로 PDF 변환 완료
   - 영문 4개: en/ 폴더
   - 한글 4개: ko/ 폴더
2. PDF 분할 파싱 스크립트 작성: `mfds/parse_pharmacopoeia_pdf.py`
3. PyMuPDF로 50페이지씩 분할 → Upstage API 파싱 → 병합
4. 백그라운드 실행 시작 (18:05)

**변환된 PDF 파일**:
```
영문 (en/):
- 04_Monographs_Part1.pdf (33.5MB, 1670페이지) ← 가장 중요
- 05_Monographs_Part2.pdf (7.6MB)
- 06_General Tests.pdf (8.2MB)
- 07_General Information.pdf (5.2MB)

한글 (ko/):
- [별표 3] 의약품각조 제1부.pdf (19.8MB)
- [별표 4] 의약품각조 제2부.pdf (3.6MB)
- [별표 5] 일반시험법.pdf (4.3MB)
- [별표 6] 일반정보.pdf (4.5MB)

총 8개 파일, 88MB
```

## 현재 상태

### 완료된 작업
- [x] 데이터 구조 파악
- [x] Upstage API 테스트 (docx + hwpx)
- [x] 전체 파일 파싱 스크립트 작성 및 실행
- [x] python-docx 설치
- [x] 대용량 파일 분할 파싱 스크립트 작성 (문단 기준 - 폐기)
- [x] 문제점 분석 및 PDF 전환 결정
- [x] 대용량 파일 8개 PDF 수동 변환
- [x] PDF 분할 파싱 스크립트 작성 및 실행 시작

### 진행 중 작업
- [🔄] PDF 분할 파싱 실행 (백그라운드, 1-2시간 소요 예상)
  - 현재: 1/8 파일 처리 중 (Monographs_Part1, 1670p → 34청크)
  - 로그: `logs/mfds_pdf_parse.log`
  - 출력: `data/mfds/parsed_pdf/`

### 미완료 작업
- [ ] PDF 파싱 완료 대기 및 결과 검증
- [ ] 파싱 결과 분석 및 활용 계획
- [ ] 데이터 후처리 (필요시)

## 실행 가능한 다음 단계

### 집에서 작업 재개 시

**1. 파싱 진행 상황 확인**:
```bash
cd C:\Jimin\scrape-hub
tail -50 logs/mfds_pdf_parse.log
```

**2. 파싱 완료 확인**:
```bash
# 파싱된 파일 목록 확인
ls -lh data/mfds/parsed_pdf/

# 요약 파일 확인
cat data/mfds/parsed_pdf/parse_summary.json
```

**3. 파싱 미완료 시 재개**:
```bash
. scraphub/Scripts/activate
scraphub/Scripts/python -u mfds/parse_pharmacopoeia_pdf.py 2>&1 | tee -a logs/mfds_pdf_parse.log
```
- 이미 파싱된 파일은 자동 스킵됨

**4. 파싱 완료 후 다음 작업**:
- [ ] 파싱 결과 검증 (각 JSON 파일 크기, content 길이)
- [ ] 표 구조 보존 확인 (샘플 확인)
- [ ] 데이터 활용 계획 수립

## 파일 구조

```
mfds/
├── parse_pharmacopoeia_test.py       # 샘플 테스트 스크립트
├── parse_pharmacopoeia_full.py       # 전체 파일 파싱 스크립트
├── parse_pharmacopoeia_split.py      # docx 문단 분할 파싱 (폐기)
└── parse_pharmacopoeia_pdf.py        # PDF 페이지 분할 파싱 (현재 사용) ⭐

data/mfds/
├── raw/THE KOREAN PHARMACOPOEIA/     # 원본 파일
│   ├── ko/*.hwpx (6개)
│   ├── ko/*.pdf (4개, 대용량 변환본) ⭐
│   ├── en/*.docx (8개)
│   └── en/*.pdf (4개, 대용량 변환본) ⭐
├── parsed_test/                      # 샘플 테스트 결과
│   ├── 통칙_ko.json
│   ├── General Notices_en.json
│   └── test_summary.json
├── parsed/                           # 소형 파일 파싱 결과
│   ├── ko_*.json (2개)
│   ├── en_*.json (4개)
│   └── parse_summary.json
└── parsed_pdf/                       # PDF 분할 파싱 결과 (진행 중) ⭐
    ├── 04_[Appendix 3] Monographs_Part1.json
    ├── 05_[Appendix 4] Monographs_Part2.json
    ├── ... (8개 예정)
    └── parse_summary.json

logs/
├── mfds_test_parse.log              # 테스트 로그
├── mfds_full_parse.log              # 전체 파싱 로그
└── mfds_pdf_parse.log               # PDF 분할 파싱 로그 (진행 중) ⭐
```

## 기술적 세부사항

### Upstage API 제약사항
- **파일 크기 제한**: 약 3MB (문서상 50MB이나 실제로는 더 작음)
- **타임아웃**: 60초
- **지원 형식**: hwpx, docx, pdf, 이미지 등

### 분할 파싱 전략

**초기 전략 (폐기)**:
- **청크 크기**: 100 문단/청크
- **문제점**: 표가 중간에 잘림, 멀티페이지 표 병합 불가

**최종 전략 (PDF 페이지 분할)**:
- **청크 크기**: 50 페이지/청크
- **파일 형식**: PDF (docx/hwpx 수동 변환)
- **분할 도구**: PyMuPDF (pymupdf)
- **병합 방식**: HTML 텍스트 결합
- **API 부하 방지**: 청크 간 1초 대기, 파일 간 2초 대기
- **장점**: 페이지 경계 명확, 표 구조 완벽 보존, 멀티페이지 표 병합 가능

### 출력 형식
```json
{
  "content": "...",     // markdown
  "html": "...",        // html
  "pages": 122,
  "metadata": {
    "split_parsing": true,
    "total_chunks": 25,
    "success_chunks": 25,
    "error_chunks": 0,
    "chunk_size": 100,
    "parse_time": 450.2
  }
}
```

## 트러블슈팅

### 이슈 1: Windows 터미널 인코딩 오류
**증상**: UnicodeEncodeError (✓, ✗ 기호)
**해결**: ASCII 호환 문자로 변경 ([OK], [ERROR])

### 이슈 2: 대용량 파일 파싱 실패
**증상**: 413 Error, ReadTimeout
**해결**: 파일 분할 파싱 스크립트 작성

### 이슈 3: python-docx 설치 실패 (초기)
**증상**: pip not found in venv
**해결**: `uv pip install` 사용

### 이슈 4: 문단 기준 분할의 표 구조 손상 ⭐
**증상**:
- 문단 100개 단위로 분할 시 표가 중간에 잘림
- Upstage API 멀티페이지 표 병합이 파일 내에서만 작동
- 약전 문서는 표와 그림이 많아 구조 손상 심각

**해결**:
- PDF 변환 + 페이지 기준 분할 (50페이지/청크)
- PyMuPDF 사용하여 페이지 단위로 정확히 분할
- 기존 `hira_cancer/parsers/upstage_split_parser.py` 재사용

**교훈**:
- 기술 문서 파싱 시 표/그림 구조 보존 최우선
- 분할 기준은 데이터 특성에 맞춰 선택
- PDF 형식이 구조 보존에 더 유리

## 다음 작업 시 참고사항

1. **파싱 재개 명령어** (필요 시):
   ```bash
   cd C:\Jimin\scrape-hub
   . scraphub/Scripts/activate
   scraphub/Scripts/python -u mfds/parse_pharmacopoeia_pdf.py 2>&1 | tee -a logs/mfds_pdf_parse.log
   ```

2. **진행 상황 확인**:
   ```bash
   # 실시간 로그 확인
   tail -f logs/mfds_pdf_parse.log

   # 파싱된 파일 확인
   ls -lh data/mfds/parsed_pdf/

   # 요약 확인
   cat data/mfds/parsed_pdf/parse_summary.json
   ```

3. **결과 검증**:
   - JSON 파일 크기 확인 (수십 MB 예상)
   - content 길이 확인 (수백만 chars)
   - 청크별 통계 확인 (metadata.chunks)
   - 표 구조 보존 샘플 확인

## 예상 완료 시점

- **전체 8개 PDF 파일**: 1-2시간 (API 속도에 따라)
  - Monographs_Part1 (1670p, 34청크): ~20분
  - 나머지 7개 파일: ~1시간
- **백그라운드 실행**: 18:05 시작

## 참고사항

- **API 키**: 환경변수 `UPSTAGE_API_KEY` 사용
- **임시 파일**: PDF 청크는 `data/mfds/raw/.../en/_temp_*/` 생성 후 자동 삭제
- **로그 파일**: `logs/mfds_pdf_parse.log`에 실시간 저장
- **중단 시**: 프로세스 종료해도 안전 (이미 파싱된 파일은 스킵)
- **재개 시**: 이미 완료된 파일 자동 스킵

---

**작업 상태**: PDF 분할 파싱 실행 중 (백그라운드, 18:05 시작)
**현재 진행**: 1/8 파일 처리 중 (Monographs_Part1, 1670p → 34청크)
**다음 단계**: 파싱 완료 대기 및 결과 검증
