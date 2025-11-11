"""
HIRA Regimen 통합 검증

전체 경로 쿼리 및 통계
"""

import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def main():
    """메인 실행"""
    print("=" * 80)
    print("HIRA Regimen 통합 검증")
    print("=" * 80)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            # 1. 노드 및 관계 통계
            print("\n[1] 노드 및 관계 통계")
            print("-" * 80)

            queries = {
                'Disease': "MATCH (n:Disease) RETURN count(n) as count",
                'Procedure': "MATCH (n:Procedure) RETURN count(n) as count",
                'Biomarker': "MATCH (n:Biomarker) RETURN count(n) as count",
                'Test': "MATCH (n:Test) RETURN count(n) as count",
                'Drug': "MATCH (n:Drug) RETURN count(n) as count",
                'Regimen': "MATCH (n:Regimen) RETURN count(n) as count",
                'HAS_BIOMARKER': "MATCH ()-[r:HAS_BIOMARKER]->() RETURN count(r) as count",
                'TESTED_BY': "MATCH ()-[r:TESTED_BY]->() RETURN count(r) as count",
                'TARGETS': "MATCH ()-[r:TARGETS]->() RETURN count(r) as count",
                'TREATED_BY': "MATCH ()-[r:TREATED_BY]->() RETURN count(r) as count",
                'INCLUDES': "MATCH ()-[r:INCLUDES]->() RETURN count(r) as count",
            }

            for name, query in queries.items():
                result = session.run(query)
                count = result.single()['count']
                print(f"  {name:20s}: {count:6d}개")

            # 2. HER2 양성 유방암 1차 급여 요법
            print("\n[2] HER2 양성 유방암 1차 급여 요법")
            print("-" * 80)

            query = """
            MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)-[:INCLUDES]->(drug:Drug)
            WHERE d.kcd_code STARTS WITH 'C50' AND tb.line = '1차'
            RETURN DISTINCT
                d.name_kr as 질병,
                r.regimen_type as 요법유형,
                r.line as 치료라인,
                collect(DISTINCT drug.ingredient_ko) as 약물목록,
                r.announcement_no as 고시번호,
                r.announcement_date as 고시일자
            LIMIT 5
            """

            result = session.run(query)
            for record in result:
                print(f"\n질병: {record['질병']}")
                print(f"  요법유형: {record['요법유형']}")
                print(f"  치료라인: {record['치료라인']}")
                print(f"  약물목록: {', '.join(record['약물목록'])}")
                print(f"  고시번호: {record['고시번호']}")
                print(f"  고시일자: {record['고시일자']}")

            # 3. 전체 경로: Test → Biomarker → Drug → Regimen → Disease
            print("\n[3] 전체 경로 쿼리 (바이오마커 검사 → 급여 요법)")
            print("-" * 80)

            query = """
            MATCH (t:Test)<-[:TESTED_BY]-(b:Biomarker)<-[:TARGETS]-(drug:Drug)
                  <-[:INCLUDES]-(r:Regimen)<-[tb:TREATED_BY]-(d:Disease)
            WHERE d.kcd_code STARTS WITH 'C50' AND b.name_en = 'HER2'
            RETURN
                d.name_kr as 질병,
                b.name_ko as 바이오마커,
                t.name_ko as 검사명,
                t.edi_code as 검사코드,
                drug.ingredient_ko as 약물,
                r.regimen_type as 요법유형,
                tb.line as 치료라인,
                r.announcement_no as 고시번호
            LIMIT 10
            """

            result = session.run(query)
            count = 0
            for record in result:
                count += 1
                print(f"\n경로 {count}:")
                print(f"  질병: {record['질병']}")
                print(f"  바이오마커: {record['바이오마커']}")
                print(f"  검사명: {record['검사명']} ({record['검사코드']})")
                print(f"  약물: {record['약물']}")
                print(f"  요법유형: {record['요법유형']}")
                print(f"  치료라인: {record['치료라인']}")
                print(f"  고시번호: {record['고시번호']}")

            if count == 0:
                print("  [INFO] 전체 경로가 연결되지 않음 (바이오마커-약물-레지멘 매칭 필요)")

            # 4. 레지멘 통계 (암종별, 라인별)
            print("\n[4] 레지멘 통계")
            print("-" * 80)

            query = """
            MATCH (d:Disease)-[tb:TREATED_BY]->(r:Regimen)
            WHERE d.is_cancer = true
            RETURN
                d.name_kr as 암종,
                count(DISTINCT r) as 레지멘수,
                collect(DISTINCT tb.line) as 치료라인목록
            ORDER BY 레지멘수 DESC
            LIMIT 10
            """

            result = session.run(query)
            print(f"\n{'암종':15s} {'레지멘수':10s} {'치료라인'}")
            print("-" * 50)
            for record in result:
                lines = ', '.join([str(l) for l in record['치료라인목록'] if l])
                print(f"{record['암종']:15s} {record['레지멘수']:10d}개 {lines}")

            # 5. 약물별 사용 빈도
            print("\n[5] 레지멘에 포함된 약물 TOP 10")
            print("-" * 80)

            query = """
            MATCH (r:Regimen)-[:INCLUDES]->(d:Drug)
            RETURN
                d.ingredient_ko as 약물,
                d.mechanism_of_action as 기전,
                count(DISTINCT r) as 레지멘수
            ORDER BY 레지멘수 DESC
            LIMIT 10
            """

            result = session.run(query)
            print(f"\n{'약물':20s} {'레지멘수':10s} {'기전'}")
            print("-" * 70)
            for record in result:
                moa = record['기전'] or 'N/A'
                print(f"{record['약물']:20s} {record['레지멘수']:10d}개 {moa}")

    finally:
        driver.close()

    print("\n" + "=" * 80)
    print("[SUCCESS] 검증 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
