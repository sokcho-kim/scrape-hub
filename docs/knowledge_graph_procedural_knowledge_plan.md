# 절차적 지식 구조화 전략 (HIRA ebook + hira_rulesvc)

**작성일**: 2025-11-06
**목적**: 절차적 지식(청구, 심사, 작성요령)을 Neo4j 지식그래프에 통합

---

## 📊 1. 절차적 지식 데이터 현황

### HIRA ebook (data/hira/ebook)
```
총 9개 PDF, 4,275페이지, ~1.8M 글자

📋 절차 관련 문서 (우선순위 높음):
1. 요양급여비용 청구방법 및 작성요령 (848페이지) ⭐⭐⭐⭐⭐
   - 청구 절차, 서식, 작성법
   - ⚠️ OCR 필요 (텍스트 추출 실패)

2. 의료급여 실무편람 (680페이지) ⭐⭐⭐⭐⭐
   - 의료급여 전체 절차
   - 대상자별 절차, 본인부담, 청구/정산

3. 자율점검 사례 모음집 (153페이지) ⭐⭐⭐⭐
   - 실제 심사 사례
   - 부당청구 예방 가이드
   - 사례 기반 학습

4. 의약품 청구 가이드 (82페이지) ⭐⭐⭐
   - 약품 청구 실무
   - 구입약가/구입수량
```

### hira_rulesvc (data/hira_rulesvc)
```
56개 법령/고시/행정해석

📋 절차 관련 문서:
1. 요양급여비용 청구방법 (보건복지부 고시) ⭐⭐⭐⭐⭐
2. 요양급여비용 청구방법 (세부사항) ⭐⭐⭐⭐
3. 요양급여비용 청구방법 (세부작성요령) ⭐⭐⭐⭐
4. 행정해석 39개 중 "청구 및 정산" 카테고리 ⭐⭐⭐
```

### 총 절차 문서
```
HIRA ebook: 4개 PDF (1,763페이지)
hira_rulesvc: 43개 HWP (법령 + 행정해석)
───────────────────────────────────
총 47개 문서 (절차적 지식)
```

---

## 🎯 2. 절차적 지식의 특징

### 2.1 구조적 특성
```
절차 = 단계들의 순차적 연결

예시: 요양급여비용 청구 절차
1단계: 진료 제공
2단계: 명세서 작성
3단계: EDI 전송
4단계: 심사 청구
5단계: 심사 결과 확인
6단계: 지급 또는 이의신청
```

### 2.2 포함 정보
```
✅ 단계 (Step)
   - 순서, 명칭, 설명

✅ 조건 (Condition)
   - 필수/선택 조건
   - 분기 (IF-THEN-ELSE)

✅ 필수 서식 (Required Forms)
   - 서식 번호, 명칭
   - 작성 예시

✅ 제출처/기한 (Submission)
   - 제출 대상 기관
   - 제출 기한

✅ 예외사항 (Exceptions)
   - 특수 상황 처리
   - 예외 규정

✅ 사례 (Cases)
   - 올바른 사례
   - 부당청구 사례
```

---

## 🏗️ 3. Neo4j 스키마 설계 (절차 중심)

### 3.1 새로운 노드 타입

#### Procedure (절차)
```cypher
(:Procedure {
  id: String,                // 절차 ID
  name: String,              // 절차명 (요양급여비용 청구)
  category: String,          // 분류 (청구/심사/지급)
  description: String,       // 설명
  total_steps: Integer,      // 총 단계 수
  estimated_time: String,    // 예상 소요 시간
  responsible_party: String, // 담당자 (의료기관/심평원)
  legal_basis: String       // 법적 근거 조항
})
```

#### Step (단계)
```cypher
(:Step {
  id: String,                // 단계 ID
  step_number: Integer,      // 단계 번호 (1, 2, 3...)
  name: String,              // 단계명
  description: String,       // 상세 설명
  is_required: Boolean,      // 필수 여부
  estimated_time: String,    // 예상 소요 시간
  tips: String,             // 주의사항/팁
  common_errors: [String]   // 흔한 오류
})
```

#### Form (서식)
```cypher
(:Form {
  id: String,                // 서식 ID/번호
  name: String,              // 서식명
  version: String,           // 버전
  category: String,          // 분류 (청구서/명세서/신청서)
  file_path: String,         // 파일 경로
  file_format: String,       // 파일 형식 (PDF/HWP/Excel)
  template_url: String,      // 다운로드 URL
  instructions: String,      // 작성 요령
  effective_date: Date      // 적용일
})
```

