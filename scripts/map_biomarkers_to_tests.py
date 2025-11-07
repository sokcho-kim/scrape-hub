"""
Phase 3: 바이오마커-검사 매핑

Phase 1에서 추출한 바이오마커와 Phase 2에서 파싱한 HINS 검사를
매핑하여 Neo4j 통합을 위한 관계 데이터를 생성합니다.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
BRIDGES_DIR = PROJECT_ROOT / "bridges"
DATA_DIR = PROJECT_ROOT / "data" / "hins" / "parsed"

INPUT_BIOMARKERS = BRIDGES_DIR / "biomarkers_extracted.json"
INPUT_TESTS = DATA_DIR / "biomarker_tests_structured.json"
OUTPUT_FILE = BRIDGES_DIR / "biomarker_test_mappings.json"


class BiomarkerTestMapper:
    """바이오마커-검사 매핑 클래스"""

    def __init__(self):
        self.biomarkers = []
        self.tests = []
        self.mappings = []
        self.stats = defaultdict(int)

    def load_data(self):
        """데이터 로드"""
        print("[INFO] 데이터 로딩...")

        # 바이오마커 로드
        with open(INPUT_BIOMARKERS, 'r', encoding='utf-8') as f:
            biomarker_data = json.load(f)
            self.biomarkers = biomarker_data['biomarkers']

        # 검사 로드
        with open(INPUT_TESTS, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
            self.tests = test_data['tests']

        print(f"[OK] 바이오마커: {len(self.biomarkers)}개")
        print(f"[OK] 검사: {len(self.tests)}개")

    def normalize_biomarker_name(self, name):
        """바이오마커명 정규화"""
        if not name:
            return None

        # 대문자 변환
        name = name.upper()

        # 공통 변형 처리
        normalization_map = {
            'HER-2': 'HER2',
            'K-RAS': 'KRAS',
            'B-RAF': 'BRAF',
            'ROS-1': 'ROS1',
            'PD-1': 'PD1',
            'PD-L1': 'PDL1',
            'CTLA-4': 'CTLA4',
            'C-MET': 'MET',
        }

        for old, new in normalization_map.items():
            if old in name:
                name = name.replace(old, new)

        return name.strip()

    def match_biomarker_to_test(self, biomarker, test):
        """바이오마커와 검사 매칭"""
        biomarker_name_en = self.normalize_biomarker_name(biomarker['biomarker_name_en'])
        test_biomarker_name = self.normalize_biomarker_name(test['biomarker_name'])

        # 직접 매칭
        if biomarker_name_en == test_biomarker_name:
            return {
                'match_type': 'exact_match',
                'confidence': 0.95
            }

        # 부분 매칭 (BCR-ABL 같은 경우)
        if biomarker_name_en and test_biomarker_name:
            if biomarker_name_en in test_biomarker_name or test_biomarker_name in biomarker_name_en:
                return {
                    'match_type': 'partial_match',
                    'confidence': 0.85
                }

        # CDK4/6 같은 복합 바이오마커
        if '/' in biomarker_name_en:
            parts = biomarker_name_en.split('/')
            if any(part in test_biomarker_name for part in parts):
                return {
                    'match_type': 'composite_match',
                    'confidence': 0.80
                }

        return None

    def create_mappings(self):
        """매핑 생성"""
        print("\n[INFO] 바이오마커-검사 매핑 생성 중...")

        mapping_id = 1

        for biomarker in self.biomarkers:
            biomarker_id = biomarker['biomarker_id']
            biomarker_name = biomarker['biomarker_name_en']

            matched_tests = []

            for test in self.tests:
                match_result = self.match_biomarker_to_test(biomarker, test)

                if match_result:
                    matched_tests.append({
                        'test_id': test['test_id'],
                        'edi_code': test['edi_code'],
                        'test_name_ko': test['test_name_ko'],
                        'test_category': test['test_category'],
                        'match_type': match_result['match_type'],
                        'confidence': match_result['confidence']
                    })

                    self.stats[match_result['match_type']] += 1

            if matched_tests:
                mapping_entry = {
                    'mapping_id': f"MAPPING_{mapping_id:03d}",
                    'biomarker_id': biomarker_id,
                    'biomarker_name_en': biomarker_name,
                    'biomarker_name_ko': biomarker['biomarker_name_ko'],
                    'biomarker_type': biomarker['biomarker_type'],
                    'matched_tests': matched_tests,
                    'test_count': len(matched_tests),
                    'related_drugs_count': biomarker['drug_count'],
                    'created_at': datetime.now().isoformat()
                }

                self.mappings.append(mapping_entry)
                mapping_id += 1

        print(f"[OK] {len(self.mappings)}개 바이오마커 매핑 완료")
        print(f"[OK] 총 {sum(m['test_count'] for m in self.mappings)}개 관계 생성")

    def save_results(self):
        """결과 저장"""
        print("\n[INFO] 결과 저장 중...")

        output_data = {
            'metadata': {
                'creation_date': datetime.now().isoformat(),
                'source_biomarkers': str(INPUT_BIOMARKERS.name),
                'source_tests': str(INPUT_TESTS.name),
                'total_biomarkers_with_tests': len(self.mappings),
                'total_relationships': sum(m['test_count'] for m in self.mappings),
                'match_statistics': dict(self.stats),
                'version': '1.0'
            },
            'mappings': self.mappings
        }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        file_size_kb = OUTPUT_FILE.stat().st_size / 1024

        print(f"[SAVED] {OUTPUT_FILE}")
        print(f"        크기: {file_size_kb:.1f} KB")

    def print_summary(self):
        """요약 출력"""
        print("\n" + "=" * 70)
        print("바이오마커-검사 매핑 완료")
        print("=" * 70)

        print(f"\n총 매핑: {len(self.mappings)}개 바이오마커")
        print(f"총 관계: {sum(m['test_count'] for m in self.mappings)}개")

        # 매칭 타입별 통계
        print("\n매칭 타입별 통계:")
        for match_type, count in sorted(self.stats.items(), key=lambda x: -x[1]):
            print(f"  - {match_type}: {count}건")

        # 검사가 가장 많은 바이오마커 상위 5개
        top5 = sorted(self.mappings, key=lambda x: x['test_count'], reverse=True)[:5]

        print("\n상위 5개 바이오마커 (검사 수):")
        for i, mapping in enumerate(top5, 1):
            print(f"  {i}. {mapping['biomarker_name_ko']} ({mapping['biomarker_name_en']})")
            print(f"     - 검사: {mapping['test_count']}개")
            print(f"     - 관련 약물: {mapping['related_drugs_count']}개")

        # Neo4j 관계 미리보기
        print("\nNeo4j 관계 예시:")
        if self.mappings:
            sample = self.mappings[0]
            print(f"  (:Biomarker {{id: '{sample['biomarker_id']}', name: '{sample['biomarker_name_en']}'}})")
            if sample['matched_tests']:
                test = sample['matched_tests'][0]
                print(f"    -[:TESTED_BY {{confidence: {test['confidence']}, match_type: '{test['match_type']}'}}]->")
                print(f"  (:Test {{id: '{test['test_id']}', edi_code: '{test['edi_code']}'}})")

        print("\n" + "=" * 70)

    def run(self):
        """전체 프로세스 실행"""
        print("=" * 70)
        print("Phase 3: 바이오마커-검사 매핑")
        print("=" * 70)

        self.load_data()
        self.create_mappings()
        self.save_results()
        self.print_summary()

        return True


def main():
    """메인 실행"""
    mapper = BiomarkerTestMapper()

    try:
        success = mapper.run()

        if success:
            print("\n[SUCCESS] Phase 3 완료!")
            print(f"출력 파일: {OUTPUT_FILE}")
            return 0
        else:
            print("\n[ERROR] Phase 3 실패")
            return 1

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
