"""
바이오마커 파일에 KCD 코드 추가

cancer_types: ["폐암"] → kcd_codes: ["C34"] 변환
공식 KCD 분류체계 기반
"""

import json
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).parent
BIOMARKER_FILE = PROJECT_ROOT / "bridges" / "biomarkers_extracted_v2.json"
MAPPING_FILE = PROJECT_ROOT / "bridges" / "cancer_type_to_kcd_official.json"
OUTPUT_FILE = PROJECT_ROOT / "bridges" / "biomarkers_with_kcd.json"


def main():
    """메인 실행"""
    print("=" * 70)
    print("바이오마커 파일에 KCD 코드 추가")
    print("=" * 70)

    # 데이터 로드
    print("\n[INFO] 데이터 로딩...")
    with open(BIOMARKER_FILE, 'r', encoding='utf-8') as f:
        biomarker_data = json.load(f)
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)

    mappings = mapping_data['mappings']
    biomarkers = biomarker_data['biomarkers']

    print(f"[OK] 바이오마커 {len(biomarkers)}개 로드")
    print(f"[OK] 암종 매핑 {len(mappings)}개 로드")

    # KCD 코드 추가
    print("\n[INFO] KCD 코드 추가 중...")
    updated_count = 0
    missing_count = 0

    for bio in biomarkers:
        cancer_types = bio.get('cancer_types', [])
        kcd_codes = []

        for cancer_name in cancer_types:
            codes = mappings.get(cancer_name, [])
            if codes:
                kcd_codes.extend(codes)
            else:
                print(f"[WARN] 매핑 없음: {bio['biomarker_name_en']} - {cancer_name}")
                missing_count += 1

        # 중복 제거
        kcd_codes = list(set(kcd_codes))
        kcd_codes.sort()

        # 필드 추가
        bio['kcd_codes'] = kcd_codes

        if kcd_codes:
            updated_count += 1
            print(f"  {bio['biomarker_name_en']}: {cancer_types} → {kcd_codes}")

    # 메타데이터 업데이트
    biomarker_data['metadata']['kcd_mapping_added'] = datetime.now().isoformat()
    biomarker_data['metadata']['kcd_mapping_source'] = str(MAPPING_FILE)
    biomarker_data['metadata']['kcd_mapping_method'] = 'official_kcd_classification'

    # 저장
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(biomarker_data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 업데이트된 파일 저장: {OUTPUT_FILE}")

    # 통계
    print("\n" + "=" * 70)
    print("업데이트 통계")
    print("=" * 70)
    print(f"총 바이오마커: {len(biomarkers)}개")
    print(f"  KCD 코드 추가: {updated_count}개")
    print(f"  매핑 실패: {missing_count}개")

    # 샘플 출력
    print("\n샘플 (처음 3개):")
    for bio in biomarkers[:3]:
        print(f"\n바이오마커: {bio['biomarker_name_en']} ({bio['biomarker_name_ko']})")
        print(f"  암종: {bio.get('cancer_types', [])}")
        print(f"  KCD 코드: {bio.get('kcd_codes', [])}")

    print("\n" + "=" * 70)
    print("다음 단계:")
    print("1. Neo4j import 스크립트 수정 (NCC 제거, KCD만 사용)")
    print("2. Disease-Biomarker 관계 생성 (kcd_codes 기반)")
    print("=" * 70)


if __name__ == "__main__":
    main()
