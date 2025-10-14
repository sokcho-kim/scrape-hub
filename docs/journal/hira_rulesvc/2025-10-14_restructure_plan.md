# HIRA 고시 문서 수집 재구조화 계획

**날짜:** 2025-10-14
**작업자:** Claude
**상태:** 계획 수립 완료

## 현재 상황

### 수집 완료 현황
- **수집된 파일:** 29개
- **위치:** `data/hira_rulesvc/documents/`
- **문제점:**
  - 폴더 구조 없이 flat하게 저장됨
  - 같은 파일명으로 여러 문서가 덮어써짐
  - 실제로는 52개 문서를 수집했지만 29개만 남음

### 이전 실행 결과
- **전체 문서:** 55개
- **성공:** 52개
- **실패:** 3개 (의료급여법, 의료급여법 시행규칙, 의료급여법 시행령)
- **실행 시간:** 약 18분

## 사용자 요구사항 분석

### 스크린샷 분석 (hira_screen_2.png)
- 왼쪽 트리: 폴더 구조 (예: "요양급여비용 청구방법, 심사청구서·명세서서식 및 작성요령")
- 오른쪽 목록: 해당 폴더의 문서 리스트
  - 예: 3개 문서 (보건복지부 고시, 세부사항, 세부작성요령)
  - 각 문서마다 다운로드 버튼 존재

### document_tree.json 구조
```json
{
  "seq": "2",
  "name": "요양급여비용 청구방법(보건복지부 고시)",
  "path": ["요양급여비용 청구방법, 심사청구서·명세서서식 및 작성요령"]
}
```

- `seq`: 문서 ID
- `name`: 파일명 (확장자 제외)
- `path`: 상위 폴더 경로 배열

### 최종 결정사항
- **폴더 구조 생성 안 함** - flat 구조로 저장
- **이유:**
  - 폴더 구조가 복잡해질 수 있음
  - `document_tree.json`에 이미 관계성 정보 존재
  - 데이터 분석 시 JSON으로 관계성 파악 가능
  - 필요시 나중에 스크립트로 폴더 재구성 가능

## 작업 계획

### Phase 1: 기존 데이터 정리
- [ ] 기존 29개 파일 삭제: `rm -rf data/hira_rulesvc/documents/*`
- [ ] 디렉토리 클린 상태 확인

### Phase 2: 스크래퍼 수정
- [ ] `law_scraper_v2.py` 수정
  - 파일 저장 경로: `output_dir / f"{name}.hwp"`
  - 폴더 생성 로직 제거
  - 중복 체크: 파일명만으로 체크
  - 파일명 충돌 처리 전략 수립 (필요시)

### Phase 3: 전체 재수집
- [ ] 55개 문서 전체 크롤링 실행
- [ ] 예상 결과: 52개 파일 (3개 실패)
- [ ] 예상 시간: 약 18분

### Phase 4: 검증
- [ ] 파일 개수 확인: 52개 예상
- [ ] 파일명 중복 확인
- [ ] document_tree.json과 매핑 확인

## 예상 결과 구조

```
data/hira_rulesvc/documents/
├── 요양급여비용 청구방법(보건복지부 고시).hwp
├── 요양급여비용 청구방법(세부사항).hwp
├── 요양급여비용 청구방법(세부작성요령).hwp
├── 요양급여비용심사청구소프트웨어의검사등에관한기준.hwp
├── 의료급여수가의 기준 및 일반기준.hwp
├── 임신,출산 진료비 등의 의료급여기준 및 방법.hwp
├── 시설수용자.hwp
├── 무연고자 등.hwp
├── 노숙인.hwp
└── ... (총 52개 파일)
```

## 관계성 파악 방법

### document_tree.json 활용
```python
import json

with open('hira_rulesvc/config/document_tree.json') as f:
    data = json.load(f)

# 폴더별 문서 그룹핑
from collections import defaultdict
by_folder = defaultdict(list)

for doc in data['documents']:
    folder = ' > '.join(doc['path'])
    by_folder[folder].append(doc['name'])

# 예시 출력
for folder, files in by_folder.items():
    print(f"{folder}/")
    for file in files:
        print(f"  - {file}.hwp")
```

## 코드 수정 포인트

### law_scraper_v2.py
```python
def _download_document(self, page: Page, doc: dict) -> bool:
    seq = doc['seq']
    name = doc['name']
    # path는 사용하지 않음

    # 파일명 생성
    filename = self._clean_filename(f"{name}.hwp")
    file_path = self.output_dir / filename

    # 중복 체크
    if file_path.exists():
        self.logger.info(f"  ○ 이미 존재: {filename} (건너뜀)")
        return True

    # 다운로드 로직...
```

## 다음 세션 작업 사항
1. 기존 29개 파일 삭제
2. 스크래퍼 코드 수정
3. 전체 재수집 실행
4. 결과 검증

## 참고 사항
- 실패하는 3개 문서는 사이트에 다운로드 파일이 없는 것으로 추정
- tree.md 파일에 전체 구조 문서화되어 있음
- hira_screen_2.png에 UI 참고 자료 있음
