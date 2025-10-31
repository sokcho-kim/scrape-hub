# 항암제 사전 구축 4-Phase 계획

## 📌 개요

### 목표
HIRA 항암 급여 문서에서 약제·질환·레짐을 정확히 추출하여 구조화 → 지식그래프 구축

### 핵심 원칙
1. **신뢰도 최우선**: 불확실한 방법론 배제
2. **코드 기반 매칭**: ATC 코드를 식별자로 사용
3. **정확 매칭만**: 퍼지/유사도 매칭 금지
4. **공식 데이터 우선**: 정부 약가 마스터 사용

### Ground Truth
- **데이터 소스**: `data/pharmalex_unity/merged_pharma_data_20250915_102415.csv`
- **전체 레코드**: 1,805,523개
- **항암제 필터링**: L01/L02 ATC 코드
- **결과**: 154개 성분, 939개 브랜드명

---

## Phase 1: 브랜드명/성분명 정제 ✅ COMPLETE

### 목표
약가 마스터에서 항암제 추출 및 브랜드명/성분명 정제

### 작업 내용

#### 1.1 항암제 추출
**스크립트**: `scripts/build_anticancer_bridge.py`

**로직**:
```python
# L01/L02 필터링
anticancer = df[
    df['ATC코드'].str.startswith('L01', na=False) |
    df['ATC코드'].str.startswith('L02', na=False)
]

# 성분별 집계
grouped = anticancer.groupby('일반명').agg({
    'ATC코드': 'first',
    '제품명': lambda x: list(x.unique()),
    '업체명': lambda x: list(x.unique()),
    '제품코드': lambda x: list(x.unique()),
    '주성분코드': 'first'
})
```

**출력**: `bridges/anticancer_master.json`
- 154개 성분
- 939개 브랜드명
- ATC 코드 매핑

#### 1.2 브랜드명/성분명 정제
**스크립트**: `scripts/clean_brand_ingredient.py`

**정제 규칙**:
```python
# 입력: "버제니오정50밀리그램(아베마시클립)_(50mg/1정)"

# 1. 괄호 안 → 성분명 추출
ingredient = "아베마시클립"

# 2. 괄호 앞 추출
left = "버제니오정50밀리그램"

# 3. 첫 숫자 앞까지 (용량 제거)
left = "버제니오정"

# 4. 제형 접미사 제거
FORM_SUFFIX = r"(서방)?정|캡슐|주|주사|주입액|현탁액|시럽|분말|과립|패치|펜|키트|액|연질|경질"
brand = "버제니오"
```

**출력**: `bridges/anticancer_master_clean.json`
```json
{
  "ingredient_ko_original": "abemaciclib",
  "atc_code": "L01EF03",
  "atc_name_en": "abemaciclib",
  "brand_names_clean": ["버제니오"],
  "brand_names_raw": ["버제니오정50밀리그램(아베마시클립)_(50mg/1정)", ...],
  "ingredient_ko_extracted": ["아베마시클립"],
  "ingredient_ko": "아베마시클립",
  "brand_name_primary": "버제니오",
  "manufacturers": ["한국릴리(유)"],
  "product_codes": ["670801140", "670801160", "670801180"],
  "ingredient_code": "686601ATB",
  "brand_count": 3
}
```

### 결과
- ✅ 브랜드명 정제: 939/939 (100%)
- ✅ 한글 성분명 추출: 148/154 (96.1%)
- ⚠️ 누락: 6개 성분 (영문명만 존재)

### 생성 파일
- `bridges/anticancer_master.json`: 원본 추출 데이터
- `bridges/anticancer_master_clean.json`: 정제된 데이터
- `bridges/anticancer_master_clean.csv`: CSV 백업
- `bridges/anticancer_master_clean_sample.json`: 검증용 샘플
- `logs/build_anticancer_bridge.log`: 추출 로그
- `logs/clean_brand_ingredient.log`: 정제 로그

---

## Phase 2: 한글 성분명 보완 🔄 PENDING

### 목표
누락된 한글 성분명 보완 및 염/기본형 분리

### 작업 항목

