# 약제 마스터 데이터 매칭 작업 계획

**작성일**: 2025-10-27
**목표**: HIRA 암질환 데이터와 약가파일 정확한 매칭 (Fuzzy Matching 제외)

---

## 📋 현재 상황 (2025-10-27)

### ✅ 완료된 작업

1. **마스터 데이터 검토 완료**
   - 약가파일: 55,398개 약제 (47,722개 고유 제품) ✅
   - 상병마스터: 실제 데이터 아님 (변경내역 문서) - KCD-8 파싱 데이터로 대체 예정 ⏸️
   - 수가반영내역: 401,538개 항목 (제한적 활용) ✅

2. **약가 사전 구축 완료**
   - 파일: `data/hira_master/drug_dictionary.json` (56MB)
   - 검색 키: 70,431개
   - 매칭 레코드: 160,233개
   - 스크립트: `hira_master/build_drug_dictionary.py`

3. **KCD 매칭 TODO 작성**
   - 파일: `docs/TODO_KCD_MATCHING.md`
   - 우선순위: 낮음 (약제 매칭 후 진행)

### ⚠️ 발견된 문제점

#### 문제 1: 짧은 제품명 검색 불가
**현상**:
```
"옵디보" 검색 → 매칭 없음 ❌
"옵디보주" 검색 → 3개 매칭 ✅
"옵디보주100mg" 검색 → 1개 매칭 ✅
```

**원인**:
- 현재 키 생성 로직이 "주/정/캡슐"을 숫자와 함께 제거
- "옵디보주100mg" → "옵디보주" (O)
- "옵디보주" → "옵디보" (X) - 추가 단축 없음

**영향도**: 중간
- 성분명("니볼루맙")으로는 검색 가능
- 제품명으로만 언급된 경우 매칭 실패 가능성

#### 문제 2: 영문명 미지원
**현상**:
```
"opdivo" 검색 → 매칭 없음 ❌
"Tisagenlecleucel" 검색 → 매칭 없음 ❌
```

**원인**:
- 약가파일에는 한글 제품명만 존재
- 영문명 매핑 데이터 부재

**영향도**: 낮음 (선택적)
- 대부분 한글 문서
- 영문명은 괄호 안 성분명으로 표기

---

## 🎯 작업 계획

### Phase 1: 약가 사전 개선 (우선순위: 높음)

#### Task 1-1: 짧은 제품명 키 추가
**목표**: "옵디보주" → "옵디보" 검색 가능하게

**구현 방안**:
```python
# build_drug_dictionary.py 수정

def extract_search_keys(product_name):
    keys = []

    # 1. 전체 제품명 (괄호 앞)
    full_name = extract_before_parenthesis(product_name)  # "옵디보주100mg"
    keys.append(full_name)

    # 2. 숫자+단위 제거
    without_dosage = remove_dosage(full_name)  # "옵디보주"
    keys.append(without_dosage)

    # 3. 제형 제거 (NEW!)
    without_form = remove_dosage_form(without_dosage)  # "옵디보"
    if without_form != without_dosage:
        keys.append(without_form)

    # 4. 성분명 (괄호 안)
    ingredient = extract_ingredient(product_name)  # "니볼루맙"
    keys.append(ingredient)

    return keys

def remove_dosage_form(name):
    """제형 제거: 주, 정, 캡슐, 시럽 등"""
    forms = ['주', '정', '캡슐', '연질캡슐', '시럽', '액', '산', '크림', '연고']
    for form in forms:
        if name.endswith(form):
            return name[:-len(form)]
    return name
```

**예상 결과**:
- "옵디보" → 3개 제품 매칭 ✅
- "킴리아" → N개 제품 매칭 ✅

**소요 시간**: 30분
- 코드 수정: 15분
- 테스트 및 검증: 15분

**파일 수정**:
- `hira_master/build_drug_dictionary.py` (Line 55-85)

---

#### Task 1-2: 영문명 별칭 사전 구축 (선택적)
**목표**: "opdivo" → "옵디보주" 매핑

**구현 방안 A**: 수동 입력 (소규모)
```json
// data/hira_master/drug_aliases_eng.json
{
  "opdivo": ["옵디보주"],
  "keytruda": ["키트루다주"],
  "herceptin": ["허셉틴주"],
  "avastin": ["아바스틴주"],
  "kymriah": ["킴리아주"]
}
```

