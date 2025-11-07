# Neo4j 그래프 데이터베이스 통합

항암제-바이오마커-검사 데이터를 Neo4j 그래프 데이터베이스에 통합하고 분석하는 시스템

---

## 📁 폴더 구조

```
neo4j/
├── scripts/
│   ├── integrate_to_neo4j.py          # 메인 통합 스크립트
│   ├── import_anticancer_drugs.py     # 항암제 임포트 (기존)
│   ├── test_connection.py             # 연결 테스트
│   └── requirements.txt               # Python 의존성
│
├── queries/
│   └── sample_queries.cypher          # 샘플 Cypher 쿼리 모음
│
├── docs/
│   └── (Neo4j 관련 문서)
│
└── README.md (this file)
```

---

## 🎯 그래프 스키마

### 노드 타입

#### 1. Biomarker (바이오마커)
```cypher
(:Biomarker {
  biomarker_id: String,      // 고유 ID (예: "BIOMARKER_001")
  name_en: String,           // 영문명 (예: "HER2")
  name_ko: String,           // 한글명 (예: "HER2 수용체")
  type: String,              // protein, mutation, fusion_gene, enzyme
  protein_gene: String,      // 유전자명
  cancer_types: [String],    // 관련 암종 목록
  drug_count: Integer,       // 관련 약물 수
  source: String,            // 데이터 출처
  confidence: Float,         // 신뢰도
  created_at: DateTime       // 생성 시간
})
```

**제약조건**: `biomarker_id` UNIQUE

#### 2. Test (검사)
```cypher
(:Test {
  test_id: String,           // 고유 ID (예: "HINS_TEST_001")
  edi_code: String,          // EDI 코드
  name_ko: String,           // 한글 검사명
  name_en: String,           // 영문 검사명
  biomarker_name: String,    // 바이오마커명
  category: String,          // 검사 카테고리
  loinc_code: String,        // LOINC 표준 코드
  snomed_ct_id: String,      // SNOMED CT 코드
  snomed_ct_name: String,    // SNOMED CT 명칭
  reference_year: Integer,   // 참조 연도
  data_source: String,       // 데이터 출처
  created_at: DateTime       // 생성 시간
})
```

**제약조건**: `test_id` UNIQUE

#### 3. Drug (항암제)
```cypher
(:Drug {
  atc_code: String,                // ATC 코드 (고유 ID)
  ingredient_ko: String,           // 한글 성분명
  ingredient_en: String,           // 영문 성분명
  mechanism_of_action: String,     // 작용 기전
  therapeutic_category: String,    // 치료 분류
  atc_level1: String,              // ATC Level 1
  atc_level2: String,              // ATC Level 2
  atc_level3: String,              // ATC Level 3
  atc_level3_name: String,         // ATC Level 3 명칭
  atc_level4: String,              // ATC Level 4
  atc_level4_name: String,         // ATC Level 4 명칭
  created_at: DateTime             // 생성 시간
})
```

**제약조건**: `atc_code` UNIQUE

### 관계 타입

#### 1. TESTED_BY (바이오마커 → 검사)
```cypher
(b:Biomarker)-[:TESTED_BY {
  match_type: String,        // exact_match, partial_match, composite_match
  confidence: Float,         // 매칭 신뢰도 (0.8-0.95)
  created_at: DateTime       // 생성 시간
}]->(t:Test)
```

**의미**: 특정 바이오마커가 특정 검사로 측정됨

#### 2. TARGETS (약물 → 바이오마커)
```cypher
(d:Drug)-[:TARGETS {
  created_at: DateTime       // 생성 시간
}]->(b:Biomarker)
```

**의미**: 특정 약물이 특정 바이오마커를 표적함

---

## 🚀 실행 방법

### 1. 사전 준비

#### Option A: Docker로 Neo4j 실행 (권장)
```bash
# Neo4j 컨테이너 실행
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# 상태 확인
docker ps
```

#### Option B: Neo4j Desktop 설치
1. https://neo4j.com/download/ 에서 Neo4j Desktop 다운로드
2. 새 데이터베이스 생성
3. 데이터베이스 시작

### 2. Python 환경 설정

```bash
# 의존성 설치
cd neo4j/scripts
pip install -r requirements.txt

# 또는 직접 설치
pip install neo4j
```

### 3. 환경 변수 설정

```bash
# Windows (PowerShell)
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="password"

# Linux/Mac
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"
```

### 4. 데이터 통합 실행

