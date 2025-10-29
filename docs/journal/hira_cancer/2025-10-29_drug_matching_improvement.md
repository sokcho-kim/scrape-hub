# HIRA 암질환 데이터 - 약제명 매칭 개선 작업

**날짜**: 2025-10-29
**작업자**: Claude Code
**작업 범위**: 약가 사전 개선, 약제명 추출/매칭, 영문명 별칭 사전 구축

---

## 작업 배경

HIRA 암질환 파싱 데이터(823개 파일)에서 약제명을 추출하고 약가 사전과 매칭하는 작업 진행. 초기 매칭률이 낮아 단계별 개선 작업 수행.

### 핵심 과제
1. 짧은 약제명 매칭 실패 ("옵디보" vs "옵디보주")
2. 영문 약제명 매칭 부재 (paclitaxel, docetaxel 등)
3. 노이즈 필터링 (일반 명사 "개정", "인정" 등)

---

## Phase 1: 약가 사전 개선 (제형 제거 키 추가)

### 문제점
- 기존 사전: 제형이 포함된 정확한 이름만 매칭 ("옥살리플라틴주5밀리그램/밀리리터(10밀리리터)")
- 문서 내 짧은 표현: "옵디보", "킴리아" 등은 매칭 실패

### 해결 방법
**파일**: `hira_master/build_drug_dictionary.py`

제형 제거 로직 추가:
```python
dosage_forms = [
    '주', '정', '캡슐', '연질캡슐', '경질캡슐', '서방정', '서방캡슐',
    '시럽', '액', '현탁액', '용액', '주사', '주사액',
    '연고', '크림', '겔', '로션', '패치', '좌제', '좌약',
    '산', '과립', '세립', '분말', '산제',
    '점안액', '점비액', '점이액', '안연고',
    '흡입제', '스프레이', '에어로졸',
    '필름', '트로키', '츄정', '발포정'
]

# 버그 수정: 제형 제거를 항상 시도 (숫자 유무와 무관)
base_name = without_dosage if without_dosage else full_product_name
without_form = base_name

for form in dosage_forms:
    if base_name.endswith(form):
        without_form = base_name[:-len(form)].strip()
        break

if without_form and without_form != base_name:
    keys.append(without_form)  # "옵디보" or "킴리아"
```

### 결과
| 항목 | 이전 | 이후 | 증가율 |
|------|------|------|--------|
| 검색 키 수 | 70,431개 | 91,699개 | +30% |
| 파일 크기 | 56MB | 71MB | +27% |

**검증 성공**:
- "옵디보" → 매칭 ✅
- "킴리아" → 매칭 ✅

---

## Phase 2-1: 약제명 후보 추출 및 분석

### 목적
파싱된 문서에서 약제명 후보 추출 패턴 분석

**파일**: `hira_cancer/analyze_drug_mentions.py`

### 추출 패턴
```python
# 패턴 1: 제형 패턴
form_pattern = r'([가-힣A-Za-z]+)(주|정|캡슐|시럽|액|연고|크림|겔)\b'

# 패턴 2: 괄호 패턴
paren_pattern = r'([가-힣A-Za-z0-9]+(?:주|정|캡슐)?)\s*\(([^)]+)\)'
```

### 결과
| 항목 | 수치 |
|------|------|
| 총 파일 수 | 823개 |
| 총 후보 추출 (중복 포함) | 106,434회 |
| 고유 후보 수 | 60,927개 |

**문제점**: 노이즈 다수 포함 ("공고개정", "급여인정", "시행일" 등)

---

## Phase 2-2: 약가 사전 매칭 (v1)

### 전략
2단계 필터링 접근:
- **Phase 1**: Regex로 광범위 추출 (고재현율)
- **Phase 2**: 약가 사전 매칭으로 필터링 (고정밀도)

**파일**: `hira_cancer/extract_and_match_drugs.py`

### 매칭 로직
```python
for candidate in candidates:
    if candidate in drug_dict:
        matched_drugs[candidate]['count'] += 1
    else:
        unmatched_drugs[candidate] += 1
```

