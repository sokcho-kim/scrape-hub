# 법령 지식그래프 실제 예시

## 📋 예시 1: 의료급여법 제11조 계층 구조

### 조문 트리 (Tree Structure)

```
의료급여법
└── 제11조(급여비용의 청구와 지급) [depth=0]
    ├── 제1항 [depth=1]
    │   └── "의료급여기관은 제10조에 따라 의료급여기금에서 부담하는..."
    │
    ├── 제2항 [depth=1]
    │   └── "제1항에 따라 급여비용을 청구하려는 의료급여기관은..."
    │
    ├── 제3항 [depth=1]
    │   └── "제2항에 따라 심사의 내용을 통보받은 시장·군수·구청장은..."
    │
    ├── 제4항 [depth=1]
    │   └── "시장·군수·구청장은 의료급여의 적정성 여부를 평가할 수 있고..."
    │
    ├── 제5항 [depth=1]
    ├── 제6항 [depth=1]
    │   ├── 제1호 [depth=2]
    │   │   └── 「의료법」 제28조제1항에 따른 의사회·치과의사회...
    │   ├── 제2호 [depth=2]
    │   └── 제3호 [depth=2]
    │
    ├── 제7항 [depth=1]
    └── 제8항 [depth=1]
```

**Neo4j 관계:**
- `(:Article {article_number: "제11조"})-[:HAS_CHILD]->(:Article {clause_number: 1})`
- `(:Article {clause_number: 6})-[:HAS_CHILD]->(:Article {subclause_number: 1})`

---

## 🔗 예시 2: 조문 참조 관계 (근거 추적)

### 제11조를 참조하는 조문들

```
제11조(급여비용의 청구와 지급)
  ↑ REFERS_TO [위임]
  │
  ├── 제11조의5(급여비용의 지급 보류)
  │   └── "제11조제3항에도 불구하고..."
  │       → 예외 조항: 제11조 제3항의 원칙에 예외 규정
  │
  ├── 제32조(보고 및 검사)
  │   └── "제11조제6항에 따라 급여비용의 심사청구를 대행하는 단체..."
  │       → 위임 조항: 제11조 제6항에서 정한 대행청구단체 규정
  │
  └── 제35조(벌칙)
      └── "제11조제6항에 따른 대행청구단체가 아닌 자로 하여금..."
          → 벌칙 조항: 제11조 위반 시 처벌 규정
```

**Neo4j 쿼리:**
```cypher
MATCH (source:Article)-[r:REFERS_TO]->(target:Article {article_number: "제11조"})
RETURN source.article_number, r.reference_type, r.reference_text
```

**결과:**
| 출발 조문 | 참조 유형 | 참조 표현 |
|-----------|-----------|-----------|
| 제11조의5 | 예외 | 제11조제3항 |
| 제32조 | 위임 | 제11조제6항 |
| 제35조 | 일반참조 | 제11조제6항 |

---

## ⚖️ 예시 3: 법령 계층 (개정 전파 분석)

### 의료급여법 패밀리

```
의료급여법 [법률]
  ↓ DERIVED_FROM [시행령]
  의료급여법 시행령

  ↓ DERIVED_FROM [시행규칙]
  의료급여법 시행규칙
```

**활용:**
- 의료급여법 제11조가 개정되면 → 시행령, 시행규칙에서 제11조를 참조하는 조문 모두 영향
- 개정 영향도 분석 쿼리:

```cypher
// 의료급여법 제11조 개정 시 영향받는 하위 법령 조문
MATCH (law:Law {law_name: "의료급여법"})<-[:DERIVED_FROM]-(child_law:Law)
MATCH (child_law)-[:HAS_ARTICLE]->(article:Article)
WHERE article.full_text CONTAINS "제11조"
RETURN child_law.law_name, article.article_number,
       substring(article.full_text, 0, 100) AS preview
```

---

## 🎯 예시 4: 준용 관계 (타법 적용)

