# HIRA 규칙 서비스 크롤러 초기 탐색

**작업일**: 2025-10-13
**작업자**: Claude Code
**프로젝트**: hira_rulesvc

---

## 📋 작업 요약

HIRA 규칙 서비스 크롤러 개발을 시작했습니다. 초기 계획에서는 폼 제출 방식을 사용하려 했으나, 실제 사이트 분석 결과 **트리 클릭 방식**이 필요함을 확인했습니다.

---

## 🎯 목표

건강보험심사평가원 청구방법 및 급여기준 조회시스템에서 서식(attach) 첨부파일을 자동으로 수집하는 크롤러 개발.

**대상 사이트**: http://rulesvc.hira.or.kr/lmxsrv/main/main.srv

---

## ✅ 완료된 작업

### 1. SEQ 매핑 테이블 완성 (100%)

**파일**: `hira_rulesvc/config/seq_mapping.py`

- 총 59개 고시 → SEQ 매핑 완료
- `tree.md`의 트리 구조를 분석하여 매핑 테이블 생성
- 기능:
  - `get_seq_by_name()`: 정확한 고시명으로 SEQ 조회
  - `get_seq_by_partial_match()`: 부분 일치로 SEQ 조회
  - `get_name_by_seq()`: SEQ로 고시명 역조회
  - `list_all_notices()`: 전체 목록 출력

**예시**:
```python
from hira_rulesvc.config import get_seq_by_name

seq = get_seq_by_name("요양급여비용 청구방법(보건복지부 고시)")
# seq = "2"
```

### 2. 프로젝트 구조 정리 (100%)

**폴더 구조**:
```
hira_rulesvc/
├── config/
│   ├── __init__.py
│   └── seq_mapping.py          # SEQ 매핑 테이블
├── scrapers/
│   ├── __init__.py
│   ├── attach_scraper.py       # 서식 스크래퍼 (미완성)
│   └── template.py             # 템플릿
└── debug/
    ├── interactive_explore.py  # 대화형 탐색 (실패)
    └── auto_capture.py         # 자동 페이지 캡처 (성공)

docs/samples/hira_rulesvc/
├── hira_rulesvc.html           # 메인 페이지 HTML
└── tree.md                     # 트리 구조

data/hira_rulesvc/
├── debug/                      # 캡처된 페이지들
│   ├── step1_main_*.html
│   ├── step2_attach_tab_*.html
│   ├── step3_seq2_submit_*.html
│   ├── step4_law_tab_*.html
│   └── *.png (스크린샷)
└── seq_2/                      # 초기 테스트 결과
    └── meta.jsonl
```

### 3. 페이지 탐색 및 분석 (100%)

**도구**: `auto_capture.py`를 사용하여 4단계 페이지 캡처 완료

1. **메인 페이지**: 초기 진입
2. **서식정보 탭 클릭**: `menu_go('2')` 실행
3. **SEQ=2 폼 제출**: 폼 제출 시도 (실패)
4. **고시정보 탭 클릭**: `menu_go('1')` 실행

**발견된 iframe 구조**:
- `frame0`: 메인 페이지
- `tree01`: 좌측 트리 (528KB HTML)
- `contentbody`: 우측 콘텐츠

---

## 🔍 핵심 발견 사항

### 문제: 폼 제출 방식이 작동하지 않음

**시도한 방법**:
```javascript
document.getElementById('SEQ').value = '2';
document.getElementById('SEQ_ATTACH_TYPE').value = '0';
document.getElementById('SEARCH_TYPE').value = 'all';
document.getElementById('seachForm').action = '/lmxsrv/attach/attachList.srv';
document.getElementById('seachForm').submit();
```

**결과**:
- contentbody iframe이 여전히 `submain.srv`(대시보드)를 표시
- 서식 목록 페이지로 이동하지 않음
- 표시된 내용: "자주보는 서식", "최근 고시정보"

### 해결책: 트리 클릭 방식 필요

**분석 결과**:
1. `tree01` iframe에서 트리 노드를 클릭해야 함
2. 트리 클릭 → `contentbody` iframe이 목록 페이지로 변경됨
3. 문서 명세(`docs/plans/hira_rulesvc.md`)가 정확했음

**tree01 iframe**:
- 크기: 528KB (대용량)
- 구조: 복잡한 트리 노드 HTML
- 동작: jQuery 기반 동적 트리

---

## 📊 데이터 분석

### 캡처된 페이지 분석

