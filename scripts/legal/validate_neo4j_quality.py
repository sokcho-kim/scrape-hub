"""
Neo4j 법령 지식그래프 품질 검증 스크립트

검증 항목:
1. 기본 통계 (노드/관계 수)
2. 데이터 무결성 (고아 노드, 깨진 참조)
3. 계층 구조 검증
4. 샘플 쿼리 실행
5. 타법 참조 현황
"""

import os
import json
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

# 환경변수 로드
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class Neo4jQualityValidator:
    """Neo4j 품질 검증기"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {},
            'quality_issues': {},
            'sample_queries': {},
            'cross_law_references': {}
        }

    def close(self):
        self.driver.close()

    def run_validation(self):
        """전체 검증 실행"""
        print("=" * 80)
        print("Neo4j 법령 지식그래프 품질 검증")
        print("=" * 80)

        self.check_basic_statistics()
        self.check_data_integrity()
        self.check_hierarchy_structure()
        self.check_cross_law_references()
        self.run_sample_queries()

        return self.report

    def check_basic_statistics(self):
        """1. 기본 통계"""
        print("\n" + "=" * 80)
        print("[1] 기본 통계")
        print("=" * 80)

        with self.driver.session() as session:
            # 노드 수
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(*) AS count
                ORDER BY count DESC
            """)
            node_stats = {r['label']: r['count'] for r in result}

            # 관계 수
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(*) AS count
                ORDER BY count DESC
            """)
            rel_stats = {r['type']: r['count'] for r in result}

            # 총계
            total_nodes = sum(node_stats.values())
            total_rels = sum(rel_stats.values())

            print(f"\n노드 총계: {total_nodes:,}개")
            for label, count in node_stats.items():
                print(f"  - {label}: {count:,}개")

            print(f"\n관계 총계: {total_rels:,}개")
            for rel_type, count in rel_stats.items():
                print(f"  - {rel_type}: {count:,}개")

            self.report['statistics'] = {
                'total_nodes': total_nodes,
                'total_relationships': total_rels,
                'nodes_by_label': node_stats,
                'relationships_by_type': rel_stats
            }

    def check_data_integrity(self):
        """2. 데이터 무결성 검증"""
        print("\n" + "=" * 80)
        print("[2] 데이터 무결성")
        print("=" * 80)

        issues = {}

        with self.driver.session() as session:
            # 2.1 고아 Article 노드 (Law와 연결 안됨)
            result = session.run("""
                MATCH (a:Article)
                WHERE NOT (a)<-[:HAS_ARTICLE]-(:Law)
                RETURN count(a) AS count
            """)
            orphan_articles = result.single()['count']
            issues['orphan_articles'] = orphan_articles
            print(f"\n고아 Article 노드: {orphan_articles}개")
            if orphan_articles > 0:
                print("  [WARN]  Law와 연결되지 않은 Article이 있습니다!")

            # 2.2 고아 Law 노드 (Article이 없음)
            result = session.run("""
                MATCH (l:Law)
                WHERE NOT (l)-[:HAS_ARTICLE]->(:Article)
                RETURN count(l) AS count
            """)
            orphan_laws = result.single()['count']
            issues['orphan_laws'] = orphan_laws
            print(f"고아 Law 노드: {orphan_laws}개")
            if orphan_laws > 0:
                print("  [WARN]  Article이 없는 Law가 있습니다!")

            # 2.3 깨진 REFERS_TO 관계 (target이 존재하지 않음)
            result = session.run("""
                MATCH (a:Article)-[r:REFERS_TO]->(target)
                WHERE target.article_id IS NULL
                RETURN count(r) AS count
            """)
            broken_refs = result.single()['count']
            issues['broken_references'] = broken_refs
            print(f"깨진 참조 관계: {broken_refs}개")
            if broken_refs > 0:
                print("  [WARN]  존재하지 않는 조문을 참조합니다!")

            # 2.4 중복 article_id
            result = session.run("""
                MATCH (a:Article)
                WITH a.article_id AS id, count(*) AS cnt
                WHERE cnt > 1
                RETURN count(*) AS duplicates
            """)
            duplicates = result.single()['duplicates']
            issues['duplicate_article_ids'] = duplicates
            print(f"중복 article_id: {duplicates}개")
            if duplicates > 0:
                print("  [WARN]  같은 article_id를 가진 노드가 여러 개 있습니다!")

            # 2.5 필수 속성 누락
            result = session.run("""
                MATCH (a:Article)
                WHERE a.article_id IS NULL
                   OR a.law_name IS NULL
                   OR a.article_number IS NULL
                RETURN count(a) AS count
            """)
            missing_props = result.single()['count']
            issues['missing_required_properties'] = missing_props
            print(f"필수 속성 누락: {missing_props}개")
            if missing_props > 0:
                print("  [WARN]  article_id, law_name, article_number 중 하나가 없습니다!")

            if all(v == 0 for v in issues.values()):
                print("\n[OK] 데이터 무결성: 문제 없음")
            else:
                print(f"\n[WARN]  발견된 이슈: {sum(issues.values())}개")

            self.report['quality_issues']['integrity'] = issues

    def check_hierarchy_structure(self):
        """3. 계층 구조 검증"""
        print("\n" + "=" * 80)
        print("[3] 계층 구조")
        print("=" * 80)

        issues = {}

        with self.driver.session() as session:
            # 3.1 조문 계층 (depth별 분포)
            result = session.run("""
                MATCH (a:Article)
                RETURN a.depth AS depth, count(*) AS count
                ORDER BY depth
            """)
            depth_dist = {r['depth']: r['count'] for r in result}

            print("\n조문 계층 분포:")
            depth_names = {0: '조', 1: '항', 2: '호', 3: '목'}
            for depth, count in sorted(depth_dist.items()):
                name = depth_names.get(depth, f'depth={depth}')
                print(f"  - {name} (depth={depth}): {count:,}개")

            # 3.2 HAS_CHILD 관계 검증 (parent가 child보다 depth가 작아야 함)
            result = session.run("""
                MATCH (parent:Article)-[:HAS_CHILD]->(child:Article)
                WHERE parent.depth >= child.depth
                RETURN count(*) AS invalid_depth
            """)
            invalid_depth = result.single()['invalid_depth']
            issues['invalid_depth_hierarchy'] = invalid_depth
            print(f"\n잘못된 depth 계층: {invalid_depth}개")
            if invalid_depth > 0:
                print("  [WARN]  부모가 자식보다 depth가 크거나 같습니다!")

            # 3.3 고아 자식 노드 (depth > 0인데 부모가 없음)
            result = session.run("""
                MATCH (a:Article)
                WHERE a.depth > 0
                  AND NOT (a)<-[:HAS_CHILD]-(:Article)
                RETURN count(a) AS orphan_children
            """)
            orphan_children = result.single()['orphan_children']
            issues['orphan_children'] = orphan_children
            print(f"고아 자식 노드: {orphan_children}개")
            if orphan_children > 0:
                print("  [WARN]  항/호/목인데 부모 조문이 없습니다!")

            # 3.4 법령 계층 (DERIVED_FROM)
            result = session.run("""
                MATCH (child:Law)-[r:DERIVED_FROM]->(parent:Law)
                RETURN count(r) AS law_hierarchy_count
            """)
            law_hierarchy = result.single()['law_hierarchy_count']
            print(f"\n법령 계층 관계: {law_hierarchy}개")

            if all(v == 0 for v in issues.values()):
                print("\n[OK] 계층 구조: 문제 없음")
            else:
                print(f"\n[WARN]  발견된 이슈: {sum(issues.values())}개")

            self.report['quality_issues']['hierarchy'] = issues
            self.report['statistics']['depth_distribution'] = depth_dist
            self.report['statistics']['law_hierarchy_count'] = law_hierarchy

    def check_cross_law_references(self):
        """4. 타법 참조 현황"""
        print("\n" + "=" * 80)
        print("[4] 타법 참조 현황")
        print("=" * 80)

        with self.driver.session() as session:
            # 4.1 현재 Neo4j에 있는 참조 (같은 법 내부만)
            result = session.run("""
                MATCH (s:Article)-[r:REFERS_TO]->(t:Article)
                WHERE s.law_name = t.law_name
                RETURN count(r) AS same_law_refs
            """)
            same_law_refs = result.single()['same_law_refs']

            result = session.run("""
                MATCH (s:Article)-[r:REFERS_TO]->(t:Article)
                WHERE s.law_name <> t.law_name
                RETURN count(r) AS cross_law_refs
            """)
            cross_law_refs = result.single()['cross_law_refs']

            print(f"\n같은 법 참조 (Neo4j): {same_law_refs:,}개")
            print(f"타법 참조 (Neo4j): {cross_law_refs:,}개")

            # 4.2 JSON 파일의 타법 참조 통계
            references_dir = PROJECT_ROOT / "data" / "legal" / "references"
            total_cross_law_in_json = 0
            target_laws = defaultdict(int)

            if references_dir.exists():
                for ref_file in references_dir.glob("*_references.json"):
                    data = json.load(ref_file.open(encoding='utf-8'))
                    for ref in data.get('references', []):
                        if ref.get('is_cross_law'):
                            total_cross_law_in_json += 1
                            target_laws[ref['target_law_name']] += 1

            print(f"\n타법 참조 (JSON): {total_cross_law_in_json:,}개")
            print(f"미연결 타법 참조: {total_cross_law_in_json - cross_law_refs:,}개")

            print(f"\n참조된 타법 종류: {len(target_laws)}개")
            print("\nTop 10 참조된 타법:")
            for law, count in sorted(target_laws.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {count:4}개: {law}")

            self.report['cross_law_references'] = {
                'neo4j_same_law': same_law_refs,
                'neo4j_cross_law': cross_law_refs,
                'json_cross_law': total_cross_law_in_json,
                'unlinked_cross_law': total_cross_law_in_json - cross_law_refs,
                'target_law_count': len(target_laws),
                'top_target_laws': dict(sorted(target_laws.items(), key=lambda x: x[1], reverse=True)[:20])
            }

    def run_sample_queries(self):
        """5. 샘플 쿼리 실행"""
        print("\n" + "=" * 80)
        print("[5] 샘플 쿼리 테스트")
        print("=" * 80)

        sample_results = {}

        with self.driver.session() as session:
            # 5.1 키워드 검색
            print("\n[5.1] 키워드 검색: '급여비용'")
            result = session.run("""
                MATCH (a:Article)
                WHERE a.full_text CONTAINS '급여비용'
                RETURN a.law_name, a.article_number, a.article_title
                LIMIT 3
            """)
            keyword_results = [dict(r) for r in result]
            for i, r in enumerate(keyword_results, 1):
                print(f"  {i}. {r['a.law_name']} {r['a.article_number']} - {r['a.article_title']}")
            sample_results['keyword_search'] = len(keyword_results)

            # 5.2 참조 관계 추적
            print("\n[5.2] 참조 관계: 의료급여법 제11조를 참조하는 조문")
            result = session.run("""
                MATCH (s:Article)-[r:REFERS_TO]->(t:Article {
                    law_name: '의료급여법',
                    article_number: '제11조'
                })
                RETURN s.article_number, r.reference_type
                LIMIT 5
            """)
            ref_results = [dict(r) for r in result]
            for i, r in enumerate(ref_results, 1):
                print(f"  {i}. {r['s.article_number']} ({r['r.reference_type']})")
            sample_results['reference_tracking'] = len(ref_results)

            # 5.3 법령 계층
            print("\n[5.3] 법령 계층: 의료급여법 관련")
            result = session.run("""
                MATCH (child:Law)-[:DERIVED_FROM]->(parent:Law {law_name: '의료급여법'})
                RETURN child.law_name
            """)
            hierarchy_results = [dict(r) for r in result]
            for i, r in enumerate(hierarchy_results, 1):
                print(f"  {i}. {r['child.law_name']} → 의료급여법")
            sample_results['law_hierarchy'] = len(hierarchy_results)

            # 5.4 조문 계층 (트리 구조)
            print("\n[5.4] 조문 계층: 의료급여법 제3조 하위 구조")
            result = session.run("""
                MATCH (parent:Article {
                    law_name: '의료급여법',
                    article_number: '제3조',
                    depth: 0
                })-[:HAS_CHILD]->(child:Article)
                RETURN child.depth, child.clause_number, child.subclause_number
                ORDER BY child.clause_number, child.subclause_number
                LIMIT 5
            """)
            tree_results = [dict(r) for r in result]
            for i, r in enumerate(tree_results, 1):
                if r['child.depth'] == 1:
                    print(f"  {i}. 제{r['child.clause_number']}항")
                elif r['child.depth'] == 2:
                    print(f"  {i}. 제{r['child.subclause_number']}호")
            sample_results['article_tree'] = len(tree_results)

            self.report['sample_queries'] = sample_results

            if all(v > 0 for v in sample_results.values()):
                print("\n[OK] 샘플 쿼리: 모두 정상 작동")
            else:
                print("\n[WARN]  일부 쿼리에서 결과가 없습니다")

    def save_report(self, output_path: Path):
        """검증 보고서 저장"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] 보고서 저장: {output_path}")


