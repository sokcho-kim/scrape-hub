"""
통합 의료 지식그래프 구축 (완전 코드 기반)

NCC 제거, KCD 코드만 사용
- Disease (KCD) ↔ Biomarker (코드 기반 매핑)
- Disease (KCD) + Procedure (KDRG)
- 모든 관계는 코드 기반
"""

import json
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR_KCD = PROJECT_ROOT / "data" / "kssc" / "kcd-9th" / "normalized"
DATA_DIR_KDRG = PROJECT_ROOT / "data" / "hira_master" / "kdrg_parsed" / "codes"
BRIDGES_DIR = PROJECT_ROOT / "bridges"

# 입력 파일
INPUT_KCD = DATA_DIR_KCD / "kcd9_full.json"
INPUT_KDRG = DATA_DIR_KDRG / "kdrg_procedures_full.json"
INPUT_BIOMARKERS = BRIDGES_DIR / "biomarkers_with_kcd.json"
INPUT_TESTS = PROJECT_ROOT / "data" / "hins" / "parsed" / "biomarker_tests_structured.json"
INPUT_DRUGS = BRIDGES_DIR / "anticancer_master_classified.json"
INPUT_MAPPINGS = BRIDGES_DIR / "biomarker_test_mappings_v2_code_based.json"

# .env 로드
load_dotenv(PROJECT_ROOT / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class CodeBasedIntegrator:
    """코드 기반 통합 클래스"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {}

    def close(self):
        self.driver.close()

    def clear_database(self):
        """데이터베이스 초기화"""
        print("[WARN] 기존 데이터 삭제 중...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("[OK] 데이터베이스 초기화 완료")

    def create_constraints(self):
        """제약조건 생성"""
        print("\n[INFO] 제약조건 생성 중...")

        constraints = [
            # Disease
            "CREATE CONSTRAINT disease_kcd IF NOT EXISTS FOR (d:Disease) REQUIRE d.kcd_code IS UNIQUE",
            # Procedure
            "CREATE CONSTRAINT procedure_kr IF NOT EXISTS FOR (p:Procedure) REQUIRE p.kdrg_code_kr IS UNIQUE",
            # Biomarker
            "CREATE CONSTRAINT biomarker_id IF NOT EXISTS FOR (b:Biomarker) REQUIRE b.biomarker_id IS UNIQUE",
            # Test
            "CREATE CONSTRAINT test_id IF NOT EXISTS FOR (t:Test) REQUIRE t.test_id IS UNIQUE",
            # Drug
            "CREATE CONSTRAINT drug_atc IF NOT EXISTS FOR (d:Drug) REQUIRE d.atc_code IS UNIQUE",
        ]

        with self.driver.session() as session:
            for c in constraints:
                try:
                    session.run(c)
                except Exception as e:
                    print(f"[SKIP] {e}")

        print("[OK] 제약조건 생성 완료")

    def import_diseases(self, kcd_data):
        """Disease 노드 생성 (KCD)"""
        print("\n[INFO] Disease 노드 생성 중...")

        codes = kcd_data['codes']
        batch_size = 1000

        cypher = """
        UNWIND $diseases AS disease
        MERGE (d:Disease {kcd_code: disease.code})
        ON CREATE SET
            d.name_kr = disease.name_kr,
            d.name_en = disease.name_en,
            d.is_cancer = disease.is_cancer,
            d.is_lowest = disease.is_lowest,
            d.classification = disease.classification,
            d.created_at = datetime()
        ON MATCH SET
            d.name_kr = COALESCE(d.name_kr, disease.name_kr),
            d.name_en = COALESCE(d.name_en, disease.name_en)
        """

        # 암 코드 태깅
        for code in codes:
            code['is_cancer'] = self.is_cancer_code(code['code'])

        with self.driver.session() as session:
            for i in range(0, len(codes), batch_size):
                batch = codes[i:i+batch_size]
                session.run(cypher, diseases=batch)

        self.stats['diseases'] = len(codes)
        cancer_count = sum(1 for c in codes if c['is_cancer'])
        print(f"[OK] {self.stats['diseases']}개 Disease 노드 생성 (암: {cancer_count}개)")

    def import_procedures(self, kdrg_data):
        """Procedure 노드 생성 (KDRG)"""
        print("\n[INFO] Procedure 노드 생성 중...")

        procedures = kdrg_data['codes']

        cypher = """
        UNWIND $procedures AS proc
        CREATE (p:Procedure {
            kdrg_code_kr: proc.korean_code,
            kdrg_code_en: proc.english_code,
            name: proc.name,
            created_at: datetime()
        })
        """

        with self.driver.session() as session:
            session.run(cypher, procedures=procedures)

        self.stats['procedures'] = len(procedures)
        print(f"[OK] {self.stats['procedures']}개 Procedure 노드 생성")

    def import_biomarkers(self, biomarker_data):
        """Biomarker 노드 생성"""
        print("\n[INFO] Biomarker 노드 생성 중...")

        biomarkers = biomarker_data['biomarkers']

        cypher = """
        UNWIND $biomarkers AS bm
        CREATE (b:Biomarker {
            biomarker_id: bm.biomarker_id,
            name_en: bm.biomarker_name_en,
            name_ko: bm.biomarker_name_ko,
            type: bm.biomarker_type,
            protein_gene: bm.protein_gene,
            kcd_codes: bm.kcd_codes,
            drug_count: bm.drug_count,
            created_at: datetime()
        })
        """

        with self.driver.session() as session:
            session.run(cypher, biomarkers=biomarkers)

        self.stats['biomarkers'] = len(biomarkers)
        print(f"[OK] {self.stats['biomarkers']}개 Biomarker 노드 생성")

    def import_tests(self, test_data):
        """Test 노드 생성"""
        print("\n[INFO] Test 노드 생성 중...")

        tests = test_data['tests']

        cypher = """
        UNWIND $tests AS test
        CREATE (t:Test {
            test_id: test.test_id,
            edi_code: test.edi_code,
            name_ko: test.test_name_ko,
            name_en: test.test_name_en,
            loinc_code: test.loinc_code,
            snomed_ct_id: test.snomed_ct_id,
            created_at: datetime()
        })
        """

        with self.driver.session() as session:
            session.run(cypher, tests=tests)

        self.stats['tests'] = len(tests)
        print(f"[OK] {self.stats['tests']}개 Test 노드 생성")

    def import_drugs(self, drug_data):
        """Drug 노드 생성"""
        print("\n[INFO] Drug 노드 생성 중...")

        # 중복 제거
        seen = set()
        drugs = []
        for d in drug_data:
            if d['atc_code'] not in seen:
                seen.add(d['atc_code'])
                drugs.append(d)

        cypher = """
        UNWIND $drugs AS drug
        CREATE (d:Drug {
            atc_code: drug.atc_code,
            ingredient_ko: drug.ingredient_ko,
            ingredient_en: drug.ingredient_base_en,
            mechanism_of_action: drug.mechanism_of_action,
            created_at: datetime()
        })
        """

        with self.driver.session() as session:
            session.run(cypher, drugs=drugs)

        self.stats['drugs'] = len(drugs)
        print(f"[OK] {self.stats['drugs']}개 Drug 노드 생성")

    def create_disease_biomarker_relationships(self, biomarker_data):
        """Disease ↔ Biomarker 관계 (코드 기반)"""
        print("\n[INFO] Disease-Biomarker 관계 생성 중 (코드 기반)...")

        biomarkers = biomarker_data['biomarkers']

        relationships = []
        for bio in biomarkers:
            kcd_codes = bio.get('kcd_codes', [])
            for kcd in kcd_codes:
                relationships.append({
                    'biomarker_id': bio['biomarker_id'],
                    'kcd_code': kcd
                })

        cypher = """
        UNWIND $rels AS rel
        MATCH (d:Disease)
        WHERE d.kcd_code = rel.kcd_code OR d.kcd_code STARTS WITH rel.kcd_code + '.'
        MATCH (b:Biomarker {biomarker_id: rel.biomarker_id})
        CREATE (d)-[:HAS_BIOMARKER {
            mapping_method: 'official_kcd_code',
            created_at: datetime()
        }]->(b)
        """

        with self.driver.session() as session:
            session.run(cypher, rels=relationships)
            count_query = "MATCH ()-[r:HAS_BIOMARKER]->() RETURN count(r) as count"
            result = session.run(count_query)
            self.stats['has_biomarker_rels'] = result.single()['count']

        print(f"[OK] {self.stats['has_biomarker_rels']}개 HAS_BIOMARKER 관계 생성")

    def create_biomarker_test_relationships(self, mapping_data):
        """Biomarker → Test 관계"""
        print("\n[INFO] Biomarker-Test 관계 생성 중...")

        mappings = mapping_data['mappings']

        relationships = []
        for m in mappings:
            for test in m['tests']:
                relationships.append({
                    'biomarker_id': m['biomarker_id'],
                    'test_id': test['test_id'],
                    'match_type': test['match_type'],
                    'matched_code': test.get('matched_code', '')
                })

        cypher = """
        UNWIND $rels AS rel
        MATCH (b:Biomarker {biomarker_id: rel.biomarker_id})
        MATCH (t:Test {test_id: rel.test_id})
        CREATE (b)-[:TESTED_BY {
            match_type: rel.match_type,
            matched_code: rel.matched_code,
            created_at: datetime()
        }]->(t)
        """

        with self.driver.session() as session:
            session.run(cypher, rels=relationships)

        self.stats['tested_by_rels'] = len(relationships)
        print(f"[OK] {self.stats['tested_by_rels']}개 TESTED_BY 관계 생성")

    def create_drug_biomarker_relationships(self, biomarker_data):
        """Drug → Biomarker 관계"""
        print("\n[INFO] Drug-Biomarker 관계 생성 중...")

        biomarkers = biomarker_data['biomarkers']

        relationships = []
        for bio in biomarkers:
            for drug in bio.get('related_drugs', []):
                relationships.append({
                    'atc_code': drug['atc_code'],
                    'biomarker_id': bio['biomarker_id']
                })

        cypher = """
        UNWIND $rels AS rel
        MATCH (drug:Drug {atc_code: rel.atc_code})
        MATCH (b:Biomarker {biomarker_id: rel.biomarker_id})
        CREATE (drug)-[:TARGETS {
            created_at: datetime()
        }]->(b)
        """

        with self.driver.session() as session:
            session.run(cypher, rels=relationships)

        self.stats['targets_rels'] = len(relationships)
        print(f"[OK] {self.stats['targets_rels']}개 TARGETS 관계 생성")

    def is_cancer_code(self, code):
        """암 코드 여부"""
        if not code or '-' in code:
            return False
        if code.startswith('C'):
            return True
        if code.startswith('D'):
            try:
                num = int(code[1:3])
                return 0 <= num <= 48
            except:
                return False
        return False

    def verify_import(self):
        """검증"""
        print("\n[INFO] 데이터 검증 중...")

        queries = {
            'diseases': "MATCH (d:Disease) RETURN count(d) as count",
            'procedures': "MATCH (p:Procedure) RETURN count(p) as count",
            'biomarkers': "MATCH (b:Biomarker) RETURN count(b) as count",
            'tests': "MATCH (t:Test) RETURN count(t) as count",
            'drugs': "MATCH (d:Drug) RETURN count(d) as count",
            'has_biomarker': "MATCH ()-[r:HAS_BIOMARKER]->() RETURN count(r) as count",
            'tested_by': "MATCH ()-[r:TESTED_BY]->() RETURN count(r) as count",
            'targets': "MATCH ()-[r:TARGETS]->() RETURN count(r) as count",
        }

        with self.driver.session() as session:
            print("\n[VERIFY] Neo4j 데이터:")
            for name, query in queries.items():
                result = session.run(query)
                count = result.single()['count']
                print(f"  - {name}: {count}개")

    def run(self, clear_db=False):
        """전체 실행"""
        print("=" * 70)
        print("통합 의료 지식그래프 구축 (완전 코드 기반)")
        print("=" * 70)

        try:
            # 데이터 로드
            print("\n[INFO] 데이터 로딩...")
            with open(INPUT_KCD, 'r', encoding='utf-8') as f:
                kcd_data = json.load(f)
            with open(INPUT_KDRG, 'r', encoding='utf-8') as f:
                kdrg_data = json.load(f)
            with open(INPUT_BIOMARKERS, 'r', encoding='utf-8') as f:
                biomarker_data = json.load(f)
            with open(INPUT_TESTS, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            with open(INPUT_DRUGS, 'r', encoding='utf-8') as f:
                drug_data = json.load(f)
            with open(INPUT_MAPPINGS, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)

            print("[OK] 모든 데이터 로드 완료")

            # 초기화
            if clear_db:
                self.clear_database()

            # 제약조건
            self.create_constraints()

            # 노드 생성
            self.import_diseases(kcd_data)
            self.import_procedures(kdrg_data)
            self.import_biomarkers(biomarker_data)
            self.import_tests(test_data)
            self.import_drugs(drug_data)

            # 관계 생성
            self.create_disease_biomarker_relationships(biomarker_data)
            self.create_biomarker_test_relationships(mapping_data)
            self.create_drug_biomarker_relationships(biomarker_data)

            # 검증
            self.verify_import()

            print("\n[SUCCESS] 통합 완료!")
            print("\n다음 쿼리로 확인:")
            print("""
// HER2 양성 유방암 약물 조회 (완전 코드 기반)
MATCH (d:Disease)-[:HAS_BIOMARKER]->(b:Biomarker {name_en: 'HER2'})<-[:TARGETS]-(drug:Drug)
MATCH (b)-[:TESTED_BY]->(t:Test)
WHERE d.kcd_code STARTS WITH 'C50'
RETURN d.name_kr, drug.ingredient_ko, t.name_ko, t.edi_code
LIMIT 10
            """)

            return True

        except Exception as e:
            print(f"\n[ERROR] 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='코드 기반 통합')
    parser.add_argument('--clear-db', action='store_true',
                        help='기존 데이터 삭제')
    args = parser.parse_args()

    integrator = CodeBasedIntegrator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        success = integrator.run(clear_db=args.clear_db)
        return 0 if success else 1
    finally:
        integrator.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
