"""
HIRA 화학요법 급여 데이터 분석 및 정규화

1. 암종명 → KCD 코드 매핑
2. 약물명(영문) → ATC 코드 매핑
3. Regimen 데이터 정규화
"""

import json
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).parent
HIRA_FILE = PROJECT_ROOT / "data" / "hira_cancer" / "parsed" / "drug_cancer_relations.json"
KCD_MAPPING = PROJECT_ROOT / "bridges" / "cancer_type_to_kcd_official.json"
DRUG_FILE = PROJECT_ROOT / "bridges" / "anticancer_master_classified.json"
OUTPUT_FILE = PROJECT_ROOT / "bridges" / "hira_regimens_normalized.json"


def load_data():
    """데이터 로드"""
    with open(HIRA_FILE, 'r', encoding='utf-8') as f:
        hira_data = json.load(f)

    with open(KCD_MAPPING, 'r', encoding='utf-8') as f:
        kcd_mapping = json.load(f)['mappings']

    with open(DRUG_FILE, 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    return hira_data, kcd_mapping, drugs


def create_drug_name_to_atc_map(drugs):
    """약물명 → ATC 코드 매핑 생성"""
    mapping = {}

    for drug in drugs:
        # 영문 성분명 (소문자)
        en_name = drug['ingredient_base_en'].lower()
        atc = drug['atc_code']

        if en_name not in mapping:
            mapping[en_name] = atc

    # 약어 및 별칭 추가
    aliases = {
        '5-fu': 'fluorouracil',
        'leucovorin': 'folinic acid',
        'lanreotide acetate': 'lanreotide',
        'octreotide lar': 'octreotide',
    }

    for alias, real_name in aliases.items():
        if real_name in mapping:
            mapping[alias] = mapping[real_name]

    return mapping


def normalize_drug_name(drug_name):
    """약물명 정규화"""
    # 소문자 변환
    name = drug_name.lower().strip()

    # 괄호와 내용 제거
    import re
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def normalize_regimen(relation, kcd_mapping, drug_atc_map):
    """요법 데이터 정규화"""
    cancer_name = relation['cancer']

    # 암종명 → KCD 매핑
    kcd_codes = kcd_mapping.get(cancer_name, [])

    # 약물명 → ATC 매핑
    drug_names = relation['drugs']
    drug_atc_list = []
    missing_drugs = []

    for drug_name in drug_names:
        # 정규화된 이름으로 매핑
        normalized_name = normalize_drug_name(drug_name)
        atc = drug_atc_map.get(normalized_name)

        if atc:
            drug_atc_list.append({
                'name': drug_name,
                'normalized_name': normalized_name,
                'atc_code': atc
            })
        else:
            missing_drugs.append(drug_name)

    # Regimen ID 생성
    regimen_id = f"REGIMEN_{relation.get('announcement_no', 'UNKNOWN').replace('-', '_')}_{len(drug_names)}DRUG"

    normalized = {
        'regimen_id': regimen_id,
        'cancer_name': cancer_name,
        'kcd_codes': kcd_codes,
        'drugs': drug_atc_list,
        'missing_drugs': missing_drugs,
        'regimen_type': relation.get('regimen_type'),
        'line': relation.get('line'),
        'purpose': relation.get('purpose'),
        'action': relation.get('action'),
        'announcement_no': relation.get('announcement_no'),
        'announcement_date': relation.get('date'),
        'source_text': relation.get('source_text'),
        'has_kcd': len(kcd_codes) > 0,
        'has_all_drugs': len(missing_drugs) == 0
    }

    return normalized


def main():
    """메인 실행"""
    print("=" * 80)
    print("HIRA 화학요법 급여 데이터 정규화")
    print("=" * 80)

    # 데이터 로드
    print("\n[INFO] 데이터 로딩...")
    hira_data, kcd_mapping, drugs = load_data()
    print(f"[OK] HIRA 관계: {len(hira_data['relations'])}개")
    print(f"[OK] KCD 매핑: {len(kcd_mapping)}개 암종")
    print(f"[OK] 약물: {len(drugs)}개")

    # 약물명 매핑 생성
    print("\n[INFO] 약물명 → ATC 매핑 생성 중...")
    drug_atc_map = create_drug_name_to_atc_map(drugs)
    print(f"[OK] {len(drug_atc_map)}개 약물 매핑 생성")

    # 정규화
    print("\n[INFO] Regimen 데이터 정규화 중...")
    normalized_regimens = []

    for rel in hira_data['relations']:
        normalized = normalize_regimen(rel, kcd_mapping, drug_atc_map)
        normalized_regimens.append(normalized)

        status = "[OK]" if normalized['has_kcd'] and normalized['has_all_drugs'] else "[X]"
        print(f"  {status} {normalized['cancer_name']} - {normalized['line']} - {len(normalized['drugs'])}개 약물")

        if not normalized['has_kcd']:
            print(f"      [WARN] KCD 매핑 없음")
        if normalized['missing_drugs']:
            print(f"      [WARN] 약물 누락: {normalized['missing_drugs']}")

    # 통계
    print("\n" + "=" * 80)
    print("정규화 통계")
    print("=" * 80)

    total = len(normalized_regimens)
    with_kcd = sum(1 for r in normalized_regimens if r['has_kcd'])
    with_all_drugs = sum(1 for r in normalized_regimens if r['has_all_drugs'])
    complete = sum(1 for r in normalized_regimens if r['has_kcd'] and r['has_all_drugs'])

    print(f"\n총 Regimen: {total}개")
    print(f"  KCD 매핑 성공: {with_kcd}개 ({with_kcd/total*100:.1f}%)")
    print(f"  약물 매핑 완료: {with_all_drugs}개 ({with_all_drugs/total*100:.1f}%)")
    print(f"  완전 매핑: {complete}개 ({complete/total*100:.1f}%)")

    # 누락된 암종
    missing_cancers = [r['cancer_name'] for r in normalized_regimens if not r['has_kcd']]
    if missing_cancers:
        print(f"\nKCD 매핑 누락 암종:")
        for cancer, count in Counter(missing_cancers).most_common():
            print(f"  - {cancer}: {count}개")

    # 누락된 약물
    all_missing_drugs = []
    for r in normalized_regimens:
        all_missing_drugs.extend(r['missing_drugs'])

    if all_missing_drugs:
        print(f"\nATC 매핑 누락 약물:")
        for drug, count in Counter(all_missing_drugs).most_common():
            print(f"  - {drug}: {count}회")

    # 저장
    output = {
        'metadata': {
            'source': str(HIRA_FILE),
            'total_regimens': total,
            'complete_mappings': complete,
            'generated_at': hira_data['summary']['extracted_at']
        },
        'regimens': normalized_regimens
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 정규화 완료: {OUTPUT_FILE}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
