"""
Neo4j 그래프 데이터 탐색 및 분석

주요 통계 및 인사이트 추출
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path
import json

# .env 파일 로드
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Neo4j 연결
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class Neo4jAnalyzer:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, params=None):
        """쿼리 실행"""
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def get_basic_stats(self):
        """기본 통계"""
        print("="*70)
        print("기본 통계")
        print("="*70)

        # 노드 수
        query = """
        MATCH (n)
        RETURN labels(n)[0] as NodeType, count(n) as Count
        ORDER BY Count DESC
        """
        results = self.run_query(query)
        print("\n노드 타입별 개수:")
        for r in results:
            print(f"  {r['NodeType']}: {r['Count']}개")

        # 관계 수
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as RelationType, count(r) as Count
        ORDER BY Count DESC
        """
        results = self.run_query(query)
        print("\n관계 타입별 개수:")
        for r in results:
            print(f"  {r['RelationType']}: {r['Count']}개")

        # 전체 요약
        query = """
        MATCH (n)
        WITH count(n) as total_nodes
        MATCH ()-[r]->()
        WITH total_nodes, count(r) as total_rels
        RETURN total_nodes, total_rels
        """
        result = self.run_query(query)[0]
        print(f"\n전체 요약:")
        print(f"  총 노드: {result['total_nodes']}개")
        print(f"  총 관계: {result['total_rels']}개")

    def get_biomarker_analysis(self):
        """바이오마커 분석"""
        print("\n" + "="*70)
        print("바이오마커 분석")
        print("="*70)

        # 바이오마커별 검사 수 (상위 10개)
        query = """
        MATCH (b:Biomarker)-[:TESTED_BY]->(t:Test)
        RETURN b.name_en as Biomarker, b.name_ko as BiomarkerKo,
               count(t) as TestCount
        ORDER BY TestCount DESC
        LIMIT 10
        """
        results = self.run_query(query)
        print("\n바이오마커별 검사 수 (상위 10개):")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['Biomarker']} ({r['BiomarkerKo']}): {r['TestCount']}개")

        # 바이오마커 타입별 분포
        query = """
        MATCH (b:Biomarker)
        RETURN b.type as BiomarkerType, count(b) as Count
        ORDER BY Count DESC
        """
        results = self.run_query(query)
        print("\n바이오마커 타입별 분포:")
        for r in results:
            print(f"  {r['BiomarkerType']}: {r['Count']}개")

    def get_drug_analysis(self):
        """약물 분석"""
        print("\n" + "="*70)
        print("약물 분석")
        print("="*70)

        # 바이오마커를 타겟하는 약물 수
        query = """
        MATCH (d:Drug)-[:TARGETS]->(b:Biomarker)
        RETURN b.name_en as Biomarker, b.name_ko as BiomarkerKo,
               count(DISTINCT d) as DrugCount
        ORDER BY DrugCount DESC
        """
        results = self.run_query(query)
        print("\n바이오마커별 타겟 약물 수:")
        for r in results:
            print(f"  {r['Biomarker']} ({r['BiomarkerKo']}): {r['DrugCount']}개")

        # ATC Level 3 분류별 약물 수
        query = """
        MATCH (d:Drug)
        WHERE d.atc_level3 IS NOT NULL
        RETURN d.atc_level3 as ATC_L3, d.atc_level3_name as ATC_L3_Name,
               count(d) as Count
        ORDER BY Count DESC
        LIMIT 10
        """
        results = self.run_query(query)
        print("\nATC Level 3 분류별 약물 수 (상위 10개):")
        for r in results:
            print(f"  {r['ATC_L3']} ({r['ATC_L3_Name']}): {r['Count']}개")

    def get_test_analysis(self):
        """검사 분석"""
        print("\n" + "="*70)
        print("검사 분석")
        print("="*70)

        # 검사 카테고리별 분포
        query = """
        MATCH (t:Test)
        WHERE t.category IS NOT NULL
        RETURN t.category as Category, count(t) as Count
        ORDER BY Count DESC
        """
        results = self.run_query(query)
        print("\n검사 카테고리별 분포:")
        for r in results:
            print(f"  {r['Category']}: {r['Count']}개")

        # SNOMED CT 코드 보유율
        query = """
        MATCH (t:Test)
        WITH count(t) as total
        MATCH (t2:Test)
        WHERE t2.snomed_ct_id IS NOT NULL AND t2.snomed_ct_id <> ''
        WITH total, count(t2) as with_snomed
        RETURN total, with_snomed,
               round(100.0 * with_snomed / total, 1) as percentage
        """
        result = self.run_query(query)[0]
        print(f"\nSNOMED CT 코드 보유율:")
        print(f"  전체: {result['total']}개")
        print(f"  SNOMED CT 보유: {result['with_snomed']}개 ({result['percentage']}%)")

        # LOINC 코드 보유율
        query = """
        MATCH (t:Test)
        WITH count(t) as total
        MATCH (t2:Test)
        WHERE t2.loinc_code IS NOT NULL AND t2.loinc_code <> ''
        WITH total, count(t2) as with_loinc
        RETURN total, with_loinc,
               round(100.0 * with_loinc / total, 1) as percentage
        """
        result = self.run_query(query)[0]
        print(f"\nLOINC 코드 보유율:")
        print(f"  전체: {result['total']}개")
        print(f"  LOINC 보유: {result['with_loinc']}개 ({result['percentage']}%)")

    def get_path_examples(self):
        """경로 예시"""
        print("\n" + "="*70)
        print("약물-바이오마커-검사 경로 예시")
        print("="*70)

        # EGFR 경로
        query = """
        MATCH path = (d:Drug)-[:TARGETS]->(b:Biomarker {name_en: 'EGFR'})-[:TESTED_BY]->(t:Test)
        RETURN d.ingredient_ko as Drug,
               b.name_ko as Biomarker,
               t.name_ko as Test,
               t.edi_code as EDI
        LIMIT 5
        """
        results = self.run_query(query)
        print("\nEGFR 표적 약물-검사 경로 (5개):")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['Drug']} → {r['Biomarker']} → {r['Test']} (EDI: {r['EDI']})")

        # HER2 경로
        query = """
        MATCH path = (d:Drug)-[:TARGETS]->(b:Biomarker {name_en: 'HER2'})-[:TESTED_BY]->(t:Test)
        RETURN d.ingredient_ko as Drug,
               b.name_ko as Biomarker,
               t.name_ko as Test,
               t.edi_code as EDI
        LIMIT 5
        """
        results = self.run_query(query)
        print("\nHER2 표적 약물-검사 경로 (5개):")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['Drug']} → {r['Biomarker']} → {r['Test']} (EDI: {r['EDI']})")

    def get_new_biomarkers_v2(self):
        """v2.0에서 추가된 바이오마커 확인"""
        print("\n" + "="*70)
        print("v2.0 신규 바이오마커 (HINS 기반)")
        print("="*70)

        query = """
        MATCH (b:Biomarker)
        WHERE b.source = 'hins_only' OR b.source CONTAINS 'hins'
        RETURN b.name_en as Biomarker, b.name_ko as BiomarkerKo,
               b.type as Type, b.source as Source
        ORDER BY b.name_en
        """
        results = self.run_query(query)

        if results:
            print("\nHINS에서 발견된 바이오마커:")
            for r in results:
                print(f"  - {r['Biomarker']} ({r['BiomarkerKo']})")
                print(f"    타입: {r['Type']}, 출처: {r['Source']}")
        else:
            print("\nℹ️ source 필드가 설정되지 않았습니다.")
            print("전체 23개 바이오마커가 통합되었으나 출처 정보는 확인 불가")


def main():
    print("="*70)
    print("Neo4j 그래프 데이터 분석")
    print("="*70)
    print(f"\n연결 정보:")
    print(f"  URI: {NEO4J_URI}")
    print(f"  User: {NEO4J_USER}")
    print()

    analyzer = Neo4jAnalyzer(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # 기본 통계
        analyzer.get_basic_stats()

        # 바이오마커 분석
        analyzer.get_biomarker_analysis()

        # 약물 분석
        analyzer.get_drug_analysis()

        # 검사 분석
        analyzer.get_test_analysis()

        # 경로 예시
        analyzer.get_path_examples()

        # v2.0 신규 바이오마커
        analyzer.get_new_biomarkers_v2()

        print("\n" + "="*70)
        print("분석 완료!")
        print("="*70)

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
