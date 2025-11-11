"""
통합 실행 스크립트: Phase 1-8 전체 실행

모든 코드 시스템을 Neo4j에 통합합니다.
- Phase 1-4: Biomarker-Test-Drug (기존)
- Phase 5: Disease 노드 (KCD)
- Phase 6: Procedure 노드 (KDRG)
- Phase 7: Cancer 노드 및 관계
- Phase 8: 표준 코드 통합 (SNOMED, LOINC)
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "neo4j" / "scripts"


class IntegratedRunner:
    """통합 실행 클래스"""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_script(self, script_name, phase_name):
        """개별 스크립트 실행"""
        print("\n" + "=" * 70)
        print(f"{phase_name}")
        print("=" * 70)

        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            print(f"[ERROR] 스크립트 파일을 찾을 수 없습니다: {script_path}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            print(result.stdout)
            if result.stderr:
                print(f"[STDERR]\n{result.stderr}")

            success = result.returncode == 0
            self.results[phase_name] = {
                'success': success,
                'returncode': result.returncode
            }

            if success:
                print(f"\n[OK] {phase_name} 완료!")
            else:
                print(f"\n[ERROR] {phase_name} 실패! (exit code: {result.returncode})")

            return success

        except Exception as e:
            print(f"\n[ERROR] {phase_name} 실행 중 오류 발생: {e}")
            self.results[phase_name] = {
                'success': False,
                'error': str(e)
            }
            return False

    def run(self, start_from_phase=1, clear_existing=False):
        """전체 통합 프로세스 실행"""
        self.start_time = datetime.now()

        print("=" * 70)
        print("통합 의료 지식그래프 구축")
        print(f"시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Phase 정의
        phases = [
            (1, "integrate_to_neo4j.py", "Phase 1-4: Biomarker-Test-Drug (기존)"),
            (5, "import_diseases.py", "Phase 5: Disease 노드 생성 (KCD 54,125개)"),
            (6, "import_procedures.py", "Phase 6: Procedure 노드 생성 (KDRG 1,487개)"),
            (7, "import_cancers.py", "Phase 7: Cancer 노드 및 관계 생성"),
        ]

        # 실행
        for phase_num, script, phase_name in phases:
            if phase_num < start_from_phase:
                print(f"\n[SKIP] {phase_name} (Phase {phase_num} < {start_from_phase})")
                continue

            success = self.run_script(script, phase_name)

            if not success:
                print(f"\n[STOP] {phase_name} 실패로 중단합니다.")
                break

        self.end_time = datetime.now()
        self.print_summary()

    def print_summary(self):
        """결과 요약 출력"""
        print("\n" + "=" * 70)
        print("통합 실행 결과 요약")
        print("=" * 70)

        total = len(self.results)
        success_count = sum(1 for r in self.results.values() if r['success'])

        print(f"\n총 Phase: {total}개")
        print(f"성공: {success_count}개")
        print(f"실패: {total - success_count}개")

        print("\n상세 결과:")
        for phase_name, result in self.results.items():
            status = "✅ 성공" if result['success'] else "❌ 실패"
            print(f"  {status}  {phase_name}")

        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"\n소요 시간: {duration:.1f}초 ({duration/60:.1f}분)")

        print("\n" + "=" * 70)

        if success_count == total:
            print("🎉 모든 Phase가 성공적으로 완료되었습니다!")
            print("\nNeo4j Browser에서 확인:")
            print("  http://localhost:7474")
            print("\n샘플 쿼리:")
            print("""
  // 전체 노드 통계
  MATCH (n)
  RETURN labels(n) as NodeType, count(n) as Count
  ORDER BY Count DESC

  // HER2 양성 유방암 약물 조회
  MATCH (d:Disease)-[:CANCER_TYPE]->(c:Cancer {name_kr: '유방암'})
        -[:HAS_BIOMARKER]->(b:Biomarker {name_en: 'HER2'})
        <-[:TARGETS]-(drug:Drug)
  MATCH (b)-[:TESTED_BY]->(t:Test)
  RETURN drug.ingredient_ko AS 약물,
         t.name_ko AS 필요검사,
         t.edi_code AS EDI코드
  LIMIT 10
            """)
        else:
            print("⚠️  일부 Phase가 실패했습니다. 로그를 확인하세요.")

        print("=" * 70)


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='통합 의료 지식그래프 구축')
    parser.add_argument('--start-from', type=int, default=1,
                        help='시작 Phase 번호 (기본: 1)')
    parser.add_argument('--clear-db', action='store_true',
                        help='기존 데이터베이스 초기화')
    args = parser.parse_args()

    runner = IntegratedRunner()
    runner.run(start_from_phase=args.start_from, clear_existing=args.clear_db)

    # 반환 코드
    all_success = all(r['success'] for r in runner.results.values())
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