#### Case (사례)
```cypher
(:Case {
  id: String,                // 사례 ID
  title: String,             // 사례 제목
  type: String,              // 유형 (올바른 사례/부당청구)
  category: String,          // 분류
  description: String,       // 사례 설명
  issue: String,             // 문제점 (부당청구인 경우)
  solution: String,          // 해결책/올바른 방법
  legal_basis: String,       // 법적 근거
  penalty: String           // 제재 (부당청구인 경우)
})
```

#### Condition (조건)
```cypher
(:Condition {
  id: String,                // 조건 ID
  type: String,              // 조건 유형 (IF/UNLESS/WHEN)
  description: String,       // 조건 설명
  evaluation: String,        // 평가 로직
  true_action: String,       // TRUE 시 행동
  false_action: String      // FALSE 시 행동
})
```

#### Deadline (기한)
```cypher
(:Deadline {
  id: String,                // 기한 ID
  description: String,       // 기한 설명
  period: String,            // 기간 (15일, 1개월 등)
  calculation_method: String, // 계산 방법
  start_event: String,       // 시작 이벤트
  end_event: String,         // 종료 이벤트
  penalty_for_delay: String // 지연 시 불이익
})
```

---

### 3.2 새로운 관계 타입

#### 절차 관련
```cypher
// 절차 → 단계 (순서)
(Procedure)-[:HAS_STEP {
  order: Integer             // 순서
}]->(Step)

// 단계 → 다음 단계
(Step)-[:NEXT_STEP {
  condition: String          // 조건 (optional)
}]->(Step)

// 단계 → 이전 단계
(Step)-[:PREVIOUS_STEP]->(Step)

// 단계 분기 (조건부)
(Step)-[:BRANCH_IF {
  condition: String
}]->(Step)
```

#### 서식 관련
```cypher
// 단계 → 필수 서식
(Step)-[:REQUIRES_FORM {
  is_mandatory: Boolean
}]->(Form)

// 절차 → 필수 서식
(Procedure)-[:REQUIRES_FORM]->(Form)

// 서식 → 작성 예시
(Form)-[:HAS_EXAMPLE]->(Case)
```

#### 조건 관련
```cypher
// 단계 → 조건
(Step)-[:HAS_CONDITION]->(Condition)

// 조건 → 분기
(Condition)-[:LEADS_TO {
  when: String               // "true" or "false"
}]->(Step)
```

#### 사례 관련
```cypher
// 사례 → 절차
(Case)-[:DEMONSTRATES]->(Procedure)

// 사례 → 단계
(Case)-[:DEMONSTRATES]->(Step)

// 사례 → 법령
(Case)-[:BASED_ON]->(Legislation)

// 사례 → 엔티티 (약제, 질병 등)
(Case)-[:INVOLVES]->(Drug)
(Case)-[:INVOLVES]->(Disease)
(Case)-[:INVOLVES]->(Procedure)
```

#### 기한 관련
```cypher
// 단계 → 기한
(Step)-[:HAS_DEADLINE]->(Deadline)

// 절차 → 기한
(Procedure)-[:HAS_DEADLINE]->(Deadline)
```

#### 법적 근거 관련
```cypher
// 절차 → 법령
(Procedure)-[:GOVERNED_BY]->(Legislation)

// 절차 → 조문
(Procedure)-[:BASED_ON]->(Article)

// 단계 → 법령
(Step)-[:BASED_ON]->(Article)
```

---

## 🤖 4. LLM API 기반 자동 추출

### 4.1 절차 구조화 프롬프트

