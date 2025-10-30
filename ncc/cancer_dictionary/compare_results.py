"""v1 vs v2 분류 결과 비교"""
import json
from pathlib import Path
from collections import Counter


def compare_results():
    """v1과 v2 분류 결과 비교"""

    # 파일 로드
    v1_file = Path("data/ncc/cancer_dictionary/classified_terms.json")
    v2_file = Path("data/ncc/cancer_dictionary/classified_terms_v2.json")

    with open(v1_file, 'r', encoding='utf-8') as f:
        v1_data = json.load(f)

    with open(v2_file, 'r', encoding='utf-8') as f:
        v2_data = json.load(f)

    v1_terms = {term['keyword']: term for term in v1_data['classified_terms']}
    v2_terms = {term['keyword']: term for term in v2_data['classified_terms']}

    # 통계 비교
    print("=" * 70)
    print("v1 vs v2 분류 결과 비교")
    print("=" * 70)

    print("\n[전체 통계 비교]")
    print("-" * 70)
    print(f"{'카테고리':20s} | {'v1':>10s} | {'v2':>10s} | {'변화':>10s}")
    print("-" * 70)

    v1_counts = Counter()
    v2_counts = Counter()

    for term in v1_data['classified_terms']:
        v1_counts[term['categories'][0]] += 1

    for term in v2_data['classified_terms']:
        v2_counts[term['categories'][0]] += 1

    all_categories = sorted(set(v1_counts.keys()) | set(v2_counts.keys()))

    for cat in all_categories:
        v1_count = v1_counts.get(cat, 0)
        v2_count = v2_counts.get(cat, 0)
        change = v2_count - v1_count
        change_str = f"{change:+d} ({change/v1_count*100:+.1f}%)" if v1_count > 0 else f"{change:+d}"
        print(f"{cat:20s} | {v1_count:>10d} | {v2_count:>10d} | {change_str:>10s}")

    # 변경된 항목 분석
    print("\n\n[카테고리 변경된 항목 분석]")
    print("-" * 70)

    category_changes = Counter()
    changed_examples = {}

    for keyword, v2_term in v2_terms.items():
        if keyword not in v1_terms:
            continue

        v1_cat = v1_terms[keyword]['categories'][0]
        v2_cat = v2_term['categories'][0]

        if v1_cat != v2_cat:
            change_key = f"{v1_cat} → {v2_cat}"
            category_changes[change_key] += 1

            if change_key not in changed_examples:
                changed_examples[change_key] = []

            if len(changed_examples[change_key]) < 3:
                changed_examples[change_key].append({
                    'keyword': keyword,
                    'v1': v1_cat,
                    'v2': v2_cat,
                    'confidence': v2_term.get('confidence', 0)
                })

    print(f"\n총 변경 항목: {sum(category_changes.values())}개 ({sum(category_changes.values())/len(v1_terms)*100:.1f}%)\n")

    for change, count in category_changes.most_common(10):
        print(f"\n{change}: {count}개")
        if change in changed_examples:
            for ex in changed_examples[change][:3]:
                print(f"  - {ex['keyword']} (신뢰도: {ex['confidence']:.2f})")

    # 주요 개선 사례
    print("\n\n[주요 개선 사례]")
    print("=" * 70)

    # 1. 임상시험 개선
    print("\n1. 임상시험 분류 개선:")
    clinical_improved = [
        ex for change, examples in changed_examples.items()
        if '임상시험/연구' in change
        for ex in examples
    ][:5]

    for ex in clinical_improved:
        print(f"  [OK] {ex['keyword']}: {ex['v1']} -> {ex['v2']} (신뢰도: {ex['confidence']:.2f})")

    # 2. 치료법 개선
    print("\n2. 치료법(요법) 분류 개선:")
    treatment_improved = [
        ex for change, examples in changed_examples.items()
        if '치료법' in change and '->' in change
        for ex in examples
    ][:5]

    for ex in treatment_improved:
        print(f"  [OK] {ex['keyword']}: {ex['v1']} -> {ex['v2']} (신뢰도: {ex['confidence']:.2f})")

    # 3. 암종 화이트리스트 효과
    print("\n3. 암종 화이트리스트 효과:")
    cancer_changed = [
        ex for change, examples in changed_examples.items()
        if '암종' in change
        for ex in examples
    ][:5]

    for ex in cancer_changed:
        print(f"  [OK] {ex['keyword']}: {ex['v1']} -> {ex['v2']} (신뢰도: {ex['confidence']:.2f})")

    # 낮은 신뢰도 항목 (의심건)
    print("\n\n[낮은 신뢰도 항목 (신뢰도 < 0.3)]")
    print("=" * 70)

    low_confidence = [
        term for term in v2_data['classified_terms']
        if term.get('confidence', 0) < 0.3
    ]

    print(f"\n총 {len(low_confidence)}개 ({len(low_confidence)/len(v2_terms)*100:.1f}%)")

    low_by_category = Counter()
    for term in low_confidence:
        low_by_category[term['categories'][0]] += 1

    print("\n카테고리별 낮은 신뢰도:")
    for cat, count in low_by_category.most_common():
        print(f"  {cat:20s}: {count:5d}개")

    # 샘플 저장
    low_confidence_samples = low_confidence[:50]
    sample_file = Path("ncc/cancer_dictionary/low_confidence_samples.json")
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(low_confidence_samples, f, ensure_ascii=False, indent=2)

    print(f"\n[완료] 낮은 신뢰도 샘플 저장: {sample_file}")


if __name__ == '__main__':
    compare_results()
