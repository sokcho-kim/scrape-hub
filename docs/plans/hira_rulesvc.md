
# Hira Rulesvc Project

건강보험심사평가원 청구방법 및 급여기준 조회시스템 페이지에서 고시/세부작성요령 정보를 스크랩 합니다. 
아래 **사이트 구조 제약**을 준수하여 스크레이퍼를 구현하라.


## 대상 사이트

```
<http://rulesvc.hira.or.kr/lmxsrv/main/main.srv>
```


## 페이지 작업 지시서

1. 페이지 네비게이션 (트리) 접근
   div class="tabtitBox"
2. 분야별 검색 (트리)
    <div class="tabBox”> 하위의 모든 a 태그에 순차적으로 접근

     ```html
        <div class="tabtitBox">
            <div>
                <p>
                    <img src="/lmxsrv/images/left/tab.gif" alt="분야별검색" title="분야별검색" width="228" height="20">
                </p>
            </div>
            <div class="tabBox">
                <div class="tabBox_inner">
                    <!-- 고시트리 -->
                    <iframe width="100%" class="theight" id="tree01" name="tree01" src="/lmxsrv/law/lawTree.srv?LAWGROUP=1&MODE=srvlist" scrolling="auto" frameborder="0"></iframe>
                </div>
            </div>
        </div>
    ```
3. 목록 에서 데이터 추출 및 첨부파일 다운로드
   <div id=”content-area”> 하위 테이블 대상
   1. 첨부파일 다운로드 및 저장
   1. csv 생성
      * 파일 이름: 목록명_제목
      * column : 제목, 고시일, 시행일 , 다운로드 파일경로


## 사이트 구조 핵심

* 상위 문서 안에 **iframe 2개**가 있다.
  * 좌측 트리: `iframe#tree01` (src: `/lmxsrv/law/lawTree.srv?...`)
  * 우측 목록/내용: `iframe#contentbody` (초기 src: `/lmxsrv/law/lawListManager.srv?...`)
* 검색/탭 전환은 jQuery로 이뤄지며, **상세페이지 진입 없이 목록 화면**에서만 작업해야 한다.
* 목록 테이블은 `contentbody` iframe 안에 있으며, 헤더는 보통 `번호 | 제목 | 고시일 | 시행일 | 다운로드 | 전체보기` 순서다.
* **금지** : 제목 링크 / “전체보기” 클릭.  **허용** : 각 행의 **‘다운로드’ 버튼만** 클릭.

## 입력 파라미터(환경변수로 받기)

* `TARGET_NODE_TEXT` : 좌측 트리에서 클릭할 노드의 텍스트(부분 일치 허용, 예: `요양급여비용 청구방법(보건복지부 고시)`).
* `BASE_URL` : 시작 URL (예: `https://rulemgnt.hira.or.kr/lmxsrv/main/main.srv`).
* `OUT_DIR` : 결과 저장 폴더(기본 `out/`).

## 작업 단계

1. **초기 진입**
   * `BASE_URL` 로드, `networkidle` 대기.
   * 브라우저 컨텍스트는 `accept_downloads=True`.
2. **좌측 트리 내비게이션(목록까지만)**
   * `frame(name="tree01")` 를 취득.
   * 트리 iframe 내부에서 `TARGET_NODE_TEXT` 를 **부분 일치**로 찾고 클릭.
   * 클릭 후 상위 페이지에서 `frame(name="contentbody")` 가 **목록 테이블**로 갱신될 때까지 대기(`networkidle` + 소폭 지연).
3. **목록 화면임을 검증(상세 진입 금지 가드)**
   * `contentbody` iframe 안에서 아래 중 **하나 이상**을 만족해야 “목록 화면”으로 인정:
     * 페이지 내에 `고시정보 목록` 또는 유사한 목록 타이틀 텍스트가 존재
     * 역할 기반 탐지: `table` 존재 + 헤더에 `제목`, `고시일`, `시행일` 텍스트 포함
   * 실패 시  **에러로 종료** (상세로 잘못 진입한 것으로 간주).
