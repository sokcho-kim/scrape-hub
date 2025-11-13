"""
법령 조문 Neo4j 통합 스크립트

파싱된 법령 조문과 참조 관계를 Neo4j 그래프 데이터베이스에 적재합니다.

노드:
- Law: 법령
- Article: 조문 (조/항/호/목)

관계:
- (Law)-[:HAS_ARTICLE]->(Article)
- (Article)-[:HAS_CHILD]->(Article)  # 조→항, 항→호 등
- (Article)-[:REFERS_TO {type}]->(Article)  # 조문 간 참조
- (Law)-[:DERIVED_FROM]->(Law)  # 법→시행령→시행규칙
"""

import json
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from collections import defaultdict


# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
PARSED_DIR = PROJECT_ROOT / "data" / "legal" / "parsed"
REFERENCES_DIR = PROJECT_ROOT / "data" / "legal" / "references"

# .env 파일 로드
load_dotenv(PROJECT_ROOT / ".env")

# Neo4j 연결 정보
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class LegalNeo4jIntegrator:
    """법령 Neo4j 통합 클래스"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = defaultdict(int)

        # 법령 계층 매핑 (법명 패턴 기반)
        self.law_hierarchy = {}

    def close(self):
        """연결 종료"""
        self.driver.close()

    def clear_legal_data(self):
        """기존 법령 데이터 삭제"""
        print("[INFO] 기존 법령 데이터 삭제 중...")
        with self.driver.session() as session:
            # Law와 Article 노드 및 관계 삭제
            session.run("""
                MATCH (a:Article)
                DETACH DELETE a
            """)
            session.run("""
                MATCH (l:Law)
                DETACH DELETE l
            """)
        print("[OK] 법령 데이터 삭제 완료")

    def create_constraints_and_indexes(self):
        """제약조건 및 인덱스 생성"""
        print("\n[INFO] 제약조건 및 인덱스 생성 중...")

        constraints = [
            "CREATE CONSTRAINT law_id IF NOT EXISTS FOR (l:Law) REQUIRE l.law_id IS UNIQUE",
            "CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.article_id IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX law_name IF NOT EXISTS FOR (l:Law) ON (l.law_name)",
            "CREATE INDEX law_type IF NOT EXISTS FOR (l:Law) ON (l.law_type)",
            "CREATE INDEX article_number IF NOT EXISTS FOR (a:Article) ON (a.article_number)",
            "CREATE INDEX article_depth IF NOT EXISTS FOR (a:Article) ON (a.depth)",
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"  [OK] {constraint.split()[1]}")
                except Exception as e:
                    print(f"  [SKIP] {constraint.split()[1]}: {e}")

            for index in indexes:
                try:
                    session.run(index)
                    print(f"  [OK] {index.split()[1]}")
                except Exception as e:
                    print(f"  [SKIP] {index.split()[1]}: {e}")

        print("[OK] 제약조건 및 인덱스 생성 완료")

    def import_laws_and_articles(self):
        """법령 및 조문 임포트"""
        print("\n[INFO] 법령 및 조문 임포트 중...")

        parsed_files = list(PARSED_DIR.glob("*_parsed.json"))
        print(f"  발견된 파싱 파일: {len(parsed_files)}개")

        for parsed_file in parsed_files:
            with open(parsed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            law_name = data['law_name']
            articles = data['articles']

            # 법령 유형 추출 (파일명에서)
            law_type = self._extract_law_type(law_name)

            # 법령 노드 생성
            law_id = articles[0]['law_id'] if articles else None
            if law_id:
                self._create_law_node(law_id, law_name, law_type)

            # 조문 노드 일괄 생성 (배치)
            self._create_articles_batch(articles)

            # 조문 계층 관계 생성
            self._create_article_hierarchy(articles)

            print(f"  [OK] {law_name}: {len(articles)}개 조문")

        print(f"[OK] 법령 {self.stats['laws']}개, 조문 {self.stats['articles']}개 임포트 완료")

    def _extract_law_type(self, law_name: str) -> str:
        """법령명에서 법령 유형 추출"""
        if '시행규칙' in law_name:
            return '시행규칙'
        elif '시행령' in law_name:
            return '시행령'
        elif '규칙' in law_name:
            return '규칙'
        elif '령' in law_name:
            return '령'
        else:
            return '법률'

    def _create_law_node(self, law_id: str, law_name: str, law_type: str):
        """법령 노드 생성"""
        with self.driver.session() as session:
            cypher = """
            MERGE (l:Law {law_id: $law_id})
            ON CREATE SET
                l.law_name = $law_name,
                l.law_type = $law_type,
                l.created_at = datetime()
            """
            session.run(cypher, law_id=law_id, law_name=law_name, law_type=law_type)
            self.stats['laws'] += 1

    def _create_articles_batch(self, articles: list):
        """조문 노드 일괄 생성"""
        with self.driver.session() as session:
            cypher = """
            UNWIND $articles AS article
            MERGE (a:Article {article_id: article.article_id})
            ON CREATE SET
                a.law_id = article.law_id,
                a.law_name = article.law_name,
                a.article_number = article.article_number,
                a.article_number_normalized = article.article_number_normalized,
                a.article_title = article.article_title,
                a.depth = article.depth,
                a.clause_number = article.clause_number,
                a.subclause_number = article.subclause_number,
                a.item_number = article.item_number,
                a.full_text = article.full_text,
                a.created_at = datetime()
            WITH a
            MATCH (l:Law {law_id: a.law_id})
            MERGE (l)-[:HAS_ARTICLE]->(a)
            """

            session.run(cypher, articles=articles)
            self.stats['articles'] += len(articles)

    def _create_article_hierarchy(self, articles: list):
        """조문 계층 관계 생성"""
        relationships = []

        for article in articles:
            if article['parent_article_id']:
                relationships.append({
                    'parent_id': article['parent_article_id'],
                    'child_id': article['article_id'],
                    'depth': article['depth']
                })

        if relationships:
            with self.driver.session() as session:
                cypher = """
                UNWIND $rels AS rel
                MATCH (parent:Article {article_id: rel.parent_id})
                MATCH (child:Article {article_id: rel.child_id})
                CREATE (parent)-[:HAS_CHILD {
                    depth_level: rel.depth,
                    created_at: datetime()
                }]->(child)
                """
                session.run(cypher, rels=relationships)
                self.stats['hierarchy_rels'] += len(relationships)

    def import_references(self):
        """조문 참조 관계 임포트"""
        print("\n[INFO] 조문 참조 관계 임포트 중...")

        reference_files = list(REFERENCES_DIR.glob("*_references.json"))
        print(f"  발견된 참조 파일: {len(reference_files)}개")

        for ref_file in reference_files:
            with open(ref_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            references = data['references']

            # 같은 법 내 참조만 (타법 참조는 추후 확장)
            same_law_refs = [
                ref for ref in references
                if not ref['is_cross_law'] and ref.get('target_article_id')
            ]

            if same_law_refs:
                self._create_references_batch(same_law_refs)

            print(f"  [OK] {data['law_name']}: {len(same_law_refs)}개 참조")

        print(f"[OK] 총 {self.stats['references']}개 참조 관계 임포트 완료")

    def _create_references_batch(self, references: list):
        """참조 관계 일괄 생성"""
        with self.driver.session() as session:
            cypher = """
            UNWIND $refs AS ref
            MATCH (source:Article {article_id: ref.source_article_id})
            MATCH (target:Article {article_id: ref.target_article_id})
            CREATE (source)-[:REFERS_TO {
                reference_type: ref.reference_type,
                reference_text: ref.reference_text,
                context: ref.context,
                created_at: datetime()
            }]->(target)
            """
            session.run(cypher, refs=references)
            self.stats['references'] += len(references)

    def create_law_hierarchy(self):
        """법령 계층 관계 생성 (법→시행령→시행규칙)"""
        print("\n[INFO] 법령 계층 관계 생성 중...")

        # 법령명 패턴으로 계층 매칭
        with self.driver.session() as session:
            # 모든 법령 가져오기
            result = session.run("""
                MATCH (l:Law)
                RETURN l.law_id AS law_id, l.law_name AS law_name, l.law_type AS law_type
            """)

            laws = {row['law_id']: row for row in result}

        # 계층 매핑 (간단한 패턴 매칭)
        hierarchy_rels = []

        for law_id, law in laws.items():
            law_name = law['law_name']
            law_type = law['law_type']

            if law_type == '시행령':
                # "의료급여법 시행령" → "의료급여법" 매칭
                base_name = law_name.replace(' 시행령', '').replace('시행령', '')
                parent = self._find_law_by_name(laws, base_name, '법률')
                if parent:
                    hierarchy_rels.append({
                        'parent_id': parent['law_id'],
                        'child_id': law_id,
                        'relationship_type': '시행령'
                    })

            elif law_type == '시행규칙':
                # "의료급여법 시행규칙" → "의료급여법" 매칭
                base_name = law_name.replace(' 시행규칙', '').replace('시행규칙', '')
                parent = self._find_law_by_name(laws, base_name, '법률')
                if parent:
                    hierarchy_rels.append({
                        'parent_id': parent['law_id'],
                        'child_id': law_id,
                        'relationship_type': '시행규칙'
                    })

        # 관계 생성
        if hierarchy_rels:
            with self.driver.session() as session:
                cypher = """
                UNWIND $rels AS rel
                MATCH (parent:Law {law_id: rel.parent_id})
                MATCH (child:Law {law_id: rel.child_id})
                CREATE (child)-[:DERIVED_FROM {
                    relationship_type: rel.relationship_type,
                    created_at: datetime()
                }]->(parent)
                """
                session.run(cypher, rels=hierarchy_rels)
                self.stats['law_hierarchy_rels'] += len(hierarchy_rels)

        print(f"[OK] {self.stats['law_hierarchy_rels']}개 법령 계층 관계 생성")

    def _find_law_by_name(self, laws: dict, name: str, law_type: str) -> dict:
        """법령명으로 법령 찾기"""
        for law_id, law in laws.items():
            if name in law['law_name'] and law['law_type'] == law_type:
                return law
        return None

    def verify_import(self):
        """데이터 임포트 검증"""
        print("\n[INFO] 데이터 검증 중...")

        queries = {
            'laws': "MATCH (l:Law) RETURN count(l) as count",
            'articles': "MATCH (a:Article) RETURN count(a) as count",
            'article_hierarchy': "MATCH ()-[r:HAS_CHILD]->() RETURN count(r) as count",
            'references': "MATCH ()-[r:REFERS_TO]->() RETURN count(r) as count",
            'law_hierarchy': "MATCH ()-[r:DERIVED_FROM]->() RETURN count(r) as count"
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

        print("\n1. 특정 법령의 모든 조문 조회:")
        print("""