def main():
    """메인 실행"""
    validator = Neo4jQualityValidator()

    try:
        # 검증 실행
        report = validator.run_validation()

        # 요약
        print("\n" + "=" * 80)
        print("검증 요약")
        print("=" * 80)
        stats = report['statistics']
        print(f"\n[OK] 총 노드: {stats['total_nodes']:,}개")
        print(f"[OK] 총 관계: {stats['total_relationships']:,}개")

        integrity = report['quality_issues'].get('integrity', {})
        hierarchy = report['quality_issues'].get('hierarchy', {})
        total_issues = sum(integrity.values()) + sum(hierarchy.values())

        if total_issues == 0:
            print(f"\n[OK] 데이터 품질: 문제 없음")
        else:
            print(f"\n[WARN]  발견된 이슈: {total_issues}개")

        cross_law = report['cross_law_references']
        print(f"\n[WARN]  타법 참조 미연결: {cross_law['unlinked_cross_law']:,}개")
        print(f"   (JSON: {cross_law['json_cross_law']:,}개, Neo4j: {cross_law['neo4j_cross_law']:,}개)")

        # 보고서 저장
        output_path = PROJECT_ROOT / "docs" / "neo4j_quality_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        validator.save_report(output_path)

        print("\n" + "=" * 80)
        print("검증 완료")
        print("=" * 80)

    finally:
        validator.close()


if __name__ == "__main__":
    main()
