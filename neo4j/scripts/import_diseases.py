"""
Phase 5: Disease 노드 생성

KCD-9 질병 코드를 Neo4j에 통합합니다.
- Disease 노드: 54,125개
- IS_A 관계: 계층 구조 표현
"""

import json
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import re


# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "kssc" / "kcd-9th" / "normalized"
INPUT_KCD = DATA_DIR / "kcd9_full.json"

# .env 파일 로드
load_dotenv(PROJECT_ROOT / ".env")

# Neo4j 연결 정보
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class DiseaseImporter:
    """Disease 노드 임포터"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {
            'diseases': 0,
            'is_a_rels': 0,
            'cancer_codes': 0
        }

    def close(self):
        """연결 종료"""
        self.driver.close()

    def create_constraints_and_indexes(self):
        """제약조건 및 인덱스 생성"""
        print("\n[INFO] Disease 제약조건 및 인덱스 생성 중...")

        constraints = [
            "CREATE CONSTRAINT disease_kcd IF NOT EXISTS FOR (d:Disease) REQUIRE d.kcd_code IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX disease_name_kr IF NOT EXISTS FOR (d:Disease) ON (d.name_kr)",
            "CREATE INDEX disease_name_en IF NOT EXISTS FOR (d:Disease) ON (d.name_en)",
            "CREATE INDEX disease_classification IF NOT EXISTS FOR (d:Disease) ON (d.classification)",
            "CREATE INDEX disease_is_cancer IF NOT EXISTS FOR (d:Disease) ON (d.is_cancer)",
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

    def parse_code_range(self, code):
        """
        코드 범위 파싱
        예: "A00-B99" → ["A", "00", "B", "99"]
            "C50.0" → ["C", "50", "0"]
        """
        # 범위 코드 (예: A00-B99)
        if '-' in code:
            parts = code.split('-')
            if len(parts) == 2:
                return {'type': 'range', 'start': parts[0], 'end': parts[1]}

        # 점 포함 코드 (예: C50.0)
        if '.' in code:
            match = re.match(r'([A-Z])(\d+)\.(\d+)', code)
            if match:
                return {
                    'type': 'detailed',
                    'chapter': match.group(1),
                    'category': match.group(2),
                    'subcategory': match.group(3)
                }

        # 카테고리 코드 (예: C50)
        match = re.match(r'([A-Z])(\d+)', code)
        if match:
            return {
                'type': 'category',
                'chapter': match.group(1),
                'category': match.group(2)
            }

        # 챕터 코드 (예: A, B)
        match = re.match(r'([A-Z])$', code)
        if match:
            return {'type': 'chapter', 'chapter': match.group(1)}

        return None

    def is_cancer_code(self, code):
        """
        암 코드 여부 확인
        C00-D48: 신생물
        """
        parsed = self.parse_code_range(code)
        if not parsed:
            return False

        if parsed['type'] == 'range':
            # C00-D48 범위 확인
            start_chapter = parsed['start'][0] if parsed['start'] else None
            end_chapter = parsed['end'][0] if parsed['end'] else None
            return start_chapter in ['C', 'D'] or end_chapter in ['C', 'D']

        elif parsed['type'] in ['category', 'detailed']:
            chapter = parsed.get('chapter', '')
            if chapter == 'C':
                return True
            if chapter == 'D':
                # D00-D48만 암 (D50 이상은 비신생물)
                category = int(parsed.get('category', '99'))
                return category <= 48

        return False

    def build_hierarchy_relationships(self, codes):
        """
        계층 관계 구축
        범위 코드 → 카테고리 → 세부 코드
        """
        relationships = []

        # 코드별로 부모 찾기
        for code_obj in codes:
            code = code_obj['code']
            parsed = self.parse_code_range(code)

            if not parsed or parsed['type'] == 'range':
                continue

            # 세부 코드 (C50.0) → 카테고리 (C50)
            if parsed['type'] == 'detailed':
                parent_code = f"{parsed['chapter']}{parsed['category']}"
                relationships.append({
                    'child': code,
                    'parent': parent_code,
                    'hierarchy_level': '소→세'
                })

            # 카테고리 (C50) → 범위 코드 찾기 (C00-D48)
            elif parsed['type'] == 'category':
                # 상위 범위 코드 찾기
                chapter = parsed['chapter']
                category_num = int(parsed['category'])

                for range_obj in codes:
                    range_code = range_obj['code']
                    if '-' not in range_code:
                        continue

                    range_parsed = self.parse_code_range(range_code)
                    if not range_parsed or range_parsed['type'] != 'range':
                        continue

                    # 범위에 속하는지 확인
                    start = range_parsed['start']
                    end = range_parsed['end']

                    # 간단한 범위 체크 (같은 챕터 내)
                    if start[0] == chapter == end[0]:
                        start_num = int(re.search(r'\d+', start).group()) if re.search(r'\d+', start) else 0
                        end_num = int(re.search(r'\d+', end).group()) if re.search(r'\d+', end) else 99

                        if start_num <= category_num <= end_num:
                            # 가장 좁은 범위 선택 (중분류 우선)
                            if range_obj['classification'] == '중':
                                relationships.append({
                                    'child': code,
                                    'parent': range_code,
                                    'hierarchy_level': '중→소'
                                })
                                break

        return relationships

    def import_diseases(self, kcd_data):
        """Disease 노드 생성"""
        print("\n[INFO] Disease 노드 생성 중...")

        codes = kcd_data['codes']

        # 암 코드 태깅
        for code_obj in codes:
            code_obj['is_cancer'] = self.is_cancer_code(code_obj['code'])
            if code_obj['is_cancer']:
                self.stats['cancer_codes'] += 1

        # 배치 처리 (1000개씩)
        batch_size = 1000
        total_batches = (len(codes) + batch_size - 1) // batch_size

        cypher = """
        UNWIND $diseases AS disease
        CREATE (d:Disease {
            kcd_code: disease.code,
            name_kr: disease.name_kr,
            name_en: disease.name_en,
            is_header: disease.is_header,
            classification: disease.classification,
            symbol: disease.symbol,
            is_lowest: disease.is_lowest,
            is_domestic: disease.is_domestic,
            is_oriental: disease.is_oriental,
            is_additional: disease.is_additional,
            is_cancer: disease.is_cancer,
            note: disease.note,
            created_at: datetime()
        })
        """

        with self.driver.session() as session:
            for i in range(0, len(codes), batch_size):
                batch = codes[i:i+batch_size]
                session.run(cypher, diseases=batch)
                batch_num = (i // batch_size) + 1
                print(f"  배치 {batch_num}/{total_batches} 완료 ({len(batch)}개)")

        self.stats['diseases'] = len(codes)
        print(f"[OK] {self.stats['diseases']}개 Disease 노드 생성 완료")
        print(f"     - 암 코드: {self.stats['cancer_codes']}개")

    def create_hierarchy_relationships(self, kcd_data):
        """IS_A 계층 관계 생성"""
        print("\n[INFO] IS_A 계층 관계 생성 중...")

        codes = kcd_data['codes']
        relationships = self.build_hierarchy_relationships(codes)

        if not relationships:
            print("[WARN] 계층 관계를 찾을 수 없습니다")
            return

        cypher = """
        UNWIND $rels AS rel
        MATCH (child:Disease {kcd_code: rel.child})
        MATCH (parent:Disease {kcd_code: rel.parent})
        CREATE (child)-[:IS_A {
            hierarchy_level: rel.hierarchy_level,
            created_at: datetime()
        }]->(parent)
        """

        # 배치 처리
        batch_size = 1000
        with self.driver.session() as session:
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i:i+batch_size]
                session.run(cypher, rels=batch)

        self.stats['is_a_rels'] = len(relationships)
        print(f"[OK] {self.stats['is_a_rels']}개 IS_A 관계 생성 완료")

    def verify_import(self):
        """데이터 임포트 검증"""
        print("\n[INFO] Disease 데이터 검증 중...")

        queries = {
            'total_diseases': "MATCH (d:Disease) RETURN count(d) as count",
            'cancer_codes': "MATCH (d:Disease {is_cancer: true}) RETURN count(d) as count",
            'lowest_codes': "MATCH (d:Disease {is_lowest: true}) RETURN count(d) as count",
            'is_a_relationships': "MATCH ()-[r:IS_A]->() RETURN count(r) as count",
        }

        with self.driver.session() as session:
            print("\n[VERIFY] Neo4j Disease 데이터:")
            for name, query in queries.items():
                result = session.run(query)
                count = result.single()['count']
                print(f"  - {name}: {count}개")

    def print_sample_queries(self):
        """샘플 쿼리 출력"""
        print("\n" + "=" * 70)
        print("Disease 샘플 쿼리")
        print("=" * 70)

        print("\n1. 유방암 관련 질병 코드 조회:")
        print("""