### 제30조의2 - 타법 준용

```
의료급여법 제30조의2(심판청구)
  ↓ REFERS_TO [준용]
  국민건강보험법 제89조(건강보험분쟁조정위원회)

조문 내용:
"제30조제2항에 따른 급여비용심사기관의 이의신청에 대한 결정에 불복이 있는 자는
「국민건강보험법」 제89조에 따른 건강보험분쟁조정위원회에 심판청구를 할 수 있다."
```

**의미:**
- 의료급여법에는 분쟁조정위원회가 없음
- 국민건강보험법의 분쟁조정위원회를 "준용"
- 근거 법령 추적 가능

---

## 📊 예시 5: RAG 정확 인용

### 기존 방식 (문제)
```
질문: "의료급여 비용은 어디서 청구하나요?"
답변: "의료급여법에 따르면 급여비용을 청구할 수 있습니다." ❌
       → 어떤 조문인지 불명확
```

### 개선 방식 (조문 단위 엔티티)
```
질문: "의료급여 비용은 어디서 청구하나요?"

[Neo4j 검색]
MATCH (a:Article)
WHERE a.full_text CONTAINS "급여비용" AND a.full_text CONTAINS "청구"
RETURN a.law_name, a.article_number, a.article_title, a.full_text
LIMIT 1

[결과]
답변: "의료급여법 제11조(급여비용의 청구와 지급) 제1항에 따르면,
      '의료급여기관은 제10조에 따라 의료급여기금에서 부담하는 급여비용의
       지급을 시장·군수·구청장에게 청구할 수 있습니다.'" ✅

출처: 의료급여법 제11조제1항 (article_id: ART_LAW_A267443F_011_C1)
```

---

## 🔍 예시 6: 복잡한 참조 체인

### 3단계 참조 추적

```
제3조의3(수급권자의 인정 절차 등)
  ↓ REFERS_TO [준용]
  국민기초생활 보장법 제22조(조사)
    ↓ REFERS_TO [위임]
    국민기초생활 보장법 시행령 제35조(조사의 방법)
      ↓ REFERS_TO
      개인정보 보호법 제15조
```

**Neo4j 쿼리:**
```cypher
MATCH path = (a1:Article {article_number: "제3조의3"})-[:REFERS_TO*1..3]->(a2)
RETURN [node IN nodes(path) | node.article_number] AS chain
```

---

## 📈 활용 시나리오

### 1. 법률 검토 시스템
```cypher
// 제11조 개정 시 영향받는 모든 조문 찾기
MATCH (changed:Article {article_number: "제11조"})<-[:REFERS_TO*..3]-(affected)
RETURN DISTINCT affected.article_number, affected.article_title
```

### 2. 챗봇 RAG 응답
```cypher
// "급여비용 청구" 키워드로 관련 조문 검색
MATCH (a:Article)
WHERE a.full_text CONTAINS "급여비용" AND a.full_text CONTAINS "청구"
RETURN a.law_name + " " + a.article_number AS citation,
       a.full_text AS source_text
LIMIT 5
```

### 3. 법령 교육 자료 생성
```cypher
// 의료급여법의 구조 시각화
MATCH path = (l:Law {law_name: "의료급여법"})-[:HAS_ARTICLE]->(a:Article)
              -[:HAS_CHILD*]->(child)
WHERE a.article_number = "제3조"
RETURN path
```

---

## 📌 요약

| 기능 | 기존 | 개선 |
|------|------|------|
| 조문 인용 | "법에 따르면..." | "의료급여법 제11조제1항" |
| 근거 추적 | 수동 검색 | 그래프 탐색 자동화 |
| 개정 영향 | 추측 | 참조 체인으로 정확 파악 |
| 법령 계층 | 파일명 추론 | DERIVED_FROM 관계 명시 |
| 검색 정확도 | 전문 검색 (낮음) | 조문 단위 검색 (높음) |
