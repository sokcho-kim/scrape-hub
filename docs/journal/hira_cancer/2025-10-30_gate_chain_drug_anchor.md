# 게이트 체인 약제 매칭 정제 시스템 구축

**작업일**: 2025-10-30
**소요 시간**: 약 3시간
**목적**: 정밀도 최우선 약제 앵커 사전(하드 레이어) 구축

---

## 📋 작업 개요

기존 `drug_matching_results_v2.json` (50개 EN↔KO 매칭)에서 **제형/포장어 오탐**과 **성분 간 오매칭**을 제거하여 고품질 약제 앵커 사전을 생성하는 게이트 체인 필터링 시스템 구축.

**핵심 원칙**: Precision > Recall (정밀도 최우선)

---

## 🏗 구현 내용

### 1. 게이트 체인 설계 (6단계)

```
Gate 1: 금칙어 필터 (제형/포장어)
  └─> Gate 2: 라우팅 (레짐/바이오마커/질환 조기 분리)
      └─> Gate 3: 접미사 정합성 (EN↔KO 계열 체크)
          └─> Gate 4: 음차 유사도 (이중 임계값: strict/loose)
              └─> Gate 5: ATC 교차검증 (현재 스킵)
                  └─> Gate 6: 충돌 해소 (동일 ko ↔ 상이 en)
```

**핵심 최적화**:
- Gate 2를 조기 배치 → 레짐/바이오마커가 약제 게이트에서 false negative 방지
- Strict suffix 매칭 시 Gate 4(음차) 스킵 → `taxel`, `platin` 등 고신뢰 접미사 활용

### 2. 구성 파일

**rules/filters.yaml** (293줄):
- 금칙어: 하드 컷 26개 + 조건부 4개
- 접미사 힌트: 13개 약제 계열 (mab, nib, platin, taxel, rubicin, sone, parib, terone 등)
- 음차 임계값: strict 0.25 (고빈도 ≥20) / loose 0.35 (희귀)
- 라우팅 패턴: regimen 17개, biomarker 14개, disease 14개
- 정규화: NFKC + quote/hyphen/space 통일

**scripts/refine_drug_anchors.py** (821줄):
- DrugAnchorRefiner 클래스
- 6개 게이트 메서드
- 한글 로마자화 (자모 분해)
- JSONL 로그 + Markdown 리포트 자동 생성

**tests/test_refine_drug_anchors.py** (6개 케이스):
- paclitaxel → active ✓
- busulfan → drop (FORM_TERM) ✓
- prednisolone → pending (PHONETIC_FAIL) ✓
- FOLFOX → route_regimen ✓
- HER2 → route_biomarker ✓
- NSCLC → route_disease ✓

### 3. 실행 결과

**입력**: 50개 항목
**출력**:
- **Active**: 14건 (28%)
  - paclitaxel, docetaxel, capecitabine, oxaliplatin, heptaplatin 등
  - Reason: PASS_ALL + SUFFIX_MATCH_STRICT
- **Pending**: 35건 (70%)
  - 주요 원인: PHONETIC_FAIL (33건)
  - 수동 검토 대기
- **Dropped**: 1건 (2%)
  - busulfan → 바이알 (FORM_TERM)
- **Routed**: 0건 (이 데이터셋엔 해당 없음)

**충돌 감지**: 1건
- 옥살리플라틴 ↔ ['oxaliplatin', 'ttttoxaliplatin'] (소스 인코딩 이슈)

---

## ✅ 검증 완료

### 유닛 테스트
```bash
$ python tests/test_refine_drug_anchors.py
Test Result: 6/6 passed
[SUCCESS] All tests passed!
```

### 수락 기준
- ✅ active에 제형/포장어 0건
- ✅ 금칙어 단독 매핑 전량 제외
- ✅ paclitaxel → active 통과
- ✅ busulfan → 바이알 제외

### 출력 파일
```yaml
# dictionary/anchor/drug.yaml (예시)
active:
  - canonical_en: paclitaxel
    canonical_ko: 파클리탁셀
    reason_codes: [PASS_ALL, SUFFIX_MATCH_STRICT]
    count: 36
  - canonical_en: docetaxel
    canonical_ko: 도세탁셀
    reason_codes: [PASS_ALL, SUFFIX_MATCH_STRICT]
    count: 36
pending:
  - canonical_en: rituximab
    canonical_ko: 리툭시맙
    reason_codes: [PHONETIC_FAIL]
    count: 32
```

---

## 🔍 주요 발견

1. **접미사 매칭 효과적**:
   - taxel, platin, nib, mab 등 약제 계열 접미사 정확 감지
   - strict suffix 매칭 시 음차 검사 스킵으로 false negative 방지

2. **제형어 필터링 성공**:
   - "바이알", "앰플" 등 포장 용어 제거 효과
   - 조건부 컷(mL, mg)은 이번 데이터셋에선 미발동

3. **음차 유사도가 주요 병목**:
   - 70% pending은 정밀도 우선 전략의 트레이드오프
   - 한글 로마자화(자모 분해) 방식의 한계
   - 예: rituximab ↔ 리툭시맙 → "rittoksimab" (distance 0.36 > 0.25)

4. **소스 데이터 인코딩 이슈**:
   - 일부 영문 약명에 "tttto" 깨진 문자 존재
   - JSON UTF-8 인코딩 문제로 추정
   - 게이트 로직엔 무영향 (KO 기준 정상 처리)