#### 2.1 누락 한글명 보완 (6개)
**방법**:
1. 약가 마스터 내 다른 레코드 검색
2. MFDS 의약품안전나라 API 조회
3. 수동 매핑 (최후 수단)

**예시**:
```python
# Before
{
  "ingredient_ko_original": "5-fluorouracil",
  "ingredient_ko": "5-fluorouracil"  # 영문명 그대로
}

# After
{
  "ingredient_ko_original": "5-fluorouracil",
  "ingredient_ko": "플루오로우라실"  # 한글명 보완
}
```

#### 2.2 염/기본형 분리
**문제**: "아비라테론아세테이트" vs "아비라테론"

**해결 전략** (RxNorm 구조 참고):
```python
{
  "ingredient_base_en": "abiraterone",        # 기본형 (영문)
  "ingredient_base_ko": "아비라테론",          # 기본형 (한글)
  "ingredient_precise_en": "abiraterone acetate",  # 정확한 형태
  "ingredient_precise_ko": "아비라테론아세테이트",   # 정확한 형태
  "salt_form": "acetate"                      # 염 형태
}
```

**염 형태 패턴**:
- 아세테이트 (acetate)
- 이말레산염 (maleate)
- 염산염 (hydrochloride)
- 황산염 (sulfate)
- 구연산염 (citrate)

#### 2.3 스키마 확장
**새 필드**:
```json
{
  "ingredient_base_en": "string",
  "ingredient_base_ko": "string",
  "ingredient_precise_en": "string",
  "ingredient_precise_ko": "string",
  "salt_form": "string | null",
  "is_recombinant": "boolean",
  "ingredient_source": "master | mfds | manual"
}
```

### 예상 출력
`bridges/anticancer_master_enhanced.json`

---

## Phase 3: ATC 기반 분류 강화 🔄 PENDING

### 목표
ATC 코드 기반 세분류 및 보조 약제 추가

### 작업 항목

#### 3.1 L01 세분류 (항종양제)
**현재**: L01 (135개 성분)

**세분류**:
- **L01A**: 알킬화제 (Alkylating agents)
  - L01AA: 질소 머스타드 유사체
  - L01AB: 에틸렌이민 유사체
  - L01AC: 니트로소우레아 유사체

- **L01B**: 대사길항제 (Antimetabolites)
  - L01BA: 엽산 유사체
  - L01BB: 퓨린 유사체
  - L01BC: 피리미딘 유사체

- **L01C**: 식물 알칼로이드 (Plant alkaloids)
  - L01CA: 빈카 알칼로이드
  - L01CB: 포도필로톡신 유도체
  - L01CD: 탁산

- **L01D**: 세포독성 항생제 (Cytotoxic antibiotics)
  - L01DA: 악티노마이신
  - L01DB: 안트라사이클린
  - L01DC: 기타

- **L01E**: 단백질 키나제 억제제 (Protein kinase inhibitors)
  - L01EA: BCR-ABL 억제제
  - L01EB: EGFR 억제제
  - L01EC: ALK 억제제
  - L01ED: ALK/ROS1 억제제
  - L01EF: CDK4/6 억제제
  - L01EL: BTK 억제제

- **L01F**: 단클론 항체 (Monoclonal antibodies)
  - L01FA: CD20 억제제
  - L01FB: EGFR 억제제
  - L01FC: HER2 억제제
  - L01FD: VEGF 억제제
  - L01FE: PD-1/PD-L1 억제제

- **L01X**: 기타 항종양제
  - L01XA: 백금 화합물
  - L01XB: 메틸히드라진
  - L01XC: 단클론 항체
  - L01XD: 감광제
  - L01XE: 단백질 키나제 억제제
  - L01XG: 프로테아좀 억제제
  - L01XH: HDAC 억제제
  - L01XX: 기타

#### 3.2 L02 세분류 (내분비치료)
**현재**: L02 (19개 성분)

**세분류**:
- **L02A**: 호르몬 및 관련 약제
  - L02AA: 에스트로겐
  - L02AB: 프로게스토겐
  - L02AE: GnRH 유사체