### 결과 (v1)
| 항목 | 수치 |
|------|------|
| 고유 후보 수 | 1,350개 |
| 매칭 성공 (고유) | 317개 (23.5%) |
| 매칭 실패 (고유) | 1,033개 (76.5%) |
| 노이즈 제거율 | 97.8% (60,927 → 1,350) |

**노이즈 제거 효과**:
- "공고개정", "급여인정", "시행일" 등 약가 사전에 없음 → 자동 제거 ✅

---

## Phase 3: 영문명 별칭 사전 구축

### 데이터 소스
**파일**: `data/pharmalex_unity/merged_pharma_data_20250915_102415.csv` (1.8M rows)

### v1: 초기 구축 (문제 발견)

**파일**: `hira_master/build_english_aliases.py`

```python
# 제품명에서 괄호 안 내용 추출
match = re.search(r'\(([^)]+)\)', product_name)
kor_ingredient = match.group(1).split(',')[0].strip()

# 문제: 규격까지 추출됨
# 예: "테바아나스트로졸정1밀리그램_(1mg/1정)" → "1mg/1정"
```

#### 결과 (v1)
- 총 매핑: 2,650개
- 약가 사전 검증: 1,876개 (70.8%)
- **문제 발견**: "anastrozole → 1mg/1정" (잘못된 매핑 379개, 14.3%)

---

### v2: 규격 필터링 추가 (수정)

**사용자 요청**: "괄호 안에 숫자/단위 패턴이 있으면 제외 (NEW!) 하는 로직 추가 해서 다시 작업해"

```python
# ⭐ NEW: 규격 필터링
if re.search(r'\d+\s*(?:mg|g|kg|ml|mL|L|μg|mcg|IU|/|%)', kor_ingredient, re.IGNORECASE):
    continue  # 규격이므로 건너뜀

# 추가 필터: 숫자로 시작하는 것도 제외
if re.match(r'^\d', kor_ingredient):
    continue
```

#### 결과 (v2)
| 항목 | v1 | v2 | 변화 |
|------|----|----|------|
| 총 매핑 수 | 2,650개 | 2,271개 | -379개 (-14.3%) |
| 약가 사전 검증 | 1,876개 | 1,876개 | 유지 |
| 잘못된 매핑 | 379개 | 0개 | **제거 완료** |

**수정 전후 비교**:
```
❌ anastrozole → 1mg/1정
✅ anastrozole → 아나스트로졸

❌ oxaliplatin → 10ml
✅ oxaliplatin → 옥살리플라틴

❌ busulfan → 바이알
✅ busulfan → 부설판

❌ dexamethasone → 5g
✅ dexamethasone → 덱사메타손
```

---

## Phase 4: 재매칭 (v3) - 영문명 별칭 적용

**파일**: `hira_cancer/extract_and_match_drugs_v2.py`

### 개선된 매칭 로직
```python
def match_drug(candidate, drug_dict, eng_aliases):
    # 1. 직접 매칭 (약가 사전)
    if candidate in drug_dict:
        return (True, candidate, 'direct')

    # 2. 영문명 별칭 매칭
    candidate_lower = candidate.lower()
    if candidate_lower in eng_aliases:
        korean_name = eng_aliases[candidate_lower]
        if korean_name in drug_dict:
            return (True, korean_name, 'english_alias')

    # 3. 미매칭
    return (False, candidate, 'unmatched')
```

### 최종 결과 (v3)

| 버전 | 매칭 성공 | 매칭률 | 개선 효과 |
|------|----------|--------|----------|
| v1 (영문명 없음) | 317개 | 23.5% | - |
| **v3 (영문명 + 규격 필터링)** | **377개** | **27.9%** | **+60개 (+4.4%p)** |

#### 세부 분석
- **직접 매칭**: 314개 (한글 약제명)
- **영문명 별칭**: 63개 (영문 → 한글 변환)
- **매칭 실패**: 970개 (의학용어, 미등록 약제 등)

