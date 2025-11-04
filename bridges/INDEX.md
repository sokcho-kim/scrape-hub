# BRIDGES 폴더 데이터 색인

bridges 폴더는 여러 데이터 소스를 연결(bridge)하여 통합 마스터 데이터를 생성하는 중간 레이어입니다.

---

## 데이터 파이프라인

```
[원천 데이터]           [bridges/]                    [최종 결과]

HIRA (약가/제품)  ──┐
MFDS (허가정보)   ──┤
ATC (국제분류)    ──┼──> 통합 & 정규화 ──> 분석/서비스
NCC (암정보)      ──┤
항암화학요법      ──┘
```

---

## 1. MASTER - 원본 통합 데이터

여러 소스에서 수집한 항암제 데이터를 ATC 코드 기반으로 통합한 1차 결과물

### anticancer_master.csv (96 KB)
- **행 수**: 154개 (성분 기준)
- **컬럼**: 8개
  - `ingredient_ko`: 성분명 (한글/영문)
  - `atc_code`: ATC 코드 (L01*/L02*)
  - `atc_name_en`: ATC 영문명
  - `brand_names`: 브랜드명 목록 (문자열 리스트)
  - `manufacturers`: 제조사 목록 (문자열 리스트)
  - `product_codes`: 제품코드 목록 (문자열 리스트)
  - `ingredient_code`: 성분코드
  - `brand_count`: 브랜드 수
- **특징**:
  - 1개 성분 = 1개 행 (여러 제품이 리스트로 저장)
  - 브랜드명, 제조사, 제품코드가 문자열 형태의 리스트
  - HIRA 약가 마스터에서 L01/L02 코드 필터링

### anticancer_master.json (144 KB)
- 위 CSV의 JSON 버전

### anticancer_master_sample.json (5.3 KB)
- 구조 확인용 샘플 (5개 레코드)

---

## 2. CLEAN - 정제 데이터

브랜드명, 성분명 추출 및 정제가 완료된 데이터 (Phase 1 완료)

### anticancer_master_clean.csv (115 KB)
- **행 수**: 154개 (성분 기준)
- **컬럼**: 12개
  - `ingredient_ko_original`: 원본 성분명
  - `atc_code`, `atc_name_en`: ATC 정보
  - `ingredient_code`: 성분코드
  - `brand_count`: 브랜드 수
  - **정제된 필드**:
    - `brand_names_clean`: 정제된 브랜드명 목록 (간략명)
    - `brand_names_raw`: 원본 브랜드명 (전체)
    - `ingredient_ko_extracted`: 괄호에서 추출한 성분명
    - `ingredient_ko`: 최종 정리된 한글 성분명
    - `brand_name_primary`: 대표 브랜드명
  - `manufacturers`: 제조사 목록
  - `product_codes`: 제품코드 목록
- **특징**:
  - 브랜드명에서 불필요한 정보 제거 (용량, 규격 등)
  - 괄호 안 성분명 추출 (예: "유토랄주(플루오로우라실)" → "플루오로우라실")
  - 대표 브랜드명 선정

### anticancer_master_clean.json (189 KB)
- 위 CSV의 JSON 버전

### anticancer_master_clean_sample.json (7.6 KB)
- 구조 확인용 샘플 (5개 레코드)

---

## 3. NORMALIZED - 정규화 데이터 (최종 권장)

1 제품 = 1 행 구조로 정규화, HIRA dictionary와 조인하여 완전한 제품 정보 제공

### anticancer_normalized.csv (187 KB) ⚠️ 구버전
- **행 수**: 1,001개 (제품 기준)
- **컬럼**: 11개
- **문제점**: 제조사 매핑 불완전 (브랜드명/제품코드 개수 불일치)
- **상태**: deprecated, v2 사용 권장

### anticancer_normalized.json (426 KB) ⚠️ 구버전
- 위 CSV의 JSON 버전