**구현 방안 B**: 외부 데이터 활용 (대규모)
- 식약처 의약품 데이터베이스
- DailyMed (FDA)
- 수동 매핑 (100개 주요 약제)

**우선순위**: 낮음
- 암질환 데이터 분석 후 필요성 판단
- 영문명 출현 빈도 확인

**소요 시간**:
- 방안 A: 2-3시간 (주요 약제 100개 수동 입력)
- 방안 B: 1주일 (외부 데이터 연동)

---

### Phase 2: 암질환 데이터 약제명 추출 (우선순위: 높음)

#### Task 2-1: 파싱 데이터 구조 분석
**목표**: 823개 파싱 파일에서 약제명이 어떻게 표현되는지 파악

**분석 대상**:
- `data/hira_cancer/parsed/announcement/` (469개)
- `data/hira_cancer/parsed/pre_announcement/` (298개)
- `data/hira_cancer/parsed/faq/` (56개)

**분석 항목**:
1. 약제명 표기 형태
   - "옵디보주" vs "옵디보" vs "니볼루맙"
   - 괄호 사용 여부: "옵디보(니볼루맙)"
   - 영문명 사용 빈도

2. 약제명 출현 위치
   - 표 (테이블) 내부
   - 본문 텍스트
   - 제목

3. 문맥 패턴
   - "~주 투여", "~정 복용"
   - 성분명 단독 사용
   - 제품명 + 성분명 병기

**구현**:
```python
# hira_cancer/analyze_drug_mentions.py

import json
from pathlib import Path
from collections import Counter

PARSED_DIR = Path('data/hira_cancer/parsed')

def extract_potential_drug_names(content):
    """
    가능한 약제명 패턴 추출
    - 괄호 패턴: X(Y)
    - 접미사 패턴: X주, X정, X캡슐
    - 표 패턴: 약제명 컬럼
    """
    patterns = []
    # ... 정규식 또는 NER
    return patterns

def analyze_all_files():
    all_mentions = Counter()

    for board in ['announcement', 'pre_announcement', 'faq']:
        board_dir = PARSED_DIR / board
        for file in board_dir.glob('*.json'):
            # 파일 읽기 및 분석
            mentions = extract_potential_drug_names(content)
            all_mentions.update(mentions)

    return all_mentions

# 실행
mentions = analyze_all_files()
print(f"총 약제명 후보: {len(mentions)}개")
print(f"상위 50개: {mentions.most_common(50)}")
```

**출력 예시**:
```
총 약제명 후보: 1,234개
상위 50개:
  1. 니볼루맙 (453회)
  2. 펨브롤리주맙 (321회)
  3. 옵디보 (287회)
  ...
```

**소요 시간**: 2-3시간

---

#### Task 2-2: 약제명 추출 규칙 개발
**목표**: 파싱 데이터에서 약제명 자동 추출

**전략**:
1. **표 기반 추출** (우선순위 1)
   - Markdown 표에서 "약제명", "성분명" 컬럼 찾기
   - 구조화된 데이터 → 정확도 높음

2. **정규식 기반 추출** (우선순위 2)
   - 패턴: `X주`, `X정`, `X캡슐`
   - 괄호 패턴: `X(Y)`

3. **문맥 기반 추출** (우선순위 3)
   - "~를/을 투여", "~의 급여인정"
   - 주변 문맥으로 약제 여부 판단

**구현**:
```python
# hira_cancer/extract_drugs_from_parsed.py

class DrugExtractor:
    def __init__(self, drug_dict_path):
        with open(drug_dict_path) as f:
            self.drug_dict = json.load(f)

    def extract_from_table(self, markdown):
        """표에서 약제명 추출"""
        # Markdown 표 파싱
        tables = parse_markdown_tables(markdown)

        drugs = []
        for table in tables:
            # "약제명", "성분명" 컬럼 찾기
            if '약제명' in table.columns:
                drugs.extend(table['약제명'].tolist())

        return drugs

    def extract_from_text(self, text):
        """본문에서 약제명 추출"""
        # 정규식 패턴
        pattern = r'([가-힣A-Za-z]+)(주|정|캡슐|시럽)'
        matches = re.findall(pattern, text)

        return [match[0] for match in matches]

    def match_with_master(self, candidate_names):
        """약가 사전과 매칭"""
        matched = []
        unmatched = []

        for name in candidate_names:
            normalized = normalize_key(name)
            if normalized in self.drug_dict:
                matched.append({
                    'original': name,
                    'normalized': normalized,
                    'master_record': self.drug_dict[normalized]['records'][0]
                })
            else:
                unmatched.append(name)

        return matched, unmatched
```

