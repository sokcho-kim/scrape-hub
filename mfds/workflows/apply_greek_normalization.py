#!/usr/bin/env python3
"""
전체 약가 마스터에 그리스 문자 정규화 적용

입력:
- data/hira_master/drug_dictionary.json (원본 마스터)
- data/mfds/greek_drugs_master.json (그리스 문자 약물 목록)

출력:
- data/hira_master/drug_dictionary_normalized.json (정규화 적용된 마스터)
"""
import json
import sys
from pathlib import Path
from typing import Dict, List

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mfds.utils.greek_normalizer import GreekLetterNormalizer


def apply_normalization_to_master(
    master_path: Path,
    greek_drugs_path: Path,
    normalizer: GreekLetterNormalizer
) -> Dict:
    """
    약가 마스터에 정규화 적용

    Returns:
        업데이트된 drug_dictionary
    """
    # 1. 마스터 로드
    print(f"[LOAD] Loading master: {master_path}")
    with open(master_path, 'r', encoding='utf-8') as f:
        master = json.load(f)
    print(f"  → {len(master)} products loaded")

    # 2. 그리스 문자 약물 목록 로드
    print(f"\n[LOAD] Loading Greek drugs list: {greek_drugs_path}")
    with open(greek_drugs_path, 'r', encoding='utf-8') as f:
        greek_data = json.load(f)
    greek_drugs = greek_data['drugs']
    print(f"  → {len(greek_drugs)} Greek letter drugs loaded")

    # 3. 그리스 문자 약물의 product_name 세트 생성
    greek_product_names = set()
    for drug in greek_drugs:
        greek_product_names.add(drug['product_name'])

    # 4. 마스터 업데이트
    print(f"\n[UPDATE] Applying normalization...")
    updated_count = 0
    new_entries_count = 0

    # 정규화된 이름으로 접근할 수 있도록 새로운 엔트리 추가
    new_entries = {}

    for product_name, product_data in master.items():
        # 그리스 문자 약물인지 확인
        if product_name in greek_product_names:
            # 정규화 적용
            records = product_data.get('records', [])
            if records:
                # product_name_full에서 성분명 추출
                sample_record = records[0]
                full_name = sample_record.get('product_name', '')

                # 성분명 추출 (괄호 안)
                import re
                match = re.search(r'\((.*?)\)', full_name)
                if match:
                    ingredient_name = match.group(1)

                    # 정규화 동의어 생성
                    normalized_result = normalizer.normalize_drug_name(ingredient_name, None)

                    # 기존 데이터에 정규화 정보 추가
                    product_data['greek_normalization'] = {
                        'has_greek': True,
                        'original_ingredient': ingredient_name,
                        'synonyms_en': normalized_result['name']['synonyms_en'],
                        'synonyms_ko': normalized_result['name'].get('synonyms_ko', [])
                    }
                    updated_count += 1

                    # 정규화된 이름으로도 검색 가능하도록 새 엔트리 생성
                    for synonym in normalized_result['name']['synonyms_en']:
                        # 제품명에서 성분명 부분을 정규화된 이름으로 교체
                        normalized_product_name = product_name

                        # 간단한 매핑: α→alpha, β→beta로 제품명 변환
                        for greek, ascii_val in normalizer.greek_to_ascii.items():
                            normalized_product_name = normalized_product_name.replace(greek, ascii_val)

                        # 새 엔트리 추가 (중복 방지)
                        if normalized_product_name != product_name and normalized_product_name not in master:
                            new_entries[normalized_product_name] = {
                                'records': records.copy(),
                                'normalized_from': product_name,
                                'is_normalized': True,
                                'greek_normalization': product_data['greek_normalization']
                            }
                            new_entries_count += 1
        else:
            # 그리스 문자 없는 약물
            product_data['greek_normalization'] = {
                'has_greek': False
            }

    # 5. 새 엔트리 병합
    print(f"\n[MERGE] Adding normalized entries...")
    master.update(new_entries)

    print(f"\n[STATS]")
    print(f"  Updated existing products: {updated_count}")
    print(f"  New normalized entries: {new_entries_count}")
    print(f"  Total products: {len(master)}")

    return master


def main():
    """실행"""
    import argparse

    parser = argparse.ArgumentParser(description='Apply Greek normalization to drug master')
    parser.add_argument('--master', default='data/hira_master/drug_dictionary.json',
                        help='Drug master file')
    parser.add_argument('--greek-drugs', default='data/mfds/greek_drugs_master.json',
                        help='Greek drugs list')
    parser.add_argument('--output', default='data/hira_master/drug_dictionary_normalized.json',
                        help='Output file')

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent.parent
    master_path = base_dir / args.master
    greek_drugs_path = base_dir / args.greek_drugs
    output_path = base_dir / args.output

    print("=" * 80)
    print("약가 마스터 그리스 문자 정규화 적용")
    print("=" * 80)
    print()

    # 정규화기 초기화
    normalizer = GreekLetterNormalizer()

    # 정규화 적용
    updated_master = apply_normalization_to_master(
        master_path,
        greek_drugs_path,
        normalizer
    )

    # 결과 저장
    print(f"\n[SAVE] Saving to: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated_master, f, ensure_ascii=False, indent=2)

    # 파일 크기 확인
    file_size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  → File size: {file_size_mb:.2f} MB")

    # 샘플 출력
    print(f"\n[SAMPLE] Normalized products:")
    normalized_products = [
        (name, data) for name, data in updated_master.items()
        if data.get('is_normalized', False)
    ]

    for i, (name, data) in enumerate(normalized_products[:10], 1):
        print(f"\n  {i}. {name}")
        print(f"     Original: {data.get('normalized_from', 'N/A')}")
        if data.get('greek_normalization'):
            synonyms = data['greek_normalization'].get('synonyms_en', [])
            if synonyms:
                print(f"     Synonyms: {', '.join(synonyms[:3])}")

    if len(normalized_products) > 10:
        print(f"\n  ... and {len(normalized_products) - 10} more normalized entries")

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
