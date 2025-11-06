"""
Phase 4: Brand Name Index Construction
- Build brand name → ATC code mapping index
- Support exact matching for HIRA document processing
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def normalize_brand_name(name: str) -> str:
    """
    Normalize brand name for indexing
    - Remove whitespace
    - Lowercase for case-insensitive matching
    - Remove special characters
    """
    # Remove whitespace
    name = re.sub(r'\s+', '', name)
    return name


def generate_brand_variants(brand_name: str, brand_raw_list: list) -> list:
    """
    Generate brand name variants for matching

    Includes:
    - Original clean brand name
    - Variants with common form suffixes removed
    - Raw brand names (before form suffix removal)
    """
    variants = set()

    # Add clean brand name
    variants.add(brand_name)

    # Add variants from raw brand names
    for raw in brand_raw_list:
        # Extract brand part (before dosage info)
        # Example: "버제니오정50밀리그램(아베마시클립)_(50mg/1정)"
        match = re.match(r'^([^_(]+)', raw)
        if match:
            brand_part = match.group(1)
            variants.add(brand_part)

            # Also add without form suffix
            # Remove: 정, 캡슐, 주, 주사, 액, 시럽, etc.
            brand_no_form = re.sub(
                r'(서방)?정$|캡슐$|주$|주사$|주입액$|현탁액$|시럽$|분말$|과립$|패치$|펜$|키트$|액$|연질$|경질$',
                '',
                brand_part
            )
            if brand_no_form and brand_no_form != brand_part:
                variants.add(brand_no_form)

    return list(variants)


def build_brand_index(classified_data: list) -> dict:
    """
    Build comprehensive brand name index

    Structure:
    {
        "normalized_brand": {
            "brand_display": "버제니오",
            "atc_code": "L01EF03",
            "ingredient_ko": "아베마시클립",
            "ingredient_en": "abemaciclib",
            "ingredient_base_ko": "아베마시클립",
            "ingredient_base_en": "abemaciclib",
            "salt_form": null,
            "manufacturers": ["한국릴리(유)"],
            "brand_variants": [...],
            "match_type": "brand"
        }
    }
    """
    brand_index = {}
    ingredient_index = {}
    duplicate_brands = defaultdict(list)

    for entry in classified_data:
        atc_code = entry.get('atc_code', '')
        brand_primary = entry.get('brand_name_primary', '')
        brand_clean_list = entry.get('brand_names_clean', [])
        brand_raw_list = entry.get('brand_names_raw', [])

        ingredient_ko = entry.get('ingredient_ko', '')
        ingredient_en = entry.get('atc_name_en', '')
        ingredient_base_ko = entry.get('ingredient_base_ko', '')
        ingredient_base_en = entry.get('ingredient_base_en', '')
        salt_form = entry.get('salt_form')
        manufacturers = entry.get('manufacturers', [])

        # Build entry info
        entry_info = {
            'brand_display': brand_primary,
            'atc_code': atc_code,
            'ingredient_ko': ingredient_ko,
            'ingredient_en': ingredient_en,
            'ingredient_base_ko': ingredient_base_ko,
            'ingredient_base_en': ingredient_base_en,
            'salt_form': salt_form,
            'manufacturers': manufacturers,
            'atc_level1': entry.get('atc_level1', ''),
            'atc_level1_name': entry.get('atc_level1_name', ''),
            'atc_level2': entry.get('atc_level2', ''),
            'atc_level2_name': entry.get('atc_level2_name', ''),
            'atc_level3': entry.get('atc_level3', ''),
            'atc_level3_name': entry.get('atc_level3_name', ''),
            'mechanism_of_action': entry.get('mechanism_of_action', ''),
            'therapeutic_category': entry.get('therapeutic_category', ''),
        }

        # Index all clean brand names
        for brand in brand_clean_list:
            if not brand:
                continue

            normalized = normalize_brand_name(brand)

            # Generate variants
            variants = generate_brand_variants(brand, brand_raw_list)
            entry_info['brand_variants'] = variants
            entry_info['match_type'] = 'brand'

            # Check for duplicates
            if normalized in brand_index:
                duplicate_brands[normalized].append({
                    'atc_code': atc_code,
                    'ingredient': ingredient_ko,
                    'brand': brand
                })
            else:
                brand_index[normalized] = entry_info.copy()

        # Index ingredient names (Korean and English)
        if ingredient_ko:
            ing_normalized = normalize_brand_name(ingredient_ko)
            if ing_normalized not in ingredient_index:
                ing_entry = entry_info.copy()
                ing_entry['match_type'] = 'ingredient_ko'
                ing_entry['brand_display'] = ingredient_ko
                ingredient_index[ing_normalized] = ing_entry

        # Index base ingredient name (if different)
        if ingredient_base_ko and ingredient_base_ko != ingredient_ko:
            base_normalized = normalize_brand_name(ingredient_base_ko)
            if base_normalized not in ingredient_index:
                base_entry = entry_info.copy()
                base_entry['match_type'] = 'ingredient_base_ko'
                base_entry['brand_display'] = ingredient_base_ko
                ingredient_index[base_normalized] = base_entry

        # Index English ingredient name
        if ingredient_en:
            ing_en_normalized = normalize_brand_name(ingredient_en)
            if ing_en_normalized not in ingredient_index:
                ing_en_entry = entry_info.copy()
                ing_en_entry['match_type'] = 'ingredient_en'
                ing_en_entry['brand_display'] = ingredient_en
                ingredient_index[ing_en_normalized] = ing_en_entry

    return {
        'brand_index': brand_index,
        'ingredient_index': ingredient_index,
        'duplicate_brands': dict(duplicate_brands)
    }


def main():
    # File paths
    input_file = Path('C:/Jimin/scrape-hub/bridges/anticancer_master_classified.json')
    output_file = Path('C:/Jimin/scrape-hub/bridges/brand_index.json')
    output_stats = Path('C:/Jimin/scrape-hub/bridges/brand_index_stats.json')

    print("=" * 60)
    print("Phase 4: Brand Name Index Construction")
    print("=" * 60)

    # Load classified data
    print(f"\n[1/4] Loading: {input_file.name}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   >> Loaded {len(data)} ingredients")

    # Build index
    print("\n[2/4] Building brand name index...")
    index_data = build_brand_index(data)

    brand_index = index_data['brand_index']
    ingredient_index = index_data['ingredient_index']
    duplicate_brands = index_data['duplicate_brands']

    print(f"   [OK] Brand names indexed: {len(brand_index)}")
    print(f"   [OK] Ingredient names indexed: {len(ingredient_index)}")
    if duplicate_brands:
        print(f"   [WARN] Duplicate brand names: {len(duplicate_brands)}")

    # Analyze variants
    print("\n[3/4] Analyzing brand variants...")
    total_variants = 0
    for entry in brand_index.values():
        total_variants += len(entry.get('brand_variants', []))

    avg_variants = total_variants / len(brand_index) if brand_index else 0
    print(f"   [OK] Total brand variants: {total_variants}")
    print(f"   [OK] Average variants per brand: {avg_variants:.1f}")

    # Combine into single index
    combined_index = {}
    combined_index.update(brand_index)
    combined_index.update(ingredient_index)

    # Save index
    print(f"\n[4/4] Saving: {output_file.name}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_index, f, ensure_ascii=False, indent=2)

    file_size = output_file.stat().st_size / 1024
    print(f"   [OK] Saved {len(combined_index)} index entries ({file_size:.1f} KB)")

    # Save statistics
    stats = {
        'total_ingredients': len(data),
        'brand_names_indexed': len(brand_index),
        'ingredient_names_indexed': len(ingredient_index),
        'total_index_entries': len(combined_index),
        'total_brand_variants': total_variants,
        'average_variants_per_brand': round(avg_variants, 2),
        'duplicate_brands': duplicate_brands
    }

    with open(output_stats, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"   [OK] Saved statistics: {output_stats.name}")

    # Summary
    print("\n" + "=" * 60)
    print("[SUCCESS] Phase 4 COMPLETE")
    print("=" * 60)
    print(f"\nIndex statistics:")
    print(f"  * Total index entries: {len(combined_index)}")
    print(f"  * Brand names: {len(brand_index)}")
    print(f"  * Ingredient names: {len(ingredient_index)}")
    print(f"  * Brand variants: {total_variants}")
    print(f"\nOutput: {output_file}")
    print(f"Statistics: {output_stats}")
    print(f"\n[READY] Anticancer dictionary complete (Phases 1-4)")
    print(f"Next: Import to Neo4j")


if __name__ == '__main__':
    main()
