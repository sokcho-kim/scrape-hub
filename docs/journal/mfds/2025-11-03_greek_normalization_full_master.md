# 약가 마스터 전체 그리스 문자 정규화 작업 일지

**날짜**: 2025-11-03
**작업자**: Claude Code
**목표**: 전체 약가 마스터에 그리스 문자 정규화 적용 (항암제 한정에서 전체로 확장)

---

## 배경

기존에는 항암제 154개에 대해서만 그리스 문자 정규화를 시도했으나, 사용자 요청으로 전체 약가 파일에 대해 적용하기로 결정.

### 정규화 목적
- 그리스 문자 (α, β 등)를 ASCII (alpha, beta)로 변환
- 검색 편의성 향상 (키보드 입력 용이)
- 동의어 생성으로 다양한 표기법 지원

---

## 작업 단계

### 1. 전체 약가 마스터 파일 확인

```bash
data/hira_master/drug_dictionary.json
```

**파일 정보**:
- 크기: 71 MB
- 제품 수: 91,699개
- 구조: 제품명을 키로 하는 딕셔너리

### 2. 그리스 문자 약물 검색

**스크립트**: `mfds/utils/search_greek_in_master.py`

**검색 결과**:
- 전체 스캔: 91,699개 제품
- **그리스 문자 발견: 77개 약물**
- 발견된 그리스 문자: **α, β**

#### 주요 약물 타입

1. **인터페론알파-2α (Interferon alpha-2α)**
   - 항바이러스제/항암제
   - 제품 예: 그린알파주, 로페론에이주 등

2. **디클로페낙β-디메틸아미노에탄올 (Diclofenac β-dimethylaminoethanol)**
   - 소염진통제
   - 제품 예: 뉴베타주, 디로낙주, 디베타씨주 등

#### 저장 파일
```
data/mfds/greek_drugs_master.json
```

**구조**:
```json
{
  "total_count": 77,
  "greek_chars_found": ["α", "β"],
  "drugs": [
    {
      "product_name": "그린알파주300만아이유",
      "product_name_full": "그린알파주300만아이유(주사용건조인터페론알파-2α(유전자재조합))",
      "ingredient_code": "175502BIJ",
      "company": "(주)녹십자",
      "greek_chars": ["α"],
      "record_count": 1
    },
    ...
  ]
}
```

### 3. 정규화 동의어 생성 및 적용

**스크립트**: `mfds/workflows/apply_greek_normalization.py`

**정규화 규칙** (from `kp12_normalization_rules_v1.json`):
```json
{
  "α": "alpha",
  "β": "beta"
}
```

**처리 결과**:
- 84개 제품에 정규화 정보 추가 (77개에서 증가한 것은 동일 성분의 다양한 제품명)
- 7개의 새로운 검색 엔트리 생성
- 총 제품 수: 91,699 → 91,706개

#### 정규화 예시

**원본**: `디클로페낙β-디메틸아미노에탄올`
**동의어**:
- `디클로페낙beta-디메틸아미노에탄올`
- `디클로페낙beta디메틸아미노에탄올`

**원본**: `주사용건조인터페론알파-2α(유전자재조합)`
**동의어**:
- `주사용건조인터페론알파-2alpha(유전자재조합)`
- `주사용건조인터페론알파2alpha유전자재조합`

#### 출력 파일

```
data/hira_master/drug_dictionary_normalized.json
```

**파일 정보**:
- 크기: 76.59 MB
- 제품 수: 91,706개 (원본 + 정규화 엔트리)

**추가된 필드**:
```json
{
  "product_name": "그린알파주300만아이유",
  "records": [...],
  "greek_normalization": {
    "has_greek": true,
    "original_ingredient": "주사용건조인터페론알파-2α(유전자재조합)",
    "synonyms_en": [
      "주사용건조인터페론알파-2alpha(유전자재조합)",
      "주사용건조인터페론알파2alpha유전자재조합"
    ],
    "synonyms_ko": []
  }
}
```

---

## 통계 요약

| 항목 | 수치 |
|------|------|
| 전체 제품 수 (원본) | 91,699개 |
| 그리스 문자 약물 발견 | 77개 (0.08%) |
| 정규화 적용 제품 | 84개 |
| 새로운 검색 엔트리 | 7개 |
| 최종 제품 수 | 91,706개 |
| 발견된 그리스 문자 | α, β (2종) |

### 약물 분포

**인터페론 계열 (α)**:
- 그린알파주 (녹십자)
- 로페론에이주 (로슈)
- 인터맥스알파주 (LG화학)
- 기타

