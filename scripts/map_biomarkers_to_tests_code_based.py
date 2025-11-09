"""
Phase 3: 바이오마커-검사 매핑 (코드 기반)

LOINC/SNOMED CT 표준 코드를 기반으로 바이오마커와 검사를 매핑합니다.
문자열 매칭은 보조 수단으로만 사용합니다.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
BRIDGES_DIR = PROJECT_ROOT / "bridges"
DATA_DIR = PROJECT_ROOT / "data" / "hins"
PARSED_DIR = DATA_DIR / "parsed"

INPUT_BIOMARKERS = BRIDGES_DIR / "biomarkers_extracted_v2.json"
INPUT_CODE_MAPPING = BRIDGES_DIR / "biomarker_code_mapping.json"
INPUT_HINS_EXCEL = DATA_DIR / "downloads" / "edi" / "2장_19_20용어매핑테이블(검사)_(심평원코드-SNOMED_CT).xlsx"
INPUT_EXISTING_TESTS = PARSED_DIR / "biomarker_tests_structured.json"  # 기존 Test 노드
OUTPUT_FILE = BRIDGES_DIR / "biomarker_test_mappings_v2_code_based.json"


class CodeBasedMapper:
    """코드 기반 바이오마커-검사 매핑"""

    # 범용 SNOMED CT 코드 (제외 대상)
    GENERIC_SNOMED_CODES = {
        '414464004',  # Immunohistochemistry procedure (범용 IHC)
        '117617002',  # Immunohistochemistry staining method (범용 IHC 염색)
        '127798001',  # Laboratory procedure (범용 검사 procedure)
    }

    def __init__(self):
        self.biomarkers = []
        self.code_mapping = {}
        self.edi_tests = None
        self.existing_tests = []  # Neo4j에 있는 실제 Test 노드
        self.edi_to_test_id = {}  # EDI 코드 -> test_id 매핑
        self.mappings = []
        self.stats = defaultdict(int)

    def load_data(self):
        """데이터 로드"""
        print("="*70)
        print("코드 기반 바이오마커-검사 매핑")
        print("="*70)

        print("\n[INFO] 데이터 로딩...")

        # 바이오마커 로드 (v2.0)
        with open(INPUT_BIOMARKERS, 'r', encoding='utf-8') as f:
            biomarker_data = json.load(f)
            self.biomarkers = biomarker_data['biomarkers']

        # 바이오마커 코드 매핑 로드
        with open(INPUT_CODE_MAPPING, 'r', encoding='utf-8') as f:
            code_data = json.load(f)
            self.code_mapping = code_data['biomarker_codes']

        # 기존 Test 노드 로드 (Neo4j에 실제로 있는 575개)
        with open(INPUT_EXISTING_TESTS, 'r', encoding='utf-8') as f:
            tests_data = json.load(f)
            self.existing_tests = tests_data['tests']
            # EDI 코드로 인덱싱
            for test in self.existing_tests:
                edi_code = test.get('edi_code')
                if edi_code:
                    self.edi_to_test_id[edi_code] = test['test_id']

        # HINS EDI 검사 데이터 로드 (코드 매칭용)
        self.edi_tests = pd.read_excel(INPUT_HINS_EXCEL)

        print(f"[OK] 바이오마커: {len(self.biomarkers)}개")
        print(f"[OK] 코드 매핑: {len(self.code_mapping)}개")
        print(f"[OK] 기존 Test 노드: {len(self.existing_tests)}개")
        print(f"[OK] EDI 검사 (코드 매칭용): {len(self.edi_tests):,}개")

    def match_by_codes(self, biomarker_name, test_row):
        """코드 기반 매칭"""
        if biomarker_name not in self.code_mapping:
            return None

        codes = self.code_mapping[biomarker_name]
        loinc_codes = set(codes['loinc_codes'])
        snomed_codes = set(codes['snomed_codes'])

        # LOINC 매칭 (1순위)
        test_loinc = str(test_row.get('loinc_icd_id', ''))
        if test_loinc != 'nan' and test_loinc in loinc_codes:
            return {
                'match_type': 'loinc_code',
                'confidence': 0.98,
                'matched_code': test_loinc
            }

        # SNOMED CT 매칭 (2순위) - 범용 코드 제외
        test_snomed_pre = str(test_row.get('pre_ct_id', ''))
        test_snomed_post = str(test_row.get('post_ct_id', ''))

        if test_snomed_pre != 'nan' and test_snomed_pre in snomed_codes:
            # 범용 코드 제외
            if test_snomed_pre not in self.GENERIC_SNOMED_CODES:
                return {
                    'match_type': 'snomed_code_pre',
                    'confidence': 0.95,
                    'matched_code': test_snomed_pre
                }

        if test_snomed_post != 'nan' and test_snomed_post in snomed_codes:
            # 범용 코드 제외
            if test_snomed_post not in self.GENERIC_SNOMED_CODES:
                return {
                    'match_type': 'snomed_code_post',
                    'confidence': 0.93,
                    'matched_code': test_snomed_post
                }

        return None

    def match_by_keyword(self, biomarker_name, test_row):
        """키워드 매칭 비활성화 - 100% 순수 코드 기반 매핑만 사용"""
        # 사용자 요구사항: "바이오 마커를 포함한 전체 매핑은 모두 코드로만 한다"
        return None

    def create_mappings(self):
        """매핑 생성"""
        print("\n[INFO] 코드 기반 매핑 생성 중...")

        for biomarker in self.biomarkers:
            biomarker_id = biomarker['biomarker_id']
            biomarker_name_en = biomarker['biomarker_name_en']
            biomarker_name_ko = biomarker['biomarker_name_ko']

            matched_tests = []

            for idx, test_row in self.edi_tests.iterrows():
                # 코드 기반 매칭 시도
                match_result = self.match_by_codes(biomarker_name_en, test_row)

                # 코드 매칭 실패 시 키워드 매칭 (백업)
                if not match_result:
                    match_result = self.match_by_keyword(biomarker_name_en, test_row)

                if match_result:
                    # EDI 코드로 기존 Test 노드의 test_id 찾기
                    edi_code = str(test_row.get('term_cd', ''))
                    test_id = self.edi_to_test_id.get(edi_code)

                    # 기존 Test 노드에 없는 경우 스킵
                    if not test_id:
                        continue

                    test_info = {
                        'test_id': test_id,  # 기존 Test 노드의 test_id 사용
                        'edi_code': edi_code,
                        'test_name_ko': str(test_row.get('term_kr', '')),
                        'test_name_en': str(test_row.get('term_en', '')),
                        'loinc_code': str(test_row.get('loinc_icd_id', '')) if pd.notna(test_row.get('loinc_icd_id')) else None,
                        'snomed_ct_id': str(test_row.get('pre_ct_id', '')) if pd.notna(test_row.get('pre_ct_id')) else str(test_row.get('post_ct_id', '')) if pd.notna(test_row.get('post_ct_id')) else None,
                        'match_type': match_result['match_type'],
                        'confidence': match_result['confidence'],
                    }

                    if 'matched_code' in match_result:
                        test_info['matched_code'] = match_result['matched_code']
                    if 'matched_keyword' in match_result:
                        test_info['matched_keyword'] = match_result['matched_keyword']

                    matched_tests.append(test_info)
                    self.stats[match_result['match_type']] += 1

            if matched_tests:
                self.mappings.append({
                    'biomarker_id': biomarker_id,
                    'biomarker_name_en': biomarker_name_en,
                    'biomarker_name_ko': biomarker_name_ko,
                    'biomarker_type': biomarker['biomarker_type'],
                    'test_count': len(matched_tests),
                    'tests': matched_tests
                })

                print(f"[OK] {biomarker_name_en} ({biomarker_name_ko}): {len(matched_tests)}개 검사 매핑")

    def save_results(self):
        """결과 저장"""
        print("\n[INFO] 결과 저장 중...")

        # 통계 계산
        total_biomarkers = len(self.mappings)
        total_relationships = sum(m['test_count'] for m in self.mappings)

        output_data = {
            'metadata': {
                'creation_date': datetime.now().isoformat(),
                'source_biomarkers': 'biomarkers_extracted_v2.json',
                'source_code_mapping': 'biomarker_code_mapping.json',
                'source_edi_tests': INPUT_HINS_EXCEL.name,
                'total_biomarkers_with_tests': total_biomarkers,
                'total_relationships': total_relationships,
                'match_statistics': dict(self.stats),
                'version': '2.0_code_based'
            },
            'mappings': self.mappings
        }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"[OK] 결과 저장: {OUTPUT_FILE}")

        # 통계 출력
        print("\n" + "="*70)
        print("매핑 통계")
        print("="*70)
        print(f"매핑된 바이오마커: {total_biomarkers}개")
        print(f"총 관계: {total_relationships}개")
        print(f"\n매칭 타입별:")
        for match_type, count in sorted(self.stats.items(), key=lambda x: x[1], reverse=True):
            pct = count / total_relationships * 100 if total_relationships > 0 else 0
            print(f"  {match_type}: {count}개 ({pct:.1f}%)")

    def run(self):
        """실행"""
        self.load_data()
        self.create_mappings()
        self.save_results()
        print("\n[SUCCESS] 코드 기반 매핑 완료!")


if __name__ == "__main__":
    mapper = CodeBasedMapper()
    mapper.run()
