# 업무 일지 - 2025년 10월 31일

## 작업 요약

**목표**: 대한민국 약전(MFDS Korean Pharmacopoeia) 전체 문서 파싱
**진행 상황**: PDF 분할 파싱 실행 중 (백그라운드, 1-2시간 소요 예상)

## 주요 작업 내용

### 1. 대용량 문서 파싱 문제 진단 및 해결

**배경**:
- 대한민국 약전 14개 파일 중 8개 대용량 파일(2.7MB~12.6MB) 파싱 실패
- API 제약: 413 Request Entity Too Large, ReadTimeout 60s

**초기 시도 (실패)**:
- 문단 100개 기준으로 docx 파일 분할
- 문제 발견: 표가 중간에 잘림
  - Upstage API의 멀티페이지 표 병합은 파일 내에서만 유효
  - 약전 문서는 표와 그림이 많은 기술 문서 → 구조 손상 심각

**최종 해결 방안**:
- **PDF 변환**: 대용량 8개 파일(docx 4개, hwpx 4개)을 PDF로 수동 변환
- **페이지 기준 분할**: 50 페이지씩 분할 (표 구조 보존)
- **기존 코드 재사용**: `hira_cancer/parsers/upstage_split_parser.py` 활용
- **PyMuPDF**: 페이지 단위 정확한 분할

### 2. PDF 분할 파싱 시스템 구축

**작성한 스크립트**: `mfds/parse_pharmacopoeia_pdf.py`

**주요 기능**:
- 8개 PDF 파일 자동 처리 (영문 4개 + 한글 4개)
- 50 페이지씩 청크 분할 (PyMuPDF)
- 각 청크를 Upstage API로 파싱 후 병합
- 이미 파싱된 파일 자동 스킵 (재실행 안전)
- 실시간 로그 저장

**처리 대상**:
```
영문 (en/): 4개 PDF, 총 55MB
- 04_Monographs_Part1 (33.5MB, 1670p) ← 핵심 문서
- 05_Monographs_Part2 (7.6MB)
- 06_General Tests (8.2MB)
- 07_General Information (5.2MB)

한글 (ko/): 4개 PDF, 총 33MB
- [별표 3] 의약품각조 제1부 (19.8MB)
- [별표 4] 의약품각조 제2부 (3.6MB)
- [별표 5] 일반시험법 (4.3MB)
- [별표 6] 일반정보 (4.5MB)
```

### 3. 실행 및 모니터링

**실행 시작**: 18:05, 백그라운드
**현재 진행**: 1/8 파일 처리 중 (Monographs_Part1, 34개 청크)
**예상 완료**: 19:00~20:00

**출력**:
- JSON 파일: `data/mfds/parsed_pdf/*.json` (8개)
- 로그: `logs/mfds_pdf_parse.log`
- 요약: `data/mfds/parsed_pdf/parse_summary.json`

## 기술적 의사결정

### PDF vs docx 분할

**선택**: PDF 페이지 분할
**이유**:
1. 표 구조 완벽 보존 (멀티페이지 표 병합 지원)
2. 페이지 경계가 명확하여 분할 단위 정확
3. 기존 검증된 파서 재사용 가능
4. docx 문단 분할은 표/그림 구조 손상

**트레이드오프**:
- 수동 PDF 변환 필요 (8개 파일, 30분 소요)
- 자동화 대신 품질 우선 선택

### 청크 크기 50페이지

**이유**:
- Upstage API 제한: 100페이지 권장
- 안전 마진 확보 (API 안정성)
- 표 병합 최적화 (파일 내 완결성)

## 산출물

### 코드
- `mfds/parse_pharmacopoeia_pdf.py` (187줄)
  - PDF 파일 자동 감지 및 처리
  - 이미 파싱된 파일 스킵
  - 상세 로그 및 요약 생성

### 문서
- `docs/journal/2025-10-31_mfds_pharmacopoeia_parsing.md` 업데이트
  - 4단계 작업 과정 상세 기록
  - 문제 해결 과정 및 교훈 문서화
  - 재개 가이드 작성

### 데이터
- 변환된 PDF 8개 (88MB)
- 파싱 진행 중 (완료 시 JSON 8개 예상)

## 다음 작업 (집에서 재개)

1. **파싱 완료 확인**:
   ```bash
   tail -50 logs/mfds_pdf_parse.log
   ls -lh data/mfds/parsed_pdf/
   ```

2. **결과 검증**:
   - JSON 파일 크기 확인
   - 표 구조 보존 샘플 확인
   - content 길이 및 품질 검증

3. **파싱 미완료 시 재실행**:
   ```bash
   . scraphub/Scripts/activate
   scraphub/Scripts/python -u mfds/parse_pharmacopoeia_pdf.py 2>&1 | tee -a logs/mfds_pdf_parse.log
   ```

## 교훈

1. **데이터 특성 우선 고려**: 기술 문서는 표/그림 구조 보존이 핵심
2. **빠른 프로토타입 검증**: 문단 분할 방식을 조기에 테스트하여 문제 발견
3. **기존 코드 재사용**: hira_cancer 파서를 활용하여 개발 시간 단축
4. **점진적 자동화**: 수동 변환으로 품질 확보 후 추후 자동화 고려

## 소요 시간

- 문제 진단 및 분석: 30분
- PDF 변환: 30분
- 스크립트 작성 및 테스트: 1시간
- 실행 시작 및 모니터링: 10분
- 문서화: 20분
- **총 소요**: 약 2.5시간

---

**작업 상태**: 진행 중 (백그라운드 실행)
**차단 요소**: 없음
**위험 요소**: API rate limit (청크 간 1초 대기로 완화)
