# 게이트 체인 약제 매칭 정제 리포트
**생성일**: C:\Jimin\scrape-hub
---

## 📊 통계 요약
- **총 입력**: 50건
- **결정 (active)**: 14건 (28.0%)
- **보류 (pending)**: 35건 (70.0%)
- **제외 (dropped)**: 1건 (2.0%)
- **라우팅**: 0건
  - 레짐: 0건
  - 바이오마커: 0건
  - 질환: 0건

## 🏆 Reason Codes Top 10
- **PHONETIC_FAIL**: 33건
- **PASS_ALL**: 14건
- **SUFFIX_MATCH_STRICT**: 14건
- **FORM_TERM**: 1건
- **SUFFIX_MISMATCH**: 1건
- **ALIAS_CONFLICT**: 1건

## 📋 샘플 케이스
### 제외 (Dropped)
- `busultttttoan → 바이알` (FORM_TERM)

### 보류 (Pending)
- `tttttoituxittttoab → 리툭시맙` (PHONETIC_FAIL)
- `anasttttttottttozttttole → 아나스트로졸` (PHONETIC_FAIL)
- `lettttttottttozttttole → 레트로졸` (PHONETIC_FAIL)

### 활성 (Active)
- `dttttocetaxel → 도세탁셀` (count: 36)
- `paclitaxel → 파클리탁셀` (count: 36)
- `capecitabine → 카페시타빈` (count: 32)
- `ttttoxaliplatin → 옥살리플라틴` (count: 31)
- `heptaplatin → 헵타플라틴` (count: 30)

## ✅ 수락 기준 검증
- ✅ **제형/포장어 0건** (통과)

### 테스트 케이스 검증
- ⚠️ `busulfan → 바이알`: 항목 없음
- ⚠️ `prednisolone → 아비라테론`: 항목 없음
- ✅ `paclitaxel → 파클리탁셀`: active (통과)
