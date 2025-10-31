# 2025-10-31: 코드 기반 접근법으로 전환 및 약가 마스터 정제

## 📋 작업 요약

### 1. 기존 음차 유사도 접근법 폐기 결정
- **문제**: Pass-3/Pass-4 결과가 음차 유사도 기반으로 진행됨
- **이슈**: 불확실한 매칭 방법, 신뢰도 낮음
- **결정**: 전량 폐기하고 코드 기반 접근법으로 전환
- **근거**: 약가 마스터에 ATC 코드가 이미 존재, 확실한 매칭 가능

### 2. 약가 마스터 분석 및 항암제 추출
- **입력**: `data/pharmalex_unity/merged_pharma_data_20250915_102415.csv`
  - 전체 레코드: 1,805,523개
  - 파일 크기: 714 MB
- **필터링**: L01/L02 ATC 코드 (항암제)
  - L01: 항종양제 (Antineoplastic agents)
  - L02: 내분비치료제 (Endocrine therapy)
- **결과**:
  - 항암제 레코드: 3,796개
  - 고유 성분: 154개
  - 브랜드명: 939개

### 3. Phase 1: 브랜드명/성분명 정제 완료

#### 작업 내용
**스크립트**: `scripts/build_anticancer_bridge.py`
- 약가 마스터에서 L01/L02 필터링
- 성분별로 그룹화 및 집계
- 출력: `bridges/anticancer_master.json`

**스크립트**: `scripts/clean_brand_ingredient.py`
- 정규식 기반 브랜드명 정제
- 괄호 안에서 한글 성분명 추출
- 제형/용량 제거

#### 정제 규칙
```python
# 1. 괄호 안 → 성분명 추출
예: "버제니오정50밀리그램(아베마시클립)_(50mg/1정)"
→ ingredient: "아베마시클립"

# 2. 괄호 앞 → 브랜드명 (제형/용량 제거)
→ brand: "버제니오"
```

#### 성과
- **브랜드명 정제**: 939/939 성공 (100%)
- **한글 성분명 추출**: 148/154 성공 (96.1%)
- **출력 파일**:
  - `bridges/anticancer_master_clean.json` (메인)
  - `bridges/anticancer_master_clean.csv` (백업)
  - `bridges/anticancer_master_clean_sample.json` (검증용)

#### 샘플 결과
```json
{
  "ingredient_ko_original": "abemaciclib",
  "atc_code": "L01EF03",
  "atc_name_en": "abemaciclib",
  "brand_names_clean": ["버제니오"],
  "brand_names_raw": [
    "버제니오정50밀리그램(아베마시클립)_(50mg/1정)",
    "버제니오정150밀리그램(아베마시클립)_(0.15g/1정)",
    "버제니오정100밀리그램(아베마시클립)_(0.1g/1정)"
  ],
  "ingredient_ko_extracted": ["아베마시클립"],
  "ingredient_ko": "아베마시클립",
  "brand_name_primary": "버제니오"
}
```

## 📊 통계

### 데이터 규모
- 전체 약가 레코드: 1,805,523개
- 항암제 레코드: 3,796개 (0.21%)
- 고유 성분: 154개
- 브랜드명: 939개
- 평균 브랜드/성분: 6.1개
- 최대 브랜드 수: 62개 (한 성분)

### ATC 분류
- L01 (항종양제): 135개 성분
- L02 (내분비치료): 19개 성분

### 정제 성공률
- 브랜드명: 100% (939/939)
- 한글 성분명: 96.1% (148/154)
- 누락: 6개 성분 (영문명만 존재)

## 🔧 기술적 이슈 및 해결

### 1. Unicode 인코딩 문제
**증상**: `UnicodeDecodeError: 'cp949' codec can't decode byte`
**해결**: `encoding='utf-8-sig'` 사용
```python
df = pd.read_csv('data/pharmalex_unity/merged_pharma_data_20250915_102415.csv',
                 encoding='utf-8-sig', low_memory=False)
```