MATCH (l:Law {law_name: '의료급여법'})-[:HAS_ARTICLE]->(a:Article)
WHERE a.depth = 0  // 조 레벨만
RETURN a.article_number, a.article_title, a.full_text
ORDER BY a.article_number_normalized
LIMIT 10
        """)

        print("\n2. 조문의 하위 구조 조회 (제3조의 모든 항/호/목):")
        print("""
MATCH path = (a:Article {article_number: '제3조'})-[:HAS_CHILD*]->(child)
RETURN path
        """)

        print("\n3. 조문 참조 관계 조회 (제11조를 참조하는 모든 조문):")
        print("""
MATCH (source:Article)-[r:REFERS_TO]->(target:Article {article_number: '제11조'})
RETURN source.article_number, source.article_title,
       r.reference_type, r.reference_text
        """)

        print("\n4. 법령 계층 구조 조회 (시행령→법률):")
        print("""
MATCH (child:Law)-[r:DERIVED_FROM]->(parent:Law)
RETURN child.law_name, r.relationship_type, parent.law_name
        """)

        print("\n5. 준용 관계 조회:")
        print("""
MATCH (source:Article)-[r:REFERS_TO {reference_type: '준용'}]->(target:Article)
RETURN source.article_number, source.article_title,
       target.article_number, target.article_title,
       r.reference_text
        """)

        print("\n" + "=" * 70)

    def run(self, clear_db=False):
        """전체 통합 프로세스 실행"""
        print("=" * 70)
        print("법령 조문 Neo4j 통합")
        print("=" * 70)

        try:
            # 데이터베이스 초기화 (옵션)
            if clear_db:
                self.clear_legal_data()

            # 제약조건 및 인덱스
            self.create_constraints_and_indexes()

            # 법령 및 조문 임포트
            self.import_laws_and_articles()

            # 참조 관계 임포트
            self.import_references()

            # 법령 계층 관계
            self.create_law_hierarchy()

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

    parser = argparse.ArgumentParser(description='법령 조문 Neo4j 통합')
    parser.add_argument('--clear-db', action='store_true',
                        help='기존 법령 데이터를 삭제하고 새로 시작')
    args = parser.parse_args()

    print(f"Neo4j 연결 정보:")
    print(f"  URI: {NEO4J_URI}")
    print(f"  User: {NEO4J_USER}")
    print()

    integrator = LegalNeo4jIntegrator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        success = integrator.run(clear_db=args.clear_db)
        return 0 if success else 1

    finally:
        integrator.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
