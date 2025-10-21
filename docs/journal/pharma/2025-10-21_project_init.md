# Pharma 프로젝트 초기 설정

**작업일**: 2025-10-21
**작업자**: Claude Code
**상태**: ✅ 초기 설정 완료

---

## 📋 작업 개요

약제 관련 데이터 수집 및 파싱을 위한 새 프로젝트 생성.

### 목적
- HIRA 약제 사용 기준 PDF 파싱
- Upstage Document Parse API 성능 평가
- pdfplumber 대비 복잡한 표 처리 능력 비교

---

## 📂 프로젝트 구조

```
pharma/
├── scrapers/           # 데이터 수집 (예정)
├── parsers/            # 데이터 파싱
│   └── upstage_test.py  # Upstage API 테스트 스크립트
└── README.md

data/pharma/
├── raw/                # 원본 데이터
│   ├── pdf/
│   └── excel/
├── parsed/             # 파싱 결과
│   └── upstage_test/
└── README.md

docs/journal/pharma/
└── 2025-10-21_project_init.md  # 본 문서
```

---

## 🎯 테스트 대상 PDF

**파일**: `요양급여의 적용기준 및 방법에 관한 세부사항(약제) - 2025년 7월판.pdf`

**특징**:
- 페이지: 858p
- 내용: 약제별 급여 기준, 사전승인, 투여 용량
- 표 구조: 병합셀, 중첩 테이블 다수
- 출처: HIRA 전자책 (이미 수집됨)

**위치**: `data/hira/ebook/`

---

## 🚀 Upstage API 테스트 계획

### 샘플 페이지 (10개)
- p10, 50, 100, 200, 300, 400, 500, 600, 700, 800
- 전략적 분산 (초반/중반/후반)

### 비교 대상
- pdfplumber (HIRA 표 파싱에서 70% 감지율)
- 병합셀 처리 능력
- 중첩 테이블 처리 능력

### 평가 메트릭
- 표 감지율
- 행/열 추출 완전성
- 병합셀 처리 품질
- API 응답 시간
- 비용 ($0.01/page 예상)

---

## 💰 예상 비용

| 항목 | 페이지 | 비용 |
|------|--------|------|
| 테스트 (10p) | 10 | **$0.10** |
| 전체 (필요 시) | 858 | $8.58 |

**예산**: $20 내

---

## 📝 다음 단계

1. **Upstage API 테스트 실행** (10페이지)
   - API 키 설정
   - 스크립트 실행
   - 결과 분석

2. **pdfplumber와 비교**
   - 동일 페이지 pdfplumber 파싱
   - 정확도, 완전성 비교
   - 비용 대비 성능 평가

3. **최종 파서 선택**
   - pdfplumber (무료, 70% 감지)
   - Upstage (유료, 95%+ 예상)
   - 하이브리드 (간단 → pdfplumber, 복잡 → Upstage)

---

## 🔗 관련 작업

- HIRA 표 파서 MVP: `docs/journal/hira/2025-10-21_table_parser_mvp.md`
- HIRA eBook 수집: `docs/journal/hira/2025-10-20_ebook_collection_and_analysis.md`

---

**작성 시각**: 2025-10-21 15:45
**다음 작업**: Upstage API 테스트 실행
