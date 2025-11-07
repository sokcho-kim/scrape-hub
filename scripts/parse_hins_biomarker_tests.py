"""
Phase 2: HINS EDI 검사 데이터 파싱 (코드 기반 개선 버전)

LOINC/SNOMED CT 코드를 우선 사용하여 바이오마커 검사를 정확하게 추출합니다.
"""

import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
from collections import defaultdict


# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "hins"
INPUT_FILE = DATA_DIR / "downloads" / "edi" / "2장_19_20용어매핑테이블(검사)_(심평원코드-SNOMED_CT).xlsx"
OUTPUT_DIR = DATA_DIR / "parsed"
OUTPUT_FILE = OUTPUT_DIR / "biomarker_tests_structured.json"


# 바이오마커별 LOINC 코드 (국제 표준)
BIOMARKER_LOINC_CODES = {
    'HER2': {
        'codes': ['48675-3', '31150-6', '74860-8', '72383-3', '85319-2'],
        'korean': 'HER2',
        'type': 'protein'
    },
    'PD-L1': {
        'codes': ['83052-1', '83054-7', '83053-9'],
        'korean': 'PD-L1',
        'type': 'protein'
    },
    'KRAS': {
        'codes': ['82535-6', '53930-6'],
        'korean': 'KRAS',
        'type': 'mutation'
    },
    'BRAF': {
        'codes': ['53844-7', '85101-4', '58415-1'],
        'korean': 'BRAF',
        'type': 'mutation'
    },
    'EGFR': {
        'codes': ['54471-8', '50926-7'],
        'korean': 'EGFR',
        'type': 'mutation'
    },
}

# 바이오마커별 SNOMED CT 코드
BIOMARKER_SNOMED_CODES = {
    'HER2': {
        'codes': ['414464004', '433114000'],
        'korean': 'HER2',
        'type': 'protein'
    },
    'PD-L1': {
        'codes': ['117617002', '127798001'],
        'korean': 'PD-L1',
        'type': 'protein'
    },
    'BRCA1': {
        'codes': ['405823003'],
        'korean': 'BRCA1',
        'type': 'mutation'
    },
    'BRCA2': {
        'codes': ['405826006'],
        'korean': 'BRCA2',
        'type': 'mutation'
    },
    'ALK': {
        'codes': ['117617002', '127798001'],  # IHC procedure
        'korean': 'ALK',
        'type': 'fusion_gene'
    },
    'ROS1': {
        'codes': ['9718006'],
        'korean': 'ROS1',
        'type': 'fusion_gene'
    },
}

# 바이오마커 키워드 (백업용 - 문자열 매칭)
BIOMARKER_KEYWORDS = {
    'HER2': ['HER2', 'HER-2', 'ERBB2'],
    'EGFR': ['EGFR'],
    'ALK': ['ALK'],
    'ROS1': ['ROS1', 'ROS-1'],
    'BCR-ABL': ['BCR-ABL', 'BCR ABL'],
    'NTRK': ['NTRK', 'NTRK1', 'NTRK2', 'NTRK3'],
    'BRAF': ['BRAF'],
    'KRAS': ['KRAS', 'K-RAS'],
    'BRCA1': ['BRCA1'],
    'BRCA2': ['BRCA2'],
    'PD-L1': ['PD-L1', 'PDL1'],
    'FLT3': ['FLT3'],
    'IDH1': ['IDH1'],
    'IDH2': ['IDH2'],
}

# 검사 키워드 (유전자검사 필수)
GENE_TEST_KEYWORDS = [
    '유전자검사',
    '면역조직화학검사',
    '면역세포화학검사',
    '염기서열',
    '돌연변이',
    'Gene',
    'mutation'
]


