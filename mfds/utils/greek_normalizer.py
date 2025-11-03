#!/usr/bin/env python3
"""
약전 약물명 그리스 문자 정규화 및 동의어 생성기

KP12 통칙 기반:
- 원본 그리스 문자 보존 (preferred)
- ASCII 변환 동의어 생성 (alpha, beta 등)
- 한글 변환 동의어 생성 (알파, 베타 등)
- 단위 기호 제외 (μg, μL 등)
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Set


class GreekLetterNormalizer:
    """그리스 문자 정규화 및 동의어 생성"""

    def __init__(self, rules_path: str = None):
        """
        Args:
            rules_path: 정규화 규칙 JSON 경로 (기본: kp12_normalization_rules_v1.json)
        """
        if rules_path is None:
            rules_path = Path(__file__).parent.parent.parent / \
                "data/hira_master/normalization/kp12_normalization_rules_v1.json"

        with open(rules_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)

        self.greek_rules = rules['greek_letters']
        self.greek_to_ascii = self.greek_rules['mappings']
        self.greek_to_ko = self.greek_rules['mappings_ko']
        self.excluded_units = set(self.greek_rules['excluded_contexts'])

    def _is_unit_context(self, text: str, match_pos: int) -> bool:
        """μ가 단위 기호인지 확인 (μg, μL 등)"""
        # match_pos 이후 문자 확인
        if match_pos + 1 < len(text):
            next_char = text[match_pos + 1]
            # μ 다음에 g, L, m, S, M, Pa 등이 오면 단위로 판단
            if next_char in 'gLmSMP':
                # 전체 단위 추출
                unit_match = re.match(r'μ[a-zA-Z]+', text[match_pos:])
                if unit_match and unit_match.group() in self.excluded_units:
                    return True
        return False

    def generate_synonyms(self, name: str, is_english: bool = True) -> Dict[str, any]:
        """
        약물명에서 그리스 문자를 찾아 동의어 생성

        Args:
            name: 약물명 (예: "α-Tocopherol")
            is_english: True면 영문명, False면 한글명

        Returns:
            {
                'preferred': 원본 그리스 문자 유지,
                'synonyms_ascii': ASCII 변환 리스트,
                'synonyms_ko': 한글 변환 리스트,
                'has_greek': 그리스 문자 포함 여부
            }
        """
        result = {
            'preferred': name,
            'synonyms_ascii': [],
            'synonyms_ko': [],
            'has_greek': False
        }

        # 그리스 문자 감지
        greek_chars = set()
        for i, char in enumerate(name):
            if char in self.greek_to_ascii:
                # 단위 기호는 제외
                if char == 'μ' and self._is_unit_context(name, i):
                    continue
                greek_chars.add(char)

        if not greek_chars:
            return result

        result['has_greek'] = True

        # ASCII 변환
        ascii_name = name
        for greek, ascii_val in self.greek_to_ascii.items():
            if greek in greek_chars:
                # 단위가 아닌 위치만 치환
                ascii_name = self._safe_replace(name, greek, ascii_val)

        if ascii_name != name:
            result['synonyms_ascii'].append(ascii_name)

            # 하이픈 변형 생성 (alpha-tocopherol vs alphatocopherol)
            if '-' in ascii_name:
                no_hyphen = ascii_name.replace('-', '')
                if no_hyphen != ascii_name:
                    result['synonyms_ascii'].append(no_hyphen)

        # 한글 변환 (영문명인 경우만)
        if is_english:
            ko_name = name
            for greek, ko_val in self.greek_to_ko.items():
                if greek in greek_chars:
                    ko_name = self._safe_replace(name, greek, ko_val)

            if ko_name != name:
                result['synonyms_ko'].append(ko_name)

                # 한글에도 하이픈 변형
                if '-' in ko_name:
                    result['synonyms_ko'].append(ko_name.replace('-', ''))

        # 중복 제거
        result['synonyms_ascii'] = list(set(result['synonyms_ascii']))
        result['synonyms_ko'] = list(set(result['synonyms_ko']))

        return result

    def _safe_replace(self, text: str, greek: str, replacement: str) -> str:
        """단위 기호를 제외하고 그리스 문자만 치환"""
        result = []
        i = 0
        while i < len(text):
            if text[i] == greek:
                # μ인 경우 단위 체크
                if greek == 'μ' and self._is_unit_context(text, i):
                    result.append(greek)  # 단위는 그대로
                else:
                    result.append(replacement)
            else:
                result.append(text[i])
            i += 1
        return ''.join(result)

    def normalize_drug_name(self, name_en: str, name_ko: str = None) -> Dict:
        """
        약물명 전체 정규화 (영문 + 한글)

        Returns KP12 표준 스키마:
        {
            'name': {
                'preferred_en': '원본 영문',
                'synonyms_en': ['ASCII 변환', ...],
                'preferred_ko': '원본 한글',
                'synonyms_ko': ['한글 변환', ...]
            },
            'normalization': {
                'greek_to_ascii': True/False,
                'keep_units_symbols': True
            }
        }
        """
        en_result = self.generate_synonyms(name_en, is_english=True)

        output = {
            'name': {
                'preferred_en': name_en,
                'synonyms_en': en_result['synonyms_ascii']
            },
            'normalization': {
                'greek_to_ascii': en_result['has_greek'],
                'keep_units_symbols': True
            }
        }

        # 한글명이 제공된 경우
        if name_ko:
            ko_result = self.generate_synonyms(name_ko, is_english=False)
            output['name']['preferred_ko'] = name_ko
            output['name']['synonyms_ko'] = ko_result['synonyms_ko']

            # 영문→한글 변환도 추가
            if en_result['synonyms_ko']:
                output['name']['synonyms_ko'].extend(en_result['synonyms_ko'])
                output['name']['synonyms_ko'] = list(set(output['name']['synonyms_ko']))

        return output


def main():
    """테스트 및 예제"""
    normalizer = GreekLetterNormalizer()

    # 테스트 케이스
    test_cases = [
        ("α-Tocopherol", "알파-토코페롤"),
        ("β-Lactam", "베타-락탐"),
        ("γ-Globulin", None),
        ("Dexamethasone", None),  # 그리스 문자 없음
        ("Test μg/mL", None),  # 단위 포함 (변환 안됨)
    ]

    print("=" * 80)
    print("그리스 문자 정규화 테스트")
    print("=" * 80)

    for name_en, name_ko in test_cases:
        result = normalizer.normalize_drug_name(name_en, name_ko)
        print(f"\n원본: {name_en}")
        print(f"결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
