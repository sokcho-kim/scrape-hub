"""
Phase 4: Neo4j 통합

Phase 1-3에서 생성한 모든 데이터를 Neo4j 그래프 데이터베이스에 통합합니다.

노드 타입:
- Biomarker: 바이오마커
- Test: HINS EDI 검사
- Drug: 항암제

관계:
- (Biomarker)-[:TESTED_BY]->(Test)
- (Drug)-[:TARGETS]->(Biomarker)
"""

import json
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv


# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent  # neo4j/scripts/ -> scrape-hub/
BRIDGES_DIR = PROJECT_ROOT / "bridges"
DATA_DIR = PROJECT_ROOT / "data" / "hins" / "parsed"

INPUT_DRUGS = BRIDGES_DIR / "anticancer_master_classified.json"
INPUT_BIOMARKERS = BRIDGES_DIR / "biomarkers_extracted.json"
INPUT_TESTS = DATA_DIR / "biomarker_tests_structured.json"
INPUT_MAPPINGS = BRIDGES_DIR / "biomarker_test_mappings.json"

# .env 파일 로드
load_dotenv(PROJECT_ROOT / ".env")

# Neo4j 연결 정보 (환경변수 또는 기본값)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class Neo4jIntegrator:
    """Neo4j 통합 클래스"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {
            'biomarkers': 0,
            'tests': 0,
            'drugs': 0,
            'tested_by_rels': 0,
            'targets_rels': 0
        }

    def close(self):
        """연결 종료"""
        self.driver.close()

    def clear_database(self):
        """데이터베이스 초기화 (선택적)"""
        print("[WARN] 기존 데이터 삭제 중...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("[OK] 데이터베이스 초기화 완료")

    def create_constraints_and_indexes(self):
        """제약조건 및 인덱스 생성"""
        print("\n[INFO] 제약조건 및 인덱스 생성 중...")

        constraints = [
            "CREATE CONSTRAINT biomarker_id IF NOT EXISTS FOR (b:Biomarker) REQUIRE b.biomarker_id IS UNIQUE",
            "CREATE CONSTRAINT test_id IF NOT EXISTS FOR (t:Test) REQUIRE t.test_id IS UNIQUE",
            "CREATE CONSTRAINT drug_atc IF NOT EXISTS FOR (d:Drug) REQUIRE d.atc_code IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX biomarker_name IF NOT EXISTS FOR (b:Biomarker) ON (b.name_en)",
            "CREATE INDEX test_edi_code IF NOT EXISTS FOR (t:Test) ON (t.edi_code)",
            "CREATE INDEX drug_ingredient IF NOT EXISTS FOR (d:Drug) ON (d.ingredient_ko)",
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"[SKIP] {e}")

            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    print(f"[SKIP] {e}")

        print("[OK] 제약조건 및 인덱스 생성 완료")

    def import_biomarkers(self, biomarkers_data):
        """바이오마커 노드 생성"""
        print("\n[INFO] 바이오마커 노드 생성 중...")

        biomarkers = biomarkers_data['biomarkers']

        cypher = """
        UNWIND $biomarkers AS bm
        CREATE (b:Biomarker {
            biomarker_id: bm.biomarker_id,
            name_en: bm.biomarker_name_en,
            name_ko: bm.biomarker_name_ko,
            type: bm.biomarker_type,
            protein_gene: bm.protein_gene,
            cancer_types: bm.cancer_types,
            drug_count: bm.drug_count,
            source: bm.source,
            confidence: bm.confidence,
            created_at: bm.created_at
        })
        """

        with self.driver.session() as session:
            result = session.run(cypher, biomarkers=biomarkers)
            self.stats['biomarkers'] = len(biomarkers)

        print(f"[OK] {self.stats['biomarkers']}개 바이오마커 노드 생성")

    def import_tests(self, tests_data):
        """검사 노드 생성"""
        print("\n[INFO] 검사 노드 생성 중...")

        tests = tests_data['tests']

        cypher = """
        UNWIND $tests AS test
        CREATE (t:Test {
            test_id: test.test_id,
            edi_code: test.edi_code,
            name_ko: test.test_name_ko,
            name_en: test.test_name_en,
            biomarker_name: test.biomarker_name,
            category: test.test_category,
            loinc_code: test.loinc_code,
            snomed_ct_id: test.snomed_ct_id,
            snomed_ct_name: test.snomed_ct_name,
            reference_year: test.reference_year,
            data_source: test.data_source,
            created_at: test.created_at
        })
        """

        with self.driver.session() as session:
            result = session.run(cypher, tests=tests)
            self.stats['tests'] = len(tests)

        print(f"[OK] {self.stats['tests']}개 검사 노드 생성")

    def import_drugs(self, drugs_data):
        """항암제 노드 생성"""
        print("\n[INFO] 항암제 노드 생성 중...")

        # 중복된 ATC 코드 제거 (첫 번째 것만 유지)
        seen_atc = set()
        unique_drugs = []
        duplicates = 0

        for drug in drugs_data:
            atc = drug['atc_code']
            if atc not in seen_atc:
                seen_atc.add(atc)
                unique_drugs.append(drug)
            else:
                duplicates += 1

        if duplicates > 0:
            print(f"[WARN] 중복된 ATC 코드 {duplicates}개 제거됨")

        drugs = unique_drugs

        cypher = """
        UNWIND $drugs AS drug
        CREATE (d:Drug {
            atc_code: drug.atc_code,
            ingredient_ko: drug.ingredient_ko,
            ingredient_en: drug.ingredient_base_en,
            mechanism_of_action: drug.mechanism_of_action,
            therapeutic_category: drug.therapeutic_category,
            atc_level1: drug.atc_level1,
            atc_level2: drug.atc_level2,
            atc_level3: drug.atc_level3,
            atc_level3_name: drug.atc_level3_name,
            atc_level4: drug.atc_level4,
            atc_level4_name: drug.atc_level4_name,
            created_at: drug.created_at
        })
        """

        with self.driver.session() as session:
            result = session.run(cypher, drugs=drugs)
            self.stats['drugs'] = len(drugs)

        print(f"[OK] {self.stats['drugs']}개 항암제 노드 생성")

    def create_biomarker_test_relationships(self, mappings_data):
        """바이오마커-검사 관계 생성"""
        print("\n[INFO] 바이오마커-검사 관계 생성 중...")

        mappings = mappings_data['mappings']

        # 관계 생성을 위한 데이터 변환
        relationships = []
        for mapping in mappings:
            biomarker_id = mapping['biomarker_id']
            for test in mapping['matched_tests']:
                relationships.append({
                    'biomarker_id': biomarker_id,
                    'test_id': test['test_id'],
                    'match_type': test['match_type'],
                    'confidence': test['confidence']
                })

        cypher = """
        UNWIND $rels AS rel
        MATCH (b:Biomarker {biomarker_id: rel.biomarker_id})
        MATCH (t:Test {test_id: rel.test_id})
        CREATE (b)-[:TESTED_BY {
            match_type: rel.match_type,
            confidence: rel.confidence,
            created_at: datetime()
        }]->(t)
        """

        with self.driver.session() as session:
            result = session.run(cypher, rels=relationships)
            self.stats['tested_by_rels'] = len(relationships)

        print(f"[OK] {self.stats['tested_by_rels']}개 TESTED_BY 관계 생성")

    def create_drug_biomarker_relationships(self, biomarkers_data):
        """약물-바이오마커 관계 생성"""
        print("\n[INFO] 약물-바이오마커 관계 생성 중...")

        biomarkers = biomarkers_data['biomarkers']

        # 관계 생성을 위한 데이터 변환
        relationships = []
        for biomarker in biomarkers:
            biomarker_id = biomarker['biomarker_id']
            for drug in biomarker['related_drugs']:
                relationships.append({
                    'atc_code': drug['atc_code'],
                    'biomarker_id': biomarker_id
                })

        cypher = """
        UNWIND $rels AS rel
        MATCH (d:Drug {atc_code: rel.atc_code})
        MATCH (b:Biomarker {biomarker_id: rel.biomarker_id})
        CREATE (d)-[:TARGETS {
            created_at: datetime()
        }]->(b)
        """

        with self.driver.session() as session:
            result = session.run(cypher, rels=relationships)
            self.stats['targets_rels'] = len(relationships)

        print(f"[OK] {self.stats['targets_rels']}개 TARGETS 관계 생성")

    def verify_import(self):
        """데이터 임포트 검증"""
        print("\n[INFO] 데이터 검증 중...")

        queries = {
            'biomarkers': "MATCH (b:Biomarker) RETURN count(b) as count",
            'tests': "MATCH (t:Test) RETURN count(t) as count",
            'drugs': "MATCH (d:Drug) RETURN count(d) as count",
            'tested_by': "MATCH ()-[r:TESTED_BY]->() RETURN count(r) as count",
            'targets': "MATCH ()-[r:TARGETS]->() RETURN count(r) as count"
        }

        with self.driver.session() as session:
            print("\n[VERIFY] Neo4j 데이터베이스 상태:")
            for name, query in queries.items():
                result = session.run(query)
                count = result.single()['count']
                print(f"  - {name}: {count}개")

    def print_sample_queries(self):
        """샘플 쿼리 출력"""
        print("\n" + "=" * 70)
        print("Neo4j 샘플 쿼리")
        print("=" * 70)

        print("\n1. HER2 바이오마커와 관련된 모든 검사 조회:")
        print("""