**소요 시간**: 4-6시간

---

#### Task 2-3: 전체 매칭 실행 및 검증
**목표**: 823개 파일 전체 약제명 추출 및 약가 사전 매칭

**구현**:
```python
# hira_cancer/run_drug_matching.py

extractor = DrugExtractor('data/hira_master/drug_dictionary.json')

results = {
    'total_files': 0,
    'total_candidates': 0,
    'matched': [],
    'unmatched': []
}

for board in ['announcement', 'pre_announcement', 'faq']:
    for file in Path(f'data/hira_cancer/parsed/{board}').glob('*.json'):
        with open(file) as f:
            data = json.load(f)

        # 약제명 추출
        candidates = extractor.extract_from_table(data['markdown'])
        candidates += extractor.extract_from_text(data['markdown'])

        # 매칭
        matched, unmatched = extractor.match_with_master(candidates)

        results['total_files'] += 1
        results['total_candidates'] += len(candidates)
        results['matched'].extend(matched)
        results['unmatched'].extend(unmatched)

# 결과 저장
with open('data/hira_cancer/drug_matching_results.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# 통계
match_rate = len(results['matched']) / results['total_candidates'] * 100
print(f"매칭률: {match_rate:.1f}%")
print(f"매칭 성공: {len(results['matched'])}개")
print(f"매칭 실패: {len(results['unmatched'])}개")
```

**예상 출력**:
```
총 파일: 823개
총 약제명 후보: 5,432개
매칭 성공: 4,123개 (75.9%)
매칭 실패: 1,309개 (24.1%)

상위 미매칭 약제:
  1. "옵디보" → "옵디보주"로 수정 필요
  2. "OPDIVO" → 영문명 별칭 추가 필요
  ...
```

**소요 시간**: 1-2시간 (실행 + 검증)

---

### Phase 3: 미매칭 해결 및 정확도 개선 (우선순위: 중간)

#### Task 3-1: 미매칭 원인 분석
**목표**: 매칭 실패한 약제명의 패턴 파악

**분석 항목**:
1. 약어/축약형 (예: "옵디보" vs "옵디보주")
2. 영문명 (예: "OPDIVO")
3. 오타 또는 비표준 명칭
4. 약가파일에 없는 약제 (보험 미등재)

**구현**:
```python
# hira_cancer/analyze_unmatched.py

def categorize_unmatched(unmatched_list, drug_dict):
    categories = {
        'short_form': [],      # "옵디보" (제형 누락)
        'english': [],         # "OPDIVO"
        'not_in_master': [],   # 약가파일 없음
        'ambiguous': []        # 판단 불가
    }

    for name in unmatched_list:
        # 제형 추가해서 재검색
        for form in ['주', '정', '캡슐']:
            if f"{name}{form}" in drug_dict:
                categories['short_form'].append((name, f"{name}{form}"))
                break

        # 영문 여부
        if re.match(r'^[A-Za-z]+$', name):
            categories['english'].append(name)

        # ...

    return categories
```

**소요 시간**: 1-2시간

---

#### Task 3-2: 별칭 사전 구축 및 적용
**목표**: 미매칭 해결을 위한 별칭 추가

**구현**:
```json
// data/hira_master/drug_aliases.json
{
  "약어": {
    "옵디보": "옵디보주",
    "킴리아": "킴리아주",
    "키트루다": "키트루다주"
  },
  "영문명": {
    "opdivo": "옵디보주",
    "kymriah": "킴리아주",
    "keytruda": "키트루다주"
  }
}
```

