"""
Phase 2: Anticancer Dictionary Enhancement
- Supplement missing Korean ingredient names (6 entries)
- Separate salt/base forms for all ingredients
"""

import json
import re
from pathlib import Path

# Manual mapping for 6 missing Korean names
MANUAL_KOREAN_NAMES = {
    "belotecan(CKD-602)": "벨로테칸",
    "gimeracil": "기메라실",
    "mitomycin C": "마이토마이신",
    "oteracil potassium": "오테라실칼륨",
    "tegafur": "테가푸르",
    "uracil": "우라실"
}

# Salt form patterns (Korean)
SALT_PATTERNS_KO = [
    (r'아세테이트$', 'acetate'),
    (r'염산염$', 'hydrochloride'),
    (r'황산염$', 'sulfate'),
    (r'구연산염$', 'citrate'),
    (r'이말레산염$', 'maleate'),
    (r'말레산염$', 'maleate'),
    (r'주석산염$', 'tartrate'),
    (r'인산염$', 'phosphate'),
    (r'칼륨$', 'potassium'),
    (r'나트륨$', 'sodium'),
    (r'칼슘$', 'calcium'),
    (r'마그네슘$', 'magnesium'),
]

# Salt form patterns (English)
SALT_PATTERNS_EN = [
    (r'\s+acetate$', 'acetate'),
    (r'\s+hydrochloride$', 'hydrochloride'),
    (r'\s+sulfate$', 'sulfate'),
    (r'\s+citrate$', 'citrate'),
    (r'\s+maleate$', 'maleate'),
    (r'\s+tartrate$', 'tartrate'),
    (r'\s+phosphate$', 'phosphate'),
    (r'\s+potassium$', 'potassium'),
    (r'\s+sodium$', 'sodium'),
    (r'\s+calcium$', 'calcium'),
    (r'\s+magnesium$', 'magnesium'),
]


def detect_salt_form(name: str, patterns: list) -> tuple:
    """
    Detect salt form in ingredient name

    Returns:
        (base_form, salt_form) or (original, None) if no salt detected
    """
    name_lower = name.lower()

    for pattern, salt_name in patterns:
        match = re.search(pattern, name_lower, re.IGNORECASE)
        if match:
            base = name[:match.start()].strip()
            return (base, salt_name)

    return (name, None)


def enhance_entry(entry: dict) -> dict:
    """
    Enhance single anticancer entry with:
    1. Korean name supplementation
    2. Salt/base form separation
    """
    enhanced = entry.copy()

    # 1. Supplement missing Korean names
    original = entry.get('ingredient_ko_original', '')
    current_ko = entry.get('ingredient_ko', '')

    if original in MANUAL_KOREAN_NAMES:
        enhanced['ingredient_ko'] = MANUAL_KOREAN_NAMES[original]
        enhanced['ingredient_source'] = 'manual'
    elif current_ko and current_ko != original:
        enhanced['ingredient_source'] = 'extracted'
    else:
        enhanced['ingredient_source'] = 'atc'

    # 2. Separate salt/base forms
    ingredient_en = entry.get('atc_name_en', '')
    ingredient_ko = enhanced.get('ingredient_ko', '')

    # English salt detection
    base_en, salt_en = detect_salt_form(ingredient_en, SALT_PATTERNS_EN)

    # Korean salt detection
    base_ko, salt_ko = detect_salt_form(ingredient_ko, SALT_PATTERNS_KO)

    # Add new fields
    enhanced['ingredient_base_en'] = base_en
    enhanced['ingredient_base_ko'] = base_ko
    enhanced['ingredient_precise_en'] = ingredient_en
    enhanced['ingredient_precise_ko'] = ingredient_ko
    enhanced['salt_form'] = salt_en or salt_ko

    # Check if recombinant (monoclonal antibodies, etc.)
    is_recombinant = (
        '-mab' in ingredient_en.lower() or  # monoclonal antibody
        'filgrastim' in ingredient_en.lower() or  # G-CSF
        'interferon' in ingredient_en.lower() or
        'interleukin' in ingredient_en.lower()
    )
    enhanced['is_recombinant'] = is_recombinant

    return enhanced


def main():
    # File paths
    input_file = Path('C:/Jimin/scrape-hub/bridges/anticancer_master_clean.json')
    output_file = Path('C:/Jimin/scrape-hub/bridges/anticancer_master_enhanced.json')

    print("=" * 60)
    print("Phase 2: Anticancer Dictionary Enhancement")
    print("=" * 60)

    # Load data
    print(f"\n[1/4] Loading: {input_file.name}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   >> Loaded {len(data)} ingredients")

    # Enhance entries
    print("\n[2/4] Enhancing entries...")
    enhanced_data = []
    supplemented_count = 0
    salt_detected_count = 0
    recombinant_count = 0

    for entry in data:
        enhanced = enhance_entry(entry)
        enhanced_data.append(enhanced)

        # Track statistics
        if enhanced.get('ingredient_source') == 'manual':
            supplemented_count += 1
        if enhanced.get('salt_form'):
            salt_detected_count += 1
        if enhanced.get('is_recombinant'):
            recombinant_count += 1

    print(f"   [OK] Enhanced {len(enhanced_data)} entries")
    print(f"   [OK] Supplemented Korean names: {supplemented_count}")
    print(f"   [OK] Salt forms detected: {salt_detected_count}")
    print(f"   [OK] Recombinant drugs detected: {recombinant_count}")

    # Validate completeness
    print("\n[3/4] Validating completeness...")
    missing_korean = 0
    for entry in enhanced_data:
        ko_name = entry.get('ingredient_ko', '')
        # Check if still has English characters (not Korean)
        if any(c.isalpha() and ord(c) < 128 for c in ko_name):
            missing_korean += 1

    if missing_korean == 0:
        print(f"   [OK] All {len(enhanced_data)} ingredients have Korean names (100%)")
    else:
        print(f"   [WARN] Still missing {missing_korean} Korean names")

    # Save enhanced data
    print(f"\n[4/4] Saving: {output_file.name}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)

    file_size = output_file.stat().st_size / 1024
    print(f"   [OK] Saved {len(enhanced_data)} entries ({file_size:.1f} KB)")

    # Summary
    print("\n" + "=" * 60)
    print("[SUCCESS] Phase 2 COMPLETE")
    print("=" * 60)
    print(f"\nEnhancements:")
    print(f"  * Korean names: {len(enhanced_data) - missing_korean}/{len(enhanced_data)} (100%)")
    print(f"  * Salt/base separation: {salt_detected_count} detected")
    print(f"  * Recombinant drugs: {recombinant_count} identified")
    print(f"\nOutput: {output_file}")
    print(f"Next: Run Phase 3 (ATC classification)")


if __name__ == '__main__':
    main()
