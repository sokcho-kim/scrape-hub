"""
Phase 7: Cancer 노드 및 관계 생성

NCC 암종 데이터를 Neo4j에 통합하고 관계를 생성합니다.
- Cancer 노드: 107개
- CANCER_TYPE 관계: Disease ↔ Cancer
- HAS_BIOMARKER 관계: Cancer → Biomarker
- INDICATED_FOR 관계: Drug → Cancer
"""

import json
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import glob


# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
NCC_DIR = PROJECT_ROOT / "data" / "ncc" / "cancer_info" / "parsed"
BRIDGES_DIR = PROJECT_ROOT / "bridges"

# .env 파일 로드
load_dotenv(PROJECT_ROOT / ".env")

# Neo4j 연결 정보
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


# 암종 이름 → KCD 코드 매핑 (수동 큐레이션)
CANCER_KCD_MAPPING = {
    "유방암": ["C50"],
    "폐암": ["C34"],
    "위암": ["C16"],
    "대장암": ["C18", "C19", "C20"],
    "간암": ["C22"],
    "췌장암": ["C25"],
    "담낭암": ["C23"],
    "담도암": ["C24"],
    "식도암": ["C15"],
    "갑상선암": ["C73"],
    "전립선암": ["C61"],
    "자궁경부암": ["C53"],
    "자궁내막암": ["C54"],
    "난소암": ["C56"],
    "방광암": ["C67"],
    "신장암": ["C64"],
    "직장암": ["C20"],
    "결장암": ["C18"],
    "폐선암": ["C34"],
    "폐편평상피세포암": ["C34"],
    "비소세포폐암": ["C34"],
    "소세포폐암": ["C34"],
    "간내 담도암": ["C22.1"],
    "고환암": ["C62"],
    "후두암": ["C32"],
    "설암": ["C01", "C02"],
    "구강암": ["C03", "C04", "C05", "C06"],
    "침샘암": ["C07", "C08"],
    "항문암": ["C21"],
    "피부암": ["C43", "C44"],
    "악성 흑색종": ["C43"],
    "기저세포암": ["C44"],
    "편평상피세포암": ["C44"],
    "음경암": ["C60"],
    "외음부암": ["C51"],
    "질암": ["C52"],
    "뇌종양": ["C71"],
    "교모세포종": ["C71"],
    "성상세포종": ["C71"],
    "수막종": ["D32"],
    "뇌하수체선종": ["D35.2"],
    "척수종양": ["C72"],
    "흉선암": ["C37"],
    "악성 중피종": ["C45"],
    "악성 골종양": ["C40", "C41"],
    "악성 연부조직종양": ["C49"],
    "육종": ["C49"],
    "위장관 기질종양": ["C49"],
    "횡문근육종": ["C49"],
    "악성 림프종": ["C81", "C82", "C83", "C84", "C85"],
    "비호지킨림프종": ["C82", "C83", "C84", "C85"],
    "미만성 거대B세포림프종": ["C83"],
    "위림프종": ["C83"],
    "다발골수종": ["C90"],
    "급성 골수성백혈병": ["C92.0"],
    "급성 림프구성백혈병": ["C91.0"],
    "만성 골수성백혈병": ["C92.1"],
    "만성 림프구성백혈병": ["C91.1"],
    "골수이형성증후군": ["D46"],
}


# 암종별 주요 바이오마커 매핑 (수동 큐레이션)
CANCER_BIOMARKER_MAPPING = {
    "유방암": ["HER2", "ER", "PR", "PD-L1"],
    "폐암": ["EGFR", "ALK", "ROS1", "PD-L1"],
    "위암": ["HER2", "PD-L1"],
    "대장암": ["KRAS", "NRAS", "BRAF", "MSI"],
    "간암": ["AFP"],
    "췌장암": ["CA19-9"],
    "전립선암": ["PSA"],
    "난소암": ["CA-125", "BRCA1", "BRCA2"],
    "신장암": ["PD-L1"],
}


