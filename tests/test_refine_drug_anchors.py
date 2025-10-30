#!/usr/bin/env python3
"""
refine_drug_anchors.py 유닛 테스트

테스트 케이스 6개:
1. paclitaxel ↔ 파클리탁셀 → active
2. busulfan ↔ 바이알 → 제외
3. prednisolone ↔ 아비라테론 → 보류
4. FOLFOX → regimen.yaml
5. HER2 → biomarker.yaml
6. NSCLC → disease_alias.yaml
"""

import sys
import json
import tempfile
from pathlib import Path

# 상위 디렉토리의 scripts 모듈 임포트
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.refine_drug_anchors import DrugAnchorRefiner, DrugEntry

# 테스트용 필터 설정
TEST_FILTERS = {
    'forbidden_forms': {
        'hard': ['바이알', '앰플'],
        'conditional': ['mL', 'mg']
    },
    'ingredient_hints': ['성분', '억제제', '투여'],
    'en_suffix_to_ko_hint': [
        {'en': 'taxel', 'ko': ['탁셀'], 'strict': True},
        {'en': 'sone', 'ko': ['손', '솔론'], 'strict': True},
    ],
    'phonetic_threshold': {
        'strict': 0.25,
        'loose': 0.35
    },
    'high_frequency_threshold': 20,
    'patterns': {
        'regimen': [r'\bFOLFOX\b'],
        'biomarker': ['HER2'],
        'disease': ['NSCLC']
    },
    'normalization': {
        'unicode_form': 'NFKC',
        'quote_normalization': [],
        'hyphen_normalization': [],
        'plus_normalization': [],
        'remove_duplicate_spaces': True,
        'case_handling': {'en': 'lowercase', 'ko': 'as_is'}
    },
    'execution': {
        'progress_interval': 10
    },
    'acceptance_criteria': {
        'test_cases': []
    }
}


def test_case_1_paclitaxel_active():
    """테스트 1: paclitaxel ↔ 파클리탁셀 → active"""
    print("\n[테스트 1] paclitaxel ↔ 파클리탁셀 → active")

    # 임시 필터 파일 생성
    import yaml
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(TEST_FILTERS, f, allow_unicode=True)
        filter_path = f.name

    # Refiner 초기화
    refiner = DrugAnchorRefiner(filter_path)

    # 테스트 항목
    entry = DrugEntry(
        en='paclitaxel',
        ko='파클리탁셀',
        count=36,
        source='test'
    )

    # 게이트 체인 적용
    result = refiner.apply_gate_chain(entry)

    # 검증
    assert result.decision == 'active', f"Expected 'active', got '{result.decision}'"
    assert 'PASS_ALL' in result.reason_codes, f"Expected 'PASS_ALL' in reason_codes, got {result.reason_codes}"

    print(f"[PASS] {result.en} -> {result.ko} = {result.decision}")
    print(f"   Reason codes: {result.reason_codes}")

    # 정리
    Path(filter_path).unlink()


def test_case_2_busulfan_drop():
    """테스트 2: busulfan ↔ 바이알 → 제외"""
    print("\n[테스트 2] busulfan ↔ 바이알 → drop")

    import yaml
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(TEST_FILTERS, f, allow_unicode=True)
        filter_path = f.name

    refiner = DrugAnchorRefiner(filter_path)

    entry = DrugEntry(
        en='busulfan',
        ko='바이알',
        count=10,
        source='test'
    )

    result = refiner.apply_gate_chain(entry)

    assert result.decision == 'drop', f"Expected 'drop', got '{result.decision}'"
    assert 'FORM_TERM' in result.reason_codes, f"Expected 'FORM_TERM' in reason_codes, got {result.reason_codes}"

    print(f"[PASS] {result.en} -> {result.ko} = {result.decision}")
    print(f"   Reason codes: {result.reason_codes}")

    Path(filter_path).unlink()