**적용**:
```python
# 매칭 시 별칭 우선 확인
def match_with_aliases(name, drug_dict, aliases):
    # 1차: 직접 매칭
    if name in drug_dict:
        return drug_dict[name]

    # 2차: 별칭 확인
    for category in aliases.values():
        if name in category:
            canonical = category[name]
            if canonical in drug_dict:
                return drug_dict[canonical]

    return None
```

**소요 시간**: 2-3시간 (수동 입력 포함)

---

#### Task 3-3: 최종 매칭률 달성
**목표**: 매칭률 90% 이상

**전략**:
1. Phase 1 개선 (짧은 키) → +10-15%
2. 별칭 사전 추가 → +5-10%
3. 수동 검증 및 보완 → +5%

**예상 최종 매칭률**: 75% → 90-95%

**소요 시간**: 전체 Phase 완료 시

---

## 📊 전체 일정

### Week 1: 약가 사전 개선 및 기초 분석
- [Day 1] Task 1-1: 짧은 제품명 키 추가 (30분)
- [Day 1-2] Task 2-1: 파싱 데이터 구조 분석 (2-3시간)
- [Day 3-4] Task 2-2: 약제명 추출 규칙 개발 (4-6시간)

### Week 2: 전체 매칭 및 검증
- [Day 1] Task 2-3: 전체 매칭 실행 (1-2시간)
- [Day 2] Task 3-1: 미매칭 원인 분석 (1-2시간)
- [Day 3-4] Task 3-2: 별칭 사전 구축 (2-3시간)
- [Day 5] Task 3-3: 최종 검증 및 보고서

### Week 3: 영문명 지원 (선택적)
- [Day 1-5] Task 1-2: 영문명 별칭 사전 구축 (2-3시간 또는 1주일)

---

## 🎯 성공 기준

### 필수 (Must Have)
- ✅ 매칭률 80% 이상
- ✅ 정확한 매칭 (Fuzzy 제외, Exact Match만)
- ✅ 성분명 기반 매칭 100% 지원
- ✅ 제품명 기반 매칭 70% 이상

### 선택 (Nice to Have)
- 📌 매칭률 90% 이상
- 📌 영문명 지원 (주요 약제 100개)
- 📌 자동화 스크립트 (정기 업데이트)

---

## 📁 산출물

### 코드
1. `hira_master/build_drug_dictionary.py` (수정)
2. `hira_cancer/analyze_drug_mentions.py` (신규)
3. `hira_cancer/extract_drugs_from_parsed.py` (신규)
4. `hira_cancer/run_drug_matching.py` (신규)
5. `hira_cancer/analyze_unmatched.py` (신규)

### 데이터
1. `data/hira_master/drug_dictionary.json` (개선)
2. `data/hira_master/drug_aliases.json` (신규)
3. `data/hira_master/drug_aliases_eng.json` (신규, 선택)
4. `data/hira_cancer/drug_matching_results.json` (신규)

### 문서
1. `docs/plans/drug_matching_master_plan.md` (본 문서)
2. `docs/TODO_KCD_MATCHING.md` (작성 완료)
3. `docs/reports/drug_matching_final_report.md` (작업 완료 시)

---

## 🚀 다음 작업 시작 시

**첫 실행 명령**:
```bash
# 1. 약가 사전 개선 (짧은 키 추가)
# → hira_master/build_drug_dictionary.py 코드 수정 후
python hira_master/build_drug_dictionary.py

# 2. 파싱 데이터 약제명 분석
python hira_cancer/analyze_drug_mentions.py

# 3. 전체 매칭 실행
python hira_cancer/run_drug_matching.py

# 4. 매칭률 확인
python hira_cancer/analyze_unmatched.py
```

**작업 재개 시 확인 사항**:
- [ ] 약가 사전 파일 존재 확인: `data/hira_master/drug_dictionary.json`
- [ ] 파싱 데이터 파일 수: 823개 (announcement: 469, pre_announcement: 298, faq: 56)
- [ ] 가상환경 활성화: `scraphub/Scripts/activate`

---

**작성자**: Claude Code
**최종 수정**: 2025-10-27
**예상 완료**: 2주 (핵심 기능), 3주 (영문명 포함)

---

수고하셨습니다! 🎉 내일 이어서 진행하시면 됩니다!
