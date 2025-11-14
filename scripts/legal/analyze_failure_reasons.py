"""
타법 참조 실패 원인 상세 분석

목적:
1. 32개 실패한 케이스 상세 분석
2. 1,261개 매칭 불가능한 법령 분석
3. Option 1 vs Option 2 효율성 비교
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "legal"
ANALYSIS_DIR = DATA_DIR / "cross_law_analysis"
PARSED_DIR = DATA_DIR / "parsed"


def analyze_option2_failures():
    """Option 2: 32개 실패 케이스 분석 (조문 누락)"""

    print("=" * 80)
    print("Option 2 분석: 조문 누락 (32개 실패)")
    print("=" * 80)

    # 통합 스크립트 실행 시 실패한 케이스를 시뮬레이션
    # matchable_references.json에서 실제 target을 찾을 수 없는 케이스 찾기

    matchable_file = ANALYSIS_DIR / "matchable_references.json"
    with open(matchable_file, 'r', encoding='utf-8') as f:
        matchable_refs = json.load(f)

    # 우리 DB의 모든 조문 목록 로드
    our_articles = {}
    for parsed_file in PARSED_DIR.glob("*_parsed.json"):
        data = json.load(parsed_file.open(encoding='utf-8'))
        for article in data['articles']:
            key = (article['law_name'], article['article_number'])
            if key not in our_articles:
                our_articles[key] = []
            our_articles[key].append(article)

    print(f"\n우리 DB의 조문 수: {sum(len(v) for v in our_articles.values()):,}개")
    print(f"우리 DB의 조 수 (depth=0): {sum(1 for articles in our_articles.values() for a in articles if a['depth'] == 0):,}개")

    # 실패 케이스 분석
    failures = []
    missing_articles = Counter()
    missing_clauses = []

    for ref in matchable_refs:
        target_law = ref['target_law']
        target_article = ref['target_article_number']
        target_clause = ref.get('target_clause')

        key = (target_law, target_article)

        # 조 자체가 없음
        if key not in our_articles:
            failures.append({
                'type': 'missing_article',
                'target_law': target_law,
                'target_article': target_article,
                'source': f"{ref['source_law']} {ref['source_article_number']}"
            })
            missing_articles[f"{target_law} {target_article}"] += 1
        else:
            # 조는 있는데 항이 없음
            if target_clause:
                articles = our_articles[key]
                has_clause = any(
                    a['depth'] == 1 and a.get('clause_number') == target_clause
                    for a in articles
                )
                if not has_clause:
                    failures.append({
                        'type': 'missing_clause',
                        'target_law': target_law,
                        'target_article': target_article,
                        'target_clause': target_clause,
                        'source': f"{ref['source_law']} {ref['source_article_number']}"
                    })
                    missing_clauses.append({
                        'law': target_law,
                        'article': target_article,
                        'clause': target_clause
                    })

    print(f"\n예상 실패 케이스: {len(failures)}개")
    print(f"  - 조 자체 누락: {len([f for f in failures if f['type'] == 'missing_article'])}개")
    print(f"  - 항 누락: {len([f for f in failures if f['type'] == 'missing_clause'])}개")

    print(f"\n누락된 조문 Top 20:")
    for article, count in missing_articles.most_common(20):
        print(f"  {count:2}회: {article}")

    if missing_clauses:
        print(f"\n누락된 항 샘플 (최대 10개):")
        for mc in missing_clauses[:10]:
            print(f"  - {mc['law']} {mc['article']} 제{mc['clause']}항")

    return {
        'total_failures': len(failures),
        'missing_articles': len([f for f in failures if f['type'] == 'missing_article']),
        'missing_clauses': len([f for f in failures if f['type'] == 'missing_clause']),
        'details': failures
    }


def analyze_option1_opportunities():
    """Option 1: 추가 법령 수집 기회 분석"""

    print("\n" + "=" * 80)
    print("Option 1 분석: 추가 법령 수집")
    print("=" * 80)

    unmatchable_file = ANALYSIS_DIR / "unmatchable_references.json"
    with open(unmatchable_file, 'r', encoding='utf-8') as f:
        unmatchable_refs = json.load(f)

    # 법령별 참조 횟수
    law_counter = Counter()
    law_examples = defaultdict(list)

    for ref in unmatchable_refs:
        target_law = ref['target_law']
        law_counter[target_law] += 1
        if len(law_examples[target_law]) < 3:
            law_examples[target_law].append({
                'source': f"{ref['source_law']} {ref['source_article_number']}",
                'target_article': ref['target_article_number'],
                'ref_type': ref['reference_type']
            })

    print(f"\n매칭 불가능한 타법: {len(law_counter)}개 법령")
    print(f"총 참조 횟수: {sum(law_counter.values())}회")

    # 효율성 분석
    print(f"\n법령별 참조 횟수 (Top 30):")
    cumulative = 0
    tier_analysis = {
        'tier1': {'count': 0, 'refs': 0, 'threshold': 20},  # 20회 이상
        'tier2': {'count': 0, 'refs': 0, 'threshold': 10},  # 10-19회
        'tier3': {'count': 0, 'refs': 0, 'threshold': 5},   # 5-9회
        'tier4': {'count': 0, 'refs': 0, 'threshold': 0}    # 1-4회
    }

    for i, (law, count) in enumerate(law_counter.most_common(30), 1):
        cumulative += count
        coverage = cumulative / sum(law_counter.values()) * 100
        print(f"  {i:2}. {count:3}회 ({coverage:5.1f}% 누적): {law}")

        # 티어 분류
        if count >= 20:
            tier_analysis['tier1']['count'] += 1
            tier_analysis['tier1']['refs'] += count
        elif count >= 10:
            tier_analysis['tier2']['count'] += 1
            tier_analysis['tier2']['refs'] += count
        elif count >= 5:
            tier_analysis['tier3']['count'] += 1
            tier_analysis['tier3']['refs'] += count
        else:
            tier_analysis['tier4']['count'] += 1
            tier_analysis['tier4']['refs'] += count

    # 티어별 효율성
    print(f"\n티어별 효율성 분석:")
    print(f"{'티어':<10} {'법령 수':<10} {'참조 횟수':<12} {'법령당 평균':<12} {'커버리지':<10}")
    print("-" * 60)
    total_refs = sum(law_counter.values())

    for tier_name, tier in tier_analysis.items():
        if tier['count'] > 0:
            avg = tier['refs'] / tier['count']
            coverage = tier['refs'] / total_refs * 100
            threshold_text = f">={tier['threshold']}" if tier['threshold'] > 0 else "<5"
            print(f"{tier_name:<10} {tier['count']:<10} {tier['refs']:<12} {avg:>10.1f}회 {coverage:>8.1f}%")

    # 추천 법령 (Top 20)
    print(f"\n우선순위 추천 (Top 20):")
    for i, (law, count) in enumerate(law_counter.most_common(20), 1):
        examples = law_examples[law]
        print(f"\n{i}. {law} ({count}회)")
        print(f"   예시:")
        for ex in examples[:2]:
            print(f"     - {ex['source']} → {ex['target_article']} ({ex['ref_type']})")

    return {
        'total_laws': len(law_counter),
        'total_refs': sum(law_counter.values()),
        'tier_analysis': tier_analysis,
        'top_laws': law_counter.most_common(20)
    }


def compare_options(option1_result, option2_result):
    """Option 1 vs Option 2 비교"""

    print("\n" + "=" * 80)
    print("Option 1 vs Option 2 효율성 비교")
    print("=" * 80)

    print(f"\n{'항목':<30} {'Option 1 (법령 수집)':<25} {'Option 2 (파싱 개선)':<25}")
    print("-" * 80)

    # 잠재적 효과
    tier1_refs = option1_result['tier_analysis']['tier1']['refs']
    tier1_count = option1_result['tier_analysis']['tier1']['count']
    tier2_refs = option1_result['tier_analysis']['tier2']['refs']
    tier2_count = option1_result['tier_analysis']['tier2']['count']

    print(f"{'잠재적 추가 연결 (최대)':<30} {option1_result['total_refs']:>24}개 {option2_result['total_failures']:>24}개")
    print(f"{'작업량':<30} {f'{tier1_count}개 법령 수집':>24} {'파싱 로직 개선':>24}")
    print(f"{'예상 소요 시간':<30} {f'{tier1_count * 2}시간':>24} {'2-4시간':>24}")
    print(f"{'1시간당 연결 효과':<30} {tier1_refs / (tier1_count * 2):>22.1f}개 {option2_result['total_failures'] / 3:>22.1f}개")

    print(f"\n추천 전략:")

    # Tier 1만 수집했을 때 효과
    if tier1_refs > option2_result['total_failures'] * 5:
        print(f"  ✅ Option 1 우선 추천 (효율 {tier1_refs / option2_result['total_failures']:.1f}배)")
        print(f"     - Tier 1 법령 {tier1_count}개만 수집해도 +{tier1_refs}개 연결 가능")
        print(f"     - 예상 소요: {tier1_count * 2}시간")
        print(f"  → Option 2는 나중에 (추가 +{option2_result['total_failures']}개)")
    else:
        print(f"  ✅ Option 2 우선 추천")
        print(f"     - 파싱 로직 개선으로 +{option2_result['total_failures']}개 연결")
        print(f"     - 예상 소요: 2-4시간")
        print(f"  → Option 1은 나중에 (Tier 1만 해도 +{tier1_refs}개)")

    print(f"\n병행 전략 (권장):")
    print(f"  1단계: Tier 1 법령만 수집 ({tier1_count}개) → +{tier1_refs}개")
    print(f"  2단계: Option 2 파싱 개선 → +{option2_result['total_failures']}개")
    print(f"  3단계: Tier 2 법령 수집 ({tier2_count}개) → +{tier2_refs}개")
    print(f"  총 효과: +{tier1_refs + option2_result['total_failures'] + tier2_refs}개")


def main():
    """메인 실행"""

    print("타법 참조 실패 원인 상세 분석\n")

    # Option 2 분석
    option2_result = analyze_option2_failures()

    # Option 1 분석
    option1_result = analyze_option1_opportunities()

    # 비교 분석
    compare_options(option1_result, option2_result)

    print("\n" + "=" * 80)
    print("분석 완료")
    print("=" * 80)


if __name__ == "__main__":
    main()
