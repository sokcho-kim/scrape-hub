# LLM API 기반 지식그래프 자동 구축 전략

**작성일**: 2025-11-06
**핵심 아이디어**: 수동 파싱 대신 LLM API로 법령 구조화 및 관계 추출 자동화

---

## 🎯 1. 핵심 인사이트

### 기존 접근 (비효율)
```
❌ 수동 작업:
- 56개 HWP 문서 → 5,000개 조문 수동 파싱 (예상 3주)
- 법령 간 참조 관계 수동 매핑 (예상 1주)
- 행정해석 ↔ 법조문 연결 수동 작업 (예상 1주)
- 엔티티 추출 (약제명, 질병명) 수동 매칭 (예상 2주)

총 소요: 약 7주 + 높은 오류율
```

### 제안 접근 (효율적)
```
✅ LLM API 자동화:
- 법령 문서 → Claude/GPT-4 → 구조화된 JSON (1-2일)
- 관계 추출 자동화 (1일)
- 엔티티 연결 자동화 (1일)
- 검증 및 보정 (2일)

총 소요: 약 5일 + 높은 정확도
```

---

## 🤖 2. 사용 가능한 API 옵션

### Option 1: Claude API (추천) ⭐⭐⭐⭐⭐
**장점**:
- 200K 토큰 컨텍스트 (긴 법령 문서 한번에 처리)
- 구조화 출력 우수
- 한국어 법령 이해도 높음
- JSON 출력 안정적

**가격**:
- Claude 3.5 Sonnet: $3/M input, $15/M output
- 56개 문서 × 평균 50K 토큰 = 2.8M 토큰
- 예상 비용: $8-10 (입력) + $10-15 (출력) = **약 $20-25**

**적용 가능 작업**:
- ✅ 법조문 파싱 (조, 항, 호 분리)
- ✅ 계층 구조 추출 (법 > 시행령 > 고시)
- ✅ 참조 관계 추출 ("제X조에 따라...")
- ✅ 엔티티 추출 (약제명, 질병명, 수술명)
- ✅ 요약 생성

---

### Option 2: GPT-4 (대안) ⭐⭐⭐⭐
**장점**:
- 범용성 높음
- Function calling 안정적

**단점**:
- 128K 토큰 제한 (긴 문서는 분할 필요)
- 한국어 법령 이해도 Claude보다 낮음

**가격**:
- GPT-4 Turbo: $10/M input, $30/M output
- 예상 비용: $28 (입력) + $40 (출력) = **약 $68**

---

### Option 3: Upstage Document Parse (현재 사용 중) ⭐⭐⭐
**장점**:
- PDF/HWP → HTML/JSON 변환 우수
- 표 추출 강력

**단점**:
- 구조화 추출 약함 (단순 텍스트 변환)
- 관계 추출 불가
- 법조문 분리 불가

**가격**:
- $0.01/page
- HIRA 암질환 파싱: $49.48 (4,948페이지)

**역할**:
- 1단계: Upstage로 HWP → 텍스트 변환
- 2단계: Claude/GPT-4로 구조화 추출

---

### 추천 조합
```
1차 변환: Upstage Document Parse (HWP → 텍스트)
2차 구조화: Claude API (텍스트 → 구조화 JSON)
3차 검증: 샘플 수동 검증 (10% 샘플링)
```

**총 예상 비용**: $25-30 (56개 문서)
**수동 작업 대비**: 인건비 대비 10분의 1 이하

---

## 🏗️ 3. LLM 기반 자동화 파이프라인

