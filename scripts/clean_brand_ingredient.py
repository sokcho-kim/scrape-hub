#!/usr/bin/env python3
"""
브랜드명/성분명 정제 (Phase 1)

입력: bridges/anticancer_master.json
출력: bridges/anticancer_master_clean.json

정제 규칙:
1. 괄호 안 → 성분명 추출
2. 괄호 앞 → 브랜드명 (제형/용량 제거)
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# 제형 접미사 패턴
FORM_SUFFIX = r"(서방)?정|캡슐|주|주사|주입액|현탁액|시럽|분말|과립|패치|펜|키트|액|연질|경질"

def parse_brand_ingredient(product_name: str):
    """
    제품명에서 브랜드명과 성분명 추출

    예: "버제니오정50밀리그램(아베마시클립)_(50mg/1정)"
    → brand_ko="버제니오", ingredient_ko="아베마시클립"
    """
    if not product_name or not isinstance(product_name, str):
        return None, None

    # 1. 괄호 안 성분명 추출 (한글 우선)
    ing_match = re.search(r'\(([가-힣A-Za-z \·\-\u00B7,]+)\)', product_name)
    ingredient_ko = ing_match.group(1).strip() if ing_match else None

    # 쉼표로 구분된 경우 첫 번째만 (예: "성분A, 성분B")
    if ingredient_ko and ',' in ingredient_ko:
        ingredient_ko = ingredient_ko.split(',')[0].strip()

    # 2. 괄호 앞 부분 추출
    left = re.split(r'[\(_]', product_name)[0]  # '(' 또는 '_' 앞까지

    # 3. 첫 숫자 앞까지만 (용량 제거)
    left = re.split(r'\d', left)[0]
    left = left.strip()

    # 4. 제형 접미사 제거
    brand_ko = re.sub(rf'({FORM_SUFFIX})$', '', left).strip()

    # 5. 빈 문자열 처리
    if not brand_ko:
        brand_ko = None
    if not ingredient_ko:
        ingredient_ko = None

    return brand_ko, ingredient_ko


def clean_anticancer_master():
    print("=" * 80)
    print("Phase 1: 브랜드명/성분명 정제")
    print("=" * 80)

    # 1. 원본 로드
    print("\n[1/4] Loading original data...")
    input_path = Path('bridges/anticancer_master.json')
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"  Loaded {len(data)} ingredients")

    # 2. 브랜드명/성분명 정제
    print("\n[2/4] Cleaning brand names and ingredients...")

    cleaned_data = []
    brand_stats = defaultdict(int)  # 추출 통계
    ingredient_stats = defaultdict(int)

    for idx, item in enumerate(data, 1):
        # 기존 데이터 복사
        cleaned_item = {
            'ingredient_ko_original': item['ingredient_ko'],
            'atc_code': item['atc_code'],
            'atc_name_en': item['atc_name_en'],
            'ingredient_code': item['ingredient_code'],
            'brand_count': item['brand_count']
        }

        # 브랜드명 정제
        brand_names_raw = item['brand_names']
        brand_names_clean = set()
        ingredient_ko_extracted = set()

        for brand_raw in brand_names_raw:
            brand_clean, ingredient_ko = parse_brand_ingredient(brand_raw)

            if brand_clean:
                brand_names_clean.add(brand_clean)
                brand_stats['success'] += 1
            else:
                brand_stats['failed'] += 1

            if ingredient_ko:
                ingredient_ko_extracted.add(ingredient_ko)
                ingredient_stats['success'] += 1
            else:
                ingredient_stats['failed'] += 1

        # 정제된 데이터 저장
        cleaned_item['brand_names_clean'] = sorted(list(brand_names_clean))
        cleaned_item['brand_names_raw'] = brand_names_raw
        cleaned_item['ingredient_ko_extracted'] = sorted(list(ingredient_ko_extracted))
        cleaned_item['manufacturers'] = item['manufacturers']
        cleaned_item['product_codes'] = item['product_codes']

        # 대표 성분명 선택 (추출된 한글 성분명 우선)
        if ingredient_ko_extracted:
            # 한글이 있으면 선택
            korean_ingredients = [ing for ing in ingredient_ko_extracted if any('\uac00' <= c <= '\ud7a3' for c in ing)]
            if korean_ingredients:
                cleaned_item['ingredient_ko'] = korean_ingredients[0]
            else:
                cleaned_item['ingredient_ko'] = list(ingredient_ko_extracted)[0]
        else:
            # 없으면 원본 유지
            cleaned_item['ingredient_ko'] = item['ingredient_ko']

        # 대표 브랜드명 선택
        if brand_names_clean:
            cleaned_item['brand_name_primary'] = sorted(list(brand_names_clean))[0]
        else:
            cleaned_item['brand_name_primary'] = None

        cleaned_data.append(cleaned_item)

        # 진행 상황 출력
        if idx % 50 == 0:
            print(f"  Processed {idx}/{len(data)} ingredients")

    print(f"\n  Cleaning complete!")
    print(f"    Brand names: {brand_stats['success']}/{brand_stats['success']+brand_stats['failed']} success")
    print(f"    Ingredients: {ingredient_stats['success']}/{ingredient_stats['success']+ingredient_stats['failed']} success")

    # 3. 저장
    print("\n[3/4] Saving cleaned data...")

    output_path = Path('bridges/anticancer_master_clean.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {output_path}")

    # CSV 백업
    import pandas as pd
    df = pd.DataFrame(cleaned_data)
    csv_path = Path('bridges/anticancer_master_clean.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  CSV: {csv_path}")

    # 샘플 저장
    sample_path = Path('bridges/anticancer_master_clean_sample.json')
    with open(sample_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data[:10], f, ensure_ascii=False, indent=2)
    print(f"  Sample: {sample_path}")

    # 4. 통계
    print("\n[4/4] Statistics")
    print(f"  Total ingredients: {len(cleaned_data)}")

    # 브랜드명 추출 성공률
    has_brand = sum(1 for item in cleaned_data if item['brand_name_primary'])
    print(f"  Ingredients with clean brand: {has_brand}/{len(cleaned_data)} ({has_brand/len(cleaned_data)*100:.1f}%)")

    # 한글 성분명 추출 성공률
    has_korean = sum(1 for item in cleaned_data if item['ingredient_ko_extracted'])
    print(f"  Ingredients with Korean name: {has_korean}/{len(cleaned_data)} ({has_korean/len(cleaned_data)*100:.1f}%)")

    # 브랜드명 중복도 (동일 브랜드 → 다른 성분)
    all_brands = defaultdict(set)
    for item in cleaned_data:
        for brand in item['brand_names_clean']:
            all_brands[brand].add(item['ingredient_ko'])

    multi_ingredient_brands = {brand: ingredients for brand, ingredients in all_brands.items() if len(ingredients) > 1}
    if multi_ingredient_brands:
        print(f"\n  ⚠️  Brands with multiple ingredients: {len(multi_ingredient_brands)}")
        for brand, ingredients in list(multi_ingredient_brands.items())[:5]:
            print(f"    - {brand}: {', '.join(ingredients)}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(clean_anticancer_master())
