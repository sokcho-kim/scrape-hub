#!/usr/bin/env python3
"""
CSV 후보 → JSON (en-ko 쌍) 변환

입력: out/candidates/drug_candidates.csv
출력: out/candidates/drug_candidates.json

전략:
1. Context에서 괄호쌍 추출
2. Brand alias 사전 활용
3. En-ko 매칭하여 쌍 생성
"""
import csv
import json
import yaml
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def extract_pairs_from_context(context: str) -> List[Tuple[str, str]]:
    """컨텍스트에서 영문(한글) 또는 한글(영문) 괄호쌍 추출"""
    pair_pattern = r'([가-힣][가-힣\s]+)\s*\(([A-Za-z][A-Za-z\s\-]+)\)|([A-Za-z][A-Za-z\s\-]+)\s*\(([가-힣][가-힣\s]+)\)'

    pairs = []
    for match in re.finditer(pair_pattern, context):
        if match.group(1) and match.group(2):
            ko = match.group(1).strip()
            en = match.group(2).strip().lower()
            pairs.append((en, ko))
        elif match.group(3) and match.group(4):
            en = match.group(3).strip().lower()
            ko = match.group(4).strip()
            pairs.append((en, ko))

    return pairs


def main():
    print("=" * 80)
    print("CSV → JSON (en-ko 쌍) 변환")
    print("=" * 80)

    # 1. Brand alias 로드
    brand_alias_path = Path("dictionary/anchor/brand_alias.yaml")
    brand_to_ingredient = {}
    ingredient_to_brands = {}

    if brand_alias_path.exists():
        with open(brand_alias_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            brand_to_ingredient = data.get('brand_to_ingredient', {})
            ingredient_to_brands = data.get('ingredient_to_brands', {})
        print(f"[1/4] Loaded {len(brand_to_ingredient)} brand mappings")

    # 2. CSV 읽기
    csv_path = Path("out/candidates/drug_candidates.csv")
    en_items = defaultdict(list)  # en -> [contexts]
    ko_items = defaultdict(list)  # ko -> [contexts]

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            surface = row['surface']
            lang = row['lang']
            context = row['context']

            if lang == 'en':
                en_items[surface.lower()].append(context)
            else:  # ko
                ko_items[surface].append(context)

    print(f"[2/4] Loaded {len(en_items)} EN and {len(ko_items)} KO items from CSV")

    # 3. En-ko 쌍 생성
    pairs = {}  # (en, ko) -> count
    pair_contexts = {}  # (en, ko) -> context

    # 전략 1: Context에서 괄호쌍 직접 추출
    for en, contexts in en_items.items():
        for context in contexts:
            extracted_pairs = extract_pairs_from_context(context)
            for en_extracted, ko_extracted in extracted_pairs:
                if en in en_extracted or en_extracted in en:  # 부분 매칭
                    key = (en_extracted, ko_extracted)
                    pairs[key] = pairs.get(key, 0) + 1
                    if key not in pair_contexts:
                        pair_contexts[key] = context[:200]

    # 전략 2: Brand alias 사전 활용
    for en in en_items.keys():
        # 브랜드명 → 성분명 변환
        if en in brand_to_ingredient:
            ingredient = brand_to_ingredient[en]
            # 성분명 → 브랜드명 목록
            if ingredient in ingredient_to_brands:
                for brand in ingredient_to_brands[ingredient]:
                    if brand and '가' <= brand[0] <= '힣':  # 한글인 경우
                        key = (ingredient, brand)
                        pairs[key] = pairs.get(key, 0) + 1
                        if key not in pair_contexts:
                            pair_contexts[key] = en_items[en][0][:200] if en_items[en] else ""

    # 전략 3: 영문 성분명이 ingredient_to_brands에 있으면 한글 브랜드 매핑
    for en in en_items.keys():
        if en in ingredient_to_brands:
            for brand in ingredient_to_brands[en]:
                if brand and '가' <= brand[0] <= '힣':  # 한글인 경우
                    key = (en, brand)
                    pairs[key] = pairs.get(key, 0) + 1
                    if key not in pair_contexts:
                        pair_contexts[key] = en_items[en][0][:200] if en_items[en] else ""

    print(f"[3/4] Generated {len(pairs)} en-ko pairs")

    # 4. JSON 생성
    output = {
        'matched_via_english': [
            {
                'english': en,
                'korean': ko,
                'count': count,
                'source': 'csv_converted',
                'context': pair_contexts.get((en, ko), '')
            }
            for (en, ko), count in sorted(pairs.items(), key=lambda x: -x[1])
        ]
    }

    output_path = Path("out/candidates/drug_candidates.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[4/4] Saved {len(output['matched_via_english'])} pairs to {output_path}")

    # 통계
    print(f"\n[Statistics]")
    print(f"  - Total pairs: {len(pairs)}")
    print(f"  - Top 10 pairs by count:")
    for (en, ko), count in sorted(pairs.items(), key=lambda x: -x[1])[:10]:
        print(f"    {en} → {ko}: {count}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
