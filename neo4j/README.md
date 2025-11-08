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

## 🚀 완전 실행 가이드

### Step 1: 환경 설정 (.env 파일)

프로젝트 루트에 `.env` 파일이 있는지 확인하세요. 없다면 생성하세요.

**파일 위치**: `C:\Jimin\scrape-hub\.env`

```env
# Neo4j Configuration
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_DATABASE=mediclaim-kg
```

⚠️ **중요**: `.env` 파일의 비밀번호는 나중에 Docker 컨테이너 실행 시 사용하는 비밀번호와 **반드시 동일**해야 합니다!

### Step 2: Docker Desktop 실행

1. Docker Desktop을 실행하세요
2. Docker가 정상적으로 실행되었는지 확인:
   ```bash
   docker ps
   ```

### Step 3: Neo4j 컨테이너 실행

```bash
# Neo4j 컨테이너 실행 (.env 파일의 비밀번호와 동일하게!)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password_here \
  neo4j:latest
```

**Windows PowerShell의 경우**:
```powershell
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/your_password_here neo4j:latest
```

#### 컨테이너 상태 확인

```bash
# 컨테이너가 실행 중인지 확인
docker ps | grep neo4j

# 로그 확인 (Neo4j가 완전히 시작될 때까지 대기)
docker logs neo4j

# "Started" 메시지가 나올 때까지 기다리세요
```

### Step 4: Python 패키지 설치

```bash
# neo4j 패키지 설치
pip install neo4j python-dotenv

# 또는 requirements.txt 사용
cd neo4j/scripts
pip install -r requirements.txt
cd ../..
```

### Step 5: Neo4j 연결 테스트

```bash
# 프로젝트 루트에서 실행
python neo4j/scripts/test_connection.py
```

**예상 출력**:
```
[SUCCESS] Connection successful!
  Neo4j Kernel: 2025.10.1
  Cypher: 5

[OK] Neo4j is ready!
```

❌ **인증 오류가 발생하면**:
- `.env` 파일의 `NEO4J_PASSWORD`와 Docker 컨테이너의 비밀번호가 일치하는지 확인
- 컨테이너를 삭제하고 다시 실행:
  ```bash
  docker stop neo4j && docker rm neo4j
  # 그리고 Step 3부터 다시 시작
  ```

### Step 6: 데이터 통합 실행

```bash
# 프로젝트 루트에서 실행
python neo4j/scripts/integrate_to_neo4j.py --clear-db
```

**실행 시간**: 약 10-30초

**예상 출력**:
```
======================================================================
Phase 4: Neo4j 통합
======================================================================

[INFO] 데이터 파일 로드...
[OK] 모든 데이터 파일 로드 완료
[WARN] 기존 데이터 삭제 중...
[OK] 데이터베이스 초기화 완료

[INFO] 제약조건 및 인덱스 생성 중...
[OK] 제약조건 및 인덱스 생성 완료

[INFO] 바이오마커 노드 생성 중...
[OK] 17개 바이오마커 노드 생성

[INFO] 검사 노드 생성 중...
[OK] 575개 검사 노드 생성

[INFO] 항암제 노드 생성 중...
[WARN] 중복된 ATC 코드 16개 제거됨
[OK] 138개 항암제 노드 생성

[INFO] 바이오마커-검사 관계 생성 중...
[OK] 996개 TESTED_BY 관계 생성

[INFO] 약물-바이오마커 관계 생성 중...
[OK] 71개 TARGETS 관계 생성

[VERIFY] Neo4j 데이터베이스 현황:
  - biomarkers: 17개
  - tests: 575개
  - drugs: 138개
  - tested_by: 996개
  - targets: 71개

[SUCCESS] Neo4j 통합 완료!
```

### Step 7: Neo4j Browser에서 확인

1. 브라우저에서 접속: **http://localhost:7474**

2. 로그인:
   - **Username**: `neo4j`
   - **Password**: `.env` 파일에 설정한 비밀번호

3. 첫 번째 쿼리 실행:
   ```cypher
   MATCH (n)
   RETURN labels(n) as NodeType, count(n) as Count
   ORDER BY Count DESC
   ```

**예상 결과**:
```
┌──────────────┬───────┐
│ NodeType     │ Count │
├──────────────┼───────┤
│ ["Test"]     │ 575   │
│ ["Drug"]     │ 138   │
│ ["Biomarker"]│  17   │
└──────────────┴───────┘
```

---

## ✅ 빠른 체크리스트

실행 전 확인 사항:

- [ ] Docker Desktop 실행됨
- [ ] `.env` 파일 존재 (Neo4j 설정 포함)
- [ ] Neo4j 컨테이너 실행 중 (`docker ps | grep neo4j`)
- [ ] Neo4j 완전히 시작됨 (`docker logs neo4j` - "Started" 확인)
- [ ] Python 패키지 설치됨 (`neo4j`, `python-dotenv`)
- [ ] 연결 테스트 성공 (`test_connection.py`)

---

## 🔄 재실행 방법

이미 데이터를 통합했고, 다시 실행하고 싶다면:

```bash
# 기존 데이터 삭제하고 재통합
python neo4j/scripts/integrate_to_neo4j.py --clear-db

# 또는 Neo4j 컨테이너를 완전히 재시작
docker stop neo4j
docker rm neo4j
# 그리고 Step 3부터 다시 시작
```

---

## 📊 데이터 현황 (2025-11-08 통합 완료)

| 노드/관계 | 개수 | 설명 |
|-----------|------|------|
| **Biomarker** | 17개 | 항암제 관련 바이오마커 |
| **Test** | 575개 | HINS EDI 검사 (SNOMED CT 94% 매칭) |
| **Drug** | 138개 | 항암제 (중복 16개 제거) |
| **TESTED_BY** | 996개 | 바이오마커-검사 관계 |
| **TARGETS** | 71개 | 약물-바이오마커 관계 |

**총 노드**: 730개
**총 관계**: 1,067개

**데이터 소스**:
- 항암제: `bridges/anticancer_master_classified.json` (154개 → 138개 unique)
- 바이오마커: `bridges/biomarkers_extracted.json` (v1.0, 17개)
- 검사: `data/hins/parsed/biomarker_tests_structured.json` (575개)
- 매핑: `bridges/biomarker_test_mappings.json` (996개 관계)

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

### ❌ 인증 오류 (Authentication Failed)

**문제**: `The client is unauthorized due to authentication failure`

**원인**: `.env` 파일의 비밀번호와 Docker 컨테이너 비밀번호 불일치

**해결**:
```bash
# 1. 컨테이너 삭제
docker stop neo4j
docker rm neo4j

# 2. .env 파일의 비밀번호 확인
cat .env | grep NEO4J_PASSWORD

# 3. 동일한 비밀번호로 컨테이너 재실행
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_actual_password \
  neo4j:latest

# 4. 연결 테스트
python neo4j/scripts/test_connection.py
```

### ❌ 파일 경로 오류 (FileNotFoundError)

**문제**: `No such file or directory: 'C:\...\anticancer_master_classified.json'`

**원인**: 스크립트를 잘못된 위치에서 실행

**해결**:
```bash
# 반드시 프로젝트 루트에서 실행
cd C:\Jimin\scrape-hub
python neo4j/scripts/integrate_to_neo4j.py --clear-db
```

### ❌ 중복 키 오류 (ConstraintError)

**문제**: `Node already exists with label 'Drug' and property 'atc_code'`

**원인**: 데이터에 중복된 ATC 코드 존재

**해결**: 이미 수정됨 (2025-11-08)
- `integrate_to_neo4j.py`가 자동으로 중복 제거
- 16개 중복 ATC 코드는 자동으로 필터링됨

### ❌ Neo4j 컨테이너 실행 안 됨

**문제**: Docker 컨테이너가 시작되지 않음

**확인**:
```bash
# Docker Desktop이 실행 중인지 확인
docker ps

# Neo4j 로그 확인
docker logs neo4j

# 포트 충돌 확인
netstat -ano | findstr :7474
netstat -ano | findstr :7687
```

**해결**:
```bash
# 포트가 이미 사용 중이면 다른 포트 사용
docker run -d --name neo4j \
  -p 7475:7474 -p 7688:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### 느린 쿼리
- 제약조건 및 인덱스 확인: `SHOW INDEXES;`
- `EXPLAIN` 또는 `PROFILE` 사용
- 필요시 추가 인덱스 생성

### 메모리 부족
```bash
# Docker 메모리 할당 증가
docker run -d --name neo4j \
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

**마지막 업데이트**: 2025-11-08
**버전**: 1.1 (실행 가이드 완성, 문제 해결 추가)

## 🎯 변경 이력

### v1.1 (2025-11-08)
- ✅ 완전 실행 가이드 추가 (Step 1-7)
- ✅ `.env` 파일 기반 설정으로 변경
- ✅ 문제 해결 섹션 확장 (실제 경험 기반)
- ✅ 데이터 현황 업데이트 (730개 노드, 1,067개 관계)
- ✅ 중복 ATC 코드 처리 (16개 제거)
- ✅ 빠른 체크리스트 추가

### v1.0 (2025-11-07)
- 초기 문서 작성
- 기본 스키마 및 쿼리 정의