```python
def extract_procedure_from_document(doc_text: str) -> dict:
    """
    절차 문서를 Claude API로 구조화
    """

    prompt = f"""
다음은 의료급여/요양급여 절차 관련 문서입니다.
이 문서를 분석하여 절차를 구조화된 JSON 형식으로 추출하세요.

문서:
{doc_text}

추출할 정보:

1. 절차 기본 정보
   - 절차명
   - 분류 (청구/심사/지급/신청 등)
   - 전체 설명
   - 법적 근거

2. 단계들 (Steps)
   각 단계마다:
   - 단계 번호
   - 단계명
   - 상세 설명
   - 필수 여부
   - 예상 소요 시간
   - 주의사항
   - 흔한 오류

3. 단계 간 순서/분기
   - 정상 흐름: 1단계 → 2단계 → 3단계
   - 조건부 분기: IF 조건 THEN A단계 ELSE B단계

4. 필수 서식
   - 서식 번호
   - 서식명
   - 어느 단계에서 필요한지
   - 작성 요령

5. 조건들
   - 조건 내용
   - 어떤 단계에 적용되는지
   - TRUE/FALSE 시 행동

6. 기한
   - 기한 설명
   - 계산 방법
   - 지연 시 불이익

7. 관련 사례
   - 사례 제목
   - 사례 유형 (올바른/부당청구)
   - 사례 설명
   - 어떤 단계/절차와 연관되는지

출력 형식:
{{
  "procedure": {{
    "name": "요양급여비용 청구",
    "category": "청구",
    "description": "...",
    "legal_basis": "요양급여비용 청구방법 제3조",
    "responsible_party": "요양기관"
  }},
  "steps": [
    {{
      "number": 1,
      "name": "진료 제공 및 기록",
      "description": "...",
      "is_required": true,
      "estimated_time": "진료 시간에 따름",
      "tips": "정확한 진료기록 작성 필수",
      "common_errors": ["진료기록 누락", "코드 오입력"]
    }},
    {{
      "number": 2,
      "name": "명세서 작성",
      "description": "...",
      "is_required": true,
      "estimated_time": "30분~1시간",
      "tips": "청구코드 정확성 확인",
      "common_errors": ["코드 중복 청구", "급여기준 미확인"]
    }}
  ],
  "step_flow": [
    {{"from": 1, "to": 2, "condition": null}},
    {{"from": 2, "to": 3, "condition": "명세서 검증 통과"}},
    {{"from": 2, "to": 2, "condition": "명세서 오류 발견 (재작성)"}}
  ],
  "required_forms": [
    {{
      "id": "서식1",
      "name": "요양급여비용 심사청구서",
      "used_in_step": 3,
      "instructions": "...",
      "mandatory": true
    }}
  ],
  "conditions": [
    {{
      "description": "명세서 검증 통과",
      "applies_to_step": 2,
      "true_action": "3단계로 진행",
      "false_action": "2단계 재수행"
    }}
  ],
  "deadlines": [
    {{
      "description": "청구 기한",
      "period": "진료월 다음달 10일까지",
      "calculation_method": "진료 종료일 기준",
      "penalty": "기한 경과 시 청구 불가"
    }}
  ],
  "cases": [
    {{
      "title": "올바른 청구 사례 - 당뇨병 외래 진료",
      "type": "올바른 사례",
      "description": "...",
      "related_steps": [2, 3],
      "legal_basis": "..."
    }},
    {{
      "title": "부당청구 사례 - 이중 청구",
      "type": "부당청구",
      "issue": "동일 진료행위 중복 청구",
      "solution": "진료내역 재확인 후 정정청구",
      "related_steps": [2],
      "penalty": "부당이득금 환수"
    }}
  ]
}}

위 형식에 맞춰 JSON만 출력하세요.
"""

    # Claude API 호출
    # ... (생략)
```

---

### 4.2 사례 자동 추출 프롬프트

```python
def extract_cases_from_document(doc_text: str) -> list:
    """
    사례집에서 개별 사례 추출
    """

    prompt = f"""
다음은 요양급여 청구 자율점검 사례 모음집입니다.
각 사례를 개별적으로 추출하여 구조화하세요.

문서:
{doc_text}

각 사례마다 다음 정보 추출:

1. 사례 기본 정보
   - 제목/번호
   - 사례 유형 (올바른 사례/부당청구/자율점검 사례)
   - 관련 분야 (약제/행위/재료)

2. 사례 내용
   - 상황 설명
   - 문제점 (부당청구인 경우)
   - 올바른 방법
   - 해결책

3. 관련 정보
   - 법적 근거 (조항)
   - 관련 절차/단계
   - 연관된 약제/질병/수술 코드
   - 제재 사항 (부당청구인 경우)

4. 키워드
   - 주요 키워드 추출

출력 형식:
{{
  "cases": [
    {{
      "id": "case_001",
      "title": "당뇨병 약제 이중 청구 사례",
      "type": "부당청구",
      "category": "약제",
      "situation": "환자에게 Metformin을 처방하면서...",
      "issue": "동일 성분 약제 중복 청구",
      "correct_method": "주성분이 동일한 약제는 1가지만 청구",
      "solution": "정정청구 진행",
      "legal_basis": "요양급여비용 청구방법 제8조",
      "related_procedure": "약제 청구",
      "related_step": 2,
      "entities": {{
        "drugs": ["Metformin", "Glucophage"],
        "diseases": ["당뇨병"],
        "codes": ["E11"]
      }},
      "penalty": "부당이득금 환수 + 가산금",
      "keywords": ["이중청구", "동일성분", "약제"]
    }}
  ]
}}
"""

    # Claude API 호출
    # ... (생략)
```

