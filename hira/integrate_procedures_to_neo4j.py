"""
건강보험요양급여비용 Procedure 데이터 Neo4j 통합

목적:
1. 파싱된 Procedure 데이터를 Neo4j에 저장
2. Procedure 노드 생성 (EDI 코드, 이름, 점수)
3. 통합 검증
"""

import json
from pathlib import Path
from neo4j import GraphDatabase
from datetime import datetime
from typing import List, Dict


class ProcedureIntegrator:
    """Procedure 데이터 Neo4j 통합"""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "na69056905%%"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {
            'total_procedures': 0,
            'created_nodes': 0,
            'skipped_existing': 0,
            'errors': 0
        }
        self.errors = []

    def close(self):
        self.driver.close()

    def load_procedures(self, json_file: Path) -> List[Dict]:
        """JSON 파일에서 Procedure 데이터 로드"""
        print(f"Loading procedures from: {json_file}")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        procedures = data.get('procedures', [])
        self.stats['total_procedures'] = len(procedures)

        print(f"Loaded {len(procedures)} procedures")
        return procedures

    def create_constraints(self):
        """Neo4j 제약조건 생성"""
        print("\nCreating constraints...")

        with self.driver.session() as session:
            try:
                # EDI 코드를 unique constraint로 설정
                session.run("""
                    CREATE CONSTRAINT procedure_edi_code IF NOT EXISTS
                    FOR (p:Procedure)
                    REQUIRE p.edi_code IS UNIQUE
                """)
                print("  Constraint created: Procedure.edi_code")

            except Exception as e:
                print(f"  Warning: Constraint creation failed (may already exist): {e}")

    def integrate_procedure(self, session, proc: Dict) -> bool:
        """단일 Procedure 통합"""
        try:
            # MERGE를 사용하여 이미 존재하면 업데이트, 없으면 생성
            result = session.run("""
                MERGE (p:Procedure {edi_code: $edi_code})
                ON CREATE SET
                    p.name = $name,
                    p.name_en = $name_en,
                    p.points = $points,
                    p.source = $source,
                    p.source_page = $source_page,
                    p.classification_number = $classification_number,
                    p.created_at = datetime(),
                    p.updated_at = datetime()
                ON MATCH SET
                    p.name = $name,
                    p.name_en = $name_en,
                    p.points = $points,
                    p.source = $source,
                    p.source_page = $source_page,
                    p.classification_number = $classification_number,
                    p.updated_at = datetime()
                RETURN p,
                    CASE WHEN p.created_at = p.updated_at THEN 'created' ELSE 'updated' END as status
            """, {
                'edi_code': proc['edi_code'],
                'name': proc.get('name', ''),
                'name_en': proc.get('name_en', ''),
                'points': proc.get('points'),
                'source': proc.get('source', ''),
                'source_page': proc.get('page'),
                'classification_number': proc.get('classification_number', '')
            })

            record = result.single()
            if record:
                status = record['status']
                if status == 'created':
                    self.stats['created_nodes'] += 1
                else:
                    self.stats['skipped_existing'] += 1
                return True

            return False

        except Exception as e:
            self.errors.append({
                'edi_code': proc.get('edi_code', 'unknown'),
                'error': str(e)
            })
            self.stats['errors'] += 1
            return False

    def integrate_procedures(self, procedures: List[Dict]):
        """Procedure 데이터를 Neo4j에 통합"""
        print("\nIntegrating procedures to Neo4j...")
        print(f"Total procedures to integrate: {len(procedures)}")
        print("="*80)

        with self.driver.session() as session:
            for i, proc in enumerate(procedures, 1):
                if i % 500 == 0:
                    print(f"Progress: {i}/{len(procedures)} "
                          f"(Created: {self.stats['created_nodes']}, "
                          f"Updated: {self.stats['skipped_existing']}, "
                          f"Errors: {self.stats['errors']})")

                self.integrate_procedure(session, proc)

        print("="*80)
        print("Integration complete!")

    def verify_integration(self):
        """통합 검증"""
        print("\nVerifying integration...")

        with self.driver.session() as session:
            # 총 Procedure 노드 수
            result = session.run("MATCH (p:Procedure) RETURN count(p) as count")
            total_procedures = result.single()['count']

            # 점수가 있는 Procedure 수
            result = session.run("MATCH (p:Procedure) WHERE p.points IS NOT NULL RETURN count(p) as count")
            procedures_with_points = result.single()['count']

            # 샘플 데이터
            result = session.run("""
                MATCH (p:Procedure)
                RETURN p.edi_code as code, p.name as name, p.points as points
                LIMIT 10
            """)
            samples = list(result)

            print(f"\nVerification results:")
            print(f"  Total Procedure nodes: {total_procedures}")
            print(f"  Procedures with points: {procedures_with_points} ({procedures_with_points/total_procedures*100:.1f}%)")
            print(f"\nSample procedures:")
            for i, sample in enumerate(samples, 1):
                code = sample['code']
                name = sample['name'][:50] if sample['name'] else ''
                points = sample['points']
                print(f"    {i}. {code}: {name}... (points: {points})")

    def save_integration_report(self, output_dir: Path):
        """통합 리포트 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"procedure_integration_report_{timestamp}.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'errors': self.errors[:100]  # 처음 100개 에러만 저장
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\nIntegration report saved: {report_file}")

        # 통계 출력
        print("\n" + "="*80)
        print("INTEGRATION STATISTICS")
        print("="*80)
        print(f"Total procedures:     {self.stats['total_procedures']}")
        print(f"Created nodes:        {self.stats['created_nodes']}")
        print(f"Updated nodes:        {self.stats['skipped_existing']}")
        print(f"Errors:               {self.stats['errors']}")
        print("="*80)


def main():
    """메인 실행"""
    # 최신 파싱 결과 파일 찾기
    parsed_dir = Path("data/hira/parsed")
    json_files = list(parsed_dir.glob("suga_procedures_*.json"))

    if not json_files:
        print("Error: No parsed procedure files found!")
        return

    # 가장 최근 파일 선택
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"Using latest file: {latest_file}")

    # 통합 실행
    integrator = ProcedureIntegrator()

    try:
        # 1. 제약조건 생성
        integrator.create_constraints()

        # 2. Procedure 데이터 로드
        procedures = integrator.load_procedures(latest_file)

        # 3. Neo4j 통합
        integrator.integrate_procedures(procedures)

        # 4. 검증
        integrator.verify_integration()

        # 5. 리포트 저장
        integrator.save_integration_report(parsed_dir)

    finally:
        integrator.close()

    print("\nAll done!")


if __name__ == "__main__":
    main()
