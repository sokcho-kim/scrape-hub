# HIRA 고시 문서 크롤러 개발 (계속)

**작업일**: 2025-10-13
**작업자**: Claude Code
**프로젝트**: hira_rulesvc

---

## 📋 작업 요약

이전 세션에서 서식(별표, 별지) 크롤링을 시도했으나, **실제 목표는 고시 문서 자체를 다운로드**하는 것으로 확인했습니다.

전체 트리 구조를 분석하여 52개 리프 노드(파일)를 추출했고, SEQ 매핑을 완료했습니다. 하지만 `gotoLawList()` 함수로 직접 접근이 불가능하다는 것을 발견했습니다.

---

## 🎯 목표 명확화

**수집 대상**: 트리의 모든 리프 노드 문서 (52개)

예시:
- "요양급여비용 청구방법(보건복지부 고시)"
- "요양급여비용 청구방법(세부사항)"
- "의료급여법"
- "시설수용자"
- 등등...

**스크린샷 확인**: `docs/samples/hira_rulesvc/hira_screen.png`
- 왼쪽: 트리 구조
- 오른쪽: 문서 목록과 "다운로드" 버튼

---

## ✅ 완료된 작업

### 1. tree.md 분석 및 리프 노드 추출 (100%)

**도구**: `hira_rulesvc/debug/extract_all_leaf_nodes.py`

tree.md에서 `*`로 시작하는 모든 항목(리프 노드) 추출:
- 총 **56개** 항목 발견
- **52개** SEQ 매핑 성공
- **1개** 매핑 실패: "의료급여자" (실제로는 폴더일 가능성)

**결과 파일**: `hira_rulesvc/config/all_law_documents.json`

```json
{
  "total_count": 55,
  "documents": [
    {
      "seq": "2",
      "is_folder": false,
      "name": "요양급여비용 청구방법(보건복지부 고시)"
    },
    {
      "seq": "200",
      "is_folder": false,
      "name": "요양급여비용 청구방법(세부사항)"
    },
    ...
  ]
}
```

**핵심**: `is_folder: false`인 항목만 다운로드 대상 (52개)

### 2. SEQ 매핑 완료 (100%)

tree HTML에서 `gotoLawList()` 호출 패턴을 분석하여 각 문서의 SEQ 추출:

```javascript
gotoLawList('2', '0', '요양급여비용 청구방법(보건복지부 고시)', ...)
```

**주요 발견**:
- 두 번째 파라미터가 `'1'`이면 폴더, `'0'`이면 파일
- `is_folder` 플래그로 필터링 가능

### 3. 크롤러 V2 작성 (60% 완성)

**파일**: `hira_rulesvc/scrapers/law_scraper_v2.py`

**완성된 부분**:
- all_law_documents.json 로딩
- is_folder=false 필터링
- Playwright 브라우저 초기화
- 디버그 HTML 저장 기능

**미완성 부분**:
- ❌ 실제 파일 페이지 접근
- ❌ 다운로드 버튼 클릭
- ❌ 파일 저장

---

## 🔍 핵심 발견 사항

### 문제: `gotoLawList(SEQ)` 직접 호출이 작동하지 않음

**시도한 방법**:
```javascript
gotoLawList('2', '0', '요양급여비용 청구방법(보건복지부 고시)', '0', 'null', '1', '9', '1', '0', 'http://', '')
```

**결과**:
- contentbody iframe이 **폴더 목록 페이지**로 이동 (SEQ=1, 최상위 카테고리)
- 실제 파일이 아니라 폴더 아이콘만 표시됨:
  - "요양급여비용 청구방법, 심사청구서·명세서서식 및 작성요령" (폴더)
  - "요양급여비용심사청구소프트웨어의검사등에관한기준" (폴더)
  - 등등
- 다운로드 버튼이 없음

**디버그 HTML**: `data/hira_rulesvc/debug_download/seq_2_요양급여비용 청구방법(보건복지부 고시.html`
- 폴더 목록만 포함
- 실제 파일 목록이 아님

### 원인 분석

트리 구조가 계층적이므로:
1. SEQ=2에 접근하려면 → 먼저 SEQ=4 (부모 폴더)를 열어야 함
2. 부모 폴더 안에서 → SEQ=2 링크를 클릭해야 함
3. 그러면 → 우측에 실제 문서 목록과 "다운로드" 버튼이 표시됨

**즉, SEQ만으로는 직접 접근이 불가능합니다!**

