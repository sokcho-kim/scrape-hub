"""
누락된 약물을 anticancer_master_classified.json에 추가
"""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
DRUG_FILE = PROJECT_ROOT / "bridges" / "anticancer_master_classified.json"


def main():
    """메인 실행"""
    # 누락된 약물들 (주로 보조 약물 및 신약)
    additional_drugs = [
        # 스테로이드
        {
            'atc_code': 'H02AB02',
            'ingredient_ko': '덱사메타손',
            'ingredient_base_en': 'dexamethasone',
            'mechanism_of_action': 'Corticosteroid'
        },
        {
            'atc_code': 'H02AB06',
            'ingredient_ko': '프레드니솔론',
            'ingredient_base_en': 'prednisolone',
            'mechanism_of_action': 'Corticosteroid'
        },
        # 면역억제제
        {
            'atc_code': 'L04AX02',
            'ingredient_ko': '탈리도마이드',
            'ingredient_base_en': 'thalidomide',
            'mechanism_of_action': 'Immunomodulatory agent'
        },
        # 해독제
        {
            'atc_code': 'V03AF03',
            'ingredient_ko': '류코보린',
            'ingredient_base_en': 'folinic acid',
            'mechanism_of_action': 'Antidote'
        },
        # 신약 (BTK 억제제)
        {
            'atc_code': 'L01EL05',
            'ingredient_ko': '피르토브루티닙',
            'ingredient_base_en': 'pirtobrutinib',
            'mechanism_of_action': 'BTK inhibitor'
        },
        # 신약 (EGFR/MET 이중 항체)
        {
            'atc_code': 'L01FX23',
            'ingredient_ko': '아미반타맙',
            'ingredient_base_en': 'amivantamab',
            'mechanism_of_action': 'EGFR/MET bispecific antibody'
        },
        # 신약 (PD-1 억제제)
        {
            'atc_code': 'L01FF09',
            'ingredient_ko': '티슬렐리주맙',
            'ingredient_base_en': 'tislelizumab',
            'mechanism_of_action': 'PD-1 inhibitor'
        },
        # 신약 (Trop-2 ADC)
        {
            'atc_code': 'L01FX17',
            'ingredient_ko': '사시투주맙 고비테칸',
            'ingredient_base_en': 'sacituzumab govitecan',
            'mechanism_of_action': 'Trop-2 directed antibody-drug conjugate'
        },
        # 신약 (FGFR 억제제)
        {
            'atc_code': 'L01EX15',
            'ingredient_ko': '페미가티닙',
            'ingredient_base_en': 'pemigatinib',
            'mechanism_of_action': 'FGFR inhibitor'
        },
        # 소마토스타틴 유사체
        {
            'atc_code': 'H01CB03',
            'ingredient_ko': '란레오타이드',
            'ingredient_base_en': 'lanreotide',
            'mechanism_of_action': 'Somatostatin analog'
        },
        {
            'atc_code': 'H01CB02',
            'ingredient_ko': '옥트레오타이드',
            'ingredient_base_en': 'octreotide',
            'mechanism_of_action': 'Somatostatin analog'
        },
        # 방사성 동위원소 치료제
        {
            'atc_code': 'V10XX04',
            'ingredient_ko': '루테튬(177Lu) 옥소도트레오타이드',
            'ingredient_base_en': 'lutetium oxodotreotide',
            'mechanism_of_action': 'Radiopharmaceutical'
        }
    ]

    # 기존 파일 로드
    with open(DRUG_FILE, 'r', encoding='utf-8') as f:
        existing_drugs = json.load(f)

    # 중복 체크
    existing_atc = {d['atc_code'] for d in existing_drugs}
    new_drugs = [d for d in additional_drugs if d['atc_code'] not in existing_atc]

    print(f'기존 약물: {len(existing_drugs)}개')
    print(f'추가할 약물: {len(new_drugs)}개')
    print(f'통합 후 총: {len(existing_drugs) + len(new_drugs)}개')

    if new_drugs:
        # 통합
        merged_drugs = existing_drugs + new_drugs

        # 저장
        with open(DRUG_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged_drugs, f, ensure_ascii=False, indent=2)

        print('\n추가된 약물:')
        for d in new_drugs:
            print(f'  {d["ingredient_base_en"]}: {d["atc_code"]}')

        print(f'\n[OK] 파일 업데이트 완료: {DRUG_FILE}')
    else:
        print('\n[INFO] 추가할 약물 없음 (모두 이미 존재)')


if __name__ == "__main__":
    main()