MATCH (d:Disease)
WHERE d.name_kr CONTAINS '유방' AND d.is_cancer = true
RETURN d.kcd_code, d.name_kr, d.classification
LIMIT 10
        """)

        print("\n2. C50 (유방암) 하위 코드 계층 조회:")
        print("""
MATCH path = (child:Disease)-[:IS_A*]->(parent:Disease {kcd_code: 'C50'})
RETURN child.kcd_code, child.name_kr, length(path) as depth
ORDER BY child.kcd_code
        """)

        print("\n3. 암 코드 분류별 통계:")
        print("""
MATCH (d:Disease {is_cancer: true})
RETURN d.classification, count(d) as count
ORDER BY count DESC
        """)

        print("\n4. 최하위 암 코드 (청구 가능):")
        print("""
MATCH (d:Disease {is_cancer: true, is_lowest: true})
RETURN d.kcd_code, d.name_kr
LIMIT 20
        """)

        print("\n" + "=" * 70)

    def run(self):
        """전체 임포트 프로세스 실행"""
        print("=" * 70)
        print("Phase 5: Disease 노드 생성")
        print("=" * 70)

        try:
            # 데이터 로드
            print("\n[INFO] KCD-9 데이터 파일 로딩...")
            with open(INPUT_KCD, 'r', encoding='utf-8') as f:
                kcd_data = json.load(f)
            print(f"[OK] KCD-9 데이터 로드 완료: {kcd_data['total_codes']}개 코드")

            # 제약조건 및 인덱스
            self.create_constraints_and_indexes()

            # Disease 노드 생성
            self.import_diseases(kcd_data)

            # 계층 관계 생성
            self.create_hierarchy_relationships(kcd_data)

            # 검증
            self.verify_import()

            # 샘플 쿼리
            self.print_sample_queries()

            print("\n[SUCCESS] Disease 노드 생성 완료!")
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

    importer = DiseaseImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        success = importer.run()
        return 0 if success else 1

    finally:
        importer.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