**디클로페낙 계열 (β)**:
- 뉴베타주 (케이엠에스제약)
- 디로낙주 (비씨월드제약)
- 디베타씨주 (대화제약)
- 뉴페낙주사 (아주약품)
- 기타

---

## 생성된 도구

### 1. `mfds/utils/search_greek_in_master.py`
**기능**: 약가 마스터 전체에서 그리스 문자 포함 약물 검색

**주요 로직**:
- 그리스 문자 유니코드 범위 패턴 매칭
- 단위 기호 (μg, μL) 제외
- product_name과 records 내부 모두 검색
- 중복 제거 및 통계 생성

**실행**:
```bash
scraphub/Scripts/python mfds/utils/search_greek_in_master.py \
  --input data/hira_master/drug_dictionary.json \
  --output data/mfds/greek_drugs_master.json
```

### 2. `mfds/workflows/apply_greek_normalization.py`
**기능**: 약가 마스터에 정규화 동의어 적용

**주요 로직**:
- GreekLetterNormalizer 사용하여 동의어 생성
- 기존 제품에 greek_normalization 필드 추가
- 정규화된 이름으로 새 검색 엔트리 생성
- 원본 데이터 보존

**실행**:
```bash
scraphub/Scripts/python mfds/workflows/apply_greek_normalization.py \
  --master data/hira_master/drug_dictionary.json \
  --greek-drugs data/mfds/greek_drugs_master.json \
  --output data/hira_master/drug_dictionary_normalized.json
```

### 3. 기존 도구 재사용
- `mfds/utils/greek_normalizer.py` (KP12 규칙 기반)
- `data/hira_master/normalization/kp12_normalization_rules_v1.json`

---

## 검증 및 테스트

### 정규화 검증

```python
# 그리스 문자 약물 수 확인
grep -c '"has_greek": true' drug_dictionary_normalized.json
# → 84개

# 새 엔트리 확인
python -c "
import json
with open('drug_dictionary_normalized.json') as f:
    data = json.load(f)
normalized = [k for k, v in data.items() if v.get('is_normalized')]
print(len(normalized))
"
# → 7개
```

### 검색 테스트 예시

**케이스 1**: `디클로페낙β` 검색
- 원본 키로 검색: ✅ (직접 매칭)
- `디클로페낙beta` 검색: ✅ (정규화 엔트리)

**케이스 2**: `인터페론알파-2α` 검색
- 원본 키로 검색: ✅
- `인터페론알파-2alpha` 검색: ✅ (정규화 엔트리)

---

## 다음 단계 제안

### 1. 추가 그리스 문자 확인
현재 α, β만 발견되었으나, 다른 그리스 문자도 확인 필요:
- γ (gamma) - 예: γ-globulin
- δ (delta)
- ω (omega) - 예: ω-3 fatty acids

### 2. 한글 동의어 추가
현재 영문 동의어만 생성됨. 한글 변환도 추가:
- α → "알파"
- β → "베타"

### 3. 검색 API 구현
정규화된 데이터를 활용한 검색 API:
```python
def search_drug(query):
    # 1. 정확한 매칭
    # 2. 정규화된 이름으로 매칭
    # 3. 동의어로 매칭
```

### 4. 품질 관리
- 정규화 결과 샘플링 검증
- 약사/의사 피드백 수집
- 오탐지/미탐지 케이스 분석

---

## 파일 목록

### 생성된 데이터 파일
- `data/mfds/greek_drugs_master.json` (77개 약물 목록)
- `data/hira_master/drug_dictionary_normalized.json` (91,706개 제품)

### 생성된 스크립트
- `mfds/utils/search_greek_in_master.py` (200+ lines)
- `mfds/workflows/apply_greek_normalization.py` (200+ lines)

### 수정된 파일
- 없음 (원본 데이터 보존)

---

## 성능 지표

- 검색 시간: ~30초 (91,699개 제품 스캔)
- 정규화 시간: ~45초 (84개 약물 처리)
- 파일 크기 증가: 71 MB → 76.59 MB (+7.9%)

---

## 결론

전체 약가 마스터 91,699개 제품에 대해 그리스 문자 정규화를 성공적으로 완료했습니다.

**핵심 성과**:
- ✅ 77개 그리스 문자 약물 식별 (α, β)
- ✅ 84개 제품에 정규화 정보 추가
- ✅ 7개 새로운 검색 엔트리 생성
- ✅ 원본 데이터 보존하면서 확장

**향후 활용**:
- 약물 검색 시스템 개선
- 약전-약가 매칭 정확도 향상
- 다국어 약물명 통합 관리

---

**작업 완료 시각**: 2025-11-03 (소요 시간: ~2시간)