### Step 1: 법령 문서 구조화
```python
import anthropic

def parse_legislation_document(document_text: str) -> dict:
    """
    법령 문서를 Claude API로 구조화
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
다음은 한국 법령 문서입니다. 이 문서를 분석하여 다음 정보를 JSON 형식으로 추출하세요:

1. 법령 메타데이터
   - 법령명
   - 법령 번호 (법률/시행령/고시 번호)
   - 발령 주체 (국회/대통령/보건복지부 등)
   - 제정일/시행일/개정일
   - 법령 유형 (법/시행령/시행규칙/고시)
   - 계층 레벨 (1: 법, 2: 시행령, 3: 고시)

2. 법조문 (Articles)
   - 각 조문의 번호 (제1조, 제2조 등)
   - 조문 제목
   - 조문 내용
   - 항 번호 (제1항, 제2항 등)
   - 호 번호 (1호, 2호 등)

3. 참조 관계 (References)
   - 현재 문서가 참조하는 상위 법령
   - 조문 간 참조 ("제X조에 따라", "제Y조를 준용" 등)
   - 참조 유형 (근거/준용/적용/제외 등)

4. 엔티티 추출
   - 약제명 (한글명, 영문명)
   - 질병명 (KCD 코드 포함 시 추출)
   - 수술/처치명 (자XXX, 차XXX 등)
   - 검사명 (HbA1C, eGFR 등)
   - 적용 대상 (노숙인, 시설수용자 등)

5. 요약
   - 각 조문의 핵심 내용 요약 (1-2문장)
   - 전체 법령 요약 (3-5문장)

출력 형식:
{{
  "metadata": {{
    "name": "의료급여법",
    "number": "법률 제20309호",
    "enacting_authority": "국회",
    "enacted_date": "2023-01-01",
    "effective_date": "2023-07-01",
    "type": "법",
    "level": 1
  }},
  "articles": [
    {{
      "number": "1",
      "title": "목적",
      "content": "이 법은...",
      "paragraphs": [
        {{"number": 1, "content": "..."}}
      ],
      "items": []
    }}
  ],
  "references": [
    {{
      "target_law": "헌법",
      "target_article": "제34조",
      "reference_type": "근거"
    }}
  ],
  "entities": {{
    "drugs": ["Metformin", "Insulin"],
    "diseases": ["당뇨병", "고혈압"],
    "procedures": ["자751", "차200"],
    "tests": ["HbA1C", "eGFR"],
    "targets": ["노숙인", "행려환자"]
  }},
  "summary": {{
    "overall": "이 법은...",
    "articles_summary": [
      {{"article": "제1조", "summary": "..."}}
    ]
  }}
}}

문서:
{document_text}

위 형식에 맞춰 JSON만 출력하세요. 설명은 불필요합니다.
"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=16000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # JSON 파싱
    import json
    result = json.loads(response.content[0].text)

    return result

# 사용 예시
with open('data/hira_rulesvc/documents/의료급여법.txt', 'r', encoding='utf-8') as f:
    doc_text = f.read()

structured_data = parse_legislation_document(doc_text)

# Neo4j에 저장
import_to_neo4j(structured_data)
```

**예상 처리 시간**: 56개 문서 × 30초 = **28분**
**예상 비용**: **$20-25**

---

### Step 2: 관계 추출 자동화
```python
def extract_relationships(all_documents: list[dict]) -> list[dict]:
    """
    여러 법령 문서 간 관계 자동 추출
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # 모든 법령 요약 생성
    doc_summaries = "\n\n".join([
        f"- {doc['metadata']['name']} ({doc['metadata']['number']}): {doc['summary']['overall']}"
        for doc in all_documents
    ])

    prompt = f"""
다음은 수집된 모든 법령 문서들의 요약입니다:

{doc_summaries}

이 법령들 간의 계층 관계와 참조 관계를 분석하여 다음 형식으로 출력하세요:

{{
  "hierarchy": [
    {{
      "parent": "의료급여법",
      "child": "의료급여법 시행령",
      "relationship_type": "BASED_ON",
      "article_reference": "제3조"
    }}
  ],
  "cross_references": [
    {{
      "source": "의료급여수가의 기준 및 일반기준",
      "source_article": "제1조",
      "target": "의료급여법",
      "target_article": "제10조",
      "reference_type": "근거"
    }}
  ]
}}

JSON만 출력하세요.
"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return json.loads(response.content[0].text)
```

---

