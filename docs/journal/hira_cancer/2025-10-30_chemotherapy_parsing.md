# HIRA 항암요법 데이터 파싱

**날짜**: 2025-10-30
**작업자**: Claude + 사용자
**소요시간**: ~2시간

## 📋 작업 개요

HIRA(건강보험심사평가원) 항암요법 데이터 2종 파싱:
1. **공고책자 PDF** (264페이지, 3.37MB)
2. **사전신청요법 엑셀** (659개 승인 요법)

## 🎯 목적

- 허가초과 항암요법 승인 데이터 수집
- 약제명, 용법용량, 레짐 정보 구조화
- 향후 약제 앵커 검증 및 KB 구축 기반 마련

## 🔧 기술 스택

- **Upstage Document Parse API** - PDF OCR & 파싱
- **PyMuPDF** - 대용량 PDF 분할 (100페이지 제한 우회)
- **pandas** - 엑셀 데이터 분석
- **python-dotenv** - API 키 관리

## 📂 입력 데이터

### 1. 공고책자 PDF
```
파일: 공고책자_20251001.pdf
위치: data/hira_cancer/raw/attachments/chemotherapy/
크기: 3.37 MB
페이지: 264 pages
```

### 2. 사전신청요법 엑셀
```
파일: 사전신청요법(용법용량 포함)및 불승인요법_250915.xlsx
위치: data/hira_cancer/raw/attachments/chemotherapy/
크기: 234 KB
시트: 5개 (안내, 검토중, 승인 659개, 불승인 663개, 변경대비표)
```

## 🚧 기술적 도전과제

### 문제 1: Upstage API 100페이지 제한
**에러**:
```
API Error 413: The uploaded document exceeds the page limit.
The maximum allowed is 100, but the current document has 264 pages.
```

**해결책**:
- PyMuPDF로 PDF를 100페이지씩 3개 청크로 분할
- 각 청크를 독립적으로 파싱
- 결과를 프로그래매틱하게 병합

**구현**:
```python
# hira_cancer/parsers/upstage_split_parser.py
def split_pdf(self, pdf_path: Path, output_dir: Path) -> List[Path]:
    doc = pymupdf.open(pdf_path)
    for i in range(0, total_pages, self.chunk_size):
        chunk_doc = pymupdf.open()
        chunk_doc.insert_pdf(doc, from_page=start, to_page=end-1)
        chunk_doc.save(chunk_path)
```

### 문제 2: Upstage API 응답 구조
**에러**:
```python
TypeError: can only concatenate str (not "dict") to str
```

**원인**: `content`가 dict 형태 `{'html': '...', 'markdown': '...', 'text': '...'}`

**해결책**:
```python
content_dict = result.get('content', {})
if isinstance(content_dict, dict):
    content_text = content_dict.get(output_format, '')
else:
    content_text = str(content_dict)
```

### 문제 3: Windows 콘솔 인코딩
**에러**: `UnicodeEncodeError: 'cp949' codec can't encode character`

**해결책**: 이모지 제거, 파일 출력으로 우회

## 📊 파싱 결과

### PDF 파싱 통계
```
총 처리 시간: ~55초
- Chunk 1 (1-100p):   23.57s → 199,048 chars
- Chunk 2 (101-200p): 19.68s → 194,411 chars
- Chunk 3 (201-264p): 11.36s → 105,135 chars

총 콘텐츠: 498,594 characters (44,011 단어, 2,143 줄)
총 elements: 2,069개
```

### Elements 타입 분포
```
- paragraph:  991개 (48%) - 일반 텍스트
- table:      248개 (12%) ⭐ 구조화 데이터
- heading1:   288개 (14%) - 섹션 제목
- footer:     336개 (16%)
- list:       161개 (8%)
- caption:     19개
- header:      19개
- figure:       4개
- footnote:     2개
- index:        1개
```

### 약제명 패턴 분석

**영문 약제명** (총 124개 유니크):
```
- 단클론항체 (-mab):     59개
  예: Nivolumab, Pembrolizumab, Denosumab, Trastuzumab

- 키나제억제제 (-nib):    51개
  예: gefitinib, erlotinib, lazertinib, alectinib

- 백금계 (-platin):       8개
  예: cisplatin, carboplatin, oxaliplatin, heptaplatin

- 탁산계 (-taxel):        6개
  예: paclitaxel, docetaxel, cabazitaxel
```

**한글 약제명** (202개 유니크):
```
Top 20:
- 메토트렉세이트: 52회
- 트라스투주맙:   25회
- 젬시타빈:        7회
- 시스플라틴:      7회
- 카페시타빈:      6회
- 도세탁셀:        6회
- 베바시주맙:      5회
- 이리노테칸:      5회
- 테모졸로마이드:  5회
...
```

**치료 레짐**:
```
- FOLFOX:  6회
- FOLFIRI: 6회
- R-CHOP:  3회
- ABVD:    2회
```

