# HIRA 암질환 사용약제 및 요법 크롤러

건강보험심사평가원 암질환 게시판 데이터 수집 및 파싱

**데이터 출처**: https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030069000000

---

## 📋 프로젝트 개요

건강보험심사평가원에서 운영하는 "암환자에게 처방·투여하는 약제" 게시판의 데이터를 수집하고 파싱하여 구조화된 형태로 저장하는 프로젝트입니다.

### 수집 대상 게시판

1. **공고 (announcement)**: 암질환 급여기준 공고문
2. **공고예고 (pre_announcement)**: 공고 예정 사항 및 의견 수렴
3. **FAQ**: 실무 지침 및 질의응답
4. **항암화학요법 (chemotherapy)**: 급여기준 다운로드 링크

---

## 📊 수집 현황

### 게시글 및 첨부파일

| 게시판 | 게시글 | 첨부파일 | 평균 파일/게시글 |
|--------|--------|----------|------------------|
| 공고 (announcement) | 217개 | 471개 | 2.2개 |
| 공고예고 (pre_announcement) | 232개 | 299개 | 1.3개 |
| FAQ | 117개 | 58개 | 0.5개 |
| 항암화학요법 (chemotherapy) | 2개 | 0개 | 0개 |
| **합계** | **484개** | **828개** | **1.7개** |

### 파싱 현황

| 항목 | 수치 | 비고 |
|------|------|------|
| 파싱 성공 | 823개 | 99.4% |
| 파싱 실패 | 4개 | timeout 2개, 413 error 2개 |
| 총 페이지 | 4,948p | - |
| 실제 비용 | $49.48 | 약 ₩64,324 |
| 출력 크기 | 19.2 MB | JSON 형식 |

### 엔티티 추출 현황 (NEW!)

| 항목 | 수치 | 비고 |
|------|------|------|
| **처리 공고** | 13개 | 217개 중 텍스트 내용 보유 |
| **추출 관계** | 38개 | 약제-암종-요법 관계 |
| **고유 암종** | 16개 | 자궁암, 림프종, 다발골수종 등 |
| **고유 약제** | 67개 | Dostarlimab, Paclitaxel 등 |
| **변경 유형** | 5가지 | 신설, 변경, 삭제, 추가, unknown |
| **출력 파일** | 2개 | JSON (전체 + 샘플) |

**실패 파일**:
- `[공고 #128]` 20180205_공고전문.hwp (timeout)
- `[공고 #85]` 공고전문.hwp (413 error - 파일 크기 초과)
- `[공고예고 #9577]` 의견조회내역_20250701.hwpx (timeout)
- `[FAQ #71]` 변경전 공고전문.hwp (413 error - 파일 크기 초과)

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# uv 가상환경 활성화
. scraphub/Scripts/activate

# 패키지 설치
uv pip install playwright beautifulsoup4 tqdm requests python-dotenv

# Playwright 브라우저 설치
playwright install chromium

# Upstage API Key 설정
# .env 파일에 UPSTAGE_API_KEY 추가
```

### 2. 데이터 수집

```bash
# 전체 게시판 수집 (게시글 + 첨부파일)
python hira_cancer/scraper.py
```

**출력**:
- `data/hira_cancer/raw/hira_cancer_YYYYMMDD_HHMMSS.json` (메타데이터)
- `data/hira_cancer/raw/attachments/{board}/` (첨부파일)

### 3. 첨부파일 파싱

```bash
# 샘플 테스트 (각 게시판 3개씩)
python hira_cancer/parse_attachments.py --sample

# 전체 파싱 (Upstage API 사용)
python hira_cancer/parse_attachments.py --all

# 게시판별 파싱
python hira_cancer/parse_attachments.py --board announcement