- **L02B**: 호르몬 길항제 및 관련 약제
  - L02BA: 항에스트로겐
  - L02BB: 항안드로겐
  - L02BG: 아로마타제 억제제
  - L02BX: 기타

#### 3.3 보조 약제 추가 고려
**범주**: 항암 치료 관련 필수 약제

**A04A: 진토제** (Antiemetics)
- A04AA: 세로토닌 (5-HT3) 길항제
  - 온단세트론, 그라니세트론, 팔로노세트론
- A04AD: NK1 수용체 길항제
  - 아프레피탄트, 로라피탄트

**M05B: 골전이 치료제** (Bone resorption inhibitors)
- M05BA: 비스포스포네이트
  - 졸레드론산, 파미드론산
- M05BX: 기타
  - 데노수맙 (RANKL 억제제)

**L03: 면역조절제** (Immunostimulants)
- L03AA: 집락자극인자 (G-CSF)
  - 필그라스팀, 페그필그라스팀

**V03: 기타 치료제**
- V03AF: 해독제
  - 레보폴린산 (류코보린)
  - 데스라조산 (심장보호제)

#### 3.4 스키마 확장
```json
{
  "atc_level1": "L01",
  "atc_level1_name_ko": "항종양제",
  "atc_level2": "L01E",
  "atc_level2_name_ko": "단백질 키나제 억제제",
  "atc_level3": "L01EF",
  "atc_level3_name_ko": "CDK4/6 억제제",
  "mechanism_of_action": "CDK4/6 억제",
  "therapeutic_category": "표적치료제"
}
```

### 데이터 소스
1. **WHO ATC/DDD Index**: https://www.whocc.no/atc_ddd_index/
2. **약가 마스터**: ATC코드 명칭 활용
3. **HIRA 약제급여목록**: 한글명 보완

### 예상 출력
`bridges/anticancer_master_classified.json`

---

## Phase 4: 코드 기반 매칭 구현 🔄 PENDING

### 목표
HIRA 텍스트 → 브랜드명 → ATC 코드 매핑 (정확 매칭만)

### 작업 항목

#### 4.1 브랜드명 인덱스 구축
**구조**:
```python
brand_index = {
    "버제니오": {
        "atc_code": "L01EF03",
        "ingredient_ko": "아베마시클립",
        "ingredient_en": "abemaciclib",
        "manufacturers": ["한국릴리(유)"],
        "brand_variants": ["버제니오정50밀리그램", "버제니오정100밀리그램", ...]
    },
    "자이티가": {
        "atc_code": "L02BX03",
        "ingredient_ko": "아비라테론",
        ...
    }
}
```

**파일**: `bridges/brand_index.json`

#### 4.2 텍스트 매칭 로직
**원칙**: 정확 매칭만 (No fuzzy matching)

**단계**:
1. **전처리**: 공백/특수문자 정규화
2. **정확 매칭**: 브랜드명 정확 일치
3. **변형 매칭**: 제형 포함 변형 (예: "버제니오정")
4. **성분명 매칭**: 한글 성분명 정확 일치

**코드**:
```python
def match_drug(text: str, brand_index: dict):
    """
    텍스트에서 약물 매칭 (정확 매칭만)

    Returns:
        {
            "matched": true/false,
            "brand": "버제니오",
            "atc_code": "L01EF03",
            "ingredient_ko": "아베마시클립",
            "match_type": "exact_brand" | "brand_variant" | "ingredient"
        }
    """
    # 1. 정확 브랜드명 매칭
    if text in brand_index:
        return {"matched": True, "match_type": "exact_brand", ...}

    # 2. 브랜드 변형 매칭 (제형 포함)
    for brand, info in brand_index.items():
        if text in info['brand_variants']:
            return {"matched": True, "match_type": "brand_variant", ...}

    # 3. 성분명 매칭
    for brand, info in brand_index.items():
        if text == info['ingredient_ko']:
            return {"matched": True, "match_type": "ingredient", ...}

    # 매칭 실패
    return {"matched": False}
```

