# HIRA 문서 파싱 작업

**작업일**: 2025-10-17
**작업자**: Claude Code
**상태**: ⚠️ 부분 완료 (44/56 파일)

---

## 📋 작업 개요

HIRA 고시/법령 문서 56개를 Upstage Document Parse API를 사용하여 Markdown/HTML로 변환

### 파싱 결과

| 항목 | 결과 |
|------|------|
| 전체 파일 | 56개 |
| 성공 | 44개 (78.6%) |
| 실패 | 12개 (21.4%) |
| 총 페이지 | 243 페이지 |
| 비용 | $2.43 (약 ₩3,159원) |

---

## 🛠️ 구현 내용

### 1. 공통 파서 모듈 구현

**파일**: `shared/parsers.py`

```
BaseParser (추상 클래스)
  ├── parse() - 추상 메서드
  └── supports() - 확장자 지원 여부

UpstageParser (구현 클래스)
  ├── API URL: https://api.upstage.ai/v1/document-ai/document-parse
  ├── 지원 형식: HWP, PDF, DOCX, PPTX, XLSX, 이미지
  ├── 출력: Markdown + HTML
  └── 최대 크기: 50MB (문서 기준)

ParserFactory
  └── create() - 파서 인스턴스 생성
```

**특징**:
- 추상 클래스 패턴으로 확장 가능한 구조
- `.env` 파일에서 API 키 자동 로드
- 에러 핸들링 (파일 없음, 지원 안함, API 실패)

### 2. HIRA 파싱 스크립트 구현

**파일**: `hira_rulesvc/parse_documents.py`

**주요 기능**:
```python
parse_sample(N)     # N개 샘플 테스트
parse_all()         # 전체 56개 파일 파싱
retry_failed()      # 실패 파일만 재시도
```

**CLI 사용법**:
```bash
python hira_rulesvc/parse_documents.py --sample 3   # 샘플 3개
python hira_rulesvc/parse_documents.py --all        # 전체 파싱
python hira_rulesvc/parse_documents.py --retry      # 재시도
```

**메타데이터 매핑**:
- `document_tree.json`에서 SEQ, name, path 추출
- 자동 카테고리 분류 (법령, 고시, 행정해석)
- 파싱 시각 (`parsed_at`) 기록

### 3. 출력 형식

**저장 경로**: `data/hira_rulesvc/parsed/{파일명}.json`

```json
{
  "content": "# 제목\n\n내용...",
  "html": "<h1>제목</h1><p>내용...</p>",
  "metadata": {
    "seq": "187",
    "name": "부당이득금",
    "path": ["의료급여", "행정해석", "의료급여비용의 청구 및 정산"],
    "category": "행정해석"
  },
  "pages": 1,
  "model": "document-parse-250618",
  "usage": {"pages": 1},
  "filename": "5-(4) 부당이득금.hwp",
  "parsed_at": "2025-10-17T17:07:47.182215"
}
```

---

## ⚠️ 실패 파일 분석

### 1. **413 Request Entity Too Large (2개)**

파일 크기가 크지 않음에도 API 요청 제한에 걸림

| 파일명 | 크기 |
|--------|------|
| 요양급여비용 심사청구서·명세서 세부작성요령(2025년 8월 1일).hwp | 1.1MB |
| 의료급여수가의 기준 및 일반기준(고시 제2025-171호, 25.10.1. 시행)_전문.hwp | 439KB |

**원인 분석**:
- Upstage API 문서상 최대 50MB 지원
- 실제로는 약 1MB 이하에서 413 에러 발생
- API의 실제 제한이 문서화된 것보다 낮을 가능성

**해결 방안**:
- Upstage Console에서 수동 업로드 테스트
- 또는 PDF 변환 후 재시도
- Upstage 지원팀 문의

### 2. **500 Server Error (10개)**

모든 파일이 반복적으로 500 에러 발생

```
근로능력평가의 기준 등에 관한 고시(보건복지부고시)(제2025-30호)(20250220).hwp
노숙인진료시설 지정 등에 관한 고시(보건복지부고시)(제2025-46호)(20250321).hwp
선택의료급여기관 적용 대상자 및 이용 절차 등에 관한 규정(보건복지부고시)(제2020-111호)(20200501).hwp
요양비의 의료급여 기준 및 방법(보건복지부고시)(제2025-26호)(20250204).hwp
의료급여 대상 여부의 확인 방법 및 절차 등에 관한 기준(보건복지부고시)(제2023-144호)(20230701).hwp
의료급여기관 간 동일성분 의약품 중복투약 관리에 관한 기준(보건복지부고시)(제2022-174호)(20220802).hwp
의료급여법 시행규칙(보건복지부령)(제01096호)(20250311).hwp
의료급여법 시행령(대통령령)(제34928호)(20241002).hwp
의료급여법(법률)(제20309호)(20240517).hwp
임신·출산 진료비 등의 의료급여기준 및 방법(보건복지부고시)(제2023-281호)(20231228).hwp
```

