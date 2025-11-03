#!/usr/bin/env python3
"""
약전 파싱 데이터에서 그리스 문자 포함 약물 추출

목적: 정규화가 필요한 약물만 선별하여 처리
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Set


class GreekDrugExtractor:
    """그리스 문자 포함 약물 추출기"""

    # 그리스 문자 유니코드 범위
    GREEK_LETTERS = set('αβγδεζηθικλμνξοπρστυφχψω')
    GREEK_PATTERN = re.compile(f"[{''.join(GREEK_LETTERS)}]")

    def __init__(self):
        self.drugs_with_greek = []

    def has_greek_letters(self, text: str) -> bool:
        """텍스트에 그리스 문자 포함 여부 확인"""
        if not text:
            return False
        return bool(self.GREEK_PATTERN.search(text))

    def extract_drug_names_from_json(self, json_path: Path) -> List[Dict]:
        """
        약전 JSON 파일에서 약물명 추출

        Returns:
            [{'name_en': '...', 'name_ko': '...', 'source': '...', 'greek_chars': [...]}]
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = []
        content = data.get('content', '')

        # HTML에서 약물명 추출 (간단한 패턴 매칭)
        # 실제로는 elements를 파싱해야 더 정확함

        # 제목 추출 (h1, h2 태그)
        title_pattern = re.compile(r'<h[12][^>]*>(.*?)</h[12]>', re.IGNORECASE)
        titles = title_pattern.findall(content)

        for title in titles:
            # HTML 태그 제거
            clean_title = re.sub(r'<[^>]+>', '', title).strip()

            if self.has_greek_letters(clean_title):
                greek_chars = self._extract_greek_chars(clean_title)
                results.append({
                    'name': clean_title,
                    'source_file': json_path.name,
                    'greek_chars': greek_chars,
                    'type': 'title'
                })

        return results

    def _extract_greek_chars(self, text: str) -> List[str]:
        """텍스트에서 그리스 문자만 추출"""
        return list(set([c for c in text if c in self.GREEK_LETTERS]))

    def extract_from_elements(self, json_path: Path) -> List[Dict]:
        """
        elements 필드에서 더 정확하게 약물명 추출
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = []
        elements = data.get('elements', [])

        for elem in elements:
            # 제목 요소만 추출
            if elem.get('category') in ['heading1', 'heading2', 'title']:
                text = elem.get('text', '').strip()

                if self.has_greek_letters(text):
                    greek_chars = self._extract_greek_chars(text)
                    results.append({
                        'name': text,
                        'source_file': json_path.name,
                        'source_page': elem.get('page', 0),
                        'greek_chars': greek_chars,
                        'category': elem.get('category'),
                        'confidence': elem.get('confidence', 1.0)
                    })

        return results

    def scan_directory(self, parsed_dir: Path, use_elements: bool = True) -> List[Dict]:
        """
        파싱된 약전 디렉토리 전체 스캔

        Args:
            parsed_dir: 파싱된 JSON 파일들이 있는 디렉토리
            use_elements: True면 elements 필드 사용 (더 정확), False면 content 필드 사용

        Returns:
            그리스 문자 포함 약물 목록
        """
        all_drugs = []
        json_files = list(parsed_dir.glob('*.json'))

        print(f"[SCAN] Found {len(json_files)} JSON files in {parsed_dir}")

        for json_file in json_files:
            if json_file.name == 'parse_summary.json':
                continue

            print(f"[SCAN] Processing: {json_file.name}")

            try:
                if use_elements:
                    drugs = self.extract_from_elements(json_file)
                else:
                    drugs = self.extract_drug_names_from_json(json_file)

                all_drugs.extend(drugs)

                if drugs:
                    print(f"  → Found {len(drugs)} drugs with Greek letters")

            except Exception as e:
                print(f"  [ERROR] {e}")
                continue

        # 중복 제거 (이름 기준)
        unique_drugs = {}
        for drug in all_drugs:
            name = drug['name']
            if name not in unique_drugs:
                unique_drugs[name] = drug
            else:
                # 기존 항목에 소스 추가
                if 'sources' not in unique_drugs[name]:
                    unique_drugs[name]['sources'] = [unique_drugs[name]['source_file']]
                if drug['source_file'] not in unique_drugs[name]['sources']:
                    unique_drugs[name]['sources'].append(drug['source_file'])

        return list(unique_drugs.values())

    def save_results(self, drugs: List[Dict], output_path: Path):
        """결과 저장"""
        summary = {
            'total_count': len(drugs),
            'greek_chars_found': list(set(
                char for drug in drugs for char in drug['greek_chars']
            )),
            'drugs': sorted(drugs, key=lambda x: x['name'])
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVE] Results saved to: {output_path}")
        print(f"  Total drugs: {summary['total_count']}")
        print(f"  Greek letters found: {', '.join(summary['greek_chars_found'])}")


def main():
    """실행"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract drugs with Greek letters from KP parsed data')
    parser.add_argument('--input', '-i',
                        default='data/mfds/parsed_pdf',
                        help='Directory containing parsed JSON files')
    parser.add_argument('--output', '-o',
                        default='data/mfds/greek_drugs_list.json',
                        help='Output JSON path')
    parser.add_argument('--use-content', action='store_true',
                        help='Use content field instead of elements (less accurate)')

    args = parser.parse_args()

    # 경로 설정
    base_dir = Path(__file__).parent.parent.parent
    input_dir = base_dir / args.input
    output_path = base_dir / args.output

    if not input_dir.exists():
        print(f"[ERROR] Input directory not found: {input_dir}")
        return 1

    # 추출 실행
    extractor = GreekDrugExtractor()
    drugs = extractor.scan_directory(input_dir, use_elements=not args.use_content)

    if not drugs:
        print("\n[INFO] No drugs with Greek letters found")
        return 0

    # 결과 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    extractor.save_results(drugs, output_path)

    # 샘플 출력
    print(f"\n[SAMPLE] First 10 drugs:")
    for i, drug in enumerate(drugs[:10], 1):
        print(f"  {i}. {drug['name']} (Greek: {', '.join(drug['greek_chars'])})")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