#### 데이터 검증 (Neo4j 없이)
```bash
cd ../..  # 프로젝트 루트로
python neo4j/scripts/integrate_to_neo4j.py --skip-neo4j
```

#### 실제 통합 (기존 데이터 삭제)
```bash
python neo4j/scripts/integrate_to_neo4j.py --clear-db
```

#### 실제 통합 (기존 데이터 유지)
```bash
python neo4j/scripts/integrate_to_neo4j.py
```

### 5. Neo4j Browser 접속

```
http://localhost:7474
```

**로그인 정보**:
- Username: `neo4j`
- Password: `password`

---

## 📊 데이터 현황

| 노드/관계 | 개수 | 설명 |
|-----------|------|------|
| **Biomarker** | 17개 | 항암제 관련 바이오마커 |
| **Test** | 575개 | HINS EDI 검사 |
| **Drug** | 154개 | 항암제 |
| **TESTED_BY** | 996개 | 바이오마커-검사 관계 |
| **TARGETS** | 55개 | 약물-바이오마커 관계 |

**총 노드**: 746개
**총 관계**: 1,051개

---

## 🔍 주요 쿼리

### 기본 확인

```cypher
// 전체 노드 수
MATCH (n)
RETURN labels(n) as NodeType, count(n) as Count
ORDER BY Count DESC;

// 전체 관계 수
MATCH ()-[r]->()
RETURN type(r) as RelationType, count(r) as Count;
```

### HER2 분석

```cypher
// HER2 관련 모든 검사
MATCH (b:Biomarker {name_en: 'HER2'})-[:TESTED_BY]->(t:Test)
RETURN b.name_ko, t.name_ko, t.edi_code, t.category
LIMIT 20;
```

### 약물-바이오마커-검사 경로

```cypher
// 게피티니브의 전체 치료 경로
MATCH path = (d:Drug {ingredient_ko: '게피티니브'})
             -[:TARGETS]->(b:Biomarker)
             -[:TESTED_BY]->(t:Test)
RETURN path
LIMIT 10;
```

**더 많은 쿼리**: `queries/sample_queries.cypher` 참조

---

## 📈 활용 사례

### 1. 임상 의사결정 지원
- 특정 암종에 대한 표적치료제 선택
- 바이오마커 검사 가이드라인 제공

### 2. 연구 및 개발
- 신약 개발 타겟 발굴
- 바이오마커-약물 연관성 분석

### 3. 보험 청구 최적화
- EDI 코드 기반 검사 비용 분석
- 검사-약물 연계 패턴 분석

---

## 🛠 유지보수

### 데이터 업데이트

```bash
# 기존 데이터 삭제 후 재통합
python neo4j/scripts/integrate_to_neo4j.py --clear-db
```

### 백업

```bash
# Neo4j 덤프
docker exec neo4j neo4j-admin database dump neo4j --to-stdout > backup.dump

# 복구
docker exec -i neo4j neo4j-admin database load neo4j --from-stdin < backup.dump
```

### 성능 최적화

```cypher
// 인덱스 확인
SHOW INDEXES;

// 쿼리 프로파일링
PROFILE
MATCH (b:Biomarker)-[:TESTED_BY]->(t:Test)
RETURN b, t
LIMIT 10;
```

---

## 🔧 문제 해결

### 연결 실패
```bash
# Neo4j 상태 확인
docker ps | grep neo4j

# 로그 확인
docker logs neo4j
```

### 느린 쿼리
- 제약조건 및 인덱스 확인
- `EXPLAIN` 또는 `PROFILE` 사용
- 필요시 추가 인덱스 생성

### 메모리 부족
```bash
# Docker 메모리 할당 증가
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_server_memory_heap_initial__size=1G \
  -e NEO4J_server_memory_heap_max__size=2G \
  neo4j:latest
```

---

## 📚 참고 자료

- **Neo4j 공식 문서**: https://neo4j.com/docs/
- **Cypher 매뉴얼**: https://neo4j.com/docs/cypher-manual/
- **Neo4j Python Driver**: https://neo4j.com/docs/python-manual/
- **프로젝트 문서**: `../docs/journal/`

---

## 🤝 기여

1. 새로운 쿼리 추가: `queries/` 폴더에 .cypher 파일 생성
2. 스크립트 개선: `scripts/` 폴더
3. 문서화: `docs/` 폴더

---

## 📝 라이선스

본 프로젝트의 라이선스를 따름

---

**마지막 업데이트**: 2025-11-07
**버전**: 1.0