**원인 분석**:
- Upstage API 서버 일시적 문제
- 재시도에서도 동일 에러 발생
- API 상태 불안정

**해결 방안**:
- 몇 시간/일 후 재시도
- `python hira_rulesvc/parse_documents.py --retry` 명령어 사용
- Upstage API 상태 모니터링

---

## 📊 카테고리별 통계 (성공한 44개)

| 카테고리 | 파일 수 | 예상 비율 |
|----------|---------|-----------|
| 행정해석 | ~30개 | ~68% |
| 고시 | ~10개 | ~23% |
| 법령 | ~4개 | ~9% |

**주요 성공 파일**:
- ✅ 의료급여법 관련 행정해석 대부분
- ✅ 각종 고시 및 규정
- ✅ 본인부담 정리 PDF

**주요 실패 파일**:
- ❌ 의료급여법 3종 (법률, 시행령, 시행규칙)
- ❌ 대형 고시 문서 2종 (413 에러)

---

## 💰 비용 분석

### 현재 비용 (44개)

| 항목 | 비용 |
|------|------|
| 페이지 수 | 243 페이지 |
| USD | $2.43 |
| KRW (₩1,300 환율) | ₩3,159 |
| 평균/파일 | 5.5 페이지 |

### 추정 최종 비용 (56개 전체)

예상 추가: 12개 × 평균 5.5p = 66페이지

| 항목 | 예상 비용 |
|------|-----------|
| 추가 페이지 | ~66 페이지 |
| 추가 USD | ~$0.66 |
| **총 예상** | **$3.09 (₩4,017)** |

> 초기 추정 $1.35보다 높지만, 대형 문서들이 예상보다 긴 것으로 판단

---

## 🔧 기술적 이슈 및 해결

### 1. 페이지 카운트 버그

**문제**: API 응답에서 `pages: 0`으로 표시

**원인**: API 응답 구조가 `{"pages": 0, "usage": {"pages": 1}}`로 되어 있음

**해결**: `shared/parsers.py:166` 수정
```python
# Before
"pages": api_result.get('pages', 0)

# After
"pages": usage.get('pages', 0)  # usage.pages에서 실제 페이지 수 가져오기
```

### 2. Windows UTF-8 인코딩

**문제**: 한글 및 유니코드 문자 출력 시 cp949 에러

**해결**: `hira_rulesvc/parse_documents.py:14-16` 추가
```python
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
```

---

## 📝 다음 단계

### 우선순위 1: 실패 파일 재시도
- [ ] 몇 시간 후 `--retry` 재실행
- [ ] 413 에러 2개 파일 수동 처리
- [ ] Upstage 지원팀 문의 (필요시)

### 우선순위 2: 데이터 전처리
- [ ] 44개 JSON 파일 분석
- [ ] Markdown 텍스트 정제
- [ ] 청크 분할 전략 수립

### 우선순위 3: 벡터 DB 준비
- [ ] 임베딩 모델 선정
- [ ] 벡터 DB 선택 (ChromaDB, Pinecone 등)
- [ ] 메타데이터 스키마 설계

---

## 📂 산출물

### 생성된 파일

```
data/hira_rulesvc/parsed/
  ├── _summary.json                    # 파싱 요약 통계
  ├── _failed_files.txt                # 실패 파일 목록
  ├── 5-(4) 부당이득금.json            # 파싱 결과 (예시)
  ├── 1-(1) 시설수용자.json
  └── ... (총 44개 JSON)
```

### 코드 파일

```
shared/
  └── parsers.py                        # 공통 파서 모듈 (219줄)

hira_rulesvc/
  └── parse_documents.py                # HIRA 파싱 스크립트 (384줄)
```

---

---

## 🔍 실패 파일 상세 분석

### 에러 유형별 분류

#### **413 Request Entity Too Large (2개)**
| 파일명 | 크기 | 카테고리 |
|--------|------|----------|
| 요양급여비용 심사청구서·명세서 세부작성요령(2025년 8월 1일).hwp | 1,090KB | 고시 |
| 의료급여수가의 기준 및 일반기준(고시 제2025-171호, 25.10.1. 시행)_전문.hwp | 438KB | 고시 |

#### **500 Server Error (10개)**

**법령 문서 (3개) - 최우선 처리 필요**
- `의료급여법(법률)(제20309호)` - 250KB ⭐⭐⭐⭐⭐
- `의료급여법 시행령(제34928호)` - 219KB ⭐⭐⭐⭐⭐
- `의료급여법 시행규칙(제01096호)` - 259KB ⭐⭐⭐⭐⭐

**고시 문서 (7개)**
- 근로능력평가의 기준 등에 관한 고시 - 122KB
- 노숙인진료시설 지정 등에 관한 고시 - 100KB
- 선택의료급여기관 적용 대상자 및 이용 절차 등에 관한 규정 - 110KB
- 요양비의 의료급여 기준 및 방법 - 112KB
- 의료급여 대상 여부의 확인 방법 및 절차 등에 관한 기준 - 112KB
- 의료급여기관 간 동일성분 의약품 중복투약 관리에 관한 기준 - 105KB
- 임신·출산 진료비 등의 의료급여기준 및 방법 - 113KB

