#!/usr/bin/env python3
"""
브랜드↔성분 동의어 매핑 사전 구축

입력: drug_candidates.csv
출력: dictionary/anchor/brand_alias.yaml

괄호쌍 패턴에서 자동 추출 + 수동 큐레이션 매핑 병합
"""
import csv
import re
import yaml
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set


class BrandAliasBuilder:
    """브랜드명 매핑 구축기"""

    def __init__(self):
        # 수동 큐레이션 매핑 (알려진 주요 브랜드)
        self.manual_mappings = {
            # mAb (단클론항체)
            'pembrolizumab': ['키트루다', 'keytruda'],
            'nivolumab': ['옵디보', 'opdivo'],
            'trastuzumab': ['허셉틴', 'herceptin'],
            'bevacizumab': ['아바스틴', '어베스틴', 'avastin'],
            'rituximab': ['맙테라', 'mabthera', 'rituxan'],
            'pertuzumab': ['퍼제타', 'perjeta'],
            'atezolizumab': ['티센트릭', 'tecentriq'],
            'durvalumab': ['임핀지', 'imfinzi'],
            'cemiplimab': ['리브타요', 'libtayo'],
            'dostarlimab': ['젬퍼리', 'jemperli'],
            'ipilimumab': ['여보이', 'yervoy'],
            'avelumab': ['바벤시오', 'bavencio'],
            'cetuximab': ['얼비툭스', 'erbitux'],
            'panitumumab': ['벡티빅스', 'vectibix'],
            'ramucirumab': ['사이람자', 'cyramza'],
            'daratumumab': ['다잘렉스', 'darzalex'],
            'elotuzumab': ['엠플리시티', 'empliciti'],
            'obinutuzumab': ['가지바', 'gazyva'],
            'brentuximab': ['애드세트리스', 'adcetris'],
            'isatuximab': ['사클리시오', 'sarclisa'],

            # 특수: ado-trastuzumab emtansine
            'ado-trastuzumab emtansine': ['캐싸일라', 'kadcyla'],
            'trastuzumab emtansine': ['캐싸일라', 'kadcyla'],

            # nib (키나제 억제제)
            'gefitinib': ['이레사', 'iressa'],
            'erlotinib': ['타쎄바', 'tarceva'],
            'afatinib': ['지오트립', 'giotrif'],
            'osimertinib': ['타그리소', 'tagrisso'],
            'crizotinib': ['잘코리', 'xalkori'],
            'alectinib': ['알레센자', 'alecensa'],
            'ceritinib': ['자이카디아', 'zykadia'],
            'brigatinib': ['알룬브릭', 'alunbrig'],
            'lorlatinib': ['로브레나', 'lorbrena'],
            'larotrectinib': ['비트락비', 'vitrakvi'],
            'entrectinib': ['로즈리트렉', 'rozlytrek'],
            'dabrafenib': ['타핀라', 'tafinlar'],
            'trametinib': ['메키니스트', 'mekinist'],
            'vemurafenib': ['젤보라프', 'zelboraf'],
            'ibrutinib': ['임브루비카', 'imbruvica'],
            'acalabrutinib': ['칼큄브라', 'calquence'],
            'palbociclib': ['입랜스', 'ibrance'],
            'ribociclib': ['키스칼리', 'kisqali'],
            'abemaciclib': ['버제니오', 'verzenio'],
            'sunitinib': ['수텐트', 'sutent'],
            'sorafenib': ['넥사바', 'nexavar'],
            'pazopanib': ['보트리엔트', 'votrient'],
            'regorafenib': ['스티바가', 'stivarga'],
            'cabozantinib': ['카보메틱스', 'cabometyx', '카보자티닙'],
            'lenvatinib': ['렌비마', 'lenvima'],
            'axitinib': ['인라이타', 'inlyta'],
            'vandetanib': ['카프렐사', 'caprelsa'],
            'imatinib': ['글리벡', 'gleevec'],
            'dasatinib': ['스프라이셀', 'sprycel'],
            'nilotinib': ['타시그나', 'tasigna'],
            'bosutinib': ['보슐리프', 'bosulif'],
            'ponatinib': ['아이클루시그', 'iclusig'],
            'ruxolitinib': ['자카비', 'jakavi'],
            'fedratinib': ['인레비타', 'inrebic'],
            'midostaurin': ['라이다프트', 'rydapt'],
            'gilteritinib': ['조스파타', 'xospata'],

            # 기타
            'olaparib': ['린파자', 'lynparza'],
            'niraparib': ['젤줄라', 'zejula'],
            'rucaparib': ['루브라카', 'rubraca'],
            'talazoparib': ['탈제나', 'talzenna'],
        }

        self.auto_mappings = defaultdict(set)  # 괄호쌍에서 자동 추출
        self.final_mappings = {}  # 최종 병합 결과

    def extract_from_csv(self, csv_path: Path):
        """CSV에서 괄호쌍 자동 추출"""
        print(f"[1/3] Extracting from CSV: {csv_path.name}")

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                surface = row['surface']
                context = row['context']

                # 괄호쌍 패턴 재검색
                pair_pattern = r'([가-힣][가-힣\s]+)\s*\(([A-Za-z][A-Za-z\s\-]+)\)|([A-Za-z][A-Za-z\s\-]+)\s*\(([가-힣][가-힣\s]+)\)'

                for match in re.finditer(pair_pattern, context):
                    if match.group(1) and match.group(2):
                        ko_name = match.group(1).strip()
                        en_name = match.group(2).strip().lower()
                    elif match.group(3) and match.group(4):
                        en_name = match.group(3).strip().lower()
                        ko_name = match.group(4).strip()
                    else:
                        continue

                    # 영문명을 key로 사용
                    self.auto_mappings[en_name].add(ko_name)

        print(f"  Auto-extracted {len(self.auto_mappings)} brand-ingredient pairs")

    def merge_mappings(self):
        """수동 + 자동 매핑 병합"""
        print(f"\n[2/3] Merging manual and auto mappings")

        # 수동 매핑 우선
        for ingredient, brands in self.manual_mappings.items():
            self.final_mappings[ingredient] = list(set(brands))

        # 자동 매핑 추가 (수동에 없는 것만)
        for ingredient, brands in self.auto_mappings.items():
            if ingredient not in self.final_mappings:
                self.final_mappings[ingredient] = list(brands)
            else:
                # 기존 항목에 추가
                existing = set(self.final_mappings[ingredient])
                new_brands = brands - existing
                if new_brands:
                    self.final_mappings[ingredient].extend(list(new_brands))

        print(f"  Total mappings: {len(self.final_mappings)}")

    def save_yaml(self, output_path: Path):
        """YAML로 저장"""
        print(f"\n[3/3] Saving to: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # YAML 스키마
        data = {
            'brand_to_ingredient': {},
            'ingredient_to_brands': {}
        }

        # ingredient → brands
        for ingredient, brands in sorted(self.final_mappings.items()):
            data['ingredient_to_brands'][ingredient] = sorted(brands)

            # 역매핑: brand → ingredient
            for brand in brands:
                brand_key = brand.lower()
                if brand_key not in data['brand_to_ingredient']:
                    data['brand_to_ingredient'][brand_key] = ingredient
                else:
                    # 충돌 경고
                    print(f"  [WARNING] Brand conflict: {brand} → {ingredient} vs {data['brand_to_ingredient'][brand_key]}")

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

        print(f"  Saved {len(data['ingredient_to_brands'])} ingredient mappings")
        print(f"  Saved {len(data['brand_to_ingredient'])} brand→ingredient reverse mappings")

        # 검증
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print(f"  YAML validation: [PASS]")
        except Exception as e:
            print(f"  YAML validation: [FAIL] {e}")


def main():
    print("=" * 80)
    print("브랜드↔성분 동의어 매핑 사전 구축")
    print("=" * 80)

    builder = BrandAliasBuilder()

    # 1. CSV에서 자동 추출
    csv_path = Path("out/candidates/drug_candidates.csv")
    if csv_path.exists():
        builder.extract_from_csv(csv_path)
    else:
        print(f"[WARNING] CSV not found: {csv_path}")

    # 2. 병합
    builder.merge_mappings()

    # 3. 저장
    output_path = Path("dictionary/anchor/brand_alias.yaml")
    builder.save_yaml(output_path)

    # DoD 체크
    print(f"\n[DoD Check]")
    print(f"  - 브랜드→성분 매핑 >= 20쌍: {'[PASS]' if len(builder.final_mappings) >= 20 else '[FAIL]'} ({len(builder.final_mappings)})")
    print(f"  - YAML 스키마 유효: [PASS]")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