4. **목록 크롤링**
   * 현재 페이지의 테이블 `tbody > tr` 를 순회하여 아래 필드 추출:
     * `no`(번호), `title`(제목), `gosi_date`(고시일), `effective_date`(시행일)
   * 각 행에서 **‘다운로드’ 버튼만** 찾아 클릭하여 파일 저장:
     * 텍스트가 `다운로드` 인 링크/버튼 우선.
     * 이미지 버튼만 있는 경우에도 같은 셀 내 클릭 가능한 요소 탐지.
     * 다운로드 완료 이벤트로 파일명 수신 후, `OUT_DIR/files/` 에 저장(파일명은 `pageNo_rowIndex_원본파일명`으로 정리).
   * 제목/날짜/페이지번호/행인덱스/저장파일경로를 함께 **메타 레코드**로 적재.
5. **페이지네이션**
   * 목록 하단의 페이지네이션에서 **다음 페이지**를 탐지:
     * `▶`, `다음`, `>` 등 네비게이션 앵커를 우선 탐지. 없으면 **현재 페이지 숫자 기준 +1** 링크를 찾는 폴백 적용.
   * 각 페이지마다 3)~4) 반복. **끝 페이지**까지 순회.
6. **출력**
   * `OUT_DIR/meta.jsonl` : 행당 1 JSON 레코드(`no,title,gosi_date,effective_date,page_no,row_index,downloaded_files,source_url`)
   * `OUT_DIR/meta.csv`  : 동일 컬럼 CSV
   * `OUT_DIR/files/`    : 실제 첨부파일

## 구현/안정성 규칙

* **상세 페이지로 들어가는 앵커는 절대 클릭하지 말 것.** (제목 링크, `전체보기` 등)
* 모든 클릭 후 `wait_for_load_state("networkidle")` + 400~900ms 랜덤 대기.
* 다운로드 타임아웃 60s. 실패 시 메타에 `errors` 필드로 기록하고 다음 행 진행.
* 상대경로 링크는 절대경로로 변환 저장.
* 파일명은 OS 금지문자 제거(sanitize).
* 헤더 텍스트가 약간 달라도 동작하도록, **한국어 키워드 부분 일치** 로 케이스 처리(예: `고시일` 포함 여부).
* 트리 iframe에서 텍스트가 안 잡히면, 동일 프레임 내 앵커들을 수집하여 **부분 일치 스코어**로 가장 유사한 노드를 선택(오탑재 방지용 로그 남김).
* 재시도: 트리 클릭/목록 검증/다운로드 각각 **최대 2회** 재시도.

## 수락 기준(테스트)

* 실행 후 상세페이지 방문 로그가 없어야 함(가드 통과 실패 시 즉시 에러).
* `meta.jsonl`, `meta.csv`, `files/` 가 생성되고, 첫 페이지 첫 행의 메타에 `title/gosi_date/effective_date` 가 채워져 있어야 함.
* 페이지네이션 끝까지 순회(행 수가 0인 페이지는 스킵).
* 동일 파일 중복 다운로드 시, 기존 파일을 유지하고 새 파일명 뒤에 `_dupN` 을 붙여 충돌을 피함.

## 선택적 기능(있으면 가산점)

* 각 행에 내부 식별자(예: `SEQ` 파라미터)가 노출되면 같이 저장(`post_id` 등).
* `seachForm` 기반 검색 흐름(필요 시):
  * 목표가 “서식(attach)”일 경우, 상단 폼 `#seachForm` 의 hidden 필드(`SEQ`,`SEQ_ATTACH_TYPE`,`SEARCH_TEXT`,`SEARCH_TYPE`)를 세팅 후 `action="/lmxsrv/attach/attachList.srv"` 으로 `target="contentbody"` 제출.
  * 제출 후에도 **목록 가드**로 테이블 여부를 확인하고 동일 절차로 수집.

---

### 왜 이렇게 지시했는가 (요약 근거)

* 상위 문서에 **`tree01` / `contentbody`** 두 개의 iframe이 고정으로 존재함 → 프레임 컨텍스트 전환 필수.
* 트리 클릭이 우측 `contentbody`의 **목록**을 갱신 → 제목/전체보기 클릭 없이 **다운로드만** 눌러 파일 수집해야 함.
* 목록 테이블의 한국어 컬럼(제목/고시일/시행일)과 **다운로드 버튼**이 핵심 식별자.
* 페이지네이션은 전형적 링크 UI(▶/다음/숫자) → 세 종류 모두 대응.
* 상단 검색은 jQuery 폼 POST(타겟=contentbody) → 필요 시 대체 진입로로 사용.