### 엑셀 데이터 구조

**5개 시트**:
```
1. 안내 (38행)
   - 허가초과 항암요법 신청 가이드라인

2. 검토중인 허가초과 항암요법 (7행)
   - 현재 심의 중인 요법

3. 인정되고 있는 허가초과 항암요법 (659행) ⭐
   - 요법코드, 암종, 항암화학요법, 투여대상, 투여단계, 용법용량 등
   - 11개 컬럼의 구조화된 데이터

4. 불승인 요법 (663행)
   - 불승인된 요법 및 사유

5. 변경대비표 (17행)
   - 요법 변경 이력
```

**주요 컬럼** (인정 요법):
```
1. 요법코드 (예: 1004, 1005, ...)
2. 암종
3. 세부암종
4. 항암화학요법
5. 투여대상
6. 투여단계
7. 투여요법
8. 급여상세사항
9. 참고사항(용법용량) ⭐
10. 기타사항
```

## 🔍 데이터 관계 분석

**PDF vs Excel**:
- PDF: 전체 공고책자 (659 승인 + 7 검토중 + 663 불승인 + 가이드라인)
- Excel: 승인된 659개 요법만 정제된 테이블

**확인 결과**:
- PDF에 엑셀 요법코드(1004, 1005 등) 포함됨
- 엑셀 = PDF의 구조화된 서브셋

**활용 전략**:
1. **엑셀 우선** - 승인 요법 659개는 엑셀에서 직접 추출
2. **PDF 보완** - 상세 설명, 가이드라인 등 추가 컨텍스트

## 📁 생성 파일

### 파서 스크립트
```
hira_cancer/parsers/
├── upstage_pdf_parser.py          # 기본 Upstage API 래퍼
├── upstage_split_parser.py        # 대용량 PDF 분할 파서 ⭐
├── test_upstage_response.py       # API 응답 구조 테스트
├── review_parsed_data.py          # PDF 파싱 결과 분석
└── review_excel.py                # 엑셀 구조 분석
```

### 파싱 결과
```
data/hira_cancer/parsed/chemotherapy/
├── 공고책자_20251001.json         # 2.3 MB, 전체 파싱 결과
├── 공고책자_20251001.html         # 648 KB, raw HTML
└── excel_analysis.txt             # 엑셀 구조 분석 결과
```

### 로그
```
logs/
├── chemotherapy_parse.log         # 첫 번째 시도 (실패)
└── chemotherapy_parse2.log        # 두 번째 시도 (성공) ✅
```

## 🎓 핵심 학습

1. **API 제한 우회**: 큰 파일은 분할 → 병합 전략
2. **응답 구조 검증**: 가정하지 말고 실제 응답 확인
3. **데이터 관계 파악**: 중복 수집 방지, 효율적 활용
4. **Windows 인코딩**: UTF-8 파일 출력으로 우회

## 📌 다음 단계

### 즉시 (Phase 1)
- [ ] 엑셀 659개 요법 → pandas DataFrame 변환
- [ ] 약제명 추출 및 정규화 (영문/한글)
- [ ] 용법용량 파싱 (복잡한 텍스트 구조)

### 단기 (Phase 2)
- [ ] PDF 248개 테이블 구조화
- [ ] 레짐 정보 추출 (FOLFOX 등)
- [ ] 암종별 요법 매핑

### 중기 (Phase 3)
- [ ] 약제 앵커와 교차 검증
  - Gate chain의 14개 Active 약제
  - 35개 Pending 약제 재검토
- [ ] 적응증-요법 관계 구축

### 장기 (Phase 4)
- [ ] Knowledge Graph 통합
  - 약제 → 레짐 → 적응증 → 암종
- [ ] 자동화된 업데이트 파이프라인
  - 신규 공고 발행 시 자동 파싱

## 🔗 관련 작업

- **약제 앵커 구축** (2025-10-30): Gate chain 필터링 시스템
  - `docs/journal/hira_cancer/2025-10-30_gate_chain_drug_anchor.md`
  - 이 데이터로 14개 Active 약제 검증 가능

## 📝 메모

- Upstage API는 안정적이고 빠름 (~20초/100페이지)
- 엑셀 데이터가 이미 잘 정제되어 있어 즉시 활용 가능
- 248개 테이블은 향후 구조화 작업 필요
- 약제명 정규화가 핵심 과제 (동일 약제의 다양한 표기)

## ✅ 완료 체크리스트

- [x] PDF 파싱 (264페이지)
- [x] 엑셀 분석 (659개 요법)
- [x] 약제명 패턴 추출
- [x] 데이터 관계 파악
- [x] 파서 스크립트 작성
- [x] 분석 스크립트 작성
- [x] Journal 문서화
- [x] README 업데이트
- [ ] 구조화된 데이터 추출