---

## 🚀 5. 구현 파이프라인

### Step 1: 문서별 절차 추출
```python
#!/usr/bin/env python3
"""
절차 문서 자동 구조화
"""

import json
from pathlib import Path
import anthropic

# 절차 문서 목록
PROCEDURE_DOCS = [
    "data/hira/ebook/2025 의료급여 실무편람.pdf",
    "data/hira/ebook/요양급여비용 청구방법, 심사청구서 명세서서식 및 작성요령- 2025년 7월판.pdf",
    "data/hira/ebook/2025년 요양기관 의약품 청구 가이드.pdf",
    "data/hira_rulesvc/documents/요양급여비용 청구방법(보건복지부 고시).hwp"
]

def main():
    print("="*80)
    print("절차적 지식 자동 구조화")
    print("="*80)

    all_procedures = []
    all_cases = []

    for doc_path in PROCEDURE_DOCS:
        print(f"\n[처리중] {doc_path}")

        # 1. 문서 읽기
        with open(doc_path, 'r', encoding='utf-8') as f:
            doc_text = f.read()

        # 2. Claude API로 절차 추출
        procedure_data = extract_procedure_from_document(doc_text)
        all_procedures.append(procedure_data)

        # 3. 사례 추출 (사례집인 경우)
        if "사례" in doc_path or "case" in doc_path.lower():
            cases = extract_cases_from_document(doc_text)
            all_cases.extend(cases)

        print(f"  ✅ 절차: {procedure_data['procedure']['name']}")
        print(f"  ✅ 단계: {len(procedure_data['steps'])}개")
        print(f"  ✅ 서식: {len(procedure_data['required_forms'])}개")
        if cases:
            print(f"  ✅ 사례: {len(cases)}개")

    # 4. 결과 저장
    output_dir = Path("data/hira/procedures_structured")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "all_procedures.json", 'w', encoding='utf-8') as f:
        json.dump(all_procedures, f, ensure_ascii=False, indent=2)

    with open(output_dir / "all_cases.json", 'w', encoding='utf-8') as f:
        json.dump(all_cases, f, ensure_ascii=False, indent=2)

    # 5. Neo4j 임포트
    import_procedures_to_neo4j(all_procedures, all_cases)

    print("\n" + "="*80)
    print("완료 통계")
    print("="*80)
    print(f"📋 절차: {len(all_procedures)}개")
    print(f"📝 총 단계: {sum(len(p['steps']) for p in all_procedures)}개")
    print(f"📄 서식: {sum(len(p['required_forms']) for p in all_procedures)}개")
    print(f"📚 사례: {len(all_cases)}개")

if __name__ == "__main__":
    main()
```

---

### Step 2: Neo4j 임포트