class HINSTestParser:
    """HINS 검사 데이터 파서 (코드 기반)"""

    def __init__(self):
        self.df = None
        self.biomarker_tests = []
        self.match_stats = defaultdict(int)

    def load_data(self):
        """Excel 파일 로드"""
        print("[INFO] HINS EDI 검사 파일 로딩...")

        if not INPUT_FILE.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {INPUT_FILE}")

        self.df = pd.read_excel(INPUT_FILE)

        print(f"[OK] {len(self.df):,}개 검사 항목 로드 완료")

    def match_biomarker_by_loinc(self, loinc_code):
        """LOINC 코드로 바이오마커 매칭 (1순위)"""
        if pd.isna(loinc_code):
            return None

        loinc_str = str(loinc_code)

        for biomarker, info in BIOMARKER_LOINC_CODES.items():
            for code in info['codes']:
                if code in loinc_str:
                    self.match_stats['loinc'] += 1
                    return biomarker

        return None

    def match_biomarker_by_snomed(self, snomed_code):
        """SNOMED CT 코드로 바이오마커 매칭 (2순위)"""
        if pd.isna(snomed_code):
            return None

        snomed_str = str(int(snomed_code)) if isinstance(snomed_code, float) else str(snomed_code)

        for biomarker, info in BIOMARKER_SNOMED_CODES.items():
            if snomed_str in info['codes']:
                self.match_stats['snomed'] += 1
                return biomarker

        return None

    def match_biomarker_by_keyword(self, test_name):
        """키워드로 바이오마커 매칭 (3순위 - 백업)"""
        if not test_name:
            return None

        # 유전자검사 키워드 필수
        has_gene_test = any(kw in test_name for kw in GENE_TEST_KEYWORDS)
        if not has_gene_test:
            return None

        # 바이오마커 키워드 확인
        test_upper = test_name.upper()
        for biomarker, keywords in BIOMARKER_KEYWORDS.items():
            for keyword in keywords:
                if keyword in test_upper:
                    self.match_stats['keyword'] += 1
                    return biomarker

        return None

    def filter_biomarker_tests(self):
        """바이오마커 관련 검사 필터링 (코드 우선)"""
        print("\n[INFO] 바이오마커 검사 필터링 (LOINC → SNOMED CT → 키워드)...")

        filtered_rows = []

        for idx, row in self.df.iterrows():
            loinc_code = row.get('loinc_icd_id')
            snomed_code = row.get('pre_ct_id')
            test_name_ko = str(row.get('term_kr', ''))

            # 1순위: LOINC 코드 매칭
            biomarker = self.match_biomarker_by_loinc(loinc_code)

            # 2순위: SNOMED CT 코드 매칭
            if not biomarker:
                biomarker = self.match_biomarker_by_snomed(snomed_code)

            # 3순위: 키워드 매칭 (백업)
            if not biomarker:
                biomarker = self.match_biomarker_by_keyword(test_name_ko)

            if biomarker:
                filtered_rows.append({
                    'index': idx,
                    'row': row,
                    'biomarker_keyword': biomarker
                })

        print(f"[OK] {len(filtered_rows)}개 검사 필터링 완료")
        print(f"[STATS] 매칭 방법:")
        print(f"  - LOINC 코드: {self.match_stats['loinc']}건")
        print(f"  - SNOMED CT 코드: {self.match_stats['snomed']}건")
        print(f"  - 키워드 매칭: {self.match_stats['keyword']}건")

        return filtered_rows

    def extract_biomarker_name(self, test_name):
        """검사명에서 바이오마커명 추출"""

        # 1. 대괄호 안 추출: [HER2 Gene] → HER2
        bracket_match = re.search(r'\[([A-Z0-9-/]+)(?:\s+Gene)?\]', test_name)
        if bracket_match:
            biomarker = bracket_match.group(1)
            biomarker = biomarker.replace(' Gene', '').replace('Gene', '').strip()
            return biomarker

        # 2. 언더스코어 뒤 추출: _PD-L1 → PD-L1
        underscore_match = re.search(r'_([A-Z0-9-/]+)$', test_name)
        if underscore_match:
            return underscore_match.group(1)

        # 3. 키워드 직접 매칭
        test_upper = test_name.upper()
        for biomarker, keywords in BIOMARKER_KEYWORDS.items():
            for keyword in keywords:
                if keyword.upper() in test_upper:
                    return biomarker

        return None

    def classify_test_category(self, test_name):
        """검사 카테고리 분류"""
        TEST_CATEGORY_PATTERNS = {
            '면역조직화학검사': ['면역조직', '면역세포화학', 'IHC', 'Immunohistochemistry'],
            '유전자염기서열검사': ['염기서열분석', 'sequencing'],
            '형광동소부합법': ['FISH', 'fluorescence in situ'],
            '교잡법': ['교잡법', 'Hybridization'],
        }

        for category, patterns in TEST_CATEGORY_PATTERNS.items():
            if any(pattern in test_name for pattern in patterns):
                return category
        return '기타'

    def parse_tests(self, filtered_rows):
        """검사 데이터 파싱"""
        print("\n[INFO] 검사 데이터 파싱 중...")

        test_id = 1

        for item in filtered_rows:
            row = item['row']

            # 기본 정보
            edi_code = str(row.get('term_cd', ''))
            test_name_ko = str(row.get('term_kr', ''))
            test_name_en = str(row.get('term_en', ''))

            # 표준 코드 정보
            loinc_code = str(row.get('loinc_icd_id', ''))
            snomed_ct_id = str(row.get('pre_ct_id', ''))
            snomed_ct_name = str(row.get('pre_ct_cn', ''))

            # 'nan' 문자열 처리
            if loinc_code == 'nan' or not loinc_code:
                loinc_code = None
            if snomed_ct_id == 'nan' or not snomed_ct_id:
                snomed_ct_id = None
            if snomed_ct_name == 'nan' or not snomed_ct_name:
                snomed_ct_name = None

            # 바이오마커명 추출
            biomarker_name = self.extract_biomarker_name(test_name_ko)
            if not biomarker_name:
                biomarker_name = item.get('biomarker_keyword')

            # 검사 카테고리 분류
            test_category = self.classify_test_category(test_name_ko)

            # 검사 항목 생성
            test_entry = {
                'test_id': f"HINS_TEST_{test_id:03d}",
                'edi_code': edi_code,
                'test_name_ko': test_name_ko,
                'test_name_en': test_name_en if test_name_en != 'nan' else None,
                'biomarker_name': biomarker_name,
                'test_category': test_category,
                'loinc_code': loinc_code,
                'snomed_ct_id': snomed_ct_id,
                'snomed_ct_name': snomed_ct_name,
                'reference_year': 2020,
                'data_source': 'HINS_EDI',
                'created_at': datetime.now().isoformat()
            }

            self.biomarker_tests.append(test_entry)
            test_id += 1

        print(f"[OK] {len(self.biomarker_tests)}개 검사 파싱 완료")

    def save_results(self):
        """결과 저장"""
        print("\n[INFO] 결과 저장 중...")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        output_data = {
            'metadata': {
                'parse_date': datetime.now().isoformat(),
                'source_file': str(INPUT_FILE.name),
                'total_tests': len(self.biomarker_tests),
                'reference_year': 2020,
                'data_source': 'HINS_EDI',
                'version': '2.0_code_based',
                'matching_methods': {
                    'loinc': self.match_stats['loinc'],
                    'snomed': self.match_stats['snomed'],
                    'keyword': self.match_stats['keyword']
                }
            },
            'tests': self.biomarker_tests
        }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        file_size_kb = OUTPUT_FILE.stat().st_size / 1024

        print(f"[SAVED] {OUTPUT_FILE}")
        print(f"        크기: {file_size_kb:.1f} KB")

    def print_statistics(self):
        """통계 출력"""
        print("\n" + "=" * 70)
        print("HINS 검사 데이터 파싱 완료 (코드 기반)")
        print("=" * 70)

        print(f"\n총 검사: {len(self.biomarker_tests)}개")

        # 매칭 방법별 통계
        print(f"\n매칭 방법별 통계:")
        print(f"  - LOINC 코드: {self.match_stats['loinc']}건 ({self.match_stats['loinc']/len(self.biomarker_tests)*100:.1f}%)")
        print(f"  - SNOMED CT 코드: {self.match_stats['snomed']}건 ({self.match_stats['snomed']/len(self.biomarker_tests)*100:.1f}%)")
        print(f"  - 키워드 매칭: {self.match_stats['keyword']}건 ({self.match_stats['keyword']/len(self.biomarker_tests)*100:.1f}%)")

        # 표준 코드 커버리지
        with_loinc = sum(1 for t in self.biomarker_tests if t['loinc_code'])
        with_snomed = sum(1 for t in self.biomarker_tests if t['snomed_ct_id'])

        print(f"\n표준 코드 커버리지:")
        print(f"  - LOINC: {with_loinc}개 ({with_loinc/len(self.biomarker_tests)*100:.1f}%)")
        print(f"  - SNOMED CT: {with_snomed}개 ({with_snomed/len(self.biomarker_tests)*100:.1f}%)")

        # 바이오마커별 통계
        biomarker_counts = defaultdict(int)
        for test in self.biomarker_tests:
            bm = test['biomarker_name']
            if bm:
                biomarker_counts[bm] += 1

        print("\n바이오마커별 검사 수 (상위 10개):")
        for i, (bm, count) in enumerate(sorted(biomarker_counts.items(), key=lambda x: -x[1])[:10], 1):
            print(f"  {i}. {bm}: {count}개")

        print("\n" + "=" * 70)

    def run(self):
        """전체 프로세스 실행"""
        print("=" * 70)
        print("Phase 2: HINS EDI 검사 데이터 파싱 (코드 기반 개선)")
        print("=" * 70)

        self.load_data()
        filtered_rows = self.filter_biomarker_tests()
        self.parse_tests(filtered_rows)
        self.save_results()
        self.print_statistics()

        return True


def main():
    """메인 실행"""
    parser = HINSTestParser()

    try:
        success = parser.run()

        if success:
            print("\n[SUCCESS] Phase 2 완료!")
            print(f"출력 파일: {OUTPUT_FILE}")
            return 0
        else:
            print("\n[ERROR] Phase 2 실패")
            return 1

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