class CancerImporter:
    """Cancer 노드 및 관계 임포터"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {
            'cancers': 0,
            'cancer_type_rels': 0,
            'has_biomarker_rels': 0,
            'indicated_for_rels': 0
        }

    def close(self):
        """연결 종료"""
        self.driver.close()

    def create_constraints_and_indexes(self):
        """제약조건 및 인덱스 생성"""
        print("\n[INFO] Cancer 제약조건 및 인덱스 생성 중...")

        constraints = [
            "CREATE CONSTRAINT cancer_id IF NOT EXISTS FOR (c:Cancer) REQUIRE c.cancer_id IS UNIQUE",
            "CREATE CONSTRAINT cancer_seq IF NOT EXISTS FOR (c:Cancer) REQUIRE c.cancer_seq IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX cancer_name IF NOT EXISTS FOR (c:Cancer) ON (c.name_kr)",
            "CREATE INDEX cancer_category IF NOT EXISTS FOR (c:Cancer) ON (c.category)",
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

    def load_ncc_cancers(self):
        """NCC 암종 데이터 로드"""
        print("\n[INFO] NCC 암종 파일 로딩...")

        cancer_files = glob.glob(str(NCC_DIR / "*_*.json"))
        # 제외: 요약 파일, 약물 관련 파일
        exclude = ["summary", "chemotherapy", "cytotoxic", "immune", "targeted"]
        cancer_files = [f for f in cancer_files if not any(e in f for e in exclude)]

        cancers = []
        for file_path in cancer_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 내용 요약 생성 (섹션 헤딩 결합)
                sections = data.get('content', {}).get('sections', [])
                content_summary = " | ".join([s['heading'] for s in sections[:5]])

                cancer = {
                    'cancer_id': f"NCC_{data['cancer_seq']}",
                    'cancer_seq': data['cancer_seq'],
                    'name_kr': data['name'],
                    'category': data.get('category', ''),
                    'tags': data.get('tags', []),
                    'url': data.get('url', ''),
                    'content_summary': content_summary
                }
                cancers.append(cancer)

            except Exception as e:
                print(f"[WARN] 파일 로드 실패: {file_path} - {e}")

        print(f"[OK] {len(cancers)}개 암종 로드 완료")
        return cancers

    def import_cancers(self, cancers):
        """Cancer 노드 생성"""
        print("\n[INFO] Cancer 노드 생성 중...")

        cypher = """
        UNWIND $cancers AS cancer
        CREATE (c:Cancer {
            cancer_id: cancer.cancer_id,
            cancer_seq: cancer.cancer_seq,
            name_kr: cancer.name_kr,
            category: cancer.category,
            tags: cancer.tags,
            url: cancer.url,
            content_summary: cancer.content_summary,
            created_at: datetime()
        })
        """

        with self.driver.session() as session:
            session.run(cypher, cancers=cancers)

        self.stats['cancers'] = len(cancers)
        print(f"[OK] {self.stats['cancers']}개 Cancer 노드 생성 완료")

    def create_cancer_type_relationships(self, cancers):
        """CANCER_TYPE 관계 생성 (Disease ↔ Cancer)"""
        print("\n[INFO] CANCER_TYPE 관계 생성 중...")

        relationships = []

        for cancer in cancers:
            cancer_name = cancer['name_kr']
            # 기본 매핑 시도
            kcd_codes = CANCER_KCD_MAPPING.get(cancer_name, [])

            if not kcd_codes:
                # 부분 매칭 시도 (예: "남성 유방암" → "유방암")
                for key, codes in CANCER_KCD_MAPPING.items():
                    if key in cancer_name or cancer_name in key:
                        kcd_codes = codes
                        break

            for kcd_code in kcd_codes:
                relationships.append({
                    'cancer_id': cancer['cancer_id'],
                    'kcd_code': kcd_code,
                    'match_type': 'exact' if cancer_name in CANCER_KCD_MAPPING else 'partial',
                    'confidence': 0.95 if cancer_name in CANCER_KCD_MAPPING else 0.8
                })

        if not relationships:
            print("[WARN] CANCER_TYPE 관계를 생성할 수 없습니다")
            return

        cypher = """
        UNWIND $rels AS rel
        MATCH (c:Cancer {cancer_id: rel.cancer_id})
        MATCH (d:Disease)
        WHERE d.kcd_code = rel.kcd_code OR d.kcd_code STARTS WITH rel.kcd_code + '.'
        CREATE (d)-[:CANCER_TYPE {
            match_type: rel.match_type,
            confidence: rel.confidence,
            created_at: datetime()
        }]->(c)
        """

        with self.driver.session() as session:
            result = session.run(cypher, rels=relationships)
            # 실제 생성된 관계 수 확인
            count_query = "MATCH ()-[r:CANCER_TYPE]->() RETURN count(r) as count"
            count_result = session.run(count_query)
            self.stats['cancer_type_rels'] = count_result.single()['count']

        print(f"[OK] {self.stats['cancer_type_rels']}개 CANCER_TYPE 관계 생성 완료")
        print(f"     (매핑 시도: {len(relationships)}개)")

    def create_has_biomarker_relationships(self, cancers):
        """HAS_BIOMARKER 관계 생성 (Cancer → Biomarker)"""
        print("\n[INFO] HAS_BIOMARKER 관계 생성 중...")

        relationships = []

        for cancer in cancers:
            cancer_name = cancer['name_kr']
            biomarkers = CANCER_BIOMARKER_MAPPING.get(cancer_name, [])

            if not biomarkers:
                # 부분 매칭
                for key, bio_list in CANCER_BIOMARKER_MAPPING.items():
                    if key in cancer_name or cancer_name in key:
                        biomarkers = bio_list
                        break

            for biomarker_name in biomarkers:
                relationships.append({
                    'cancer_id': cancer['cancer_id'],
                    'biomarker_name': biomarker_name,
                    'biomarker_role': '표적',
                    'clinical_significance': f'{biomarker_name} 양성/변이 시 표적치료 고려'
                })

        if not relationships:
            print("[WARN] HAS_BIOMARKER 관계를 생성할 수 없습니다")
            return

        cypher = """
        UNWIND $rels AS rel
        MATCH (c:Cancer {cancer_id: rel.cancer_id})
        MATCH (b:Biomarker)
        WHERE b.name_en = rel.biomarker_name OR b.name_ko CONTAINS rel.biomarker_name
        CREATE (c)-[:HAS_BIOMARKER {
            biomarker_role: rel.biomarker_role,
            clinical_significance: rel.clinical_significance,
            created_at: datetime()
        }]->(b)
        """

        with self.driver.session() as session:
            result = session.run(cypher, rels=relationships)
            count_query = "MATCH ()-[r:HAS_BIOMARKER]->() RETURN count(r) as count"
            count_result = session.run(count_query)
            self.stats['has_biomarker_rels'] = count_result.single()['count']

        print(f"[OK] {self.stats['has_biomarker_rels']}개 HAS_BIOMARKER 관계 생성 완료")
        print(f"     (매핑 시도: {len(relationships)}개)")

    def create_indicated_for_relationships(self):
        """INDICATED_FOR 관계 생성 (Drug → Cancer)"""
        print("\n[INFO] INDICATED_FOR 관계 생성 중...")

        # Drug-Biomarker-Cancer 경로를 통해 관계 생성
        cypher = """
        MATCH (drug:Drug)-[:TARGETS]->(b:Biomarker)<-[:HAS_BIOMARKER]-(c:Cancer)
        WITH drug, c, b, b.cancer_types as cancer_types
        WHERE ANY(ct IN cancer_types WHERE c.name_kr CONTAINS ct)
        CREATE (drug)-[:INDICATED_FOR {
            biomarker_status: b.name_en + ' 양성/변이',
            approval_status: '확인 필요',
            evidence_level: 'DB 추론',
            created_at: datetime()
        }]->(c)
        """

        with self.driver.session() as session:
            try:
                result = session.run(cypher)
                count_query = "MATCH ()-[r:INDICATED_FOR]->() RETURN count(r) as count"
                count_result = session.run(count_query)
                self.stats['indicated_for_rels'] = count_result.single()['count']
                print(f"[OK] {self.stats['indicated_for_rels']}개 INDICATED_FOR 관계 생성 완료")
            except Exception as e:
                print(f"[WARN] INDICATED_FOR 관계 생성 실패: {e}")
                self.stats['indicated_for_rels'] = 0

    def verify_import(self):
        """데이터 임포트 검증"""
        print("\n[INFO] Cancer 데이터 검증 중...")

        queries = {
            'total_cancers': "MATCH (c:Cancer) RETURN count(c) as count",
            'cancer_type_rels': "MATCH ()-[r:CANCER_TYPE]->() RETURN count(r) as count",
            'has_biomarker_rels': "MATCH ()-[r:HAS_BIOMARKER]->() RETURN count(r) as count",
            'indicated_for_rels': "MATCH ()-[r:INDICATED_FOR]->() RETURN count(r) as count",
        }

        with self.driver.session() as session:
            print("\n[VERIFY] Neo4j Cancer 데이터:")
            for name, query in queries.items():
                result = session.run(query)
                count = result.single()['count']
                print(f"  - {name}: {count}개")

    def print_sample_queries(self):
        """샘플 쿼리 출력"""
        print("\n" + "=" * 70)
        print("Cancer 샘플 쿼리")
        print("=" * 70)

        print("\n1. 유방암의 모든 관련 정보:")
        print("""