def test_case_3_prednisolone_pending():
    """테스트 3: prednisolone ↔ 아비라테론 → 보류"""
    print("\n[테스트 3] prednisolone ↔ 아비라테론 → pending")

    import yaml
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(TEST_FILTERS, f, allow_unicode=True)
        filter_path = f.name

    refiner = DrugAnchorRefiner(filter_path)

    entry = DrugEntry(
        en='prednisolone',
        ko='아비라테론',
        count=15,
        source='test'
    )

    result = refiner.apply_gate_chain(entry)

    assert result.decision == 'pending', f"Expected 'pending', got '{result.decision}'"
    # SUFFIX_MISMATCH 또는 PHONETIC_FAIL 중 하나라도 있으면 통과
    has_error_code = any(code in result.reason_codes for code in ['SUFFIX_MISMATCH', 'PHONETIC_FAIL'])
    assert has_error_code, f"Expected error code in reason_codes, got {result.reason_codes}"

    print(f"[PASS] {result.en} -> {result.ko} = {result.decision}")
    print(f"   Reason codes: {result.reason_codes}")

    Path(filter_path).unlink()


def test_case_4_folfox_regimen():
    """테스트 4: FOLFOX → regimen"""
    print("\n[테스트 4] FOLFOX → regimen")

    import yaml
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(TEST_FILTERS, f, allow_unicode=True)
        filter_path = f.name

    refiner = DrugAnchorRefiner(filter_path)

    entry = DrugEntry(
        en='FOLFOX',
        ko='폴폭스',
        count=20,
        source='test'
    )

    result = refiner.apply_gate_chain(entry)

    assert result.decision == 'route_regimen', f"Expected 'route_regimen', got '{result.decision}'"
    assert 'ROUTE_REGIMEN' in result.reason_codes, f"Expected 'ROUTE_REGIMEN' in reason_codes, got {result.reason_codes}"

    print(f"[PASS] {result.en} -> {result.ko} = {result.decision}")
    print(f"   Reason codes: {result.reason_codes}")

    Path(filter_path).unlink()


def test_case_5_her2_biomarker():
    """테스트 5: HER2 → biomarker"""
    print("\n[테스트 5] HER2 → biomarker")

    import yaml
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(TEST_FILTERS, f, allow_unicode=True)
        filter_path = f.name

    refiner = DrugAnchorRefiner(filter_path)

    entry = DrugEntry(
        en='HER2',
        ko='허투',
        count=30,
        source='test'
    )

    result = refiner.apply_gate_chain(entry)

    assert result.decision == 'route_biomarker', f"Expected 'route_biomarker', got '{result.decision}'"
    assert 'ROUTE_BIOMARKER' in result.reason_codes, f"Expected 'ROUTE_BIOMARKER' in reason_codes, got {result.reason_codes}"

    print(f"[PASS] {result.en} -> {result.ko} = {result.decision}")
    print(f"   Reason codes: {result.reason_codes}")

    Path(filter_path).unlink()


def test_case_6_nsclc_disease():
    """테스트 6: NSCLC → disease"""
    print("\n[테스트 6] NSCLC → disease")

    import yaml
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(TEST_FILTERS, f, allow_unicode=True)
        filter_path = f.name

    refiner = DrugAnchorRefiner(filter_path)

    entry = DrugEntry(
        en='NSCLC',
        ko='비소세포폐암',
        count=25,
        source='test'
    )

    result = refiner.apply_gate_chain(entry)

    assert result.decision == 'route_disease', f"Expected 'route_disease', got '{result.decision}'"
    assert 'ROUTE_DISEASE' in result.reason_codes, f"Expected 'ROUTE_DISEASE' in reason_codes, got {result.reason_codes}"

    print(f"[PASS] {result.en} -> {result.ko} = {result.decision}")
    print(f"   Reason codes: {result.reason_codes}")

    Path(filter_path).unlink()


def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 70)
    print("refine_drug_anchors.py 유닛 테스트")
    print("=" * 70)

    tests = [
        test_case_1_paclitaxel_active,
        test_case_2_busulfan_drop,
        test_case_3_prednisolone_pending,
        test_case_4_folfox_regimen,
        test_case_5_her2_biomarker,
        test_case_6_nsclc_disease
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Test Result: {passed}/{len(tests)} passed")
    if failed > 0:
        print(f"[WARNING] {failed} test(s) failed")
    else:
        print("[SUCCESS] All tests passed!")
    print("=" * 70)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