### 2. PyArrow 누락 경고
**증상**: `DeprecationWarning: Pyarrow will become a required dependency`
**영향**: Parquet 저장 불가
**해결**: JSON/CSV로 출력 포맷 변경

### 3. Windows 터미널 출력 오류
**증상**: `UnicodeEncodeError: 'cp949' codec can't encode character '\u26a0'`
**영향**: 통계 출력 시 이모지 표시 실패 (데이터 파일은 정상 저장)
**상태**: 무시 (기능에 영향 없음)

## 📁 생성된 파일

### 스크립트
- `scripts/build_anticancer_bridge.py`: 약가 마스터 → 항암제 추출
- `scripts/clean_brand_ingredient.py`: Phase 1 브랜드/성분명 정제

### 데이터
- `bridges/anticancer_master.json`: 154개 성분 + 939개 브랜드 (원본)
- `bridges/anticancer_master_clean.json`: 정제된 데이터 (메인)
- `bridges/anticancer_master_clean.csv`: CSV 백업
- `bridges/anticancer_master_clean_sample.json`: 검증용 샘플 (10개)
- `bridges/anticancer_master_sample.json`: 원본 샘플 (10개)

### 로그
- `logs/build_anticancer_bridge.log`: 항암제 추출 로그
- `logs/clean_brand_ingredient.log`: 정제 로그

## 🎯 Next Steps (4-Phase Plan)

### Phase 2: 한글 성분명 보완 (Pending)
- 누락된 6개 한글명 보완
- 염/기본형 분리 (예: "아비라테론아세테이트" → 기본형 "아비라테론")
- 필드 추가:
  - `ingredient_base_en`: 기본형 영문명
  - `ingredient_base_ko`: 기본형 한글명
  - `ingredient_precise_en`: 정확한 형태 (염 포함)

### Phase 3: ATC 기반 분류 강화 (Pending)
- L01/L02 세분류 (L01BC, L01EF 등)
- 보조 약제 추가 고려:
  - A04A: 진토제
  - M05B: 골전이 치료제
  - L03: 면역조절제

### Phase 4: 코드 기반 매칭 구현 (Pending)
- HIRA 텍스트 → 브랜드명 매칭 (정확 매칭)
- 브랜드명 → ATC 코드 조회
- 출력: ATC 코드가 할당된 약물 목록
- **원칙**: 음차/유사도 미사용, 코드 기반만 사용

## 💡 핵심 결정 사항

### 1. 접근법 전환
- ❌ **폐기**: 음차 유사도 기반 매칭
- ✅ **채택**: ATC 코드 기반 매칭

### 2. Ground Truth
- **정답지**: 약가 마스터 CSV (1.8M 레코드)
- **필터링**: L01/L02 ATC 코드
- **신뢰도**: 정부 공식 데이터

### 3. 데이터 정제 방향
- 중복 제거: 허가 시기 등으로 인한 중복 레코드
- 브랜드명 정제: 제형/용량 제거
- 성분명 보완: 한글명 우선, 염/기본형 분리

## 📌 참고사항

### 폐기된 작업물
- `dictionary/anchor/drug_pass3.yaml`: 60개 약물 (음차 기반)
- `dictionary/anchor/drug_pass4.yaml`: 63개 약물 (음차 기반)
- `scripts/refine_drug_anchors.py`: 음차 유사도 게이트 포함
- `scripts/harvest_candidates.py`: 패턴 기반 추출

### 아키텍처 원칙
1. **신뢰도 최우선**: 불확실한 방법론 배제
2. **코드 기반 매칭**: ATC 코드를 식별자로 사용
3. **정확 매칭만**: 퍼지/유사도 매칭 금지
4. **공식 데이터 우선**: 정부 약가 마스터 사용

## 🔗 관련 문서
- GPT 논의 내역: `C:\Jimin\notes\gpt_discussion_anticancer_plan.txt`
- 4-Phase 계획: `docs/plan/anticancer_dictionary_phases.md` (작성 예정)
- 프로젝트 README: 업데이트 예정