```python
def import_procedures_to_neo4j(procedures: list, cases: list):
    """
    절차 데이터 Neo4j 임포트
    """
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver("bolt://localhost:7687")

    with driver.session() as session:
        # 1. Procedure 노드 생성
        for proc_data in procedures:
            proc = proc_data['procedure']

            session.run("""
                CREATE (p:Procedure {
                    id: $id,
                    name: $name,
                    category: $category,
                    description: $description,
                    legal_basis: $legal_basis,
                    responsible_party: $responsible_party
                })
            """,
                id=proc['name'].replace(' ', '_'),
                name=proc['name'],
                category=proc['category'],
                description=proc['description'],
                legal_basis=proc.get('legal_basis'),
                responsible_party=proc.get('responsible_party')
            )

            # 2. Step 노드 생성 및 연결
            for step in proc_data['steps']:
                session.run("""
                    MATCH (p:Procedure {id: $proc_id})
                    CREATE (s:Step {
                        id: $step_id,
                        step_number: $number,
                        name: $name,
                        description: $description,
                        is_required: $is_required,
                        estimated_time: $estimated_time,
                        tips: $tips,
                        common_errors: $common_errors
                    })
                    CREATE (p)-[:HAS_STEP {order: $number}]->(s)
                """,
                    proc_id=proc['name'].replace(' ', '_'),
                    step_id=f"{proc['name']}_{step['number']}",
                    number=step['number'],
                    name=step['name'],
                    description=step['description'],
                    is_required=step.get('is_required', True),
                    estimated_time=step.get('estimated_time'),
                    tips=step.get('tips'),
                    common_errors=step.get('common_errors', [])
                )

            # 3. Step 간 NEXT_STEP 관계
            for flow in proc_data.get('step_flow', []):
                session.run("""
                    MATCH (s1:Step {id: $from_id})
                    MATCH (s2:Step {id: $to_id})
                    CREATE (s1)-[:NEXT_STEP {condition: $condition}]->(s2)
                """,
                    from_id=f"{proc['name']}_{flow['from']}",
                    to_id=f"{proc['name']}_{flow['to']}",
                    condition=flow.get('condition')
                )

            # 4. Form 노드 생성 및 연결
            for form in proc_data.get('required_forms', []):
                session.run("""
                    MERGE (f:Form {id: $form_id})
                    ON CREATE SET
                        f.name = $name,
                        f.instructions = $instructions,
                        f.mandatory = $mandatory

                    WITH f
                    MATCH (p:Procedure {id: $proc_id})
                    CREATE (p)-[:REQUIRES_FORM]->(f)

                    WITH f
                    MATCH (s:Step {id: $step_id})
                    CREATE (s)-[:REQUIRES_FORM {is_mandatory: $mandatory}]->(f)
                """,
                    form_id=form['id'],
                    name=form['name'],
                    instructions=form.get('instructions'),
                    mandatory=form.get('mandatory', True),
                    proc_id=proc['name'].replace(' ', '_'),
                    step_id=f"{proc['name']}_{form.get('used_in_step')}"
                )

        # 5. Case 노드 생성
        for case in cases:
            session.run("""
                CREATE (c:Case {
                    id: $id,
                    title: $title,
                    type: $type,
                    category: $category,
                    situation: $situation,
                    issue: $issue,
                    solution: $solution,
                    legal_basis: $legal_basis,
                    penalty: $penalty
                })
            """,
                id=case['id'],
                title=case['title'],
                type=case['type'],
                category=case['category'],
                situation=case.get('situation'),
                issue=case.get('issue'),
                solution=case.get('solution'),
                legal_basis=case.get('legal_basis'),
                penalty=case.get('penalty')
            )

            # Case → Procedure 연결
            if case.get('related_procedure'):
                session.run("""
                    MATCH (c:Case {id: $case_id})
                    MATCH (p:Procedure {name: $proc_name})
                    CREATE (c)-[:DEMONSTRATES]->(p)
                """,
                    case_id=case['id'],
                    proc_name=case['related_procedure']
                )

            # Case → Drug/Disease 연결 (엔티티)
            for drug in case.get('entities', {}).get('drugs', []):
                session.run("""
                    MATCH (c:Case {id: $case_id})
                    MATCH (d:Drug {name: $drug_name})
                    CREATE (c)-[:INVOLVES]->(d)
                """,
                    case_id=case['id'],
                    drug_name=drug
                )
```

---

## 💰 6. 비용 예상

### 절차 문서 (4개 PDF, 1,763페이지)
```
입력:
- 1,763페이지 × 400 토큰/페이지 = 705,200 토큰
- 비용: 0.7M × $3/M = $2.10

출력:
- 4개 절차 JSON × 10,000 토큰 = 40,000 토큰
- 비용: 0.04M × $15/M = $0.60

총: $2.70
```

### 사례집 (153페이지)
```
입력: 153 × 400 = 61,200 토큰 → $0.18
출력: 약 50개 사례 × 500 토큰 = 25,000 토큰 → $0.38

총: $0.56
```

### 전체 비용
```
절차 문서: $2.70
사례 문서: $0.56
──────────
총 비용: $3.26
```

**수동 작업 대비**: 4주 작업 → 2일 작업 (95% 시간 절감)

---

## 📊 7. 예상 결과

### Neo4j 노드 추가
```
Procedure: 약 10개
Step: 약 100개
Form: 약 30개
Case: 약 50개
Condition: 약 20개
Deadline: 약 15개
────────────────
총 추가: 약 225개 노드
```

### 관계 추가
```
HAS_STEP: 100개
NEXT_STEP: 90개
REQUIRES_FORM: 50개
DEMONSTRATES: 60개
HAS_CONDITION: 20개
HAS_DEADLINE: 15개
────────────────
총 추가: 약 335개 관계
```

---

## 🎯 8. RAG 활용 시나리오