# 실패 파일만 재시도
python hira_cancer/parse_attachments.py --retry
```

**출력**:
- `data/hira_cancer/parsed/{board}/` (Markdown + HTML JSON)
- `data/hira_cancer/parsed/_summary.json` (통계)
- `data/hira_cancer/parsed/_failed_files.json` (실패 목록)

### 4. 엔티티 추출 (NEW!)

```bash
# 공고 문서에서 약제-암종-요법 관계 추출
python hira_cancer/parsers/entity_extractor.py
```

**출력**:
- `data/hira_cancer/parsed/drug_cancer_relations.json` (전체 38개 관계)
- `data/hira_cancer/parsed/drug_cancer_relations_samples.json` (샘플 10개)

**추출 내용**:
```json
{
  "cancer": "자궁암",
  "drugs": ["Dostarlimab", "Paclitaxel", "Carboplatin"],
  "regimen_type": "병용요법",
  "line": "1차",
  "purpose": "고식적요법",
  "action": "신설",
  "source_text": "- 자궁암에 'Dostarlimab + Paclitaxel + Carboplatin' 병용요법(1차, 고식적요법) 신설",
  "announcement_no": "제2025-210호",
  "date": "2025.10.1."
}
```

### 5. 데이터 확인

```bash
# 콘솔에서 샘플 확인
python hira_cancer/view_parsed_samples.py

# 텍스트 파일로 추출
python hira_cancer/export_parsed_content.py

# 데이터 분석
python hira_cancer/analyze_data.py
```

---

## 📂 데이터 구조

### 원본 데이터 (raw)

```json
{
  "scraped_at": "2025-10-23 18:48:48",
  "total_posts": 484,
  "total_attachments": 828,
  "boards": {
    "announcement": {
      "posts": [
        {
          "number": 217,
          "title": "암환자에게 처방·투여하는 약제에 대한 공고 변경 안내",
          "date": "2025.10.01",
          "author": "요양급여기준부 양한방약제기준과",
          "detail_url": "https://www.hira.or.kr/bbsDummy.do?...",
          "content": "본문 텍스트...",
          "content_html": "<p>HTML 구조 보존</p>...",
          "attachments": [
            {
              "filename": "암질환_20251001.pdf",
              "extension": ".pdf",
              "download_url": "https://www.hira.or.kr/bbsDownload.do?...",
              "downloaded": true,
              "local_path": "C:\\...\\217_암질환_20251001.pdf"
            }
          ],
          "attachment_count": 4
        }
      ]
    }
  }
}
```

### 파싱 데이터 (parsed)

```json
{
  "content": "# 제목\n\n본문 내용 (Markdown)",
  "html": "<h1>제목</h1><p>본문 내용</p>",
  "model": "document-parse-240506",
  "pages": 5,
  "attachment_metadata": {
    "board": "announcement",
    "board_name": "공고",
    "post_number": "217",
    "post_title": "암환자에게 처방·투여하는 약제...",
    "attachment_index": 0,
    "filename": "암질환_20251001.pdf",
    "download_url": "https://www.hira.or.kr/bbsDownload.do?..."
  },
  "parsed_at": "2025-10-24T01:23:45.123456"
}
```

---

## 🛠️ 스크립트 설명

### 핵심 스크립트

| 파일 | 설명 | 용도 |
|------|------|------|
| `scraper.py` | 게시판 크롤러 | 게시글 + 첨부파일 수집 |
| `parse_attachments.py` | 첨부파일 파서 | HWP/PDF → Markdown/HTML |
| **`parsers/entity_extractor.py`** | **엔티티 추출기 (NEW!)** | **약제-암종-요법 관계 추출** |
| `analyze_data.py` | 데이터 분석 | 통계 및 샘플 출력 |
| `view_parsed_samples.py` | 파싱 샘플 뷰어 | 콘솔 출력 |
| `export_parsed_content.py` | 텍스트 추출 | 텍스트 파일 생성 |

### 유틸리티

| 폴더/파일 | 설명 |
|-----------|------|
| `archive/` | 구버전 스크립트 및 디버그 파일 |

---

## 📚 데이터 특징

### 1. 공고 (announcement)

**특징**:
- 월별 정기 공고 (매월 1일 또는 월 초)
- 주요 파일: `암질환_YYYYMM.pdf`, `주요변경사항_YYYYMM.hwpx`
- 내용: 급여기준 변경사항, 신규 약제 추가

**샘플 제목**:
- "암환자에게 처방·투여하는 약제에 대한 공고 변경 안내"
- "암질환 급여기준 개정안내(20XX.XX.XX)"

### 2. 공고예고 (pre_announcement)

**특징**:
- 의견 수렴 프로세스 (공고 전 예고)
- **HWP 파일 83.3%** (249/299개) - 내부 문서 특성
- 주요 파일: `주요공고개정내역(예정)_YYYYMMDD.hwpx`, `의견조회내역_YYYYMMDD.hwpx`

**샘플 제목**:
- "암환자에게 처방·투여하는 약제에 대한 공고 개정(안)에 대한 의견조회"
- "주요 공고개정 내역(예정)"

### 3. FAQ

**특징**:
- 실무 지침서 역할 (117개 Q&A)
- 약제별 상세 질의응답
- 파일 첨부 비율 낮음 (평균 0.5개/게시글)

**샘플 제목**:
- "Tisagenlecleucel(품명: 킴리아주) 관련 질의 응답"
- "소세포폐암 1차 치료 관련 Q&A"

### 4. 항암화학요법 (chemotherapy)

**특징**:
- 다운로드 전용 페이지 (2개 게시글)
- 첨부파일 없음
- 특수 HTML 구조 (`title_cell_index=1`)

---

## 🔍 파싱 품질

### 우수 사례: FAQ #117 (Tisagenlecleucel)

**원본**: HWP, 2페이지

**파싱 결과**:
- ✅ 제목 및 섹션 구조 완벽 보존
- ✅ 표 형식 정확히 Markdown 변환
- ✅ 주석(주6, 주7 등) 올바르게 매핑
- ✅ Q&A 구조 명확히 분리

**Markdown 샘플**:
```markdown
# Tisagenlecleucel(품명: 킴리아주) 관련 질의 응답