#### 4.3 HIRA 문서 약물 추출
**입력**: HIRA 항암 급여 문서 (HTML 파싱 결과)

**로직**:
```python
def extract_drugs_from_hira_doc(html_content: str, brand_index: dict):
    """
    HIRA 문서에서 약물 추출
    """
    # 1. 테이블 파싱
    tables = parse_hira_tables(html_content)

    # 2. 약물 후보 추출 (패턴 기반)
    candidates = extract_drug_candidates(tables)

    # 3. 브랜드 인덱스 매칭
    matched_drugs = []
    for candidate in candidates:
        result = match_drug(candidate, brand_index)
        if result['matched']:
            matched_drugs.append(result)

    return matched_drugs
```

#### 4.4 출력 포맷
**파일**: `dictionary/drugs/hira_matched_drugs.json`

```json
[
  {
    "source_doc": "chemotherapy/공고책자_20251001.pdf",
    "source_section": "유방암",
    "drug_mention": "버제니오",
    "atc_code": "L01EF03",
    "ingredient_ko": "아베마시클립",
    "ingredient_en": "abemaciclib",
    "match_type": "exact_brand",
    "match_confidence": "high",
    "context": "호르몬 수용체 양성, HER2 음성 진행성 유방암에 버제니오와 아로마타제 억제제 병용요법"
  }
]
```

#### 4.5 검증 및 통계
**매칭 통계**:
```python
{
  "total_mentions": 523,
  "matched": 487,
  "unmatched": 36,
  "match_rate": 93.1%,
  "match_type_distribution": {
    "exact_brand": 412,
    "brand_variant": 51,
    "ingredient": 24
  }
}
```

**미매칭 분석**:
- 오타/약어: "허셉틴" → "허셉틴" (정상)
- 신약 미등재: 최근 허가 약물
- 복합제: "아비테론듀오" (아비라테론+프레드니솔론)
- 일반명: "백금제제", "면역항암제" (카테고리명)

### 제약사항
❌ **사용 금지**:
- 음차 유사도
- 편집 거리 (Levenshtein distance)
- 퍼지 매칭 (fuzzy matching)
- TF-IDF 유사도
- 임베딩 기반 유사도

✅ **사용 허용**:
- 정확 문자열 매칭
- 정규화 (공백/대소문자)
- 제형 접미사 제거 (기정의된 패턴만)
- ATC 코드 조회

---

## 데이터 플로우

```
┌─────────────────────────────────────────┐
│ 약가 마스터 (1.8M records)               │
│ merged_pharma_data_20250915_102415.csv  │
└────────────┬────────────────────────────┘
             │
             ▼ [Phase 1] L01/L02 필터링
┌─────────────────────────────────────────┐
│ anticancer_master.json (154 ingredients) │
│ - ATC 코드                               │
│ - 브랜드명 (raw)                         │
│ - 성분명 (원본)                          │
└────────────┬────────────────────────────┘
             │
             ▼ [Phase 1] 정제
┌─────────────────────────────────────────┐
│ anticancer_master_clean.json             │
│ - 브랜드명 (clean)                       │
│ - 성분명 (한글 추출)                     │
└────────────┬────────────────────────────┘
             │
             ▼ [Phase 2] 보완
┌─────────────────────────────────────────┐
│ anticancer_master_enhanced.json          │
│ - 한글명 보완 (154/154)                  │
│ - 염/기본형 분리                         │
└────────────┬────────────────────────────┘
             │
             ▼ [Phase 3] 분류
┌─────────────────────────────────────────┐
│ anticancer_master_classified.json        │
│ - ATC 세분류 (L01EA, L01EB, ...)        │
│ - 보조 약제 추가                         │
│ - 작용기전 태깅                          │
└────────────┬────────────────────────────┘
             │
             ▼ [Phase 4] 인덱싱
┌─────────────────────────────────────────┐
│ brand_index.json                         │
│ - 브랜드명 → ATC 매핑                    │
│ - 성분명 → ATC 매핑                      │
└────────────┬────────────────────────────┘
             │
             ▼ [Phase 4] 매칭
┌─────────────────────────────────────────┐
│ HIRA 문서                                │
│ chemotherapy/공고책자_20251001.pdf      │
└────────────┬────────────────────────────┘
             │
             ▼ 정확 매칭
┌─────────────────────────────────────────┐
│ hira_matched_drugs.json                  │
│ - 문서별 약물 목록                       │
│ - ATC 코드 매핑                          │
│ - 컨텍스트 보존                          │
└─────────────────────────────────────────┘
```

