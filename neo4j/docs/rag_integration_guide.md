# Knowledge Graph RAG 통합 가이드

## 목차

- [개요](#개요)
- [접근법 비교](#접근법-비교)
- [1. Text-to-Cypher](#1-text-to-cypher-nl2cypher)
- [2. Template-based Query](#2-template-based-query-추천---phase-1)
- [3. GraphRAG (Hybrid)](#3-graphrag-hybrid-추천---phase-2)
- [4. Graph-to-Vector](#4-graph-to-vector)
- [구현 로드맵](#구현-로드맵)
- [Use Case 시나리오](#use-case-시나리오)

---

## 개요

Neo4j 의료 지식그래프를 RAG(Retrieval-Augmented Generation)에 통합하는 방법론입니다.

### 현재 그래프 구조

```
Disease (KCD-9)
  ↓ HAS_BIOMARKER
Biomarker
  ↓ TESTED_BY          ↑ TARGETS
Test (EDI/LOINC)     Drug (ATC)
                      ↑ INCLUDES
                   Regimen (HIRA)
                      ↑ TREATED_BY
                  Disease (KCD-9)
```

**노드**: 21,589 Disease + 1,487 Procedure + 23 Biomarker + 575 Test + 138 Drug + 28 Regimen
**관계**: 1,413개 (HAS_BIOMARKER, TESTED_BY, TARGETS, TREATED_BY, INCLUDES)

---

## 접근법 비교

| 접근법 | 복잡도 | 유연성 | 정확도 | 구현 시간 | 적합한 Phase |
|--------|--------|--------|--------|-----------|-------------|
| **Template-based** | ⭐ 낮음 | ⭐⭐ 중간 | ⭐⭐⭐ 높음 | 1-2주 | Phase 1 (프로토타입) |
| **GraphRAG** | ⭐⭐ 중간 | ⭐⭐⭐ 높음 | ⭐⭐⭐ 높음 | 2-4주 | Phase 2 (운영) |
| **Text-to-Cypher** | ⭐⭐⭐ 높음 | ⭐⭐⭐ 매우 높음 | ⭐⭐ 중간 | 1-2개월 | Phase 3 (확장) |
| **Graph-to-Vector** | ⭐ 낮음 | ⭐⭐ 중간 | ⭐⭐ 중간 | 1주 | 보조 수단 |

---

## 1. Text-to-Cypher (NL2Cypher)

### 개념

자연어 질문을 Cypher 쿼리로 변환하여 그래프 데이터베이스에서 직접 정보 검색

```
사용자 질문 → LLM (스키마 이해) → Cypher 쿼리 생성 → Neo4j 실행 → 결과 반환 → LLM이 자연어로 변환
```

### 구현 예시 (LangChain)

```python
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI

# Neo4j 연결
graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# LLM 설정
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0
)

# Chain 생성
cypher_chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    return_intermediate_steps=True,
    validate_cypher=True  # 쿼리 유효성 검증
)

# 질문
response = cypher_chain.invoke({
    "query": "HER2 양성 유방암의 1차 치료 레지멘은 무엇인가?"
})

print("생성된 Cypher:", response['intermediate_steps'][0])
print("결과:", response['result'])
```

### LLM이 생성하는 Cypher 예시

```cypher
// 질문: "HER2 양성 유방암의 1차 급여 요법은?"
MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)-[:INCLUDES]->(drug:Drug)
MATCH (d)-[:HAS_BIOMARKER]->(b:Biomarker {name_en: 'HER2'})
WHERE d.kcd_code STARTS WITH 'C50'
  AND tb.line = '1차'
RETURN
    d.name_kr as 질병,
    r.regimen_type as 요법유형,
    collect(drug.ingredient_ko) as 약물목록,
    r.announcement_no as 고시번호
```

### Few-shot Prompting

```python
CYPHER_EXAMPLES = """
Example 1:
Question: 폐암의 바이오마커는?
Cypher:
MATCH (d:Disease)-[:HAS_BIOMARKER]->(b:Biomarker)
WHERE d.kcd_code STARTS WITH 'C34'
RETURN DISTINCT b.name_ko, b.name_en

Example 2:
Question: PD-L1 바이오마커를 타겟하는 약물은?
Cypher:
MATCH (d:Drug)-[:TARGETS]->(b:Biomarker {name_en: 'PD-L1'})
RETURN d.ingredient_ko, d.atc_code

Example 3:
Question: 유방암 2차 치료에 사용되는 레지멘은?
Cypher:
MATCH (d:Disease)-[tb:TREATED_BY {line: '2차'}]->(r:Regimen)
WHERE d.kcd_code STARTS WITH 'C50'
RETURN r.regimen_type, r.announcement_no
"""

cypher_chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    cypher_prompt=custom_prompt_with_examples,
    verbose=True
)
```

### 장점

- ✅ **유연성 최고**: 예상치 못한 질문 대응 가능
- ✅ **확장성**: 새로운 노드/관계 추가 시 코드 수정 불필요
- ✅ **복잡한 쿼리**: Multi-hop reasoning 가능

### 단점

- ❌ **구현 복잡도**: 스키마 문서화, Few-shot 예시 필요
- ❌ **오류 가능성**: LLM이 잘못된 Cypher 생성 가능
- ❌ **비용**: GPT-4 API 호출 많음
- ❌ **보안**: Cypher injection 위험 (validation 필수)

### 추천 사용 시기

- Phase 3 (확장 단계)
- 질문 유형을 미리 예측하기 어려운 경우
- 연구/탐색 용도

---

## 2. Template-based Query (추천 - Phase 1)

### 개념

미리 정의된 쿼리 템플릿을 사용하고, LLM은 파라미터만 추출

```
사용자 질문 → LLM (파라미터 추출) → 템플릿 선택 → 파라미터 바인딩 → Neo4j 실행
```

### 구현 예시

```python
from typing import Dict, Any
from neo4j import GraphDatabase
from pydantic import BaseModel

# 파라미터 모델
class RegimenQueryParams(BaseModel):
    kcd_prefix: str  # "C50"
    biomarker: str   # "HER2"
    line: str        # "1차"

# 템플릿 정의
QUERY_TEMPLATES = {
    "regimen_by_cancer_biomarker_line": {
        "description": "특정 암종, 바이오마커, 치료 라인에 대한 급여 인정 레지멘 조회",
        "params": ["kcd_prefix", "biomarker", "line"],
        "cypher": """
            MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)-[:INCLUDES]->(drug:Drug)
            MATCH (d)-[:HAS_BIOMARKER]->(b:Biomarker)
            WHERE d.kcd_code STARTS WITH $kcd_prefix
              AND b.name_en = $biomarker
              AND tb.line = $line
            RETURN
                d.name_kr as 질병,
                r.regimen_type as 요법유형,
                collect(DISTINCT drug.ingredient_ko) as 약물목록,
                r.announcement_no as 고시번호,
                r.announcement_date as 고시일자
        """
    },

    "biomarker_tests": {
        "description": "특정 바이오마커 검사 방법 조회",
        "params": ["biomarker"],
        "cypher": """
            MATCH (b:Biomarker)-[:TESTED_BY]->(t:Test)
            WHERE b.name_en = $biomarker OR b.name_ko = $biomarker
            RETURN
                b.name_ko as 바이오마커,
                t.name_ko as 검사명,
                t.edi_code as EDI코드,
                t.loinc_code as LOINC코드
        """
    },

    "drug_regimens": {
        "description": "특정 약물이 포함된 레지멘 조회",
        "params": ["drug_name"],
        "cypher": """
            MATCH (r:Regimen)-[:INCLUDES]->(d:Drug)
            MATCH (disease:Disease)-[:TREATED_BY]->(r)
            WHERE d.ingredient_ko = $drug_name
               OR d.ingredient_en = $drug_name
            RETURN
                disease.name_kr as 암종,
                r.regimen_type as 요법유형,
                r.line as 치료라인,
                r.announcement_date as 고시일자
        """
    },

    "cancer_biomarkers": {
        "description": "특정 암종의 바이오마커 목록",
        "params": ["kcd_prefix"],
        "cypher": """
            MATCH (d:Disease)-[:HAS_BIOMARKER]->(b:Biomarker)
            WHERE d.kcd_code STARTS WITH $kcd_prefix
            RETURN DISTINCT
                b.name_ko as 바이오마커명,
                b.name_en as 영문명,
                b.type as 유형
        """
    },

    "biomarker_drugs": {
        "description": "특정 바이오마커를 타겟하는 약물",
        "params": ["biomarker"],
        "cypher": """
            MATCH (drug:Drug)-[:TARGETS]->(b:Biomarker)
            WHERE b.name_en = $biomarker OR b.name_ko = $biomarker
            RETURN
                drug.ingredient_ko as 약물명,
                drug.atc_code as ATC코드,
                drug.mechanism_of_action as 작용기전
        """
    }
}

# LLM을 사용한 파라미터 추출
def extract_params_with_llm(question: str, template_name: str) -> Dict[str, Any]:
    """LLM이 질문에서 파라미터 추출"""

    template = QUERY_TEMPLATES[template_name]
    required_params = template["params"]

    prompt = f"""
다음 질문에서 파라미터를 추출하세요.

필요한 파라미터: {required_params}

참고 정보:
- kcd_prefix: 암종 코드 (예: C34=폐암, C50=유방암, C16=위암)
- biomarker: 바이오마커 영문명 (예: HER2, EGFR, PD-L1)
- line: 치료 라인 (1차, 2차, 3차)
- drug_name: 약물명 (한글 또는 영문)

질문: {question}

JSON 형식으로 답변:
"""

    response = llm.invoke(prompt)
    params = json.loads(response.content)
    return params

# 쿼리 실행 래퍼
class TemplateQueryEngine:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def query(self, template_name: str, params: Dict[str, Any]):
        """템플릿 쿼리 실행"""
        template = QUERY_TEMPLATES[template_name]
        cypher = template["cypher"]

        with self.driver.session() as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]

    def close(self):
        self.driver.close()

# 사용 예시
engine = TemplateQueryEngine(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# 질문 분류 및 파라미터 추출 (LLM)
question = "HER2 양성 유방암의 1차 급여 요법은?"
template_name = "regimen_by_cancer_biomarker_line"  # LLM이 선택
params = extract_params_with_llm(question, template_name)
# → {"kcd_prefix": "C50", "biomarker": "HER2", "line": "1차"}

# 쿼리 실행
results = engine.query(template_name, params)

# 결과를 자연어로 변환 (LLM)
answer = llm_generate_answer(question, results)
print(answer)
```

### 템플릿 선택 로직

```python
def select_template(question: str) -> str:
    """LLM이 질문에 맞는 템플릿 선택"""

    template_descriptions = "\n".join([
        f"{name}: {info['description']}"
        for name, info in QUERY_TEMPLATES.items()
    ])

    prompt = f"""
다음 질문에 가장 적합한 쿼리 템플릿을 선택하세요.

사용 가능한 템플릿:
{template_descriptions}

질문: {question}

템플릿 이름만 답변하세요:
"""

    response = llm.invoke(prompt)
    return response.content.strip()
```

### 장점

- ✅ **빠른 구현**: 1-2주 내 프로토타입 가능
- ✅ **안정성**: 검증된 쿼리만 실행
- ✅ **정확도**: 의료 도메인에 적합 (예측 가능)
- ✅ **디버깅 용이**: 쿼리가 고정되어 있어 오류 추적 쉬움
- ✅ **비용 효율**: LLM 호출 최소화

### 단점

- ❌ **유연성 제한**: 새로운 질문 유형마다 템플릿 추가 필요
- ❌ **유지보수**: 템플릿 관리 필요
- ❌ **복잡한 쿼리**: Multi-hop reasoning 어려움

### 추천 사용 시기

- **Phase 1 (프로토타입)**
- 질문 유형이 어느 정도 예측 가능한 경우
- 의료진/환자 대상 서비스 (정확도 중요)

### 핵심 질문 템플릿 (의료용)

```python
# 5가지 핵심 질문 유형
CORE_TEMPLATES = {
    1: "암종 X의 바이오마커는?",
    2: "바이오마커 Y 검사 방법은?",
    3: "암종 X + 바이오마커 Y 치료제는?",
    4: "약물 Z가 포함된 레지멘은?",
    5: "암종 X의 급여 인정 요법은?"
}
```

---

## 3. GraphRAG (Hybrid) (추천 - Phase 2)

### 개념

벡터 검색으로 관련 노드 찾기 → 그래프 탐색으로 주변 컨텍스트 수집 → LLM에 전달

```
질문 임베딩 → 벡터 유사도 검색 → 관련 노드 발견 → n-hop 그래프 탐색 → 서브그래프 추출 → 텍스트 변환 → LLM 생성
```

### 아키텍처

```
┌─────────────┐
│ User Query  │ "HER2 양성 유방암 치료는?"
└──────┬──────┘
       ↓
┌─────────────────┐
│ Vector Search   │ 임베딩 유사도 검색
│ (FAISS/Pinecone)│ → ["HER2", "유방암", "Trastuzumab"]
└──────┬──────────┘
       ↓
┌─────────────────┐
│ Graph Traversal │ Neo4j Cypher로 서브그래프 추출
│ (Neo4j)         │ 2-3 hop neighbors
└──────┬──────────┘
       ↓
┌─────────────────┐
│ Context Builder │ 그래프 → 자연어 변환
│                 │ "유방암은 HER2를 가지며, HER2는..."
└──────┬──────────┘
       ↓
┌─────────────────┐
│ LLM Generate    │ 질문 + 컨텍스트 → 답변
└─────────────────┘
```

### 구현 예시 (LlamaIndex)

```python
from llama_index.core import KnowledgeGraphIndex
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# Neo4j 그래프 저장소
graph_store = Neo4jGraphStore(
    username="neo4j",
    password="password",
    url="bolt://localhost:7687",
    database="neo4j"
)

# 임베딩 모델
embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# LLM
llm = OpenAI(model="gpt-4", temperature=0)

# Knowledge Graph Index 생성
index = KnowledgeGraphIndex.from_documents(
    [],  # 이미 Neo4j에 데이터 있음
    graph_store=graph_store,
    embed_model=embed_model,
    llm=llm,
    max_triplets_per_chunk=10
)

# 쿼리 엔진
query_engine = index.as_query_engine(
    include_embeddings=True,
    response_mode="tree_summarize",
    graph_traversal_depth=2  # 2-hop neighbors
)

# 질문
response = query_engine.query(
    "HER2 양성 유방암의 급여 인정 1차 치료 레지멘과 검사 방법을 알려주세요"
)

print(response.response)
print("\n사용된 그래프 노드:", response.source_nodes)
```

### Custom GraphRAG 구현

```python
import numpy as np
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

class CustomGraphRAG:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.embed_model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
        self.node_embeddings = {}  # 노드 임베딩 캐시

    def embed_nodes(self):
        """모든 노드 임베딩 생성"""
        with self.driver.session() as session:
            # Disease 노드
            diseases = session.run("""
                MATCH (d:Disease) WHERE d.is_cancer = true
                RETURN d.kcd_code as id, d.name_kr as text
            """)
            for record in diseases:
                self.node_embeddings[record['id']] = {
                    'text': record['text'],
                    'embedding': self.embed_model.encode(record['text']),
                    'type': 'Disease'
                }

            # Biomarker 노드
            biomarkers = session.run("""
                MATCH (b:Biomarker)
                RETURN b.biomarker_id as id,
                       b.name_ko + ' ' + b.name_en as text
            """)
            for record in biomarkers:
                self.node_embeddings[record['id']] = {
                    'text': record['text'],
                    'embedding': self.embed_model.encode(record['text']),
                    'type': 'Biomarker'
                }

            # Drug 노드
            drugs = session.run("""
                MATCH (d:Drug)
                RETURN d.atc_code as id, d.ingredient_ko as text
            """)
            for record in drugs:
                self.node_embeddings[record['id']] = {
                    'text': record['text'],
                    'embedding': self.embed_model.encode(record['text']),
                    'type': 'Drug'
                }

    def find_similar_nodes(self, query: str, top_k: int = 5):
        """질문과 유사한 노드 찾기"""
        query_embedding = self.embed_model.encode(query)

        similarities = []
        for node_id, node_data in self.node_embeddings.items():
            similarity = np.dot(query_embedding, node_data['embedding'])
            similarities.append((node_id, similarity, node_data))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def extract_subgraph(self, seed_nodes: list, depth: int = 2):
        """시드 노드 주변 서브그래프 추출"""
        with self.driver.session() as session:
            # 동적으로 노드 타입 결정
            node_conditions = []
            for node_id, _, node_data in seed_nodes:
                node_type = node_data['type']
                if node_type == 'Disease':
                    node_conditions.append(f"n.kcd_code = '{node_id}'")
                elif node_type == 'Biomarker':
                    node_conditions.append(f"n.biomarker_id = '{node_id}'")
                elif node_type == 'Drug':
                    node_conditions.append(f"n.atc_code = '{node_id}'")

            condition_str = " OR ".join(node_conditions)

            query = f"""
                MATCH (n)
                WHERE {condition_str}
                CALL apoc.path.subgraphAll(n, {{
                    maxLevel: {depth},
                    relationshipFilter: 'HAS_BIOMARKER|TESTED_BY|TARGETS|TREATED_BY|INCLUDES'
                }})
                YIELD nodes, relationships
                RETURN nodes, relationships
            """

            result = session.run(query)
            record = result.single()

            return {
                'nodes': record['nodes'],
                'relationships': record['relationships']
            }

    def subgraph_to_text(self, subgraph):
        """서브그래프를 자연어 컨텍스트로 변환"""
        context_parts = []

        for rel in subgraph['relationships']:
            start_node = rel.start_node
            end_node = rel.end_node
            rel_type = rel.type

            # 노드 정보 추출
            start_label = list(start_node.labels)[0]
            end_label = list(end_node.labels)[0]

            # 자연어 변환
            if rel_type == 'HAS_BIOMARKER':
                context_parts.append(
                    f"{start_node.get('name_kr', '질병')}은(는) "
                    f"{end_node.get('name_ko', '바이오마커')} 바이오마커를 가질 수 있습니다."
                )
            elif rel_type == 'TESTED_BY':
                context_parts.append(
                    f"{start_node.get('name_ko', '바이오마커')} 바이오마커는 "
                    f"{end_node.get('name_ko', '검사')} 검사로 확인할 수 있습니다 "
                    f"(EDI: {end_node.get('edi_code', 'N/A')})."
                )
            elif rel_type == 'TARGETS':
                context_parts.append(
                    f"{start_node.get('ingredient_ko', '약물')}은(는) "
                    f"{end_node.get('name_ko', '바이오마커')} 바이오마커를 타겟합니다."
                )
            elif rel_type == 'TREATED_BY':
                line = rel.get('line', '치료')
                context_parts.append(
                    f"{start_node.get('name_kr', '질병')}은(는) "
                    f"{line} 치료로 레지멘 치료를 받을 수 있습니다 "
                    f"(고시: {rel.get('announcement_no', 'N/A')})."
                )
            elif rel_type == 'INCLUDES':
                context_parts.append(
                    f"레지멘에는 {end_node.get('ingredient_ko', '약물')} 약물이 포함됩니다."
                )

        return "\n".join(context_parts)

    def query(self, question: str, llm):
        """GraphRAG 쿼리 실행"""
        # 1. 유사 노드 찾기
        similar_nodes = self.find_similar_nodes(question, top_k=5)
        print(f"[1] 유사 노드: {[n[2]['text'] for n in similar_nodes]}")

        # 2. 서브그래프 추출
        subgraph = self.extract_subgraph(similar_nodes, depth=2)
        print(f"[2] 서브그래프: {len(subgraph['nodes'])} 노드, {len(subgraph['relationships'])} 관계")

        # 3. 컨텍스트 변환
        context = self.subgraph_to_text(subgraph)
        print(f"[3] 컨텍스트:\n{context}\n")

        # 4. LLM 생성
        prompt = f"""
다음 의료 지식그래프 정보를 바탕으로 질문에 답변하세요.

컨텍스트:
{context}

질문: {question}

답변:
"""
        response = llm.invoke(prompt)
        return response.content

# 사용 예시
rag = CustomGraphRAG(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)

# 노드 임베딩 (최초 1회)
rag.embed_nodes()

# 쿼리
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4", temperature=0)

answer = rag.query("HER2 양성 유방암의 검사와 치료 방법은?", llm)
print(answer)
```

### 장점

- ✅ **관계 활용**: 그래프 구조의 이점 최대화
- ✅ **유연성 + 정확도**: Template과 Text-to-Cypher의 중간
- ✅ **확장성**: 새로운 노드 추가 시 자동 반영
- ✅ **Multi-hop reasoning**: 복잡한 경로 추론 가능

### 단점

- ❌ **중간 복잡도**: 벡터 DB + 그래프 DB 모두 필요
- ❌ **초기 설정**: 노드 임베딩 생성 필요
- ❌ **비용**: 벡터 검색 + LLM 호출

### 추천 사용 시기

- **Phase 2 (운영 단계)**
- 복잡한 질문 처리 필요
- 확장성 중요

---

## 4. Graph-to-Vector

### 개념

그래프 데이터를 텍스트로 변환하여 벡터 DB에 저장, 기존 RAG 파이프라인 활용

```
그래프 노드/관계 → 자연어 문장 생성 → 임베딩 → 벡터 DB 저장 → 유사도 검색 → LLM 생성
```

### 구현 예시

```python
from neo4j import GraphDatabase
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter

class GraphToVector:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def extract_graph_facts(self):
        """그래프를 fact 문장으로 변환"""
        facts = []

        with self.driver.session() as session:
            # Disease-Biomarker facts
            query1 = """
                MATCH (d:Disease)-[:HAS_BIOMARKER]->(b:Biomarker)
                WHERE d.is_cancer = true
                RETURN
                    d.name_kr as disease,
                    d.kcd_code as kcd,
                    b.name_ko as biomarker_ko,
                    b.name_en as biomarker_en
            """
            result = session.run(query1)
            for record in result:
                fact = (
                    f"{record['disease']}(KCD: {record['kcd']})은(는) "
                    f"{record['biomarker_ko']}({record['biomarker_en']}) "
                    f"바이오마커를 가질 수 있습니다."
                )
                facts.append(fact)

            # Biomarker-Test facts
            query2 = """
                MATCH (b:Biomarker)-[:TESTED_BY]->(t:Test)
                RETURN
                    b.name_ko as biomarker,
                    t.name_ko as test,
                    t.edi_code as edi
            """
            result = session.run(query2)
            for record in result:
                fact = (
                    f"{record['biomarker']} 바이오마커는 "
                    f"{record['test']} 검사로 확인할 수 있습니다 "
                    f"(EDI 코드: {record['edi']})."
                )
                facts.append(fact)

            # Drug-Biomarker facts
            query3 = """
                MATCH (d:Drug)-[:TARGETS]->(b:Biomarker)
                RETURN
                    d.ingredient_ko as drug,
                    d.atc_code as atc,
                    d.mechanism_of_action as moa,
                    b.name_ko as biomarker
            """
            result = session.run(query3)
            for record in result:
                fact = (
                    f"{record['drug']}(ATC: {record['atc']})은(는) "
                    f"{record['biomarker']} 바이오마커를 타겟하는 약물입니다. "
                    f"작용기전: {record['moa']}."
                )
                facts.append(fact)

            # Regimen facts
            query4 = """
                MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)-[:INCLUDES]->(drug:Drug)
                RETURN
                    d.name_kr as disease,
                    tb.line as line,
                    r.regimen_type as type,
                    collect(drug.ingredient_ko) as drugs,
                    r.announcement_no as announcement
            """
            result = session.run(query4)
            for record in result:
                drugs_str = ', '.join(record['drugs'])
                fact = (
                    f"{record['disease']}의 {record['line']} 치료로 "
                    f"{record['type']} 레지멘이 급여 인정됩니다. "
                    f"포함 약물: {drugs_str}. "
                    f"고시번호: {record['announcement']}."
                )
                facts.append(fact)

        return facts

    def create_vector_store(self, facts):
        """벡터 DB 생성"""
        embeddings = OpenAIEmbeddings()

        # FAISS 벡터 저장소
        vector_store = FAISS.from_texts(
            texts=facts,
            embedding=embeddings
        )

        return vector_store

# 사용 예시
converter = GraphToVector(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)

# 그래프 → 텍스트 변환
facts = converter.extract_graph_facts()
print(f"총 {len(facts)}개 fact 추출")

# 벡터 DB 생성
vector_store = converter.create_vector_store(facts)

# 저장
vector_store.save_local("medical_kg_vectors")

# 쿼리
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_store.as_retriever(search_kwargs={"k": 5})
)

answer = qa_chain.invoke({"query": "HER2 양성 유방암 치료제는?"})
print(answer['result'])
```

### 장점

- ✅ **기존 파이프라인 재활용**: 표준 RAG 사용
- ✅ **구현 간단**: 1주 내 가능
- ✅ **확장 용이**: 새로운 fact 추가 쉬움

### 단점

- ❌ **그래프 구조 손실**: 경로 정보 상실
- ❌ **복잡한 쿼리 어려움**: Multi-hop reasoning 제한
- ❌ **업데이트 오버헤드**: 그래프 변경 시 벡터 재생성 필요

### 추천 사용 시기

- 빠른 프로토타입
- 기존 RAG 시스템에 그래프 데이터 추가
- 보조 수단으로 활용

---

## 구현 로드맵

### Phase 1: Template-based (1-2주) 🎯

**목표**: 빠른 프로토타입, 핵심 기능 검증

**작업**:
1. 핵심 질문 유형 5-10개 정의
2. Cypher 템플릿 작성
3. LLM 파라미터 추출 로직
4. 간단한 웹 UI (Streamlit)

**결과물**:
- `query_templates.py` - 템플릿 정의
- `param_extractor.py` - LLM 기반 파라미터 추출
- `app.py` - Streamlit UI

**예상 질문 유형**:
```python
PHASE1_TEMPLATES = [
    "암종 X의 바이오마커는?",
    "바이오마커 Y 검사 방법은?",
    "암종 X, 바이오마커 Y 치료제는?",
    "약물 Z가 포함된 레지멘은?",
    "암종 X의 급여 인정 요법은?",
    "바이오마커 Y를 타겟하는 약물은?",
    "암종 X의 N차 치료 레지멘은?",
]
```

---

### Phase 2: GraphRAG (2-4주) 🔥

**목표**: 유연한 질문 처리, 관계 활용

**작업**:
1. 노드 임베딩 생성 (SentenceTransformer)
2. 벡터 유사도 검색 구현
3. 서브그래프 추출 로직
4. 그래프 → 텍스트 변환
5. LLM 통합

**결과물**:
- `graph_rag.py` - GraphRAG 엔진
- `node_embeddings.pkl` - 사전 계산된 임베딩
- `subgraph_extractor.py` - 서브그래프 추출

**기술 스택**:
- LlamaIndex 또는 Custom 구현
- FAISS (벡터 검색)
- Neo4j APOC (그래프 알고리즘)

---

### Phase 3: Text-to-Cypher (1-2개월) 🚀

**목표**: 완전한 자연어 인터페이스

**작업**:
1. 스키마 문서화 (상세)
2. Few-shot 예시 20-30개 작성
3. Cypher validation 로직
4. GPT-4 fine-tuning 고려
5. 오류 처리 및 폴백

**결과물**:
- `text_to_cypher.py` - NL2Cypher 엔진
- `cypher_examples.json` - Few-shot 예시
- `cypher_validator.py` - 쿼리 검증
- `schema_docs.md` - 상세 스키마 문서

**Few-shot 예시 구조**:
```json
[
  {
    "question": "폐암의 바이오마커는?",
    "cypher": "MATCH (d:Disease)-[:HAS_BIOMARKER]->(b:Biomarker)\nWHERE d.kcd_code STARTS WITH 'C34'\nRETURN DISTINCT b.name_ko, b.name_en",
    "explanation": "폐암은 KCD 코드 C34로 시작하며, HAS_BIOMARKER 관계를 따라 바이오마커를 찾습니다."
  },
  ...
]
```

---

## Use Case 시나리오

### 시나리오 1: 의사 진료 보조

**상황**: 의사가 환자 진단 후 치료법 검색

**질문 예시**:
- "EGFR 돌연변이 양성 비소세포폐암 1차 치료는?"
- "이 환자에게 필요한 바이오마커 검사는?"
- "Osimertinib 급여 인정 기준은?"

**추천 방법**: Template-based (Phase 1)
- 정확도 최우선
- 질문 패턴 예측 가능
- 빠른 응답 필요

**구현**:
```python
# 템플릿: regimen_by_cancer_biomarker_line
질문: "EGFR 돌연변이 양성 비소세포폐암 1차 치료는?"
↓ 파라미터 추출
{
    "kcd_prefix": "C34",
    "biomarker": "EGFR",
    "line": "1차"
}
↓ Cypher 실행
MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)...
↓ 결과
"Osimertinib 단독요법 (고시 제2024-XXX호)"
```

---

### 시나리오 2: 환자 교육 챗봇

**상황**: 환자가 진단명 듣고 질문

**질문 예시**:
- "유방암이 뭔가요?"
- "HER2 검사는 어떻게 하나요?"
- "항암 치료 비용은 얼마나 드나요?"

**추천 방법**: GraphRAG (Phase 2)
- 다양한 질문 유형
- 관련 정보 함께 제공
- 자연스러운 대화

**구현**:
```python
질문: "HER2 검사는 어떻게 하나요?"
↓ 벡터 검색
유사 노드: ["HER2", "면역조직화학염색", "유방암"]
↓ 서브그래프 추출
HER2 -[:TESTED_BY]-> Test
HER2 <-[:HAS_BIOMARKER]- Disease
↓ 컨텍스트
"HER2는 면역조직화학염색(EDI: C5731)으로 검사합니다.
 유방암 환자에서 주로 검사하며..."
↓ LLM 생성
자연어 답변
```

---

### 시나리오 3: 연구자 데이터 탐색

**상황**: 연구자가 복잡한 패턴 분석

**질문 예시**:
- "PD-L1 억제제를 사용하는 모든 암종과 병용 약물 조합은?"
- "바이오마커 검사 없이 급여 인정되는 면역항암제는?"
- "최근 2년간 신규 급여 인정된 표적치료제는?"

**추천 방법**: Text-to-Cypher (Phase 3)
- 복잡한 쿼리
- 탐색적 분석
- 정형화 어려움

**구현**:
```python
질문: "PD-L1 억제제를 사용하는 모든 암종과 병용 약물은?"
↓ Cypher 생성
MATCH (d:Disease)-[:TREATED_BY]->(r:Regimen)-[:INCLUDES]->(drug1:Drug)
MATCH (r)-[:INCLUDES]->(drug2:Drug)
WHERE drug1.mechanism_of_action CONTAINS 'PD-L1'
  AND drug1 <> drug2
RETURN d.name_kr, drug1.ingredient_ko,
       collect(DISTINCT drug2.ingredient_ko) as combo
↓ 결과
복잡한 분석 데이터
```

---

## 성능 비교

### 응답 시간

| 방법 | 평균 응답 시간 | LLM 호출 | DB 쿼리 |
|------|---------------|----------|---------|
| Template-based | 1-2초 | 2회 (파라미터 + 답변) | 1회 |
| GraphRAG | 2-4초 | 2회 (파라미터 + 답변) | 2회 (벡터 + 그래프) |
| Text-to-Cypher | 3-5초 | 3회 (Cypher생성 + 검증 + 답변) | 1회 |
| Graph-to-Vector | 1-2초 | 1회 (답변) | 0회 (벡터만) |

### 정확도 (의료 도메인)

| 방법 | 질문 이해 | 정보 검색 | 답변 정확도 |
|------|-----------|-----------|------------|
| Template-based | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ (95%+) |
| GraphRAG | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ (90%+) |
| Text-to-Cypher | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ (80%+) |
| Graph-to-Vector | ⭐⭐ | ⭐⭐ | ⭐⭐ (75%+) |

### 비용 (1000 쿼리 기준)

| 방법 | LLM 비용 | 인프라 비용 | 총 비용 |
|------|----------|------------|---------|
| Template-based | $5 | $1 (Neo4j) | $6 |
| GraphRAG | $8 | $3 (Neo4j + Vector) | $11 |
| Text-to-Cypher | $15 | $1 (Neo4j) | $16 |
| Graph-to-Vector | $3 | $2 (Vector) | $5 |

---

## 참고 자료

### LangChain
- [GraphCypherQAChain](https://python.langchain.com/docs/use_cases/graph/graph_cypher_qa)
- [Neo4j Integration](https://python.langchain.com/docs/integrations/graphs/neo4j_cypher)

### LlamaIndex
- [Knowledge Graph Index](https://docs.llamaindex.ai/en/stable/examples/index_structs/knowledge_graph/)
- [Neo4j Graph Store](https://docs.llamaindex.ai/en/stable/examples/storage/graph_store/)

### Neo4j
- [Graph Data Science](https://neo4j.com/docs/graph-data-science/current/)
- [APOC Procedures](https://neo4j.com/labs/apoc/)

### 논문
- GraphRAG: [arxiv.org/abs/2404.16130](https://arxiv.org/abs/2404.16130)
- Text-to-Cypher: [arxiv.org/abs/2308.07109](https://arxiv.org/abs/2308.07109)

---

## 다음 단계

### 즉시 시작 가능

1. **Template-based 프로토타입** (1일)
   ```bash
   python create_template_engine.py
   streamlit run app.py
   ```

2. **노드 임베딩 생성** (1일)
   ```bash
   python embed_nodes.py
   ```

3. **GraphRAG 구현** (1주)
   ```bash
   python setup_graphrag.py
   ```

어떤 방법으로 시작하시겠습니까?
