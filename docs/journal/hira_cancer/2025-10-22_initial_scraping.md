# HIRA 암질환 사용약제 및 요법 데이터 수집

**날짜**: 2025-10-22
**작업자**: Claude Code
**상태**: 진행 중 (공고 완료, 공고예고 실패)

## 📋 프로젝트 개요

HIRA(건강보험심사평가원) 암질환 사용약제 및 요법 게시판 4개에서 전체 데이터 수집

**목표**: 568건 수집 (4개 board 전체)

## 🎯 수집 대상

| Board | URL | 게시글 수 | 페이지 | 상태 |
|-------|-----|----------|--------|------|
| 공고 | `/bbsDummy.do?pgmid=HIRAA030023010000` | 217건 | 22페이지 | ✅ 완료 |
| 공고예고 | `/rc/drug/anticancer/antiCncrAnnceList.do?pgmid=HIRAA030023020000` | 232건 | 24페이지 | ❌ 실패 |
| 항암화학요법 | `/bbsDummy.do?pgmid=HIRAA030023030000` | 2건 | 1페이지 | ⏸️ 미수집 |
| FAQ | `/bbsDummy.do?pgmid=HIRAA030023080000` | 117건 | 12페이지 | ⏸️ 미수집 |
| **합계** | - | **568건** | **59페이지** | **38% 완료** |

## ✅ 완료된 작업

### 1. 공고 board 수집 완료 (217건)

**파일**: `data/hira_cancer/raw/announcement_only_20251022_173907.json`
**크기**: 723KB
**수집 시간**: 17:24~17:39 (약 14분)

**데이터 품질**:
- ✅ 본문: 모든 게시글 정상 (평균 ~1000자)
- ✅ 첨부파일: 2~4개/게시글
- ✅ 메타데이터: 파일명, 확장자, 다운로드 URL 포함

**샘플 데이터**:
```json
{
  "metadata": {
    "collected_at": "2025-10-22T17:39:07.186090",
    "total_posts": 217,
    "board": "공고"
  },
  "data": [
    {
      "title": "암환자에게 처방·투여하는 약제에 대한 공고 변경 안내",
      "content": "1775자",
      "attachments": [
        {
          "filename": "...",
          "extension": "hwp",
          "download_url": "https://www.hira.or.kr/bbsDownload.do?..."
        }
      ]
    }
  ]
}
```

### 2. 버그 수정

#### (1) 페이징 버그 (100개→217개)

**문제**: 페이지 수를 10개로 잘못 인식 (실제 22페이지)

**원인**:
```python
# 기존 코드 (scraper.py:114)
paging_text = await self.page.locator('.paging').text_content()  # ❌ 셀렉터 없음
```

**해결**:
```python
# 수정 코드 (scraper.py:113-121)
total_text = await self.page.locator('.total-txt').text_content()
# "전체 : 217건 [1/22페이지]" 에서 추출
match = re.search(r'\[(\d+)/(\d+)\s*페이지\]', total_text)
```

**위치**: `hira_cancer/scraper.py:113-121`

#### (2) URL 구성 버그

**문제**: 상세 페이지 URL 잘못 생성

**원인**: href가 `?pgmid=...`로 시작하는데 base URL에 바로 붙임
```python
# 잘못된 결과
https://www.hira.or.kr/?pgmid=...  # ❌
```

**해결**:
```python
# 수정 코드 (scraper.py:189-207)
elif detail_url.startswith('?'):
    # 현재 경로 유지하고 쿼리 스트링 추가
    current_path = board['url'].split('?')[0]
    detail_url = self.BASE_URL + current_path + detail_url
```

**결과**:
```python
https://www.hira.or.kr/bbsDummy.do?pgmid=...  # ✅
```

**위치**: `hira_cancer/scraper.py:189-207`

## ❌ 발견된 문제

### 공고예고 board 파싱 실패 (232건 전부)

**증상**: 모든 게시글 `내용: 0자, 첨부: 0개`

**원인**: URL 구조가 완전히 다름
- 공고: `/bbsDummy.do?pgmid=...`
- 공고예고: `/rc/drug/anticancer/antiCncrAnnceList.do?pgmid=...` ⚠️

**로그**:
```
2025-10-22 18:24:49 - INFO - [공고예고] 상세 조회: ...
2025-10-22 18:24:53 - INFO -   내용: 0자, 첨부: 0개  ❌
```

**영향**:
- 공고예고: 232건 실패
- 항암화학요법, FAQ: 미확인 (아직 수집 안 함)

## 🔧 기술 세부사항

### 스크래퍼 구조

**파일**: `hira_cancer/scraper.py`

**주요 클래스**: `HIRACancerScraper`

**Board 설정**:
```python
BOARDS = {
    'announcement': {
        'name': '공고',
        'url': '/bbsDummy.do?pgmid=HIRAA030023010000',
        'list_selector': 'tbody tr',
        'title_cell_index': 2,  # 제목이 3번째 셀
        'cells_count': 6
    },
    # ... (공고예고, 항암화학요법, FAQ)
}
```