| 단계 | contentbody URL | 상태 | 비고 |
|------|-----------------|------|------|
| step1 | submain.srv | ✓ | 초기 메인 페이지 |
| step2 | submain.srv | ✓ | 서식정보 탭 (여전히 대시보드) |
| step3 | submain.srv | ✗ | 폼 제출 실패 |
| step4 | lawListManager.srv | ✓ | 고시정보 탭 (다른 페이지) |

**결론**: 서식 목록으로 진입하려면 트리 클릭이 필수!

---

## 🚧 미완성 작업

### 1. attach_scraper.py (30% 완성)

**완성된 부분**:
- 기본 클래스 구조
- SEQ 매핑 통합
- 폼 제출 네비게이션 (작동 안 함)
- 기본 파싱 로직
- 다운로드 처리 로직
- 메타데이터 저장

**미완성 부분**:
- ❌ 트리 클릭 네비게이션
- ❌ 실제 목록 페이지 HTML 구조 파악
- ❌ 다운로드 버튼 실제 동작 확인
- ❌ 페이지네이션 구현

### 2. 실제 목록 페이지 HTML 필요

현재까지 확인한 페이지:
- ✓ 메인 대시보드 (`submain.srv`)
- ✗ 서식 목록 페이지 (아직 접근 못함)

**필요한 작업**:
1. tree01 iframe에서 노드 클릭
2. 변경된 contentbody iframe HTML 캡처
3. 테이블 구조 분석
4. 다운로드 버튼 selector 확인

---

## 📝 다음 세션 작업 계획

### Phase 1: 트리 클릭 네비게이션 구현 (우선순위: 높음)

**작업 내용**:
1. `tree01` iframe HTML 분석 (이미 캡처됨: `step1_main_tree01.html`)
2. 트리 노드 selector 찾기
3. TARGET_NODE_TEXT로 노드 찾기 로직 구현
4. 클릭 후 contentbody 변경 대기

**예상 코드**:
```python
def navigate_via_tree(self, page: Page, target_text: str):
    """트리에서 노드 클릭하여 목록 페이지 진입"""
    # tree01 iframe 접근
    tree_frame = page.frame(name="tree01")

    # 노드 찾기 (부분 일치)
    nodes = tree_frame.query_selector_all('a')
    for node in nodes:
        text = node.inner_text()
        if target_text in text:
            node.click()
            break

    # contentbody 변경 대기
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # contentbody iframe 재참조
    content_frame = page.frame(name="contentbody")
    return content_frame
```

### Phase 2: 실제 목록 페이지 HTML 캡처

**작업 내용**:
1. `auto_capture.py` 수정하여 트리 클릭 추가
2. 트리 클릭 후 contentbody HTML 저장
3. 테이블 구조 분석
4. 다운로드 버튼 selector 확인

**추가할 단계**:
```python
# 5. 트리에서 "요양급여비용 청구방법(보건복지부 고시)" 클릭
print("\n5. 트리 노드 클릭")
tree_frame = page.frame(name="tree01")
# ... 노드 찾아서 클릭
save_all_frames(page, "step5_after_tree_click")
```

### Phase 3: 목록 파싱 로직 수정

**작업 내용**:
1. 실제 HTML 구조에 맞게 selector 수정
2. 컬럼 구조 확인 (번호, 제목, 서식 타입, 파일명, 다운로드)
3. 다운로드 버튼 클릭 방식 확인

### Phase 4: 다운로드 처리 검증

**작업 내용**:
1. 다운로드가 실제로 트리거되는지 확인
2. 파일명 추출 방식 확인
3. 타임아웃 조정

### Phase 5: 페이지네이션 구현

**작업 내용**:
1. 목록 하단 페이지네이션 구조 확인
2. "다음" 버튼 selector 찾기
3. 마지막 페이지 감지 로직

---

## 🔧 기술적 이슈

### 1. iframe 중첩 구조

**문제**: 2단계 iframe (메인 → tree01/contentbody)
**해결**: Playwright의 `page.frame(name="...")` 사용

### 2. 동적 jQuery 기반 페이지

**문제**: 트리 클릭이 JavaScript로 처리됨
**해결**: `wait_for_load_state("networkidle")` + 추가 대기

### 3. 다운로드 타임아웃

**문제**: 60초 다운로드 타임아웃 발생
**원인**: 다운로드 버튼이 실제로 다운로드를 트리거하지 않았을 가능성
**해결**: 실제 목록 페이지 확인 후 재검증 필요

### 4. Windows 인코딩 이슈