MATCH (b:Biomarker {name_en: 'HER2'})-[:TESTED_BY]->(t:Test)
RETURN b.name_ko, t.name_ko, t.edi_code, t.category
LIMIT 10
        """)

        print("\n2. EGFR을 표적하는 모든 항암제 조회:")
        print("""
MATCH (d:Drug)-[:TARGETS]->(b:Biomarker {name_en: 'EGFR'})
RETURN d.ingredient_ko, d.mechanism_of_action, d.therapeutic_category
        """)

        print("\n3. 특정 약물의 바이오마커 및 검사 경로 조회:")
        print("""
MATCH path = (d:Drug {ingredient_ko: '게피티니브'})-[:TARGETS]->(b:Biomarker)-[:TESTED_BY]->(t:Test)
RETURN path
        """)

        print("\n4. 바이오마커별 검사 수 통계:")
        print("""
MATCH (b:Biomarker)-[:TESTED_BY]->(t:Test)
RETURN b.name_ko, b.name_en, count(t) as test_count
ORDER BY test_count DESC
        """)

        print("\n" + "=" * 70)

    def run(self, clear_db=False):
        """전체 통합 프로세스 실행"""
        print("=" * 70)
        print("Phase 4: Neo4j 통합")
        print("=" * 70)

        try:
            # 데이터 로드
            print("\n[INFO] 데이터 파일 로딩...")
            with open(INPUT_DRUGS, 'r', encoding='utf-8') as f:
                drugs_data = json.load(f)
            with open(INPUT_BIOMARKERS, 'r', encoding='utf-8') as f:
                biomarkers_data = json.load(f)
            with open(INPUT_TESTS, 'r', encoding='utf-8') as f:
                tests_data = json.load(f)
            with open(INPUT_MAPPINGS, 'r', encoding='utf-8') as f:
                mappings_data = json.load(f)
            print("[OK] 모든 데이터 파일 로드 완료")

            # 데이터베이스 초기화 (옵션)
            if clear_db:
                self.clear_database()

            # 제약조건 및 인덱스
            self.create_constraints_and_indexes()

            # 노드 생성
            self.import_biomarkers(biomarkers_data)
            self.import_tests(tests_data)
            self.import_drugs(drugs_data)

            # 관계 생성
            self.create_biomarker_test_relationships(mappings_data)
            self.create_drug_biomarker_relationships(biomarkers_data)

            # 검증
            self.verify_import()

            # 샘플 쿼리
            self.print_sample_queries()

            print("\n[SUCCESS] Neo4j 통합 완료!")
            return True

        except Exception as e:
            print(f"\n[ERROR] 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='Neo4j 데이터베이스 통합')
    parser.add_argument('--clear-db', action='store_true',
                        help='기존 데이터를 삭제하고 새로 시작')
    parser.add_argument('--skip-neo4j', action='store_true',
                        help='Neo4j 연결 없이 데이터만 검증 (dry-run)')
    args = parser.parse_args()

    print(f"Neo4j 연결 정보:")
    print(f"  URI: {NEO4J_URI}")
    print(f"  User: {NEO4J_USER}")
    print()

    if args.skip_neo4j:
        print("[INFO] --skip-neo4j 모드: Neo4j 연결 없이 데이터 검증만 수행")
        # 데이터 파일만 로드하여 검증
        try:
            with open(INPUT_DRUGS, 'r', encoding='utf-8') as f:
                drugs_data = json.load(f)
            with open(INPUT_BIOMARKERS, 'r', encoding='utf-8') as f:
                biomarkers_data = json.load(f)
            with open(INPUT_TESTS, 'r', encoding='utf-8') as f:
                tests_data = json.load(f)
            with open(INPUT_MAPPINGS, 'r', encoding='utf-8') as f:
                mappings_data = json.load(f)

            print(f"[OK] 데이터 로드 완료:")
            print(f"  - 항암제: {len(drugs_data)}개")
            print(f"  - 바이오마커: {len(biomarkers_data['biomarkers'])}개")
            print(f"  - 검사: {len(tests_data['tests'])}개")
            print(f"  - 매핑: {len(mappings_data['mappings'])}개")
            print(f"  - 총 관계: {sum(m['test_count'] for m in mappings_data['mappings'])}개")
            print("\n[SUCCESS] 데이터 검증 완료! Neo4j 준비되면 --skip-neo4j 없이 실행하세요.")
            return 0
        except Exception as e:
            print(f"[ERROR] 데이터 검증 실패: {e}")
            return 1

    integrator = Neo4jIntegrator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        success = integrator.run(clear_db=args.clear_db)
        return 0 if success else 1

    finally:
        integrator.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
