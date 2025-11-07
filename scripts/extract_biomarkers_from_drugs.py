"""
Phase 1: 항암제 사전에서 바이오마커 추출

항암제 154개의 mechanism_of_action과 ATC 분류에서
바이오마커 정보를 추출합니다.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime


# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
BRIDGES_DIR = PROJECT_ROOT / "bridges"
INPUT_FILE = BRIDGES_DIR / "anticancer_master_classified.json"
OUTPUT_FILE = BRIDGES_DIR / "biomarkers_extracted.json"


# 바이오마커 패턴 사전
BIOMARKER_PATTERNS = {
    # 티로신 키나제 수용체
    'HER2': {
        'keywords': ['HER2', 'HER-2', 'ERBB2'],
        'type': 'protein',
        'gene': 'ERBB2',
        'korean': 'HER2 수용체',
        'cancer_types': ['유방암', '위암']
    },
    'EGFR': {
        'keywords': ['EGFR'],
        'type': 'protein',
        'gene': 'EGFR',
        'korean': 'EGFR 수용체',
        'cancer_types': ['폐암']
    },
    'VEGF': {
        'keywords': ['VEGF', 'VEGFR'],
        'type': 'protein',
        'gene': 'VEGFA',
        'korean': 'VEGF 수용체',
        'cancer_types': ['대장암', '폐암', '신장암']
    },

    # 융합 유전자 / 전좌
    'ALK': {
        'keywords': ['ALK'],
        'type': 'fusion_gene',
        'gene': 'ALK',
        'korean': 'ALK 융합 유전자',
        'cancer_types': ['폐암']
    },
    'ROS1': {
        'keywords': ['ROS1', 'ROS-1'],
        'type': 'fusion_gene',
        'gene': 'ROS1',
        'korean': 'ROS1 융합 유전자',
        'cancer_types': ['폐암']
    },
    'BCR-ABL': {
        'keywords': ['BCR-ABL', 'BCR ABL', 'BCRABL'],
        'type': 'fusion_gene',
        'gene': 'BCR-ABL1',
        'korean': 'BCR-ABL 융합 유전자',
        'cancer_types': ['만성골수성백혈병']
    },
    'NTRK': {
        'keywords': ['NTRK', 'NTRK1', 'NTRK2', 'NTRK3'],
        'type': 'fusion_gene',
        'gene': 'NTRK',
        'korean': 'NTRK 융합 유전자',
        'cancer_types': ['범종양']
    },

    # 돌연변이
    'BRAF': {
        'keywords': ['BRAF', 'B-RAF'],
        'type': 'mutation',
        'gene': 'BRAF',
        'korean': 'BRAF 돌연변이',
        'cancer_types': ['흑색종', '대장암', '갑상선암']
    },
    'KRAS': {
        'keywords': ['KRAS', 'K-RAS'],
        'type': 'mutation',
        'gene': 'KRAS',
        'korean': 'KRAS 돌연변이',
        'cancer_types': ['대장암', '폐암']
    },
    'BRCA1': {
        'keywords': ['BRCA1', 'BRCA-1'],
        'type': 'mutation',
        'gene': 'BRCA1',
        'korean': 'BRCA1 돌연변이',
        'cancer_types': ['유방암', '난소암']
    },
    'BRCA2': {
        'keywords': ['BRCA2', 'BRCA-2'],
        'type': 'mutation',
        'gene': 'BRCA2',
        'korean': 'BRCA2 돌연변이',
        'cancer_types': ['유방암', '난소암']
    },

    # 면역관문
    'PD-1': {
        'keywords': ['PD-1', 'PD1', 'PDCD1'],
        'type': 'protein',
        'gene': 'PDCD1',
        'korean': 'PD-1',
        'cancer_types': ['범종양']
    },
    'PD-L1': {
        'keywords': ['PD-L1', 'PDL1', 'CD274'],
        'type': 'protein',
        'gene': 'CD274',
        'korean': 'PD-L1',
        'cancer_types': ['범종양']
    },
    'CTLA-4': {
        'keywords': ['CTLA-4', 'CTLA4'],
        'type': 'protein',
        'gene': 'CTLA4',
        'korean': 'CTLA-4',
        'cancer_types': ['흑색종']
    },

    # 호르몬 수용체
    'ER': {
        'keywords': ['에스트로겐 수용체', '에스트로젠', 'estrogen receptor'],
        'type': 'protein',
        'gene': 'ESR1',
        'korean': '에스트로겐 수용체',
        'cancer_types': ['유방암']
    },
    'AR': {
        'keywords': ['안드로겐 수용체', 'androgen receptor', '남성호르몬 수용체'],
        'type': 'protein',
        'gene': 'AR',
        'korean': '안드로겐 수용체',
        'cancer_types': ['전립선암']
    },

    # 기타 표적
    'CD20': {
        'keywords': ['CD20'],
        'type': 'protein',
        'gene': 'MS4A1',
        'korean': 'CD20',
        'cancer_types': ['림프종']
    },
    'CD30': {
        'keywords': ['CD30'],
        'type': 'protein',
        'gene': 'TNFRSF8',
        'korean': 'CD30',
        'cancer_types': ['호지킨림프종']
    },
    'CD33': {
        'keywords': ['CD33'],
        'type': 'protein',
        'gene': 'CD33',
        'korean': 'CD33',
        'cancer_types': ['급성골수성백혈병']
    },
    'CD38': {
        'keywords': ['CD38'],
        'type': 'protein',
        'gene': 'CD38',
        'korean': 'CD38',
        'cancer_types': ['다발골수종']
    },
    'SLAMF7': {
        'keywords': ['SLAMF7', 'CD319'],
        'type': 'protein',
        'gene': 'SLAMF7',
        'korean': 'SLAMF7',
        'cancer_types': ['다발골수종']
    },
    'PARP': {
        'keywords': ['PARP'],
        'type': 'enzyme',
        'gene': 'PARP1',
        'korean': 'PARP',
        'cancer_types': ['유방암', '난소암']
    },
    'FLT3': {
        'keywords': ['FLT3'],
        'type': 'protein',
        'gene': 'FLT3',
        'korean': 'FLT3',
        'cancer_types': ['급성골수성백혈병']
    },
    'IDH1': {
        'keywords': ['IDH1'],
        'type': 'enzyme',
        'gene': 'IDH1',
        'korean': 'IDH1',
        'cancer_types': ['급성골수성백혈병', '교모세포종']
    },
    'IDH2': {
        'keywords': ['IDH2'],
        'type': 'enzyme',
        'gene': 'IDH2',
        'korean': 'IDH2',
        'cancer_types': ['급성골수성백혈병']
    },
    'MET': {
        'keywords': ['MET', 'c-MET'],
        'type': 'protein',
        'gene': 'MET',
        'korean': 'MET',
        'cancer_types': ['폐암']
    },
    'mTOR': {
        'keywords': ['mTOR', 'MTOR'],
        'type': 'protein',
        'gene': 'MTOR',
        'korean': 'mTOR',
        'cancer_types': ['신장암']
    },
    'MEK': {
        'keywords': ['MEK'],
        'type': 'protein',
        'gene': 'MAP2K1',
        'korean': 'MEK',
        'cancer_types': ['흑색종']
    },
    'CDK4/6': {
        'keywords': ['CDK4', 'CDK6', 'CDK4/6'],
        'type': 'enzyme',
        'gene': 'CDK4',
        'korean': 'CDK4/6',
        'cancer_types': ['유방암']
    },
}


class BiomarkerExtractor:
    """바이오마커 추출기"""

    def __init__(self):
        self.drugs = []
        self.biomarkers = {}
        self.drug_biomarker_map = defaultdict(list)

    def load_drugs(self):
        """항암제 데이터 로드"""
        print("[INFO] 항암제 데이터 로딩...")

        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            self.drugs = json.load(f)

        print(f"[OK] {len(self.drugs)}개 항암제 로드 완료")

    def extract_biomarkers_from_text(self, text, drug):
        """텍스트에서 바이오마커 추출"""
        if not text:
            return []

        text_upper = text.upper()
        found_biomarkers = []

        for biomarker_name, info in BIOMARKER_PATTERNS.items():
            for keyword in info['keywords']:
                if keyword.upper() in text_upper:
                    found_biomarkers.append(biomarker_name)
                    break

        return found_biomarkers

    def process_drugs(self):
        """모든 항암제 처리"""
        print("\n[INFO] 바이오마커 추출 중...")

        extraction_stats = {
            'from_mechanism': 0,
            'from_atc': 0,
            'total_drugs_with_biomarkers': 0
        }

        for drug in self.drugs:
            drug_biomarkers = set()

            # 1. mechanism_of_action에서 추출
            moa = drug.get('mechanism_of_action', '')
            if moa:
                found = self.extract_biomarkers_from_text(moa, drug)
                if found:
                    drug_biomarkers.update(found)
                    extraction_stats['from_mechanism'] += len(found)

            # 2. ATC Level 3에서 추출
            atc_level3_name = drug.get('atc_level3_name', '')
            if atc_level3_name:
                found = self.extract_biomarkers_from_text(atc_level3_name, drug)
                if found:
                    drug_biomarkers.update(found)
                    extraction_stats['from_atc'] += len(found)

            # 바이오마커 발견 시 매핑 저장
            if drug_biomarkers:
                extraction_stats['total_drugs_with_biomarkers'] += 1

                for biomarker_name in drug_biomarkers:
                    self.drug_biomarker_map[biomarker_name].append({
                        'atc_code': drug['atc_code'],
                        'ingredient_ko': drug['ingredient_ko'],
                        'ingredient_en': drug.get('ingredient_base_en', ''),
                        'mechanism_of_action': drug.get('mechanism_of_action', ''),
                        'therapeutic_category': drug.get('therapeutic_category', '')
                    })

        print(f"\n[STATS] 추출 통계:")
        print(f"  - mechanism_of_action에서: {extraction_stats['from_mechanism']}건")
        print(f"  - ATC Level 3에서: {extraction_stats['from_atc']}건")
        print(f"  - 바이오마커 보유 약물: {extraction_stats['total_drugs_with_biomarkers']}개")

    def build_biomarker_entries(self):
        """바이오마커 엔트리 생성"""
        print("\n[INFO] 바이오마커 엔트리 구축 중...")

        biomarker_id = 1

        for biomarker_name in sorted(self.drug_biomarker_map.keys()):
            info = BIOMARKER_PATTERNS[biomarker_name]
            related_drugs = self.drug_biomarker_map[biomarker_name]

            self.biomarkers[biomarker_name] = {
                'biomarker_id': f"BIOMARKER_{biomarker_id:03d}",
                'biomarker_name_en': biomarker_name,
                'biomarker_name_ko': info['korean'],
                'biomarker_type': info['type'],
                'protein_gene': info['gene'],
                'cancer_types': info['cancer_types'],
                'related_drugs': related_drugs,
                'drug_count': len(related_drugs),
                'source': 'anticancer_dictionary',
                'extraction_method': 'pattern_match',
                'confidence': 0.95,
                'created_at': datetime.now().isoformat()
            }

            biomarker_id += 1

        print(f"[OK] {len(self.biomarkers)}개 바이오마커 엔트리 생성")

    def save_results(self):
        """결과 저장"""
        print("\n[INFO] 결과 저장 중...")

        output_data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'source_file': str(INPUT_FILE.name),
                'total_drugs': len(self.drugs),
                'total_biomarkers': len(self.biomarkers),
                'extraction_version': '1.0'
            },
            'biomarkers': list(self.biomarkers.values())
        }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        file_size_kb = OUTPUT_FILE.stat().st_size / 1024

        print(f"[SAVED] {OUTPUT_FILE}")
        print(f"        크기: {file_size_kb:.1f} KB")

    def print_summary(self):
        """요약 출력"""
        print("\n" + "=" * 70)
        print("바이오마커 추출 완료")
        print("=" * 70)

        print(f"\n총 바이오마커: {len(self.biomarkers)}개")

        # 타입별 통계
        type_counts = defaultdict(int)
        for biomarker in self.biomarkers.values():
            type_counts[biomarker['biomarker_type']] += 1

        print("\n타입별 분포:")
        for btype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  - {btype}: {count}개")

        # 상위 5개 바이오마커 (약물 수 기준)
        top5 = sorted(
            self.biomarkers.values(),
            key=lambda x: x['drug_count'],
            reverse=True
        )[:5]

        print("\n상위 5개 바이오마커 (관련 약물 수):")
        for i, biomarker in enumerate(top5, 1):
            print(f"  {i}. {biomarker['biomarker_name_ko']} ({biomarker['biomarker_name_en']})")
            print(f"     - 관련 약물: {biomarker['drug_count']}개")
            print(f"     - 암종: {', '.join(biomarker['cancer_types'])}")

        print("\n" + "=" * 70)

    def run(self):
        """전체 프로세스 실행"""
        print("=" * 70)
        print("Phase 1: 항암제 사전에서 바이오마커 추출")
        print("=" * 70)

        self.load_drugs()
        self.process_drugs()
        self.build_biomarker_entries()
        self.save_results()
        self.print_summary()

        return True


def main():
    """메인 실행"""
    extractor = BiomarkerExtractor()
    success = extractor.run()

    if success:
        print("\n[SUCCESS] Phase 1 완료!")
        print(f"출력 파일: {OUTPUT_FILE}")
    else:
        print("\n[ERROR] Phase 1 실패")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