### anticancer_normalized_v2.csv (283 KB) ✅ 최신
- **행 수**: 1,001개 (제품 기준)
- **컬럼**: 15개
  - **식별 정보**:
    - `product_code`: 제품코드 (9자리, 키)
    - `ingredient_code_original`: 원본 성분코드
    - `ingredient_code_hira`: HIRA 성분코드
  - **브랜드/제품명**:
    - `brand_name_short`: 간략 브랜드명
    - `brand_name_full`: 전체 브랜드명
    - `product_name_hira`: HIRA 공식 제품명
  - **규격/용량**:
    - `specification_brand`: 브랜드명 추출 규격
    - `specification_hira`: HIRA 규격
  - **성분 정보**:
    - `ingredient_ko_original`: 원본 성분명
    - `ingredient_in_brand`: 브랜드명 내 성분명
  - **ATC 분류**:
    - `atc_code`: ATC 코드
    - `atc_name_en`: ATC 영문명
  - **제조사/가격** (HIRA dictionary 조인):
    - `company`: 제조사명 (100% 매핑)
    - `price`: 약가 (원)
    - `route`: 투여경로 (주사/내복)
- **특징**:
  - HIRA dictionary와 제품코드 기반 완전 조인
  - 제조사 정보 100% 매핑 (1,001/1,001)
  - 약가 정보 100% 추가
  - 154개 성분 → 1,001개 개별 제품으로 확장
- **데이터 품질**:
  - 제조사: 121개
  - 평균 약가: 952,060원
  - 최고가: 킴리아주 (3.6억원)
  - 투여경로: 주사 63.3%, 내복 36.7%

### anticancer_normalized_v2.json (651 KB) ✅ 최신
- 위 CSV의 JSON 버전
- 배열 형태로 저장되어 API/웹 서비스에 적합

---

## 4. 스크립트 파일

### normalize_anticancer.py (5.0 KB) ⚠️ 구버전
- 최초 정규화 스크립트
- 제조사 매핑 문제로 v2로 대체됨

### normalize_anticancer_v2.py (7.6 KB) ✅ 최신
- HIRA dictionary 조인을 포함한 정규화 스크립트
- 기능:
  - 문자열 리스트 파싱
  - 제품코드별 행 분리
  - HIRA dictionary와 조인
  - 브랜드명/규격 파싱
  - CSV/JSON 출력

### test_hira_mapping.py (1.3 KB)
- HIRA dictionary 매핑 테스트
- 제품코드로 제조사 정보 조회 검증

### analyze_normalized_data.py (3.5 KB)
- 정규화 결과 분석 스크립트
- 통계, 품질 검증, 이슈 리포트

### create_index.py (6.7 KB)
- 이 색인 문서 생성 스크립트

---

## 권장 사용 방법

### ✅ 일반 사용
**anticancer_normalized_v2.csv** (또는 .json)
- 가장 최신이며 완전한 데이터
- HIRA dictionary 조인 완료
- 제조사, 약가, 투여경로 정보 포함
- 1,001개 제품, 154개 성분

### 사용 예시:
1. **항암제 검색/조회 시스템**
   ```python
   df = pd.read_csv('anticancer_normalized_v2.csv')
   result = df[df['brand_name_short'].str.contains('유토랄')]
   ```

2. **약가 비교 분석**
   ```python
   expensive = df.nlargest(10, 'price')
   ```

3. **제조사별 제품 현황**
   ```python
   company_stats = df.groupby('company').size()
   ```

4. **ATC 코드 기반 분류**
   ```python
   l01 = df[df['atc_code'].str.startswith('L01')]  # 항종양제
   l02 = df[df['atc_code'].str.startswith('L02')]  # 내분비요법
   ```

---

## 데이터 계보 (Lineage)

```
anticancer_master.csv (154행)
    └─> Phase 1: 정제
        anticancer_master_clean.csv (154행)
            └─> Phase 2: 정규화 v1
                anticancer_normalized.csv (1,001행) ⚠️
                    └─> Phase 3: HIRA 조인
                        anticancer_normalized_v2.csv (1,001행) ✅
```

---

## 다음 단계 (TODO)

- [ ] Phase 2: 한글명 보완 + 염/기본형 분리
- [ ] Phase 3: ATC 세분류 매핑
- [ ] Phase 4: 다른 소스와 코드 기반 매칭
  - MFDS 허가정보
  - NCC 암정보 사전
  - 항암화학요법 급여기준
- [ ] 버전 관리 정리 (deprecated 파일 아카이브)

---

**최종 수정**: 2025-11-04
**버전**: v2 (HIRA dictionary 조인)