#### 영문명 별칭 효과 Top 10
| 영문명 | 한글명 | 출현 횟수 |
|--------|--------|----------|
| docetaxel | 도세탁셀 | 36회 |
| paclitaxel | 파클리탁셀 | 36회 |
| rituximab | 리툭시맙 | 32회 |
| anastrozole | 아나스트로졸 | 32회 |
| capecitabine | 카페시타빈 | 32회 |
| letrozole | 레트로졸 | 31회 |
| oxaliplatin | 옥살리플라틴 | 31회 |
| exemestane | 엑스메스탄 | 31회 |
| cetuximab | 세툭시맙 | 31회 |
| heptaplatin | 헵타플라틴 | 30회 |

---

## 최종 성과

### 정량적 성과
1. **약가 사전 개선**: 70,431 → 91,699 검색 키 (+30%)
2. **노이즈 제거**: 60,927 → 1,350 후보 (97.8% 정화)
3. **매칭률 향상**: 23.5% → 27.9% (+4.4%p)
4. **영문명 매칭**: 63개 약제 추가 매칭

### 정성적 성과
1. **제형 제거 키 추가**로 짧은 약제명 매칭 가능
2. **2단계 필터링**으로 노이즈 자동 제거 (수동 블랙리스트 불필요)
3. **영문명 별칭 사전**으로 국제 표준명 매칭 지원
4. **규격 필터링**으로 매핑 품질 개선 (379개 잘못된 매핑 제거)

---

## 파일 목록

### 생성/수정된 코드
| 파일 | 설명 |
|------|------|
| `hira_master/build_drug_dictionary.py` | 약가 사전 구축 (제형 제거 키 추가) |
| `hira_cancer/analyze_drug_mentions.py` | 약제명 후보 분석 |
| `hira_cancer/extract_and_match_drugs.py` | v1 매칭 (한글만) |
| `hira_master/build_english_aliases.py` | 영문명 별칭 사전 구축 (규격 필터링 포함) |
| `hira_cancer/extract_and_match_drugs_v2.py` | v3 매칭 (한글 + 영문) |

### 생성된 데이터
| 파일 | 크기 | 설명 |
|------|------|------|
| `data/hira_master/drug_dictionary.json` | 71MB | 91,699개 검색 키 |
| `data/hira_master/drug_aliases_eng.json` | 128KB | 2,271개 영문→한글 매핑 |
| `data/hira_cancer/drug_matching_results_v2.json` | 11.7KB | v3 매칭 결과 |

---

## 추가 개선 가능 영역

### 미매칭 영문 약제 (Top 10)
pharmalex_unity CSV에 없어 매칭 실패:

| 영문명 | 출현 횟수 | 비고 |
|--------|----------|------|
| fludarabine | 33회 | 백혈병 치료제 |
| gemcitabine | 33회 | 항암제 |
| bortezomib | 32회 | 다발성골수종 치료제 |
| erlotinib | 31회 | 폐암 표적치료제 |
| irinotecan | 30회 | 대장암 치료제 |
| anagrelide | 30회 | 혈소판감소제 |
| belotecan | 30회 | 소세포폐암 치료제 |
| topotecan | 30회 | 난소암/폐암 치료제 |
| pemetrexed | 28회 | 폐암 치료제 |
| raltitrexed | 28회 | 대장암 치료제 |

### 개선 방안
1. **수동 별칭 추가**: 미매칭 영문명 수동 입력
2. **제품명 패턴 학습**: "티에스원캡슐", "제바린키트주" 등 브랜드명 매칭
3. **의학용어 사전**: palliative, adjuvant, neoadjuvant 등 별도 수집

---

## 다음 단계

- [ ] KCD 코드 매칭 (TODO_KCD.md 참조)
- [ ] 의학용어 사전 구축 (별도 데이터 소스 필요)
- [ ] 미매칭 약제 수동 검토 및 별칭 추가
- [ ] 최종 매칭 결과 활용 (데이터 분석, 시각화)

---

## 참고 문서
- `docs/TODO_KCD.md`: KCD 코드 매칭 계획
- `docs/journal/hira_cancer/2025-10-24_attachment_parsing.md`: 이전 작업 (파싱 완료)
- `docs/drug_matching_master_plan.md`: 전체 계획서