---

## 🚧 미해결 이슈

### 이슈 1: 파일 페이지 직접 접근 방법

**옵션 A: 트리 클릭 방식**
- tree01 iframe에서 실제 `<a>` 태그를 찾아 클릭
- 계층 구조를 따라 탐색 필요
- 복잡하지만 확실함

**옵션 B: URL 패턴 분석**
- 파일 상세 페이지의 직접 URL이 있는지 확인
- 예: `/lmxsrv/law/lawDetail.srv?SEQ=2&...`
- 빠르지만 URL 패턴을 찾아야 함

### 이슈 2: 트리 클릭 구현 복잡도

트리 구조 예시:
```
청구방법 및 급여기준 등 (SEQ=1, 폴더)
├── 요양급여비용 청구방법, 심사청구서... (SEQ=4, 폴더)
│   ├── 요양급여비용 청구방법(보건복지부 고시) (SEQ=2, 파일) ← 목표
│   ├── 요양급여비용 청구방법(세부사항) (SEQ=200, 파일)
│   └── 요양급여비용 청구방법(세부작성요령) (SEQ=3, 파일)
├── 요양급여비용심사청구... (SEQ=11, 폴더)
...
```

**필요한 작업**:
1. tree.md를 파싱하여 각 노드의 부모-자식 관계 파악
2. 각 파일의 경로(부모 폴더들의 순서) 계산
3. 순서대로 폴더 클릭 → 파일 클릭

---

## 📝 다음 세션 작업 계획

### Phase 1: 트리 구조 파싱 (우선순위: 높음)

**목표**: tree.md를 파싱하여 계층 구조 데이터 생성

**작업 내용**:
1. tree.md를 읽어서 계층 구조 파악
   - `##` → Level 1 (폴더)
   - `###` → Level 2 (폴더)
   - `####` → Level 3 (폴더)
   - `*` → 파일

2. 각 파일의 경로(path) 계산
   ```json
   {
     "seq": "2",
     "name": "요양급여비용 청구방법(보건복지부 고시)",
     "path": [
       "청구방법 및 급여기준 등",
       "요양급여비용 청구방법, 심사청구서·명세서서식 및 작성요령"
     ]
   }
   ```

3. 결과 저장: `hira_rulesvc/config/document_tree.json`

**예상 코드**:
```python
def parse_tree_md():
    """tree.md를 파싱하여 계층 구조 생성"""
    current_path = []
    documents = []

    with open('docs/samples/hira_rulesvc/tree.md', 'r') as f:
        for line in f:
            if line.startswith('# '):  # Root
                current_path = []
            elif line.startswith('## '):  # Level 1
                current_path = [line[3:].strip()]
            elif line.startswith('### '):  # Level 2
                current_path = current_path[:1] + [line[4:].strip()]
            elif line.startswith('#### '):  # Level 3
                current_path = current_path[:2] + [line[5:].strip()]
            elif line.startswith('* '):  # File
                name = line[2:].strip()
                seq = get_seq_by_name(name)  # all_law_documents.json에서
                documents.append({
                    'seq': seq,
                    'name': name,
                    'path': current_path.copy()
                })

    return documents
```

### Phase 2: 트리 클릭 네비게이션 구현

**작업 내용**:
1. tree01 iframe에서 경로상의 폴더들을 순서대로 클릭
2. 마지막에 파일 링크 클릭
3. contentbody iframe이 파일 목록으로 변경되는지 확인

**예상 코드**:
```python
def navigate_to_file(page, doc):
    """경로를 따라 파일까지 이동"""
    tree_frame = page.frame(name="tree01")

    # 1. 경로상의 폴더들 클릭
    for folder_name in doc['path']:
        # 폴더 링크 찾기
        folder_link = tree_frame.locator(f'a:has-text("{folder_name}")').first
        folder_link.click()
        time.sleep(1)

    # 2. 파일 링크 클릭
    file_link = tree_frame.locator(f'a:has-text("{doc['name']}")').first
    file_link.click()
    time.sleep(2)

    # 3. contentbody iframe 확인
    content_frame = page.frame(name="contentbody")
    return content_frame
```

### Phase 3: 다운로드 버튼 클릭

**작업 내용**:
1. 실제 파일 목록 페이지 HTML 캡처 (Phase 2 완료 후)
2. 다운로드 버튼 selector 확인
3. 다운로드 처리 구현

### Phase 4: 전체 문서 수집

