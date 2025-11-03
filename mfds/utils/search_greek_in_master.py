#!/usr/bin/env python3
"""
전체 약가 마스터에서 그리스 문자 검색

목적: drug_dictionary.json 전체 데이터에서 그리스 문자 포함 약물 추출
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Set


class MasterGreekSearcher:
    """약가 마스터 그리스 문자 검색"""

    # 그리스 문자 유니코드 범위
    GREEK_LETTERS = set('αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ')
    GREEK_PATTERN = re.compile(f"[{''.join(GREEK_LETTERS)}]")

    # 단위 기호 (그리스 문자처럼 보이지만 제외해야 함)
    EXCLUDED_UNITS = {'μg', 'μL', 'μm', 'μS', 'μmol', 'μM', 'μPa'}

    def __init__(self):
        self.drugs_with_greek = []
        self.greek_chars_found = set()

    def has_greek_letters(self, text: str) -> bool:
        """텍스트에 그리스 문자 포함 여부 확인"""
        if not text:
            return False
        return bool(self.GREEK_PATTERN.search(text))

    def is_unit_symbol(self, text: str, match_pos: int) -> bool:
        """μ가 단위 기호인지 확인"""
        if match_pos + 1 < len(text):
            for unit in self.EXCLUDED_UNITS:
                if text[match_pos:match_pos+len(unit)] == unit:
                    return True
        return False

    def extract_greek_chars(self, text: str) -> List[str]:
        """텍스트에서 그리스 문자만 추출 (단위 제외)"""
        chars = []
        for i, char in enumerate(text):
            if char in self.GREEK_LETTERS:
                # μ가 단위 기호인지 확인
                if char == 'μ' and self.is_unit_symbol(text, i):
                    continue
                chars.append(char)
        return list(set(chars))

    def search_dictionary(self, dict_path: Path) -> List[Dict]:
        """
        drug_dictionary.json에서 그리스 문자 검색

        Returns:
            [{'product_name': '...', 'ingredient_code': '...', 'greek_chars': [...]}]
        """
        print(f"[LOAD] Loading {dict_path}...")
        with open(dict_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"  → Loaded {len(data)} product entries")

        results = []
        processed = 0

        for product_key, product_data in data.items():
            processed += 1
            if processed % 1000 == 0:
                print(f"  [PROGRESS] {processed}/{len(data)} processed...")

            # 제품명 검색
            if self.has_greek_letters(product_key):
                greek_chars = self.extract_greek_chars(product_key)
                if greek_chars:  # 단위 기호 제외 후에도 그리스 문자가 있으면
                    self.greek_chars_found.update(greek_chars)

                    # 레코드 정보 추출
                    records = product_data.get('records', [])
                    if records:
                        sample_record = records[0]
                        results.append({
                            'product_name': product_key,
                            'product_name_full': sample_record.get('product_name', ''),
                            'ingredient_code': sample_record.get('ingredient_code', ''),
                            'company': sample_record.get('company', ''),
                            'greek_chars': greek_chars,
                            'record_count': len(records)
                        })

            # records 내부의 product_name도 검색
            for record in product_data.get('records', []):
                full_name = record.get('product_name', '')
                if self.has_greek_letters(full_name):
                    greek_chars = self.extract_greek_chars(full_name)
                    if greek_chars:
                        self.greek_chars_found.update(greek_chars)

                        # 이미 추가되지 않은 경우만 추가
                        if not any(r['product_name'] == product_key for r in results):
                            results.append({
                                'product_name': product_key,
                                'product_name_full': full_name,
                                'ingredient_code': record.get('ingredient_code', ''),
                                'company': record.get('company', ''),
                                'greek_chars': greek_chars,
                                'record_count': len(product_data.get('records', []))
                            })

        print(f"\n[SEARCH] Complete!")
        print(f"  Total products scanned: {len(data)}")
        print(f"  Products with Greek letters: {len(results)}")

        return results

    def save_results(self, drugs: List[Dict], output_path: Path):
        """결과 저장"""
        summary = {
            'total_count': len(drugs),
            'greek_chars_found': sorted(list(self.greek_chars_found)),
            'drugs': sorted(drugs, key=lambda x: x['product_name'])
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVE] Results saved to: {output_path}")
        print(f"  Total drugs: {summary['total_count']}")
        print(f"  Greek letters found: {', '.join(summary['greek_chars_found'])}")


def main():
    """실행"""
    import argparse

    parser = argparse.ArgumentParser(description='Search Greek letters in drug master')
    parser.add_argument('--input', '-i',
                        default='data/hira_master/drug_dictionary.json',
                        help='Drug dictionary JSON path')
    parser.add_argument('--output', '-o',
                        default='data/mfds/greek_drugs_master.json',
                        help='Output JSON path')

    args = parser.parse_args()

    # 경로 설정
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return 1

    print("=" * 80)
    print("약가 마스터 그리스 문자 검색")
    print("=" * 80)
    print()

    # 검색 실행
    searcher = MasterGreekSearcher()
    drugs = searcher.search_dictionary(input_path)

    if not drugs:
        print("\n[INFO] No drugs with Greek letters found")
        return 0

    # 결과 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    searcher.save_results(drugs, output_path)

    # 샘플 출력
    print(f"\n[SAMPLE] First 10 drugs:")
    for i, drug in enumerate(drugs[:10], 1):
        print(f"\n  {i}. {drug['product_name']}")
        print(f"     Full name: {drug['product_name_full']}")
        print(f"     Greek chars: {', '.join(drug['greek_chars'])}")
        print(f"     Ingredient: {drug['ingredient_code']}")
        print(f"     Company: {drug['company']}")

    if len(drugs) > 10:
        print(f"\n  ... and {len(drugs) - 10} more")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
