# Neo4j Import Scripts

## 사전 준비

### 1. Neo4j 설치

**Option 1: Neo4j Desktop (추천)**
```
1. https://neo4j.com/download/ 방문
2. Neo4j Desktop 다운로드 (Windows)
3. 설치 후 실행
4. "New Project" 클릭
5. "Add Database" → "Create Local Database"
6. Database name: anticancer-kg
7. Password 설정 (예: password123)
8. "Create" 클릭
9. "Start" 버튼 클릭 (데이터베이스 시작)
```

**Option 2: Docker**
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### 2. Python 패키지 설치

```bash
pip install neo4j
```

---

## 사용 방법

### 1. 비밀번호 설정

`import_anticancer_drugs.py` 파일을 열고 비밀번호 변경:

```python
NEO4J_PASSWORD = "password"  # ← 여기를 Neo4j 설치 시 설정한 비밀번호로 변경
```

### 2. 스크립트 실행

```bash
cd C:/Jimin/scrape-hub
python scripts/neo4j/import_anticancer_drugs.py
```

### 3. 예상 출력

```
============================================================
Neo4j Import: AnticancerDrug Nodes
============================================================

[1/5] Loading data: anticancer_master_classified.json
   >> Loaded 154 drugs

[2/5] Connecting to Neo4j...
   URI: bolt://localhost:7687
   User: neo4j
[OK] Connected to Neo4j at bolt://localhost:7687

[3/5] Clearing existing AnticancerDrug nodes...
[OK] Cleared existing AnticancerDrug nodes

[4/5] Importing 154 AnticancerDrug nodes...
   [OK] Created 154 nodes

[5/5] Creating indexes...
[OK] Created 6 indexes

[6/6] Verifying import...
   Total nodes: 154

   ATC Level 1 distribution:
      L01 (항종양제): 135
      L02 (내분비치료제): 19

   Therapeutic category distribution:
      표적치료제: 89
      세포독성 항암제: 46
      내분비치료제: 19

   Sample drugs:
      플루오로우라실 (L01BC02) - 세포독성 항암제
      세리티닙 (L01ED02) - 표적치료제
      ...

============================================================
[SUCCESS] Import Complete
============================================================

 Imported: 154 AnticancerDrug nodes
 Indexes: 6 created

Next steps:
  1. Open Neo4j Browser: http://localhost:7474
  2. Run query: MATCH (d:AnticancerDrug) RETURN d LIMIT 25
  3. Explore the graph!
```

---

## 데이터 확인

### Neo4j Browser 접속

1. 브라우저에서 http://localhost:7474 접속
2. Username: `neo4j`, Password: (설정한 비밀번호) 입력
3. 로그인

### 샘플 쿼리

#### 1. 전체 약제 조회 (처음 25개)
```cypher
MATCH (d:AnticancerDrug)
RETURN d
LIMIT 25
```

#### 2. L01 항종양제만 조회
```cypher
MATCH (d:AnticancerDrug)
WHERE d.atc_level1 = 'L01'
RETURN d.ingredient_ko, d.atc_code, d.therapeutic_category
LIMIT 10
```

#### 3. 표적치료제 조회
```cypher
MATCH (d:AnticancerDrug)
WHERE d.therapeutic_category = '표적치료제'
RETURN d.ingredient_ko, d.mechanism_of_action, d.atc_level3_name
LIMIT 10
```

#### 4. CDK4/6 억제제 조회
```cypher
MATCH (d:AnticancerDrug)
WHERE d.mechanism_of_action = 'CDK4/6 억제'
RETURN d.ingredient_ko, d.brand_name_primary, d.atc_code
```

#### 5. 특정 브랜드명으로 검색
```cypher
MATCH (d:AnticancerDrug)
WHERE '버제니오' IN d.brand_names_clean
RETURN d
```

#### 6. 통계 조회
```cypher
MATCH (d:AnticancerDrug)
RETURN
  d.atc_level1 as ATC_Level,
  d.atc_level1_name as Category,
  count(d) as Count
ORDER BY Count DESC
```

#### 7. 염 형태가 있는 약제
```cypher
MATCH (d:AnticancerDrug)
WHERE d.salt_form IS NOT NULL
RETURN d.ingredient_ko, d.ingredient_base_ko, d.salt_form
LIMIT 10
```

---

## 트러블슈팅

### 에러: "Failed to connect to Neo4j"

**원인**: Neo4j가 실행되지 않음

**해결**:
1. Neo4j Desktop에서 데이터베이스 "Start" 버튼 확인
2. 또는 Docker 컨테이너 실행 확인: `docker ps`

---

### 에러: "Authentication failed"

**원인**: 비밀번호가 틀림

**해결**:
1. 스크립트의 `NEO4J_PASSWORD` 확인
2. Neo4j Desktop에서 설정한 비밀번호와 일치하는지 확인

---

### 에러: "neo4j module not found"

**원인**: Python 패키지 미설치

**해결**:
```bash
pip install neo4j
```

---

## 노드 스키마

```cypher
(:AnticancerDrug {
  // 기본 정보
  atc_code: "L01EF03",
  ingredient_ko: "아베마시클립",
  ingredient_en: "abemaciclib",

  // 염/기본형
  ingredient_base_ko: "아베마시클립",
  ingredient_base_en: "abemaciclib",
  salt_form: null,

  // 브랜드명
  brand_name_primary: "버제니오",
  brand_names_clean: ["버제니오"],
  brand_names_raw: ["버제니오정50밀리그램(아베마시클립)_..."],

  // ATC 분류
  atc_level1: "L01",
  atc_level1_name: "항종양제",
  atc_level2: "L01E",
  atc_level2_name: "단백질 키나제 억제제",
  atc_level3: "L01EF",
  atc_level3_name: "CDK4/6 억제제",

  // 약리학적 정보
  mechanism_of_action: "CDK4/6 억제",
  therapeutic_category: "표적치료제",

  // 제조사
  manufacturers: ["한국릴리(유)"],

  // 기타
  ingredient_code: "686601ATB",
  product_codes: ["670801140", "670801160", "670801180"],
  is_recombinant: false
})
```

---

## 인덱스 목록

1. `anticancer_atc`: atc_code
2. `anticancer_ingredient_ko`: ingredient_ko
3. `anticancer_ingredient_en`: ingredient_en
4. `anticancer_level1`: atc_level1
5. `anticancer_level2`: atc_level2
6. `anticancer_category`: therapeutic_category

---

**다음 단계**: Week 2 - Cancer 및 Biomarker 노드 추가