---

## 의존성 및 도구

### Python 패키지
```txt
pandas>=2.0.0
pyyaml>=6.0
```

### 외부 데이터 소스 (선택)
1. **WHO ATC/DDD Index**: ATC 세분류 및 한글명
   - URL: https://www.whocc.no/atc_ddd_index/
   - 접근: 공개 웹사이트

2. **MFDS 의약품안전나라**: 한글 성분명 보완
   - URL: https://nedrug.mfds.go.kr/
   - 접근: API 또는 크롤링

3. **UMLS/RxNorm** (선택사항):
   - 염/기본형 매핑 참고
   - 라이선스: 계정 필요 (1-2일 승인)
   - 우선순위: 낮음 (내부 데이터로 충분)

---

## 타임라인 (예상)

| Phase | 작업 | 예상 시간 | 상태 |
|-------|------|----------|------|
| Phase 1 | 브랜드명/성분명 정제 | 2 hours | ✅ DONE |
| Phase 2 | 한글명 보완 + 염 분리 | 3-4 hours | 🔄 PENDING |
| Phase 3 | ATC 세분류 + 보조약제 | 4-5 hours | 🔄 PENDING |
| Phase 4 | 매칭 구현 + 검증 | 5-6 hours | 🔄 PENDING |
| **Total** | | **14-17 hours** | 25% |

---

## 품질 보증

### 검증 항목
1. **데이터 완전성**:
   - [ ] 154개 성분 모두 한글명 존재
   - [ ] 939개 브랜드 모두 정제 성공
   - [ ] ATC 코드 100% 매핑

2. **매칭 정확도**:
   - [ ] False positive < 1%
   - [ ] False negative < 5%
   - [ ] 미매칭 원인 분석

3. **스키마 일관성**:
   - [ ] 모든 JSON 파일 스키마 검증
   - [ ] 필수 필드 누락 없음
   - [ ] 데이터 타입 일치

### 테스트 케이스
```python
# 정확 브랜드명 매칭
assert match_drug("버제니오", brand_index)['atc_code'] == "L01EF03"

# 브랜드 변형 매칭
assert match_drug("버제니오정", brand_index)['atc_code'] == "L01EF03"

# 성분명 매칭
assert match_drug("아베마시클립", brand_index)['atc_code'] == "L01EF03"

# 미매칭 (음차 금지)
assert match_drug("버제니", brand_index)['matched'] == False  # 오타
```

---

## 리스크 및 제약

### 리스크
1. **신약 미등재**: 최근 허가 약물이 약가 마스터에 없을 수 있음
   - 대응: MFDS 의약품안전나라 크롤링 추가

2. **복합제 처리**: 성분 2개 이상 포함 (예: "아비테론듀오")
   - 대응: 주성분 우선, 별도 복합제 플래그

3. **해외 약물**: 국내 미승인 약물 (임상시험, 특례수입)
   - 대응: 수동 추가 (낮은 우선순위)

### 제약사항
1. **데이터 갱신 주기**: 약가 마스터 2025년 9월 기준
   - 대응: 분기별 업데이트 스크립트

2. **한글명 표준화**: 동일 성분 여러 표기 (예: "플루오로우라실" vs "5-플루오로우라실")
   - 대응: 별칭 테이블 유지

---

## 관련 문서
- 작업 일지: `docs/journal/hira_cancer/2025-10-31_code_based_pivot.md`
- 프로젝트 README: `README.md` (업데이트 예정)
- 지식그래프 로드맵: `docs/knowledge_graph_roadmap.md`

---

## 변경 이력
- 2025-10-31: 초안 작성 (Phase 1 완료 후)
