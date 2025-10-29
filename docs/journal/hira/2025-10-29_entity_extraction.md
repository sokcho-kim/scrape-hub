# HIRA 암질환 공고 엔티티 추출 작업 일지

**날짜**: 2025-10-29
**작업자**: Claude Code
**프로젝트**: scrape-hub / HIRA 암질환 데이터
**목표**: HIRA 공고 문서에서 약제-암종-요법 관계를 구조화된 형태로 추출

---

## 📋 작업 개요

HIRA 암질환 공고 문서(217개)를 파싱하여 약제, 암종, 치료 요법 간의 관계를 추출하고 구조화된 JSON 데이터로 변환하는 작업을 완료했습니다.

## 🎯 작업 목표

1. HIRA 공고 텍스트에서 약제명 추출
2. 암종 정보 추출 (NCC 100개 암종 목록 기반)
3. 치료 요법 정보 추출 (병용/단독, 1차/2차 등)
4. 변경 유형 파악 (신설/변경/삭제)
5. 구조화된 JSON으로 저장

## 📊 최종 결과

### 처리 통계
- **입력 공고**: 217개
- **텍스트 내용 있는 공고**: 13개
- **추출된 관계**: 38개
- **고유 암종**: 16개
- **고유 약제**: 67개

### 변경 유형 분포
| 유형 | 개수 |
|------|------|
| 신설 | 22개 |
| 변경 | 8개 |
| 삭제 | 4개 |
| 추가 | 2개 |
| 미분류 | 2개 |

### 요법 유형 분포
| 유형 | 개수 |
|------|------|
| 병용요법 | 14개 |
| 단독요법 | 12개 |
| 미분류 | 12개 |

## 🔧 기술적 구현

### 1. 엔티티 추출기 개발
**파일**: `hira_cancer/parsers/entity_extractor.py`

```python
class HIRAEntityExtractor:
    def __init__(self):
        # NCC 암종 목록 (100개)
        self.cancer_types = self._load_cancer_types()

        # 약제 패턴 (유니코드 작은따옴표 지원)
        self.drug_pattern = re.compile(r"[\u2018\u201c]([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)[\u2019\u201d]")

        # 요법 패턴
        self.regimen_patterns = {
            'type': re.compile(r'(병용요법|단독요법|복합요법)'),
            'line': re.compile(r'(\d+차|차\s*이상)'),
            'purpose': re.compile(r'(고식적요법|보조요법|adjuvant|neoadjuvant)'),
        }

        # 변경 유형 패턴
        self.action_pattern = re.compile(r'(신설|변경|삭제|추가|개정)')
```

### 2. 주요 메서드

#### `extract_cancer_type(text)` - 암종 추출
- NCC 100개 암종 목록 기반 매칭
- 텍스트 내 암종명 포함 여부 검사

#### `extract_drugs(text)` - 약제명 추출
- 유니코드 작은따옴표(U+2018, U+2019) 패턴 매칭
- '+' 구분자로 병용 약제 분리
- 중복 제거 후 리스트 반환

#### `extract_regimen_info(text)` - 요법 정보 추출
- 병용요법 vs 단독요법
- 치료 단계 (1차, 2차, 3차 이상)
- 목적 (고식적요법, 보조요법, adjuvant, neoadjuvant)

#### `_split_sections(content)` - 섹션 분리
- '- ' 또는 'ㆍ'로 시작하는 항목 기준 분리
- 각 섹션별 독립적 엔티티 추출

## 🐛 트러블슈팅

### 문제 1: 약제명 추출 실패 (0개 매치)
**증상**: 정규표현식이 HIRA JSON의 약제명을 전혀 매치하지 못함

**원인**:
- 초기 패턴: ASCII 작은따옴표 `'` (U+0027) 사용
- 실제 데이터: 유니코드 Curly Quote `'` (U+2018), `'` (U+2019) 사용

**해결**:
```python
# 초기 (실패)
self.drug_pattern = re.compile(r"'([A-Z][a-zA-Z0-9\s\+\-]+?)'")

# 최종 (성공)
self.drug_pattern = re.compile(r"[\u2018\u201c]([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)[\u2019\u201d]")
```

**디버깅 과정**:
1. `debug_announcements.json` 생성 → 약제명이 육안으로 확인됨
2. `test_direct.py` 실행 → "작은따옴표 0개 발견"
3. `check_surrounding.py` - Dostarlimab 주변 유니코드 분석
4. **발견**: 'D' 앞 문자가 U+2018 (LEFT SINGLE QUOTATION MARK)
5. 유니코드 이스케이프 시퀀스 `\u2018`, `\u2019` 사용하여 해결

### 문제 2: Windows 콘솔 출력 인코딩 에러
**증상**:
```
UnicodeEncodeError: 'cp949' codec can't encode character '\uf09e'
```

**해결**: 샘플 출력을 콘솔 대신 JSON 파일로 저장
```python
# 콘솔 출력 대신
with open(sample_file, 'w', encoding='utf-8') as f:
    json.dump(samples, f, ensure_ascii=False, indent=2)
```

## 📁 생성된 파일

### 1. `data/hira_cancer/parsed/drug_cancer_relations.json`
전체 38개 관계의 완전한 데이터

