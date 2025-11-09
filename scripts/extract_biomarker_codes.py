"""
HINS 데이터에서 바이오마커별 LOINC/SNOMED CT 코드 추출

v2.0 23개 바이오마커에 대한 표준 코드 매핑 테이블 생성
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "hins"
INPUT_FILE = DATA_DIR / "downloads" / "edi" / "2장_19_20용어매핑테이블(검사)_(심평원코드-SNOMED_CT).xlsx"
OUTPUT_FILE = PROJECT_ROOT / "bridges" / "biomarker_code_mapping.json"

# v2.0 바이오마커 목록
V2_BIOMARKERS = [
    'ALK', 'AR', 'BCR-ABL', 'BRAF', 'BRCA1', 'BRCA2',
    'CD20', 'CD38', 'CDK4/6', 'EGFR', 'ER', 'FLT3',
    'HER2', 'IDH1', 'IDH2', 'KRAS', 'MEK', 'PARP',
    'PD-1', 'PD-L1', 'ROS1', 'VEGF', 'mTOR'
]

# 바이오마커 키워드 변형
BIOMARKER_VARIANTS = {
    'HER2': ['HER2', 'HER-2', 'ERBB2'],
    'EGFR': ['EGFR'],
    'ALK': ['ALK'],
    'ROS1': ['ROS1', 'ROS-1'],
    'BCR-ABL': ['BCR-ABL', 'BCR ABL', 'BCRABL'],
    'BRAF': ['BRAF', 'B-RAF'],
    'KRAS': ['KRAS', 'K-RAS'],
    'BRCA1': ['BRCA1'],
    'BRCA2': ['BRCA2'],
    'PD-L1': ['PD-L1', 'PDL1', 'PD L1'],
    'PD-1': ['PD-1', 'PD1', 'PD 1'],
    'FLT3': ['FLT3'],
    'IDH1': ['IDH1'],
    'IDH2': ['IDH2'],
    'ER': ['에스트로겐 수용체', 'ESTROGEN RECEPTOR', 'ER 수용체'],  # 정확한 용어만
    'AR': ['안드로겐 수용체', 'ANDROGEN RECEPTOR', 'AR 수용체'],  # 정확한 용어만
    'CD20': ['CD20'],
    'CD38': ['CD38'],
    'CDK4/6': ['CDK4', 'CDK6', 'CDK4/6'],
    'MEK': ['MEK'],
    'PARP': ['PARP'],
    'VEGF': ['VEGF'],
    'mTOR': ['mTOR', 'MTOR'],
}


def extract_codes():
    """HINS 데이터에서 바이오마커별 코드 추출"""

    print("="*70)
    print("HINS 데이터에서 바이오마커 코드 추출")
    print("="*70)

    # Excel 파일 로드
    print(f"\n[INFO] HINS EDI 검사 파일 로딩...")
    df = pd.read_excel(INPUT_FILE)
    print(f"[OK] {len(df):,}개 검사 항목 로드 완료")

    # 바이오마커별 코드 저장
    biomarker_codes = {}

    for biomarker in V2_BIOMARKERS:
        variants = BIOMARKER_VARIANTS.get(biomarker, [biomarker])

        loinc_codes = set()
        snomed_codes = set()
        matched_tests = []

        # 바이오마커 관련 검사 필터 키워드
        biomarker_test_keywords = [
            '면역', '유전자', '염기서열', '돌연변이', '증폭', '융합',
            '종양', '암', '바이오마커', '수용체', 'Gene', 'mutation',
            'Immuno', 'receptor', 'tumor', 'cancer', 'biomarker'
        ]

        # 한글명 또는 영문명에서 바이오마커 키워드 검색
        for idx, row in df.iterrows():
            test_name_ko = str(row.get('term_kr', ''))
            test_name_en = str(row.get('term_en', ''))
            combined = (test_name_ko + ' ' + test_name_en).upper()

            # 바이오마커 관련 검사가 아니면 스킵
            if not any(keyword in combined for keyword in biomarker_test_keywords):
                continue

            # 변형 중 하나라도 매칭되면
            if any(variant.upper() in combined for variant in variants):
                # LOINC 코드 추출
                loinc = row.get('loinc_icd_id')
                if pd.notna(loinc):
                    loinc_codes.add(str(loinc))

                # SNOMED CT 코드 추출 (pre_ct_id 우선, 없으면 post_ct_id)
                snomed = row.get('pre_ct_id')
                if pd.isna(snomed):
                    snomed = row.get('post_ct_id')
                if pd.notna(snomed):
                    snomed_codes.add(str(snomed))

                # 샘플 테스트 저장
                if len(matched_tests) < 5:
                    matched_tests.append({
                        'test_name_ko': test_name_ko,
                        'test_name_en': test_name_en,
                        'loinc': str(loinc) if pd.notna(loinc) else None,
                        'snomed': str(snomed) if pd.notna(snomed) else None,
                    })

        biomarker_codes[biomarker] = {
            'loinc_codes': sorted(list(loinc_codes)),
            'snomed_codes': sorted(list(snomed_codes)),
            'total_tests': len(matched_tests),
            'sample_tests': matched_tests[:3]
        }

        print(f"\n{biomarker}:")
        print(f"  LOINC: {len(loinc_codes)}개")
        print(f"  SNOMED CT: {len(snomed_codes)}개")
        print(f"  매칭된 검사: {len(matched_tests)}개")

    # 결과 저장
    output_data = {
        'metadata': {
            'description': 'HINS EDI 데이터에서 추출한 바이오마커별 LOINC/SNOMED CT 코드',
            'source_file': str(INPUT_FILE.name),
            'total_biomarkers': len(biomarker_codes),
            'extraction_date': pd.Timestamp.now().isoformat()
        },
        'biomarker_codes': biomarker_codes
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 코드 매핑 테이블 저장: {OUTPUT_FILE}")

    # 통계
    print("\n" + "="*70)
    print("요약 통계")
    print("="*70)

    total_loinc = sum(len(v['loinc_codes']) for v in biomarker_codes.values())
    total_snomed = sum(len(v['snomed_codes']) for v in biomarker_codes.values())
    has_loinc = sum(1 for v in biomarker_codes.values() if v['loinc_codes'])
    has_snomed = sum(1 for v in biomarker_codes.values() if v['snomed_codes'])

    print(f"총 바이오마커: {len(biomarker_codes)}개")
    print(f"LOINC 보유: {has_loinc}개 ({has_loinc/len(biomarker_codes)*100:.1f}%)")
    print(f"SNOMED CT 보유: {has_snomed}개 ({has_snomed/len(biomarker_codes)*100:.1f}%)")
    print(f"총 LOINC 코드: {total_loinc}개")
    print(f"총 SNOMED CT 코드: {total_snomed}개")

    # 코드 없는 바이오마커
    no_codes = [b for b, v in biomarker_codes.items()
                if not v['loinc_codes'] and not v['snomed_codes']]
    if no_codes:
        print(f"\n[WARN] 코드 없는 바이오마커 ({len(no_codes)}개):")
        for b in no_codes:
            print(f"  - {b}")

    return biomarker_codes


if __name__ == "__main__":
    extract_codes()