### 패턴 발견

1. **법령 3종 실패가 치명적**: 의료급여의 가장 기본이 되는 법률·시행령·시행규칙
2. **크기는 정상**: 200~300KB인데 500 에러 → 파일 내부 복잡도 또는 HWP 형식 문제 추정
3. **413 에러**: Upstage API 실제 제한이 약 1MB 이하로 추정 (문서상 50MB와 차이)

---

## 🛠️ 추가 구현 사항

### Document Digitization API 지원

**배경**: 사용자가 Upstage의 Document Digitization API 제공
- 엔드포인트: `/v1/document-digitization`
- 강제 OCR 옵션: `ocr: "force"`

**구현**:
```python
# shared/parsers.py
def parse_with_ocr(self, file_path: Path) -> Dict[str, Any]:
    """강제 OCR로 파일 파싱"""
    result = self._call_api_digitization(file_path)
    return self._format_result(result)

# hira_rulesvc/parse_documents.py
python hira_rulesvc/parse_documents.py --retry --ocr
```

**결과**: 동일한 에러 발생 (500 Server Error, 413 Request Too Large)
→ API 종류와 무관하게 파일 자체의 문제로 확인

---

## 🎯 결론

### ✅ 성과
- **공통 파서 모듈 완성** (재사용 가능)
  - `shared/parsers.py` - BaseParser, UpstageParser, ParserFactory
  - Document Parse API + Digitization API 모두 지원
- **56개 중 44개 (78.6%) 파싱 성공**
- **Markdown + HTML + 메타데이터** 완벽 연동
- **비용 효율적**: $2.43 (243페이지)

### ⚠️ 제약
- **법령 3종 실패** - 의료급여법, 시행령, 시행규칙 (최우선 해결 필요)
- Upstage API 불안정 (500 에러)
- 일부 파일 크기 제한 (413 에러, 실제 제한 ~1MB)
- **12개 파일 미완료** (21.4%)

### 💡 교훈
- HWP 직접 파싱 가능 (변환 불필요)
- API 제한이 문서와 다를 수 있음 (50MB → 실제 ~1MB)
- 실패 파일 재시도 로직 필수
- OCR 강제 모드도 동일 에러 발생 → 파일 자체 문제

---

## 📋 다음 단계 권장 사항

### 우선순위 1: 법령 3종 확보 ⭐⭐⭐⭐⭐
**옵션 1**: 국가법령정보센터 크롤링
- https://www.law.go.kr
- 텍스트 형식 제공
- **현재 사용 불가 상태**

**옵션 2**: 수동 텍스트 추출
- 한글 Viewer로 TXT 변환
- Markdown 수동 작성

**옵션 3**: 공공데이터 Open API
- 법제처 API 활용

### 우선순위 2: 나머지 9개
- **413 에러 2개**: Upstage Console 수동 업로드
- **500 에러 7개**: 며칠 후 API 재시도 또는 HIRA 재다운로드

### 우선순위 3: 현재 데이터로 진행
- **44개 파일(78.6%)로 RAG 시스템 구축 시작**
- 데이터 전처리 및 청크 분할
- 벡터 DB 준비
- 법령 3종은 별도 추가

---

## 📂 최종 산출물

```
shared/parsers.py                        # 공통 파서 (286줄)
  ├── BaseParser (추상 클래스)
  ├── UpstageParser
  │   ├── parse() - Document Parse API
  │   └── parse_with_ocr() - Digitization API
  └── ParserFactory

hira_rulesvc/parse_documents.py          # 파싱 스크립트 (405줄)
  ├── parse_sample(N)
  ├── parse_all()
  └── retry_failed(use_ocr)

data/hira_rulesvc/parsed/
  ├── _summary.json                      # 통계 요약
  ├── _failed_files.txt                  # 실패 목록
  ├── _failed_analysis.md                # 실패 상세 분석
  └── *.json (44개)                      # 파싱 결과

docs/journal/hira_rulesvc/
  └── 2025-10-17_document_parsing.md     # 작업 일지 (본 문서)

scripts/
  ├── estimate_pages.py                  # 페이지 수 추정
  └── check_failed.py                    # 실패 파일 분석
```

---

**참고 링크**:
- Upstage Document Parse API: https://console.upstage.ai
- Upstage Digitization API: https://api.upstage.ai/v1/document-digitization
- 실패 파일 목록: `data/hira_rulesvc/parsed/_failed_files.txt`
- 실패 상세 분석: `data/hira_rulesvc/parsed/_failed_analysis.md`
- 파싱 요약: `data/hira_rulesvc/parsed/_summary.json`

---

**작업 종료**: 2025-10-17 18:30
**다음 작업**: 법령 3종 확보 또는 현재 44개로 전처리 시작