**핵심 메서드**:
1. `get_total_pages()`: 총 페이지 수 조회
2. `scrape_board_list()`: 목록 페이지 파싱
3. `scrape_post_detail()`: 상세 페이지 파싱
4. `scrape_board()`: 전체 board 수집
5. `scrape_all()`: 모든 board 수집

**수집 항목**:
- 게시글 번호
- 제목
- 작성일
- 본문 내용 (`.view` 셀렉터)
- 첨부파일 (파일명, 확장자, 다운로드 URL)
- 상세 페이지 URL

### 디버그 스크립트

생성된 디버그 도구들:

1. **`debug_pagination.py`**: 페이징 구조 확인
2. **`debug_href.py`**: URL 구조 확인
3. **`debug_all_boards.py`**: 전체 board 구조 분석
4. **`scrape_announcement_only.py`**: 공고 단독 수집
5. **`check_results.py`**: 결과 검증

## 📊 수집 통계

### 공고 board (완료)

```
총 게시글: 217건
총 페이지: 22페이지
수집 시간: 14분
평균 속도: 15.5건/분

본문 길이: 600~4200자
첨부파일: 0~4개/게시글
파일 형식: HWP, PDF, XLSX
```

### 전체 시도 (중단)

```
시작 시각: 17:59:10
중단 시각: 18:26 (추정)
경과 시간: ~27분

완료: 217건 (38%)
실패: 232건 (41%) - 공고예고
미수집: 119건 (21%) - 항암화학요법, FAQ
```

## 📝 다음 단계 (TODO)

### 즉시 수행 필요

1. **공고예고 board 구조 분석**
   - [ ] 상세 페이지 HTML 확인
   - [ ] 본문 셀렉터 찾기 (`.view`가 아닐 수 있음)
   - [ ] 첨부파일 셀렉터 찾기
   - [ ] URL 패턴 확인

2. **스크래퍼 수정**
   - [ ] 공고예고 전용 파싱 로직 추가
   - [ ] Board별 다른 셀렉터 지원
   - [ ] 테스트 후 전체 재수집

3. **항암화학요법, FAQ board 확인**
   - [ ] HTML 구조 분석
   - [ ] 필요시 파싱 로직 수정

### 수집 완료 후

4. **데이터 검증**
   - [ ] 본문 누락 확인
   - [ ] 첨부파일 메타데이터 검증
   - [ ] 중복 데이터 확인

5. **데이터 정리**
   - [ ] 4개 board 통합 JSON 생성
   - [ ] 통계 분석 및 보고서 작성
   - [ ] README 업데이트

## 🔍 참고 정보

### 관련 파일

**스크래퍼**:
- `hira_cancer/scraper.py` - 메인 스크래퍼
- `hira_cancer/scrape_announcement_only.py` - 공고 전용
- `hira_cancer/check_results.py` - 결과 검증

**디버그**:
- `hira_cancer/debug_*.py` - 각종 디버그 스크립트

**로그**:
- `hira_cancer/full_scrape.log` - 전체 수집 로그 (977 라인)
- `hira_cancer/announcement_collection.log` - 공고 수집 로그

**데이터**:
- `data/hira_cancer/raw/announcement_only_20251022_173907.json` - 공고 217건

### 발견한 HTML 패턴

**페이징 정보**:
```html
<p class="total-txt">
  <i class="icon-total"></i>
  전체 : <span class="fcO">217</span>건 [1/22페이지]
</p>
```

**게시글 목록**:
```html
<tbody>
  <tr>
    <td>번호</td>
    <td>공고번호</td>
    <td><a href="?pgmid=...">제목</a></td>  <!-- ⚠️ 쿼리 스트링으로 시작 -->
    <td>작성일</td>
    ...
  </tr>
</tbody>
```

**상세 페이지** (공고 board):
```html
<div class="view">
  <!-- 본문 내용 -->
</div>

<a onclick="downLoad('1','45648','6','49')">
  첨부파일.hwp
</a>
```

### 트러블슈팅

**문제**: `Locator.text_content: Timeout 30000ms exceeded`
- **원인**: 존재하지 않는 셀렉터
- **해결**: 정확한 셀렉터 찾기 (개발자 도구 활용)

**문제**: URL 구성 오류
- **원인**: href 속성의 다양한 패턴 (절대/상대/쿼리)
- **해결**: 조건문으로 모든 케이스 처리

## 📌 메모

- 공고 board는 성공적으로 수집 완료
- 공고예고 board는 완전히 다른 구조 - 별도 분석 필요
- 페이지네이션 버그로 인해 처음에 100개만 수집했으나 수정 후 217개 전체 수집 성공
- 첨부파일 다운로드는 비활성화 (메타데이터만 수집)

---

**다음 작업**: 공고예고 board 구조 분석 및 스크래퍼 수정