## ▷ 관련 급여기준

[28] 비호지킨림프종(Non-Hodgkin's Lymphoma)

| 연번 | 항암요법 | 투여대상 | 투여단계 |
| --- | --- | --- | --- |
| 18 | tisagenlecleucel주 | 두 가지 이상의 전신 치료 후... | 3차 이상 |

# 질문 1 투여대상 기준 시점은 언제인가요?

<답변>
○ 약물 투입 전이 아닌 세포 채집단계에 급여기준 요건을 만족해야 합니다.
```

### 파싱 품질 지표

| 항목 | 평가 | 비고 |
|------|------|------|
| 제목/섹션 구조 | ⭐⭐⭐⭐⭐ | 완벽 |
| 표 형식 변환 | ⭐⭐⭐⭐⭐ | Markdown table 정확 |
| 특수문자 처리 | ⭐⭐⭐⭐☆ | 일부 기호 변환 필요 |
| 레이아웃 보존 | ⭐⭐⭐⭐☆ | 여백/들여쓰기 근사 |
| 주석 매핑 | ⭐⭐⭐⭐⭐ | 완벽 |

**총평**: Upstage API의 한글 문서 파싱 품질은 매우 우수하며, 구조화된 데이터 추출에 적합함.

---

## 💡 활용 방안

### 1. 엔티티 추출 ✅ 완료!

**현재 구현됨**: `parsers/entity_extractor.py`를 통한 자동 추출

**추출 예시**:
```json
{
  "cancer": "자궁암",
  "drugs": ["Dostarlimab", "Paclitaxel", "Carboplatin"],
  "regimen_type": "병용요법",
  "line": "1차",
  "purpose": "고식적요법",
  "action": "신설",
  "announcement_no": "제2025-210호"
}
```

**통계**:
- 38개 약제-암종-요법 관계 추출
- 16개 고유 암종
- 67개 고유 약제
- 병용요법 14개, 단독요법 12개

**추가 계획**: PDF 첨부파일에서 추가 관계 추출 (예상 +500~1,000개)

### 2. 시계열 분석

- 월별 공고 추이
- 신규 약제 추가 패턴
- 급여기준 변경사항 추적

### 3. FAQ 챗봇

- 823개 파싱 문서 임베딩
- RAG 기반 질의응답 시스템
- 실무 지침 검색

### 4. Graph RAG 구축

```cypher
# Neo4j 그래프 예시
(Drug:Tisagenlecleucel)
  -[:TREATS]->(Cancer:DLBCL)
  -[:HAS_RESTRICTION]->(Restriction:평생1회)
  -[:MENTIONED_IN]->(FAQ:117)
  -[:CHANGED_IN]->(Announcement:217)
```

---

## 🔧 기술 스택

| 항목 | 기술 |
|------|------|
| 브라우저 자동화 | Playwright |
| HTML 파싱 | BeautifulSoup4 |
| 문서 파싱 | Upstage Document Parse API |
| 진행 표시 | tqdm |
| 환경 변수 | python-dotenv |
| 출력 형식 | JSON, Markdown, HTML |

---

## 📅 프로젝트 타임라인

| 날짜 | 작업 | 결과 |
|------|------|------|
| 2025-10-22 | 초기 스크래핑 | 구조 분석 완료 |
| 2025-10-23 | 전체 수집 | 484개 게시글 + 828개 첨부파일 |
| 2025-10-24 | 첨부파일 파싱 | 823개 파싱 완료 (4,948p, $49.48) |
| **2025-10-29** | **엔티티 추출** | **38개 약제-암종-요법 관계 추출** |

---

## 🚀 향후 계획

### 데이터 통합
- [ ] 게시글 메타데이터 + 파싱 내용 통합
- [ ] 검색 가능한 SQLite DB 구축

### 엔티티 추출
- [x] ✅ Regex 기반 정보 추출 (약제명, 암종, 요법 정보) - **완료!**
- [x] ✅ 구조화된 데이터셋 구축 (38개 관계) - **완료!**
- [ ] PDF 첨부파일에서 추가 관계 추출 (예상 +500~1,000개)

### RAG 시스템
- [ ] 벡터 임베딩 (Sentence Transformers)
- [ ] Graph RAG 구축 (Neo4j)
- [ ] FAQ 챗봇 프로토타입 (Streamlit)

### 시계열 분석
- [ ] 공고별 변경사항 자동 비교
- [ ] 신규 약제 추가 알림
- [ ] 대시보드 구축

---

## 📖 문서

### 작업 일지
- [2025-10-22: 초기 스크래핑](../docs/journal/hira/2025-10-22_initial_scraping.md)
- [2025-10-23: 전체 수집 완료](../docs/journal/hira/2025-10-23_complete_scraping.md)
- [2025-10-24: 첨부파일 파싱 완료](../docs/journal/hira/2025-10-24_attachment_parsing.md)
- **[2025-10-29: 엔티티 추출 완료](../docs/journal/hira/2025-10-29_entity_extraction.md)** - NEW!

---

## 📄 라이선스

이 프로젝트는 수집된 데이터의 2차 저작물 사용 권한을 포함하지 않습니다.

**데이터 출처**: 건강보험심사평가원 암질환 게시판 (https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA030069000000)

---

**최종 업데이트**: 2025-10-29
**수집 상태**: ✅ 완료 (484개 게시글 + 828개 첨부파일)
**파싱 상태**: ✅ 완료 (823개, 99.4%)
**엔티티 추출**: ✅ 완료 (38개 약제-암종-요법 관계)
**다음 단계**: 지식 그래프 구축 (Neo4j) + NCC 사전 통합
