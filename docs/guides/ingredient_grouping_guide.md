# 성분별 약제 그룹화 가이드

## 개요

`hira_master/tools/group_by_ingredient.py`를 사용하면 동일 성분의 약품들을 묶어서 볼 수 있습니다.

---

## 주요 기능

1. **성분명 검색** - 성분명으로 관련 약품 찾기
2. **성분코드 조회** - 특정 성분의 모든 제품 목록 보기
3. **제네릭 비교** - 동일 성분의 여러 제조사 제품 비교
4. **가격 비교** - 동일 성분 약품 간 가격 비교

---

## 사용법

### 1. 성분명으로 검색

```bash
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py --search "아세클로페낙"
```

**결과**:
```
=== 검색 결과: '아세클로페낙' ===
매칭된 성분: 4개

1. 성분코드: 100901ATB
   제품 예시: 센트로펜정(아세클로페낙)_(0.1g/1정)
   제품 수: 153개
   제조사 수: 152개
   가격 범위: 106원 ~ 188원

2. 성분코드: 100903ATR
   제품 예시: 아세크CR정(아세클로페낙)_(0.2g/1정)
   제품 수: 53개
   제조사 수: 53개
   가격 범위: 352원 ~ 414원
```

→ **동일 성분(아세클로페낙)이 153개 제품으로 나와있음을 확인!**

---

### 2. 특정 성분의 모든 제품 보기

```bash
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py --code "100901ATB"
```

**결과**:
```
=== 성분코드: 100901ATB ===
총 제품 수: 153개

제품 목록 (가격순):

1. 센트로펜정100밀리그램(아세클로페낙)_(0.1g/1정)
   제조사: (주)대웅제약바이오사업부
   약가: 188.0원
   투여경로: 내복

2. 아세크정(아세클로페낙)_(0.1g/1정)
   제조사: (주)유한양행
   약가: 188.0원
   투여경로: 내복

3. 아세론정(아세클로페낙)_(0.1g/1정)
   제조사: (주)화이트제약바이오
   약가: 188.0원
   투여경로: 내복
...
```

→ **153개 제네릭 약품의 제조사와 가격을 한눈에 비교!**

---

### 3. 제네릭이 많은 성분 TOP 10

```bash
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py
```

**결과**:
```
=== 제네릭이 가장 많은 성분 TOP 10 ===

1. 성분코드: 125201ACH
   제품 예시: 안국동아클로람캡슐(트리아졸람)(수출명:안국동아트리캡슐)_(0.25g/1캡슐)
   제품 수: 162개
   제조사 수: 164개
   가격 범위: 0원 ~ 438원

2. 성분코드: 136901ATB
   제품 예시: 클로피드정75밀리그램(클로피도그렐황산염)_(97.875mg/1정)
   제품 수: 165개
   제조사 수: 163개
   가격 범위: 0원 ~ 1164원
```

→ **경쟁이 가장 치열한 약품 확인 (제네릭 164개!)**

---

### 4. 결과를 JSON으로 저장

```bash
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py \
  --output data/hira_master/ingredient_groups.json
```

**생성되는 파일**:
- `data/hira_master/ingredient_groups.json`
- 전체 8,954개 성분별 그룹 데이터 포함
- API나 다른 프로그램에서 활용 가능

---

## 실전 활용 예시

### 예시 1: 혈압약 비교

```bash
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py --search "암로디핀"
```

→ 암로디핀 성분의 모든 제네릭 약품과 가격 확인

---

### 예시 2: 항생제 제네릭 찾기

```bash
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py --search "아목시실린"
```

→ 아목시실린 제네릭 목록과 제조사 확인

---

### 예시 3: 특정 성분의 가격 범위 확인

```bash
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py --code "136901ATB"
```

→ 클로피도그렐 (항혈소판제) 165개 제품의 가격 비교
→ 0원 ~ 1,164원까지 다양한 가격대 확인

---

## 핵심 통계

### 전체 데이터 현황

| 항목 | 수량 |
|------|------|
| 총 성분 수 | 8,954개 |
| 총 의약품 수 (유니크) | 49,952개 |
| 검색 키 수 | 91,699개 |
| 1개 성분당 평균 제품 수 | 약 5.6개 |

### 제네릭 경쟁 TOP 5

1. **트리아졸람** (수면제) - 164개 제조사
2. **클로피도그렐** (항혈소판제) - 163개 제조사
3. **로수바스타틴** (고지혈증) - 161개 제조사
4. **아세클로페낙** (소염진통제) - 161개 제조사
5. **로르카세린** (비만치료제) - 160개 제조사

---

## 데이터 구조

### ingredient_code (성분코드)

**형식**: `숫자6자리` + `문자3자리`
- 예: `100901ATB`
- 숫자: 성분 식별
- 문자: 제형 구분
  - `ATB` = 정제 (Tablet)
  - `ACH` = 캡슐 (Capsule)
  - `ATR` = 서방정 (Time-Release)
  - `BIJ` = 주사 (Injection)

### 그룹화 키

동일 성분 = **동일 ingredient_code**

예시:
```
아세클로페낙 100mg 정제 → 100901ATB
아세클로페낙 100mg 캡슐 → 100901ACH
아세클로페낙 200mg 서방정 → 100903ATR
```

→ **제형이 달라도 성분이 같으면 다른 코드!**

---

## 활용 시나리오

### 1. 제약사 관점
- 경쟁 제품 가격 모니터링
- 시장 점유율 분석
- 신규 제네릭 진입 기회 파악

### 2. 병원/약국 관점
- 동일 효능 저렴한 약품 찾기
- 대체 조제 가능 약품 확인
- 제조사별 공급 안정성 비교

### 3. 환자 관점
- 처방받은 약의 제네릭 확인
- 가격 비교로 의료비 절감
- 제조사 선택 정보 제공

---

## 주의사항

### 1. 가격이 0원인 경우
- 퇴출된 약품
- 급여 중단된 약품
- 데이터 오류 가능성

### 2. 동일 성분 ≠ 동일 효능
- 제형이 다르면 흡수율 다름 (정제 vs 서방정)
- 부형제가 달라 부작용 가능
- **반드시 의사/약사와 상담 필요!**

### 3. 최신 데이터 확인
- 현재 데이터: 2022.11 ~ 2025.11
- 최신 약가는 심평원 홈페이지 확인
- 정기적인 데이터 업데이트 필요

---

## 명령어 치트시트

```bash
# 성분명 검색
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py -s "아세클로페낙"

# 성분코드 조회
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py -c "100901ATB"

# TOP 20 제네릭
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py -t 20

# JSON 저장
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py -o data/output.json

# 도움말
scraphub/Scripts/python hira_master/tools/group_by_ingredient.py --help
```

---

## 관련 파일

- **도구**: `hira_master/tools/group_by_ingredient.py`
- **데이터**: `data/hira_master/drug_dictionary.json` (71 MB)
- **원본**: `data/hira_master/20221101_20251101 적용약가파일_사전제공 1부.xlsx`

---

**작성일**: 2025-11-03
**버전**: 1.0