---

## 📊 통계 분석

### Reason Code 분포
```
PHONETIC_FAIL        : 33건 (66%)  ← 주요 병목
PASS_ALL            : 14건 (28%)
SUFFIX_MATCH_STRICT : 14건 (28%)  ← 효과적
FORM_TERM           : 1건  (2%)
SUFFIX_MISMATCH     : 1건  (2%)
ALIAS_CONFLICT      : 1건  (2%)
```

### 접미사별 성공률
```
-taxel  : 2/2 (100%)  ✓ (paclitaxel, docetaxel)
-platin : 3/4 (75%)   ✓ (oxaliplatin, heptaplatin)
-nib    : 1/1 (100%)  ✓ (dasatinib)
-mab    : 0/5 (0%)    ✗ (음차 실패로 pending)
```

→ 단클론항체(-mab)는 음차 거리가 커서 추가 조정 필요

---

## 🚧 한계점 및 개선 방향

### 현재 한계
1. **낮은 Active 비율 (28%)**: 정밀도 우선이지만 커버리지 부족
2. **음차 알고리즘 단순**: 자모 분해 방식의 한계
3. **ATC 검증 미구현**: Gate 5 스킵 상태
4. **소스 데이터 품질**: 인코딩 이슈, 중복 항목

### Pass-2 개선 계획 (15~30분)

#### 1. 조건부 음차 완화
```python
# suffix 일치 & 금칙/충돌 없음인 pending만 대상
if entry.has_suffix_match and not entry.has_forbidden and not entry.has_conflict:
    threshold = 0.35  # 0.25 → 0.35 완화
```
**예상 효과**: Active +10~20%p (rituximab, bevacizumab 등 구제)

#### 2. 정규화 강화
```yaml
# 하이픈/공백 변종 추가 통일
normalization:
  drug_name_cleanup:
    - remove: ["α-", "β-", "γ-"]  # 그리스 문자
    - normalize: ["-taxel" → "taxel", " platin" → "platin"]
```

#### 3. 레짐 기반 승격
```python
# pending 약제가 확정 레짐(FOLFOX 등) 구성약이면
# 스팬검증 통과 시 auto-promote
if entry in known_regimen_drugs and span_verified:
    entry.decision = "active"
```

#### 4. 수동 승격 리스트
```yaml
# 고빈도 pending 중 수동 검증 통과 항목
manual_promote:
  - {en: rituximab, ko: 리툭시맙, reason: "high_freq_validated"}
  - {en: bevacizumab, ko: 베바시주맙, reason: "high_freq_validated"}
```

---

## 📈 다음 단계 (우선순위순)

### Phase 1: 커버리지 개선 (Pass-2)
- [ ] 조건부 음차 완화 (15분)
- [ ] 정규화 강화 (10분)
- [ ] 레짐 기반 승격 로직 추가 (20분)
- [ ] 재실행 → 목표: Active 40~45%

### Phase 2: 스팬 검증
- [ ] announcement_217.txt / faq_117.txt / pre_announcement_9579.txt 샘플링
- [ ] 원문 스팬 ±20자 추출 → Active 약제 매칭 검증
- [ ] 지표: **정밀도 ≥95%**, **커버리지 ≥60%**
- [ ] 오탐 케이스 분석 → 규칙 보완

### Phase 3: 문서 단위 라벨링
- [ ] 변경 내역별 [암종·라인·행위] 추출
- [ ] Regimen/Drug 자동 태깅
- [ ] 요약 라벨 생성: `[위암·1차·급여확대] XELOX (capecitabine+oxaliplatin)`

### Phase 4: KG 통합
- [ ] Neo4j 스키마 설계:
  ```cypher
  (:ChangeItem)-[:MENTIONS]->(:Drug|:Regimen|:Cancer)
  (:Regimen)-[:USES]->(:Drug)
  (:ChangeItem)-[:HAS_ACTION {type: '신설|변경|삭제'}]
  ```
- [ ] 앵커 사전 → KG 노드 임포트
- [ ] 문서 라벨 → 관계 생성

### Phase 5: 전량 재실행 판단
**조건**: 스팬검증 후
- 커버리지 < 50% **OR**
- 정밀도 < 90%

→ 그때 규칙 재학습 + 전량 재실행

---

## 💡 교훈

1. **게이트 순서가 중요**: 라우팅을 조기 배치해야 false negative 방지
2. **Strict suffix는 강력한 신호**: 음차 검사 스킵 가능
3. **정밀도 우선은 트레이드오프**: 70% pending은 예상된 결과
4. **유닛 테스트 필수**: 6개 케이스가 게이트 로직 버그 조기 발견
5. **인코딩 이슈는 조기 처리**: 소스 데이터 품질이 결과에 직접 영향

---

## 📚 참고 자료

- 작업지시서: `data/pharmalex_unity/251030_하드레이어 구축.md`
- 필터 규칙: `rules/filters.yaml`
- 메인 스크립트: `scripts/refine_drug_anchors.py`
- 유닛 테스트: `tests/test_refine_drug_anchors.py`
- 최종 리포트: `reports/drug_gate_report.md`
- 앵커 사전: `dictionary/anchor/drug.yaml`

---

**작성자**: Claude Code
**최종 수정**: 2025-10-30