**구조**:
```json
{
  "summary": {
    "total_relations": 38,
    "unique_cancers": 16,
    "unique_drugs": 67,
    "by_action": {...},
    "by_regimen_type": {...},
    "extracted_at": "2025-10-29T18:10:47.968430"
  },
  "relations": [
    {
      "cancer": "자궁암",
      "drugs": ["Dostarlimab", "Paclitaxel", "Carboplatin"],
      "regimen_type": "병용요법",
      "line": "1차",
      "purpose": "고식적요법",
      "action": "신설",
      "source_text": "...",
      "announcement_no": "제2025-210호",
      "date": "2025.10.1.",
      "board": "announcement"
    }
  ]
}
```

### 2. `data/hira_cancer/parsed/drug_cancer_relations_samples.json`
처음 10개 관계의 미리보기

## 💡 추출 결과 예시

### 예시 1: 자궁암 병용요법 (신설)
```json
{
  "cancer": "자궁암",
  "drugs": ["Dostarlimab", "Paclitaxel", "Carboplatin"],
  "regimen_type": "병용요법",
  "line": "1차",
  "purpose": "고식적요법",
  "action": "신설",
  "source_text": "- 자궁암에 'Dostarlimab + Paclitaxel + Carboplatin' 병용요법(1차, 고식적요법) 신설"
}
```

### 예시 2: 림프종 단독요법 (신설)
```json
{
  "cancer": "림프종",
  "drugs": ["Pirtobrutinib"],
  "regimen_type": "단독요법",
  "line": "3차",
  "purpose": null,
  "action": "신설",
  "source_text": "- 비호지킨림프종에 'Pirtobrutinib' 단독요법(3차 이상) 신설"
}
```

### 예시 3: 다발골수종 병용요법 (신설)
```json
{
  "cancer": "다발골수종",
  "drugs": ["Daratumumab", "Bortezomib", "Dexamethasone"],
  "regimen_type": "병용요법",
  "line": "2차",
  "purpose": null,
  "action": "신설"
}
```

## 📈 추출된 암종 목록 (16개)

자궁암, 림프종, 다발골수종, 위암, 신경내분비종양, 피부암, 폐암, 식도암, 담도암, 유방암, 난소암, 요로상피암, 전립선암, 두경부암, 백혈병, 만성림프구성백혈병

## 💊 추출된 주요 약제 (67개 중 일부)

- **면역항암제**: Pembrolizumab, Nivolumab, Dostarlimab, Durvalumab, Atezolizumab
- **표적치료제**: Trastuzumab, Bevacizumab, Olaparib, Pirtobrutinib, Osimertinib
- **세포독성 항암제**: Paclitaxel, Carboplatin, Cisplatin, Doxorubicin, 5-FU
- **기타**: Daratumumab, Bortezomib, Dexamethasone, Everolimus, Sunitinib

## 🎓 배운 점

1. **유니코드 처리의 중요성**:
   - 실제 데이터는 ASCII가 아닌 다양한 유니코드 문자 사용
   - 디버깅 시 바이트 레벨 분석 필요

2. **Windows 환경 인코딩**:
   - cp949 기본 인코딩 문제
   - UTF-8 명시적 지정 필요

3. **Regex 패턴 설계**:
   - Non-greedy 매칭 (`+?`) 중요
   - 문자 클래스에 특수문자(+, -, 괄호) 포함 필요

4. **데이터 품질**:
   - 217개 공고 중 13개만 텍스트 내용 보유
   - 나머지는 첨부파일(PDF/HWP)로만 제공
   - 향후 PDF 파싱 필요

## 🚀 다음 단계

### 지식 그래프 구축 로드맵 진행 상황
- [x] **1순위: HIRA 공고 문서 파싱** ✅ 완료
- [ ] 2순위: NCC 사전 엔티티 분류 (3,543개 용어)
- [ ] 3순위: 그래프 스키마 설계
- [ ] 4순위: Neo4j 데이터베이스 구축

### PDF 파싱 계획
- 나머지 204개 공고의 첨부파일(PDF/HWP) 파싱
- 예상 추가 관계: 500-1,000개
- 도구: pdfplumber, PyMuPDF, Upstage Document Parse API

### 데이터 품질 개선
- 약제명 표준화 (대소문자, 공백 처리)
- 암종명 매핑 (비호지킨림프종 → 림프종)
- 요법 정보 완성도 향상 (null 값 최소화)

## 📝 파일 목록

### 생성된 코드
- `hira_cancer/parsers/entity_extractor.py` - 메인 추출기
- `hira_cancer/parsers/debug_data.py` - 디버깅 스크립트
- `hira_cancer/parsers/test_extraction.py` - 테스트 스크립트

### 생성된 데이터
- `data/hira_cancer/parsed/drug_cancer_relations.json` (38개 관계)
- `data/hira_cancer/parsed/drug_cancer_relations_samples.json` (샘플 10개)

### 디버그 파일
- `hira_cancer/parsers/debug_announcements.json`
- `hira_cancer/parsers/surrounding_dostarlimab.json`
- `hira_cancer/parsers/test_results.json`

## ⏱️ 소요 시간

- 코드 개발: ~2시간
- 디버깅 (유니코드 문제): ~1시간
- 문서화: ~30분
- **총 소요 시간**: ~3.5시간

## ✅ 성공 지표

- ✅ 38개 약제-암종-요법 관계 추출
- ✅ 16개 고유 암종 식별
- ✅ 67개 고유 약제 식별
- ✅ 구조화된 JSON 데이터 생성
- ✅ 재현 가능한 추출 파이프라인 구축
- ✅ 지식 그래프 구축 준비 완료

---

**작업 완료일**: 2025-10-29
**다음 작업**: NCC 암 용어 사전 3,543개 엔티티 분류