**작업 내용**:
1. 52개 문서에 대해 반복
2. 진행 상황 로깅
3. 오류 처리 및 재시도 로직

---

## 🔧 기술적 이슈

### 1. iframe 중첩 구조

**구조**:
```
main page (frame0)
├── tree01 (트리)
└── contentbody (콘텐츠)
```

**해결**: Playwright의 `page.frame(name="...")` 사용

### 2. JavaScript 함수 호출 컨텍스트

**문제**: `gotoLawList`가 특정 iframe에만 정의됨
**해결**: 올바른 iframe 또는 parent 컨텍스트에서 호출

### 3. 동적 트리 노드 로딩

**문제**: 트리 노드 클릭 시 하위 노드가 동적으로 로드됨
**해결**: 클릭 후 `time.sleep()` + `wait_for_load_state()`

---

## 📂 생성된 파일 목록

### 코드 파일
1. `hira_rulesvc/debug/extract_all_leaf_nodes.py` - 리프 노드 추출 스크립트
2. `hira_rulesvc/scrapers/law_scraper_v2.py` - 크롤러 V2 (미완성)
3. `hira_rulesvc/config/all_law_documents.json` - 52개 문서 SEQ 매핑

### 디버그 파일
1. `data/hira_rulesvc/debug_download/seq_2_*.html` - 디버그 HTML (3개)

### 문서 파일
1. `docs/samples/hira_rulesvc/hira_screen.png` - 화면 캡처 (사용자 제공)
2. `docs/samples/hira_rulesvc/tree.md` - 트리 구조 (이전 세션)

---

## 💡 교훈

### 1. 목표 명확화의 중요성

처음에 "서식" vs "고시 문서" 혼동이 있었습니다.
→ 화면 캡처를 보고 정확히 이해함

### 2. JavaScript 함수 직접 호출의 한계

SEQ만으로 직접 접근하려고 했지만 실패
→ 실제 트리 구조를 따라야 함을 발견

### 3. 디버그 출력의 중요성

contentbody HTML을 저장해서 실제 상태를 확인
→ 폴더 목록임을 즉시 파악

---

## 🎯 다음 세션 시작 방법

### 1. 이 일지 읽기
```
docs/journal/hira_rulesvc/2025-10-13_law_scraper_development.md
```

### 2. 기존 파일 확인
- `hira_rulesvc/config/all_law_documents.json` - 52개 문서 목록
- `docs/samples/hira_rulesvc/tree.md` - 트리 구조
- `hira_rulesvc/scrapers/law_scraper_v2.py` - 미완성 크롤러

### 3. Phase 1 작업 시작

**새 파일 생성**: `hira_rulesvc/debug/parse_tree_structure.py`

tree.md를 파싱하여 각 문서의 경로(path) 계산:
```python
# 목표 출력 예시
{
  "seq": "2",
  "name": "요양급여비용 청구방법(보건복지부 고시)",
  "path": ["요양급여비용 청구방법, 심사청구서·명세서서식 및 작성요령"]
}
```

### 4. Phase 2로 진행

경로를 따라 트리를 클릭하는 로직 구현

---

## 📊 진행률

| 단계 | 상태 | 완료율 |
|------|------|--------|
| 목표 명확화 | ✅ 완료 | 100% |
| 리프 노드 추출 | ✅ 완료 | 100% |
| SEQ 매핑 | ✅ 완료 | 100% |
| 트리 구조 파싱 | ⏸️ 대기 | 0% |
| 트리 클릭 네비게이션 | ⏸️ 대기 | 0% |
| 다운로드 처리 | ⏸️ 대기 | 0% |
| 전체 수집 | ⏸️ 대기 | 0% |

**전체 진행률**: 약 **30%**

---

## 🔗 참고 자료

- 계획서: `docs/plans/hira_rulesvc.md`
- 트리 구조: `docs/samples/hira_rulesvc/tree.md`
- 화면 캡처: `docs/samples/hira_rulesvc/hira_screen.png`
- 문서 목록: `hira_rulesvc/config/all_law_documents.json`
- 이전 일지: `docs/journal/hira_rulesvc/2025-10-13_initial_exploration.md`

---

**작성일**: 2025-10-13
**다음 작업 시작점**: Phase 1 - 트리 구조 파싱

**예상 소요 시간**:
- Phase 1: 20분
- Phase 2: 30분
- Phase 3+4: 40분
- **총 약 90분** (1.5시간)