### Step 3: 엔티티 연결 자동화
```python
def link_entities_to_legislation(
    legislation_data: dict,
    existing_drugs: list[str],
    existing_diseases: list[str],
    existing_procedures: list[str]
) -> dict:
    """
    법령 내 엔티티를 기존 Neo4j 노드와 자동 연결
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
다음 법령에서 언급된 엔티티들을 기존 데이터베이스의 엔티티와 매칭하세요:

법령 엔티티:
- 약제: {legislation_data['entities']['drugs']}
- 질병: {legislation_data['entities']['diseases']}
- 수술/처치: {legislation_data['entities']['procedures']}

데이터베이스 엔티티 (샘플):
- 약제: {existing_drugs[:100]}
- 질병: {existing_diseases[:100]}
- 수술/처치: {existing_procedures[:100]}

각 법령 엔티티를 가장 유사한 데이터베이스 엔티티와 매칭하고,
해당 엔티티가 어떤 조문에서 언급되었는지 추출하세요.

출력 형식:
{{
  "entity_links": [
    {{
      "legislation_entity": "메트포민",
      "entity_type": "drug",
      "matched_db_entity": "Metformin",
      "confidence": 0.95,
      "mentioned_in_articles": ["제10조", "제15조"],
      "context": "당뇨병 치료제로 급여 적용"
    }}
  ]
}}
"""

    # ... (생략)
```

---

### Step 4: 전체 자동화 스크립트
```python
#!/usr/bin/env python3
"""
법령 문서 자동 구조화 및 Neo4j 임포트
"""

import os
import json
from pathlib import Path
from neo4j import GraphDatabase
import anthropic

# 설정
DOCUMENTS_DIR = "data/hira_rulesvc/documents"
OUTPUT_DIR = "data/hira_rulesvc/structured"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def main():
    """메인 파이프라인"""

    print("="*80)
    print("법령 문서 자동 구조화 파이프라인")
    print("="*80)

    # Step 1: 모든 문서 읽기
    print("\n[Step 1] 문서 읽기...")
    documents = []
    for file_path in Path(DOCUMENTS_DIR).glob("*.txt"):
        with open(file_path, 'r', encoding='utf-8') as f:
            documents.append({
                'file_name': file_path.name,
                'content': f.read()
            })
    print(f"✅ {len(documents)}개 문서 로드 완료")

    # Step 2: Claude API로 구조화
    print("\n[Step 2] Claude API로 구조화 중...")
    structured_docs = []
    for i, doc in enumerate(documents):
        print(f"  [{i+1}/{len(documents)}] {doc['file_name']} 처리 중...")
        structured = parse_legislation_document(doc['content'])
        structured['file_name'] = doc['file_name']
        structured_docs.append(structured)

        # 중간 저장
        with open(f"{OUTPUT_DIR}/{doc['file_name']}.json", 'w', encoding='utf-8') as f:
            json.dump(structured, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(structured_docs)}개 문서 구조화 완료")

    # Step 3: 관계 추출
    print("\n[Step 3] 법령 간 관계 추출 중...")
    relationships = extract_relationships(structured_docs)
    with open(f"{OUTPUT_DIR}/relationships.json", 'w', encoding='utf-8') as f:
        json.dump(relationships, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(relationships['hierarchy'])}개 계층 관계 추출")
    print(f"✅ {len(relationships['cross_references'])}개 참조 관계 추출")

    # Step 4: Neo4j 임포트
    print("\n[Step 4] Neo4j 임포트 중...")
    import_to_neo4j(structured_docs, relationships)
    print("✅ Neo4j 임포트 완료")

    # Step 5: 통계 출력
    print("\n" + "="*80)
    print("완료 통계")
    print("="*80)
    total_articles = sum(len(doc['articles']) for doc in structured_docs)
    total_entities = sum(
        len(doc['entities']['drugs']) +
        len(doc['entities']['diseases']) +
        len(doc['entities']['procedures'])
        for doc in structured_docs
    )
    print(f"📄 처리된 법령: {len(structured_docs)}개")
    print(f"📋 추출된 조문: {total_articles}개")
    print(f"🏷️  추출된 엔티티: {total_entities}개")
    print(f"🔗 계층 관계: {len(relationships['hierarchy'])}개")
    print(f"🔗 참조 관계: {len(relationships['cross_references'])}개")
    print("="*80)

if __name__ == "__main__":
    main()
```

**실행 명령**:
```bash
python scripts/neo4j/auto_structure_legislation.py
```

**예상 실행 시간**: 30-40분
**예상 비용**: $20-25

---

## 💰 4. 비용 분석

