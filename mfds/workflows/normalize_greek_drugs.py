#!/usr/bin/env python3
"""
약전 그리스 문자 약물 정규화 통합 워크플로우

1. 파싱된 약전에서 그리스 문자 약물 추출
2. 정규화 동의어 생성
3. 약가 마스터와 매칭하여 업데이트
"""
import json
import sys
from pathlib import Path
from typing import List, Dict

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mfds.utils.extract_greek_drugs import GreekDrugExtractor
from mfds.utils.greek_normalizer import GreekLetterNormalizer


def load_anticancer_master(master_path: Path) -> List[Dict]:
    """약가 마스터 로드"""
    with open(master_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def match_and_normalize(
    greek_drugs: List[Dict],
    master_drugs: List[Dict],
    normalizer: GreekLetterNormalizer
) -> Dict:
    """
    약전 그리스 문자 약물과 약가 마스터 매칭 후 정규화 적용

    Returns:
        {
            'matched': [매칭된 약물 목록],
            'unmatched_kp': [약전에만 있는 약물],
            'stats': {...}
        }
    """
    # 약가 마스터의 영문/한글 성분명 세트 생성
    master_en_names = set()
    master_ko_names = set()

    for drug in master_drugs:
        # ATC name
        if drug.get('atc_name_en'):
            master_en_names.add(drug['atc_name_en'].lower())

        # 추출된 한글명
        if drug.get('ingredient_ko'):
            master_ko_names.add(drug['ingredient_ko'])

        # 원본 한글명
        if drug.get('ingredient_ko_original'):
            master_en_names.add(drug['ingredient_ko_original'].lower())

    matched = []
    unmatched = []

    for kp_drug in greek_drugs:
        name = kp_drug['name']

        # 영문명으로 매칭 시도
        name_lower = name.lower()

        # 그리스 문자를 ASCII로 변환한 버전도 확인
        normalized = normalizer.normalize_drug_name(name, None)
        ascii_variants = normalized['name']['synonyms_en']

        is_matched = False

        # 원본 또는 ASCII 변환 버전으로 매칭
        for variant in [name_lower] + [v.lower() for v in ascii_variants]:
            if variant in master_en_names:
                matched.append({
                    'kp_name': name,
                    'master_match': variant,
                    'normalization': normalized,
                    'greek_chars': kp_drug['greek_chars']
                })
                is_matched = True
                break

        if not is_matched:
            unmatched.append(kp_drug)

    return {
        'matched': matched,
        'unmatched_kp': unmatched,
        'stats': {
            'total_kp_greek_drugs': len(greek_drugs),
            'matched_count': len(matched),
            'unmatched_count': len(unmatched),
            'match_rate': len(matched) / len(greek_drugs) if greek_drugs else 0
        }
    }


def update_master_with_normalization(
    master_drugs: List[Dict],
    matched_drugs: List[Dict]
) -> List[Dict]:
    """
    약가 마스터에 정규화 정보 추가

    매칭된 약물에만 synonyms_en, synonyms_ko 필드 추가
    """
    # 매칭 맵 생성 (소문자 기준)
    match_map = {}
    for match in matched_drugs:
        key = match['master_match']
        match_map[key] = match['normalization']

    updated_drugs = []

    for drug in master_drugs:
        updated_drug = drug.copy()

        # 영문명으로 매칭 확인
        atc_name = drug.get('atc_name_en', '').lower()
        original_name = drug.get('ingredient_ko_original', '').lower()

        normalization = None
        if atc_name in match_map:
            normalization = match_map[atc_name]
        elif original_name in match_map:
            normalization = match_map[original_name]

        # 정규화 정보 추가
        if normalization:
            updated_drug['synonyms_en'] = normalization['name']['synonyms_en']
            updated_drug['synonyms_ko'] = normalization['name'].get('synonyms_ko', [])
            updated_drug['has_greek_letters'] = normalization['normalization']['greek_to_ascii']
        else:
            # 그리스 문자 없는 약물
            updated_drug['synonyms_en'] = []
            updated_drug['synonyms_ko'] = []
            updated_drug['has_greek_letters'] = False

        updated_drugs.append(updated_drug)

    return updated_drugs


def main():
    """통합 워크플로우 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='Greek letter drug normalization workflow')
    parser.add_argument('--kp-parsed', default='data/mfds/parsed_pdf',
                        help='KP parsed directory')
    parser.add_argument('--master', default='bridges/anticancer_master_clean.json',
                        help='Drug master file')
    parser.add_argument('--output', default='bridges/anticancer_master_normalized.json',
                        help='Output file')
    parser.add_argument('--report', default='data/mfds/greek_normalization_report.json',
                        help='Matching report')

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent.parent
    kp_dir = base_dir / args.kp_parsed
    master_path = base_dir / args.master
    output_path = base_dir / args.output
    report_path = base_dir / args.report

    print("=" * 80)
    print("약전 그리스 문자 약물 정규화 워크플로우")
    print("=" * 80)

    # 1. 약전에서 그리스 문자 약물 추출
    print("\n[STEP 1] Extracting Greek letter drugs from KP...")
    extractor = GreekDrugExtractor()
    kp_drugs = extractor.scan_directory(kp_dir, use_elements=True)

    if not kp_drugs:
        print("[INFO] No Greek letter drugs found in KP")
        return 0

    print(f"  → Found {len(kp_drugs)} drugs with Greek letters")

    # 2. 약가 마스터 로드
    print("\n[STEP 2] Loading drug master...")
    master_drugs = load_anticancer_master(master_path)
    print(f"  → Loaded {len(master_drugs)} drugs from master")

    # 3. 매칭 및 정규화
    print("\n[STEP 3] Matching and normalizing...")
    normalizer = GreekLetterNormalizer()
    match_result = match_and_normalize(kp_drugs, master_drugs, normalizer)

    print(f"\n[STATS]")
    print(f"  Total KP Greek drugs: {match_result['stats']['total_kp_greek_drugs']}")
    print(f"  Matched: {match_result['stats']['matched_count']}")
    print(f"  Unmatched: {match_result['stats']['unmatched_count']}")
    print(f"  Match rate: {match_result['stats']['match_rate']:.1%}")

    # 4. 마스터 업데이트
    print("\n[STEP 4] Updating master with normalization...")
    updated_master = update_master_with_normalization(
        master_drugs,
        match_result['matched']
    )

    # 5. 결과 저장
    print("\n[STEP 5] Saving results...")

    # 업데이트된 마스터 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated_master, f, ensure_ascii=False, indent=2)
    print(f"  → Updated master: {output_path}")

    # 리포트 저장
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(match_result, f, ensure_ascii=False, indent=2)
    print(f"  → Match report: {report_path}")

    # 6. 매칭된 약물 샘플 출력
    print("\n[SAMPLE] Matched drugs with normalization:")
    for i, match in enumerate(match_result['matched'][:5], 1):
        print(f"\n  {i}. {match['kp_name']}")
        print(f"     Greek: {', '.join(match['greek_chars'])}")
        print(f"     Synonyms (EN): {', '.join(match['normalization']['name']['synonyms_en'][:3])}")
        if match['normalization']['name'].get('synonyms_ko'):
            print(f"     Synonyms (KO): {', '.join(match['normalization']['name']['synonyms_ko'][:3])}")

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