### 시나리오 1: 절차 질문
```
질문: "당뇨병 환자에게 Metformin을 처방했습니다. 약제비를 청구하려면 어떤 절차를 거쳐야 하나요?"

Neo4j 쿼리:
MATCH (drug:Drug {name: "Metformin"})<-[:TREATS]-(disease:Disease {name: "당뇨병"})
MATCH (proc:Procedure {category: "청구"})-[:HAS_STEP]->(step:Step)
MATCH (step)-[:REQUIRES_FORM]->(form:Form)
OPTIONAL MATCH (case:Case)-[:INVOLVES]->(drug)
WHERE case.type = "올바른 사례"
RETURN proc, step, form, case
ORDER BY step.step_number

답변:
"당뇨병 환자의 Metformin 청구 절차:

**전체 절차**: 요양급여비용 청구 (약제)

**단계별 안내**:
1단계: 진료 및 처방 (예상 시간: 10분)
   - Metformin 처방전 작성
   - 진료기록 등록

2단계: 명세서 작성 (예상 시간: 5분)
   - 약제 코드 입력
   - 용량, 일수 확인
   - 필수 서식: 요양급여비용청구서

3단계: 청구 (예상 시간: 5분)
   - EDI 전송
   - 기한: 처방일 다음달 10일까지

**올바른 사례**:
[Case #123] 당뇨병 Metformin 청구 사례
- 1일 2회, 30일분 처방
- 급여기준: HbA1C ≥6.5%
- 법적 근거: 당뇨병 급여기준 [일반원칙] 제1조

**주의사항**:
- 동일성분 중복 청구 금지
- 용량 초과 시 급여 제외"
```

---

### 시나리오 2: 부당청구 예방
```
질문: "Metformin과 Glucophage를 같이 청구해도 되나요?"

Neo4j 쿼리:
MATCH (drug1:Drug {name: "Metformin"})
MATCH (drug2:Drug {name: "Glucophage"})
MATCH (case:Case)-[:INVOLVES]->(drug1)
MATCH (case)-[:INVOLVES]->(drug2)
WHERE case.type = "부당청구"
RETURN case

답변:
"⚠️ 부당청구에 해당합니다.

**문제점**:
Metformin과 Glucophage는 동일 주성분(Metformin)입니다.
동일 성분 약제는 1가지만 청구 가능합니다.

**올바른 방법**:
둘 중 1가지만 선택하여 청구하세요.

**법적 근거**:
요양급여비용 청구방법 제8조 (중복청구 금지)

**제재**:
- 부당이득금 환수
- 가산금 부과 (최대 5배)

**유사 사례**: [Case #045] 동일성분 중복청구 사례"
```

---

## 🚀 9. 즉시 실행 계획

### 오늘 (3시간)
1. **프로토타입 작성**
   - 1개 문서 테스트 (의료급여 실무편람 일부)
   - Claude API 스크립트
   - 절차 추출 검증

### 내일 (1일)
2. **전체 자동화**
   - 4개 절차 문서 일괄 처리
   - 사례집 사례 추출
   - 결과 검증

### 모레 (반나절)
3. **Neo4j 임포트**
   - 절차/단계/서식/사례 노드 생성
   - 관계 구축
   - 쿼리 테스트

---

## ✅ 10. 최종 권장사항

### 즉시 채택
1. **Claude API 기반 절차 자동화**
   - 비용: $3-4
   - 시간: 2-3일
   - 품질: 높음

2. **ebook + hira_rulesvc 통합 활용**
   - 절차 문서: ebook (상세 가이드)
   - 법적 근거: hira_rulesvc (법령/고시)
   - 상호 보완적

3. **절차 → 법령 연결**
   - 각 단계의 법적 근거 자동 연결
   - GOVERNED_BY, BASED_ON 관계

### 기대 효과
| 항목 | 개선 |
|-----|------|
| **절차 안내** | 단계별 상세 안내 가능 |
| **부당청구 예방** | 사례 기반 경고 |
| **법적 근거 제시** | 절차 → 법령 추적 |
| **서식 제공** | 필수 서식 자동 안내 |

---

**결론**: HIRA ebook의 절차적 지식을 LLM API로 구조화하면, 단계별 안내, 사례 기반 학습, 법적 근거 추적이 가능한 완전한 절차 지식 그래프를 구축할 수 있습니다. 비용은 $3-4로 매우 저렴하며, 수동 작업 대비 95% 시간 절감 효과가 있습니다.