### 시나리오 1: Claude API 사용
```
입력:
- 56개 문서 × 평균 50,000 토큰 = 2,800,000 토큰
- 비용: 2.8M × $3/M = $8.40

출력:
- 56개 구조화 JSON × 평균 8,000 토큰 = 448,000 토큰
- 비용: 0.448M × $15/M = $6.72

관계 추출:
- 입력: 56개 요약 × 500 토큰 = 28,000 토큰 → $0.08
- 출력: 관계 JSON 10,000 토큰 → $0.15

총 비용: $8.40 + $6.72 + $0.08 + $0.15 = $15.35
여유 포함: 약 $20
```

### 시나리오 2: Upstage + Claude 조합
```
Upstage (1단계):
- 56개 HWP × 평균 20페이지 = 1,120페이지
- 비용: 1,120 × $0.01 = $11.20

Claude (2단계):
- Upstage 출력 → 구조화
- 비용: 약 $15 (위와 동일)

총 비용: $11.20 + $15 = $26.20
```

### 수동 작업 비교
```
수동 파싱 작업:
- 5,000개 조문 수동 파싱: 3주
- 관계 매핑: 1주
- 엔티티 연결: 1주
- 검증: 1주

총 6주 × 5일 × 8시간 = 240시간
시급 $30 가정: $7,200

API 비용: $20-26
절감: 99.6%
```

---

## ⚡ 5. 구현 우선순위 (재조정)

### Week 1: LLM 기반 자동화 구축
**Day 1-2**: 자동화 스크립트 개발
- parse_legislation_document() 함수
- extract_relationships() 함수
- Neo4j 임포트 스크립트

**Day 3**: 실행 및 검증
- 56개 법령 자동 구조화 (실행 시간: 30분)
- 샘플 검증 (10개 문서)
- 오류 수정

**Day 4-5**: 전체 데이터 처리
- 나머지 데이터 소스 적용 (HIRA 고시 8,539개)
- 엔티티 연결 자동화
- 품질 검증

---

### Week 2: 기존 계획 그대로 진행
- Drug, Disease, Procedure, Cancer 노드 구축
- 관계 구축 (자동 추출된 관계 활용)

---

## 🎯 6. 즉시 시작 작업

### 오늘 (2-3시간)
1. **프로토타입 작성**
   - 1개 법령 문서로 테스트 (의료급여법)
   - Claude API 호출 스크립트
   - JSON 출력 검증

2. **비용 확인**
   - 실제 토큰 수 측정
   - 비용 재계산

### 내일
3. **전체 자동화**
   - 56개 법령 일괄 처리
   - 결과 검증 (10% 샘플링)

### 모레
4. **Neo4j 임포트**
   - 구조화된 JSON → Neo4j
   - 관계 생성
   - 쿼리 테스트

---

## ✅ 7. 기대 효과

| 항목 | 수동 작업 | LLM 자동화 | 개선 |
|-----|----------|-----------|------|
| **소요 시간** | 6주 | 3일 | **93% 단축** |
| **비용** | $7,200 | $20-26 | **99.6% 절감** |
| **정확도** | 70-80% | 90-95% | **+15%p** |
| **확장성** | 낮음 | 높음 | ✅ |
| **유지보수** | 어려움 | 쉬움 | ✅ |

---

## 🚀 8. 최종 권장사항

### ✅ 즉시 채택
1. **Claude API 기반 자동화**
   - 비용: $20-26
   - 시간: 3일
   - 품질: 높음

2. **프로토타입 우선**
   - 오늘 1개 문서 테스트
   - 검증 후 전체 적용

3. **기존 계획 유지**
   - Week 1: LLM 자동화
   - Week 2-4: 기존 계획 그대로

### 📋 다음 단계
- [ ] Claude API 키 확인
- [ ] 프로토타입 스크립트 작성 (2시간)
- [ ] 1개 문서 테스트
- [ ] 비용/품질 확인 후 전체 적용 결정

---

**결론**: 수동 파싱 대신 Claude API를 활용하면 **99.6% 비용 절감, 93% 시간 단축, 정확도 향상**을 달성할 수 있습니다. 즉시 프로토타입부터 시작하는 것을 강력히 권장합니다.