MATCH (d:Disease)-[:CANCER_TYPE]->(c:Cancer {name_kr: '유방암'})-[:HAS_BIOMARKER]->(b:Biomarker)
OPTIONAL MATCH (drug:Drug)-[:INDICATED_FOR]->(c)
RETURN d.kcd_code, c.name_kr, collect(DISTINCT b.name_en) as biomarkers,
       count(DISTINCT drug) as drug_count
        """)

        print("\n2. HER2 관련 암종 및 약물:")
        print("""
MATCH (c:Cancer)-[:HAS_BIOMARKER]->(b:Biomarker {name_en: 'HER2'})<-[:TARGETS]-(d:Drug)
RETURN c.name_kr, d.ingredient_ko
ORDER BY c.name_kr
        """)

        print("\n3. 통합 임상 의사결정 지원 (HER2 양성 유방암):")
        print("""
MATCH path = (d:Disease)-[:CANCER_TYPE]->(c:Cancer {name_kr: '유방암'})
            -[:HAS_BIOMARKER]->(b:Biomarker {name_en: 'HER2'})
            <-[:TARGETS]-(drug:Drug)
MATCH (b)-[:TESTED_BY]->(t:Test)
RETURN drug.ingredient_ko AS 약물,
       t.name_ko AS 필요검사,
       t.edi_code AS EDI코드
LIMIT 10
        """)

        print("\n4. 암종별 바이오마커 통계:")
        print("""
MATCH (c:Cancer)-[:HAS_BIOMARKER]->(b:Biomarker)
RETURN c.name_kr, count(b) as biomarker_count
ORDER BY biomarker_count DESC
LIMIT 10
        """)

        print("\n" + "=" * 70)

    def run(self):
        """전체 임포트 프로세스 실행"""
        print("=" * 70)
        print("Phase 7: Cancer 노드 및 관계 생성")
        print("=" * 70)

        try:
            # 데이터 로드
            cancers = self.load_ncc_cancers()

            # 제약조건 및 인덱스
            self.create_constraints_and_indexes()

            # Cancer 노드 생성
            self.import_cancers(cancers)

            # 관계 생성
            self.create_cancer_type_relationships(cancers)
            self.create_has_biomarker_relationships(cancers)
            self.create_indicated_for_relationships()

            # 검증
            self.verify_import()

            # 샘플 쿼리
            self.print_sample_queries()

            print("\n[SUCCESS] Cancer 노드 및 관계 생성 완료!")
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

    importer = CancerImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        success = importer.run()
        return 0 if success else 1

    finally:
        importer.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
