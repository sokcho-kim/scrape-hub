"""
HIRA Regimen 노드 및 관계 통합

Regimen 노드 생성 및 Disease-Regimen-Drug 관계 구축
"""

import json
from pathlib import Path
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_REGIMENS = PROJECT_ROOT / "bridges" / "hira_regimens_normalized.json"

# .env 로드
load_dotenv(PROJECT_ROOT / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class RegimenImporter:
    """Regimen 통합 클래스"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {}

    def close(self):
        self.driver.close()

    def create_constraints(self):
        """제약조건 생성"""
        print("\n[INFO] Regimen 제약조건 생성 중...")

        constraints = [
            "CREATE CONSTRAINT regimen_id IF NOT EXISTS FOR (r:Regimen) REQUIRE r.regimen_id IS UNIQUE",
        ]

        with self.driver.session() as session:
            for c in constraints:
                try:
                    session.run(c)
                except Exception as e:
                    print(f"[SKIP] {e}")

        print("[OK] 제약조건 생성 완료")

    def import_regimens(self, regimen_data):
        """Regimen 노드 생성"""
        print("\n[INFO] Regimen 노드 생성 중...")

        regimens = regimen_data['regimens']

        # 노드 데이터 준비
        regimen_nodes = []
        for r in regimens:
            regimen_nodes.append({
                'regimen_id': r['regimen_id'],
                'cancer_name': r['cancer_name'],
                'regimen_type': r.get('regimen_type'),
                'line': r.get('line'),
                'purpose': r.get('purpose'),
                'action': r.get('action'),
                'announcement_no': r.get('announcement_no'),
                'announcement_date': r.get('announcement_date'),
                'source_text': r.get('source_text'),
                'drug_count': len(r['drugs']),
                'kcd_codes': r['kcd_codes'],
                'has_kcd': r['has_kcd'],
                'has_all_drugs': r['has_all_drugs']
            })

        cypher = """
        UNWIND $regimens AS reg
        MERGE (r:Regimen {regimen_id: reg.regimen_id})
        ON CREATE SET
            r.cancer_name = reg.cancer_name,
            r.regimen_type = reg.regimen_type,
            r.line = reg.line,
            r.purpose = reg.purpose,
            r.action = reg.action,
            r.announcement_no = reg.announcement_no,
            r.announcement_date = reg.announcement_date,
            r.source_text = reg.source_text,
            r.drug_count = reg.drug_count,
            r.kcd_codes = reg.kcd_codes,
            r.has_kcd = reg.has_kcd,
            r.has_all_drugs = reg.has_all_drugs,
            r.created_at = datetime()
        ON MATCH SET
            r.cancer_name = COALESCE(r.cancer_name, reg.cancer_name),
            r.announcement_date = COALESCE(r.announcement_date, reg.announcement_date)
        """

        with self.driver.session() as session:
            session.run(cypher, regimens=regimen_nodes)

        self.stats['regimens'] = len(regimen_nodes)
        print(f"[OK] {self.stats['regimens']}개 Regimen 노드 생성")

    def create_disease_regimen_relationships(self, regimen_data):
        """Disease → TREATED_BY → Regimen 관계"""
        print("\n[INFO] Disease-Regimen 관계 생성 중...")

        regimens = regimen_data['regimens']

        relationships = []
        for r in regimens:
            if not r['has_kcd']:
                continue

            kcd_codes = r['kcd_codes']
            for kcd in kcd_codes:
                relationships.append({
                    'regimen_id': r['regimen_id'],
                    'kcd_code': kcd,
                    'line': r.get('line'),
                    'purpose': r.get('purpose'),
                    'announcement_no': r.get('announcement_no'),
                    'announcement_date': r.get('announcement_date')
                })

        cypher = """
        UNWIND $rels AS rel
        MATCH (d:Disease)
        WHERE d.kcd_code = rel.kcd_code OR d.kcd_code STARTS WITH rel.kcd_code + '.'
        MATCH (r:Regimen {regimen_id: rel.regimen_id})
        MERGE (d)-[t:TREATED_BY]->(r)
        ON CREATE SET
            t.line = rel.line,
            t.purpose = rel.purpose,
            t.announcement_no = rel.announcement_no,
            t.announcement_date = rel.announcement_date,
            t.mapping_method = 'kcd_code',
            t.created_at = datetime()
        """

        with self.driver.session() as session:
            session.run(cypher, rels=relationships)
            count_query = "MATCH ()-[r:TREATED_BY]->() RETURN count(r) as count"
            result = session.run(count_query)
            self.stats['treated_by_rels'] = result.single()['count']

        print(f"[OK] {self.stats['treated_by_rels']}개 TREATED_BY 관계 생성")

    def create_regimen_drug_relationships(self, regimen_data):
        """Regimen → INCLUDES → Drug 관계"""
        print("\n[INFO] Regimen-Drug 관계 생성 중...")

        regimens = regimen_data['regimens']

        relationships = []
        for r in regimens:
            for idx, drug in enumerate(r['drugs']):
                relationships.append({
                    'regimen_id': r['regimen_id'],
                    'atc_code': drug['atc_code'],
                    'drug_name': drug['name'],
                    'normalized_name': drug['normalized_name'],
                    'order': idx + 1
                })

        cypher = """
        UNWIND $rels AS rel
        MATCH (r:Regimen {regimen_id: rel.regimen_id})
        MATCH (d:Drug {atc_code: rel.atc_code})
        MERGE (r)-[i:INCLUDES]->(d)
        ON CREATE SET
            i.drug_name = rel.drug_name,
            i.normalized_name = rel.normalized_name,
            i.order = rel.order,
            i.created_at = datetime()
        """

        with self.driver.session() as session:
            session.run(cypher, rels=relationships)

        self.stats['includes_rels'] = len(relationships)
        print(f"[OK] {self.stats['includes_rels']}개 INCLUDES 관계 생성")

    def verify_import(self):
        """검증"""
        print("\n[INFO] 데이터 검증 중...")

        queries = {
            'regimens': "MATCH (r:Regimen) RETURN count(r) as count",
            'treated_by': "MATCH ()-[r:TREATED_BY]->() RETURN count(r) as count",
            'includes': "MATCH ()-[r:INCLUDES]->() RETURN count(r) as count",
        }

        with self.driver.session() as session:
            print("\n[VERIFY] Neo4j 데이터:")
            for name, query in queries.items():
                result = session.run(query)
                count = result.single()['count']
                print(f"  - {name}: {count}개")

    def run(self):
        """전체 실행"""
        print("=" * 70)
        print("HIRA Regimen 노드 및 관계 통합")
        print("=" * 70)

        try:
            # 데이터 로드
            print("\n[INFO] 데이터 로딩...")
            with open(INPUT_REGIMENS, 'r', encoding='utf-8') as f:
                regimen_data = json.load(f)

            print(f"[OK] {regimen_data['metadata']['total_regimens']}개 Regimen 로드")

            # 제약조건
            self.create_constraints()

            # 노드 생성
            self.import_regimens(regimen_data)

            # 관계 생성
            self.create_disease_regimen_relationships(regimen_data)
            self.create_regimen_drug_relationships(regimen_data)

            # 검증
            self.verify_import()

            print("\n[SUCCESS] Regimen 통합 완료!")
            print("\n다음 쿼리로 확인:")
            print("""
// HER2 양성 유방암 1차 급여 요법
MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)-[:INCLUDES]->(drug:Drug)
MATCH (d)-[:HAS_BIOMARKER]->(b:Biomarker {name_en: 'HER2'})<-[:TARGETS]-(drug)
WHERE d.kcd_code STARTS WITH 'C50' AND tb.line = '1차'
RETURN d.name_kr, r.regimen_type, collect(drug.ingredient_ko) as drugs,
       r.announcement_no, r.announcement_date
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
    importer = RegimenImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        success = importer.run()
        return 0 if success else 1
    finally:
        importer.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
