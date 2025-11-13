"""
Python에서 Neo4j 직접 쿼리하는 예시

Neo4j Browser 없이 Python 스크립트만으로 법령 데이터 조회
"""

import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 환경변수 로드
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class LegalQueryService:
    """법령 조회 서비스"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def find_article_by_keyword(self, keyword: str, limit: int = 5):
        """키워드로 조문 검색"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Article)
                WHERE a.full_text CONTAINS $keyword
                RETURN a.law_name AS law_name,
                       a.article_number AS article_number,
                       a.article_title AS article_title,
                       substring(a.full_text, 0, 150) + '...' AS preview
                LIMIT $limit
            """, keyword=keyword, limit=limit)

            return [dict(record) for record in result]

    def get_article_references(self, law_name: str, article_number: str):
        """특정 조문을 참조하는 조문들 조회"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (source:Article)-[r:REFERS_TO]->(target:Article {
                    law_name: $law_name,
                    article_number: $article_number
                })
                RETURN source.article_number AS source_article,
                       source.article_title AS source_title,
                       r.reference_type AS ref_type,
                       r.reference_text AS ref_text
            """, law_name=law_name, article_number=article_number)

            return [dict(record) for record in result]

    def get_law_hierarchy(self):
        """법령 계층 구조 조회"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (child:Law)-[r:DERIVED_FROM]->(parent:Law)
                RETURN parent.law_name AS parent_law,
                       child.law_name AS child_law,
                       r.relationship_type AS relation_type
                ORDER BY parent_law
            """)

            return [dict(record) for record in result]

    def get_article_hierarchy(self, law_name: str, article_number: str):
        """조문의 하위 구조 조회 (항/호/목)"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (parent:Article {
                    law_name: $law_name,
                    article_number: $article_number,
                    depth: 0
                })-[:HAS_CHILD*]->(child:Article)
                RETURN child.article_number AS article_number,
                       child.depth AS depth,
                       child.clause_number AS clause,
                       child.subclause_number AS subclause,
                       child.item_number AS item,
                       substring(child.full_text, 0, 100) + '...' AS text
                ORDER BY child.depth, clause, subclause, item
            """, law_name=law_name, article_number=article_number)

            return [dict(record) for record in result]


def main():
    """메인 실행"""
    service = LegalQueryService()

    try:
        print("=" * 70)
        print("Python에서 Neo4j 직접 쿼리 예시")
        print("=" * 70)

        # 1. 키워드 검색
        print("\n[1] 키워드 검색: '급여비용 청구'")
        print("-" * 70)
        results = service.find_article_by_keyword("급여비용", limit=3)
        for i, article in enumerate(results, 1):
            print(f"\n{i}. {article['law_name']} {article['article_number']}")
            print(f"   제목: {article['article_title']}")
            print(f"   내용: {article['preview']}")

        # 2. 참조 관계 조회
        print("\n" + "=" * 70)
        print("[2] 제11조를 참조하는 조문들")
        print("-" * 70)
        refs = service.get_article_references("의료급여법", "제11조")
        for i, ref in enumerate(refs[:5], 1):
            print(f"\n{i}. {ref['source_article']} ({ref['source_title']})")
            print(f"   참조유형: {ref['ref_type']}")
            print(f"   참조표현: {ref['ref_text']}")

        # 3. 법령 계층
        print("\n" + "=" * 70)
        print("[3] 법령 계층 구조")
        print("-" * 70)
        hierarchy = service.get_law_hierarchy()
        for h in hierarchy[:10]:
            print(f"{h['child_law']} ({h['relation_type']}) → {h['parent_law']}")

        # 4. 조문 계층
        print("\n" + "=" * 70)
        print("[4] 의료급여법 제3조의 하위 구조")
        print("-" * 70)
        structure = service.get_article_hierarchy("의료급여법", "제3조")
        for item in structure[:10]:
            indent = "  " * item['depth']
            if item['depth'] == 1:
                label = f"제{item['clause']}항"
            elif item['depth'] == 2:
                label = f"제{item['subclause']}호"
            elif item['depth'] == 3:
                label = f"{item['item']}목"
            else:
                label = ""

            print(f"{indent}{label}")
            print(f"{indent}└─ {item['text']}")

        print("\n" + "=" * 70)
        print("[OK] Neo4j Browser 없이 Python만으로 모든 쿼리 가능!")
        print("=" * 70)

    finally:
        service.close()


if __name__ == "__main__":
    main()
