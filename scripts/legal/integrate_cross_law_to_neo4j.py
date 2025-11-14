"""
타법 참조를 Neo4j에 적재하는 스크립트

단계:
1. 매칭 가능한 타법 참조 로드
2. 각 참조의 source와 target article_id 찾기
3. Neo4j에 CROSS_LAW_REFERS_TO 관계 생성
"""

import os
import json
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime

# 환경변수 로드
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

DATA_DIR = PROJECT_ROOT / "data" / "legal" / "cross_law_analysis"


class CrossLawReferenceIntegrator:
    """타법 참조 통합기"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        self.stats = {
            'total_refs': 0,
            'found_source': 0,
            'found_target': 0,
            'created_rels': 0,
            'failed': 0,
            'failures': []
        }

    def close(self):
        self.driver.close()

    def load_matchable_references(self):
        """매칭 가능한 타법 참조 로드"""
        ref_file = DATA_DIR / "matchable_references.json"
        with open(ref_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def find_target_article_id(self, target_law, article_number, clause=None):
        """타법 조문의 article_id 찾기"""
        with self.driver.session() as session:
            # article_number는 "제11조" 또는 "제11조의2" 형식
            # clause는 항 번호 (1, 2, 3, ...)

            # 먼저 조(depth=0) 찾기
            result = session.run("""
                MATCH (a:Article {
                    law_name: $law_name,
                    article_number: $article_number,
                    depth: 0
                })
                RETURN a.article_id AS article_id
                LIMIT 1
            """, law_name=target_law, article_number=article_number)

            record = result.single()
            if not record:
                return None

            base_article_id = record['article_id']

            # 항이 지정된 경우
            if clause:
                result = session.run("""
                    MATCH (parent:Article {article_id: $parent_id})
                          -[:HAS_CHILD]->(child:Article {
                              clause_number: $clause,
                              depth: 1
                          })
                    RETURN child.article_id AS article_id
                    LIMIT 1
                """, parent_id=base_article_id, clause=clause)

                child_record = result.single()
                if child_record:
                    return child_record['article_id']

            return base_article_id

    def create_cross_law_relationship(self, source_id, target_id, ref_type, ref_text):
        """CROSS_LAW_REFERS_TO 관계 생성"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (source:Article {article_id: $source_id})
                MATCH (target:Article {article_id: $target_id})
                MERGE (source)-[r:CROSS_LAW_REFERS_TO {
                    reference_type: $ref_type,
                    reference_text: $ref_text,
                    created_at: datetime()
                }]->(target)
                RETURN r
            """, source_id=source_id, target_id=target_id,
                 ref_type=ref_type, ref_text=ref_text)

            return result.single() is not None

    def integrate_references(self, references):
        """타법 참조 통합"""
        self.stats['total_refs'] = len(references)

        print(f"\n타법 참조 통합 시작: {len(references)}개")
        print("=" * 80)

        for i, ref in enumerate(references, 1):
            if i % 100 == 0:
                print(f"진행: {i}/{len(references)} ({i/len(references)*100:.1f}%)")

            try:
                # source article_id는 이미 있음
                source_id = ref['source_article_id']
                self.stats['found_source'] += 1

                # target article_id 찾기
                target_law = ref['target_law']
                target_article_number = ref['target_article_number']
                target_clause = ref.get('target_clause')

                target_id = self.find_target_article_id(
                    target_law,
                    target_article_number,
                    target_clause
                )

                if not target_id:
                    self.stats['failed'] += 1
                    self.stats['failures'].append({
                        'reason': 'target_not_found',
                        'source': f"{ref['source_law']} {ref['source_article_number']}",
                        'target': f"{target_law} {target_article_number}",
                        'target_clause': target_clause
                    })
                    continue

                self.stats['found_target'] += 1

                # 관계 생성
                success = self.create_cross_law_relationship(
                    source_id,
                    target_id,
                    ref['reference_type'],
                    ref['reference_text']
                )

                if success:
                    self.stats['created_rels'] += 1
                else:
                    self.stats['failed'] += 1
                    self.stats['failures'].append({
                        'reason': 'relationship_creation_failed',
                        'source_id': source_id,
                        'target_id': target_id
                    })

            except Exception as e:
                self.stats['failed'] += 1
                self.stats['failures'].append({
                    'reason': 'exception',
                    'error': str(e),
                    'ref': ref
                })

        print(f"\n진행: {len(references)}/{len(references)} (100%)")

    def print_stats(self):
        """통계 출력"""
        print("\n" + "=" * 80)
        print("타법 참조 통합 결과")
        print("=" * 80)

        print(f"\n총 참조: {self.stats['total_refs']:,}개")
        print(f"Source 찾음: {self.stats['found_source']:,}개")
        print(f"Target 찾음: {self.stats['found_target']:,}개")
        print(f"관계 생성 성공: {self.stats['created_rels']:,}개")
        print(f"실패: {self.stats['failed']:,}개")

        if self.stats['failures']:
            print(f"\n실패 이유별 분석:")
            from collections import Counter
            reasons = Counter(f['reason'] for f in self.stats['failures'])
            for reason, count in reasons.items():
                print(f"  - {reason}: {count}개")

            print(f"\n실패 샘플 (최대 10개):")
            for failure in self.stats['failures'][:10]:
                print(f"  {failure}")

    def verify_integration(self):
        """통합 검증"""
        print("\n" + "=" * 80)
        print("통합 검증")
        print("=" * 80)

        with self.driver.session() as session:
            # 1. CROSS_LAW_REFERS_TO 관계 개수
            result = session.run("""
                MATCH ()-[r:CROSS_LAW_REFERS_TO]->()
                RETURN count(r) AS count
            """)
            cross_law_count = result.single()['count']
            print(f"\nCROSS_LAW_REFERS_TO 관계: {cross_law_count:,}개")

            # 2. 타법 참조 예시
            result = session.run("""
                MATCH (s:Article)-[r:CROSS_LAW_REFERS_TO]->(t:Article)
                WHERE s.law_name <> t.law_name
                RETURN s.law_name AS source_law,
                       s.article_number AS source_article,
                       t.law_name AS target_law,
                       t.article_number AS target_article,
                       r.reference_type AS ref_type
                LIMIT 10
            """)

            print(f"\n타법 참조 샘플 (10개):")
            for i, record in enumerate(result, 1):
                print(f"  {i}. {record['source_law']} {record['source_article']}")
                print(f"     → {record['target_law']} {record['target_article']}")
                print(f"     ({record['ref_type']})")

            # 3. 법령별 타법 참조 통계
            result = session.run("""
                MATCH (s:Article)-[r:CROSS_LAW_REFERS_TO]->(t:Article)
                WHERE s.law_name <> t.law_name
                RETURN s.law_name AS source_law, count(r) AS count
                ORDER BY count DESC
                LIMIT 10
            """)

            print(f"\n법령별 타법 참조 (Top 10):")
            for record in result:
                print(f"  {record['count']:4}개: {record['source_law']}")


def main():
    """메인 실행"""
    integrator = CrossLawReferenceIntegrator()

    try:
        print("=" * 80)
        print("타법 참조 Neo4j 통합")
        print("=" * 80)

        # 1. 매칭 가능한 참조 로드
        print("\n[1] 매칭 가능한 타법 참조 로드")
        references = integrator.load_matchable_references()
        print(f"로드 완료: {len(references):,}개")

        # 2. Neo4j에 통합
        print("\n[2] Neo4j에 타법 참조 통합")
        integrator.integrate_references(references)

        # 3. 통계 출력
        integrator.print_stats()

        # 4. 검증
        integrator.verify_integration()

        print("\n" + "=" * 80)
        print("통합 완료")
        print("=" * 80)

    finally:
        integrator.close()


if __name__ == "__main__":
    main()
