"""
Phase 6: Procedure 노드 생성

KDRG 수술/처치 코드를 Neo4j에 통합합니다.
- Procedure 노드: 1,487개
- 한글↔영문 코드 양방향 매핑
"""

import json
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv


# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "hira_master" / "kdrg_parsed" / "codes"
INPUT_KDRG = DATA_DIR / "kdrg_procedures_full.json"

# .env 파일 로드
load_dotenv(PROJECT_ROOT / ".env")

# Neo4j 연결 정보
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class ProcedureImporter:
    """Procedure 노드 임포터"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {
            'procedures': 0
        }

    def close(self):
        """연결 종료"""
        self.driver.close()

    def create_constraints_and_indexes(self):
        """제약조건 및 인덱스 생성"""
        print("\n[INFO] Procedure 제약조건 및 인덱스 생성 중...")

        constraints = [
            "CREATE CONSTRAINT procedure_kr IF NOT EXISTS FOR (p:Procedure) REQUIRE p.kdrg_code_kr IS UNIQUE",
            "CREATE CONSTRAINT procedure_en IF NOT EXISTS FOR (p:Procedure) REQUIRE p.kdrg_code_en IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX procedure_name IF NOT EXISTS FOR (p:Procedure) ON (p.name)",
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

    def import_procedures(self, kdrg_data):
        """Procedure 노드 생성"""
        print("\n[INFO] Procedure 노드 생성 중...")

        procedures = kdrg_data['codes']

        cypher = """
        UNWIND $procedures AS proc
        CREATE (p:Procedure {
            kdrg_code_kr: proc.korean_code,
            kdrg_code_en: proc.english_code,
            name: proc.name,
            table_index: proc.table_index,
            created_at: datetime()
        })
        """

        with self.driver.session() as session:
            session.run(cypher, procedures=procedures)

        self.stats['procedures'] = len(procedures)
        print(f"[OK] {self.stats['procedures']}개 Procedure 노드 생성 완료")

    def verify_import(self):
        """데이터 임포트 검증"""
        print("\n[INFO] Procedure 데이터 검증 중...")

        queries = {
            'total_procedures': "MATCH (p:Procedure) RETURN count(p) as count",
            'unique_korean_codes': "MATCH (p:Procedure) RETURN count(DISTINCT p.kdrg_code_kr) as count",
            'unique_english_codes': "MATCH (p:Procedure) RETURN count(DISTINCT p.kdrg_code_en) as count",
        }

        with self.driver.session() as session:
            print("\n[VERIFY] Neo4j Procedure 데이터:")
            for name, query in queries.items():
                result = session.run(query)
                count = result.single()['count']
                print(f"  - {name}: {count}개")

    def print_sample_queries(self):
        """샘플 쿼리 출력"""
        print("\n" + "=" * 70)
        print("Procedure 샘플 쿼리")
        print("=" * 70)

        print("\n1. 췌장 관련 수술 조회:")
        print("""
MATCH (p:Procedure)
WHERE p.name CONTAINS '췌장'
RETURN p.kdrg_code_kr, p.kdrg_code_en, p.name
LIMIT 10
        """)

        print("\n2. 한글 코드로 영문 코드 조회:")
        print("""
MATCH (p:Procedure {kdrg_code_kr: '자751'})
RETURN p.kdrg_code_en, p.name
        """)

        print("\n3. 영문 코드로 한글 코드 조회:")
        print("""
MATCH (p:Procedure {kdrg_code_en: 'Q7511'})
RETURN p.kdrg_code_kr, p.name
        """)

        print("\n4. 테이블 인덱스별 수술 통계:")
        print("""
MATCH (p:Procedure)
RETURN p.table_index, count(p) as count
ORDER BY p.table_index
LIMIT 10
        """)

        print("\n" + "=" * 70)

    def run(self):
        """전체 임포트 프로세스 실행"""
        print("=" * 70)
        print("Phase 6: Procedure 노드 생성")
        print("=" * 70)

        try:
            # 데이터 로드
            print("\n[INFO] KDRG 데이터 파일 로딩...")
            with open(INPUT_KDRG, 'r', encoding='utf-8') as f:
                kdrg_data = json.load(f)
            print(f"[OK] KDRG 데이터 로드 완료: {kdrg_data['total_codes']}개 코드")

            # 제약조건 및 인덱스
            self.create_constraints_and_indexes()

            # Procedure 노드 생성
            self.import_procedures(kdrg_data)

            # 검증
            self.verify_import()

            # 샘플 쿼리
            self.print_sample_queries()

            print("\n[SUCCESS] Procedure 노드 생성 완료!")
            return True

        except Exception as e:
            print(f"\n[ERROR] 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """메인 실행"""
    print(f"Neo4j 연결 정보:")
    print(f"  URI: {NEO4J_URI}")
    print(f"  User: {NEO4J_USER}")
    print()

    importer = ProcedureImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        success = importer.run()
        return 0 if success else 1

    finally:
        importer.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