**문제**: 이모지(✓, ✗) 출력 시 UnicodeEncodeError
**해결**: `[OK]`, `[FAIL]` 등 ASCII 텍스트로 대체

---

## 📂 생성된 파일 목록

### 코드 파일
1. `hira_rulesvc/config/seq_mapping.py` - SEQ 매핑 테이블
2. `hira_rulesvc/config/__init__.py` - Config 패키지 초기화
3. `hira_rulesvc/scrapers/attach_scraper.py` - 서식 스크래퍼 (미완성)
4. `hira_rulesvc/debug/auto_capture.py` - 자동 페이지 캡처 도구

### 데이터 파일
1. `data/hira_rulesvc/debug/step1_main_*.html` (3개)
2. `data/hira_rulesvc/debug/step2_attach_tab_*.html` (3개)
3. `data/hira_rulesvc/debug/step3_seq2_submit_*.html` (3개)
4. `data/hira_rulesvc/debug/step4_law_tab_*.html` (3개)
5. `data/hira_rulesvc/debug/*.png` (4개 스크린샷)

### 문서 파일
1. `docs/samples/hira_rulesvc/hira_rulesvc.html` - 메인 페이지
2. `docs/samples/hira_rulesvc/tree.md` - 트리 구조

---

## 💡 교훈

### 1. 실제 사이트 탐색이 최우선

계획서(`hira_rulesvc.md`)를 먼저 읽었지만, 실제 HTML을 보지 않고 추측으로 구현을 시작했다가 시간을 낭비했습니다.

**개선 방법**: 처음부터 `auto_capture.py` 같은 탐색 도구를 만들어 실제 HTML을 먼저 확인해야 합니다.

### 2. iframe 구조 이해 필수

iframe 중첩 구조에서는 어느 iframe의 HTML을 보고 있는지 명확히 해야 합니다.

### 3. 폼 제출 vs 트리 클릭

SELECT 드롭다운의 SEQ 값이 있다고 해서 폼 제출이 가능한 것은 아닙니다. 실제 사이트의 JavaScript 동작을 확인해야 합니다.

---

## 🎯 다음 세션 시작 방법

### 1. 이 일지를 읽고 컨텍스트 파악

```
docs/journal/hira_rulesvc/2025-10-13_initial_exploration.md
```

### 2. 캡처된 HTML 확인

```bash
ls data/hira_rulesvc/debug/
```

**중요한 파일**:
- `step1_main_tree01.html` - 트리 구조 (528KB)
- `step2_attach_tab_contentbody.html` - 대시보드

### 3. tree01 iframe HTML 분석

```bash
# tree01 iframe 구조 확인
head -100 data/hira_rulesvc/debug/step1_main_tree01.html
```

트리 노드의 HTML 구조를 파악하고 selector 찾기

### 4. auto_capture.py 실행하여 트리 클릭 테스트

```python
# auto_capture.py에 새 단계 추가
# 5. 트리 노드 클릭
tree_frame = page.frame(name="tree01")
node = tree_frame.query_selector('a:has-text("요양급여비용 청구방법")')
node.click()
time.sleep(3)
save_all_frames(page, "step5_after_tree_click")
```

### 5. 실제 목록 페이지 HTML 분석

```bash
# 트리 클릭 후 contentbody HTML 확인
cat data/hira_rulesvc/debug/step5_after_tree_click_contentbody.html
```

---

## 📊 진행률

| 단계 | 상태 | 완료율 |
|------|------|--------|
| SEQ 매핑 테이블 | ✅ 완료 | 100% |
| 프로젝트 구조 | ✅ 완료 | 100% |
| 페이지 탐색 분석 | ✅ 완료 | 100% |
| 트리 클릭 네비게이션 | ⏸️ 대기 | 0% |
| 목록 파싱 | ⏸️ 대기 | 0% |
| 다운로드 처리 | ⏸️ 대기 | 0% |
| 페이지네이션 | ⏸️ 대기 | 0% |
| 메타데이터 출력 | 🟡 부분 | 30% |

**전체 진행률**: 약 **40%**

---

## 🔗 참고 자료

- 계획서: `docs/plans/hira_rulesvc.md`
- 트리 구조: `docs/samples/hira_rulesvc/tree.md`
- SEQ 매핑: `hira_rulesvc/config/seq_mapping.py`
- 캡처된 페이지: `data/hira_rulesvc/debug/`

---

**작성일**: 2025-10-13
**다음 작업 시작점**: Phase 1 - 트리 클릭 네비게이션 구현
