"""
타법 참조 매칭 가능성 분석

목적:
1. 우리 DB에 있는 법령 목록 추출
2. JSON 파일의 타법 참조 분석
3. 매칭 가능한 타법 참조 식별
4. 법령명 정규화 매핑 테이블 생성
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
PARSED_DIR = PROJECT_ROOT / "data" / "legal" / "parsed"
REFERENCES_DIR = PROJECT_ROOT / "data" / "legal" / "references"


def get_our_laws():
    """우리 DB에 있는 법령 목록 추출"""
    our_laws = {}

    for parsed_file in PARSED_DIR.glob("*_parsed.json"):
        data = json.load(parsed_file.open(encoding='utf-8'))
        if data['articles']:
            law_name = data['articles'][0]['law_name']
            law_id = data['articles'][0]['law_id']
            our_laws[law_name] = {
                'law_id': law_id,
                'file': parsed_file.name,
                'article_count': len(data['articles'])
            }

    return our_laws


def analyze_cross_law_references(our_laws):
    """타법 참조 분석 및 매칭"""

    cross_law_refs = []
    target_law_counter = Counter()
    matchable_refs = []
    unmatchable_refs = []

    for ref_file in REFERENCES_DIR.glob("*_references.json"):
        data = json.load(ref_file.open(encoding='utf-8'))
        source_law = data['law_name']

        for ref in data.get('references', []):
            if ref.get('is_cross_law'):
                target_law = ref['target_law_name']
                target_law_counter[target_law] += 1

                ref_info = {
                    'source_law': source_law,
                    'source_article_id': ref['source_article_id'],
                    'source_article_number': ref['source_article_number'],
                    'target_law': target_law,
                    'target_article_number': ref['target_article_number'],
                    'target_clause': ref.get('target_clause'),
                    'reference_type': ref['reference_type'],
                    'reference_text': ref['reference_text'],
                    'context': ref.get('context', '')[:100]
                }

                # 매칭 가능 여부 확인
                if target_law in our_laws:
                    ref_info['matchable'] = True
                    ref_info['match_type'] = 'exact'
                    matchable_refs.append(ref_info)
                else:
                    # 부분 매칭 시도
                    matched = False
                    for our_law in our_laws:
                        # 시행령/시행규칙 제거 후 비교
                        target_base = target_law.replace(' 시행령', '').replace(' 시행규칙', '')
                        our_base = our_law.replace(' 시행령', '').replace(' 시행규칙', '')

                        if target_base in our_base or our_base in target_base:
                            ref_info['matchable'] = True
                            ref_info['match_type'] = 'partial'
                            ref_info['matched_law'] = our_law
                            matchable_refs.append(ref_info)
                            matched = True
                            break

                    if not matched:
                        ref_info['matchable'] = False
                        unmatchable_refs.append(ref_info)

                cross_law_refs.append(ref_info)

    return {
        'all_refs': cross_law_refs,
        'matchable': matchable_refs,
        'unmatchable': unmatchable_refs,
        'target_law_counter': target_law_counter
    }


def create_law_mapping(our_laws, analysis):
    """법령명 정규화 매핑 테이블 생성"""

    mapping = {}

    # exact 매칭
    for ref in analysis['matchable']:
        if ref['match_type'] == 'exact':
            target = ref['target_law']
            if target not in mapping:
                mapping[target] = target

    # partial 매칭
    for ref in analysis['matchable']:
        if ref['match_type'] == 'partial':
            target = ref['target_law']
            matched = ref['matched_law']
            if target not in mapping:
                mapping[target] = matched

    return mapping


def print_analysis(our_laws, analysis, mapping):
    """분석 결과 출력"""

    print("=" * 80)
    print("타법 참조 매칭 가능성 분석")
    print("=" * 80)

    print(f"\n[1] 우리 데이터베이스의 법령 ({len(our_laws)}개)")
    print("-" * 80)
    for law_name, info in sorted(our_laws.items()):
        print(f"  - {law_name} ({info['article_count']}개 조문)")

    print(f"\n[2] 타법 참조 통계")
    print("-" * 80)
    print(f"총 타법 참조: {len(analysis['all_refs'])}개")
    print(f"매칭 가능: {len(analysis['matchable'])}개 ({len(analysis['matchable'])/len(analysis['all_refs'])*100:.1f}%)")
    print(f"  - exact 매칭: {sum(1 for r in analysis['matchable'] if r['match_type'] == 'exact')}개")
    print(f"  - partial 매칭: {sum(1 for r in analysis['matchable'] if r['match_type'] == 'partial')}개")
    print(f"매칭 불가: {len(analysis['unmatchable'])}개 ({len(analysis['unmatchable'])/len(analysis['all_refs'])*100:.1f}%)")

    print(f"\n[3] 매칭 가능한 타법 참조 (상위 20개)")
    print("-" * 80)
    matchable_counter = Counter()
    for ref in analysis['matchable']:
        matchable_counter[ref['target_law']] += 1

    for law, count in matchable_counter.most_common(20):
        match_type = "exact" if law in our_laws else "partial"
        print(f"  {count:4}개: {law} ({match_type})")

    print(f"\n[4] 매칭 불가능한 타법 (상위 20개)")
    print("-" * 80)
    unmatchable_counter = Counter()
    for ref in analysis['unmatchable']:
        unmatchable_counter[ref['target_law']] += 1

    for law, count in unmatchable_counter.most_common(20):
        print(f"  {count:4}개: {law}")

    print(f"\n[5] 법령명 정규화 매핑 테이블 ({len(mapping)}개)")
    print("-" * 80)
    for target, normalized in sorted(mapping.items())[:20]:
        if target != normalized:
            print(f"  '{target}' → '{normalized}'")

    print(f"\n[6] 매칭 가능한 타법 참조 샘플 (5개)")
    print("-" * 80)
    for i, ref in enumerate(analysis['matchable'][:5], 1):
        print(f"\n{i}. {ref['source_law']} {ref['source_article_number']}")
        print(f"   → {ref['target_law']} {ref['target_article_number']}")
        print(f"   유형: {ref['reference_type']}, 매칭: {ref['match_type']}")
        print(f"   표현: {ref['reference_text']}")


def save_results(our_laws, analysis, mapping):
    """결과 저장"""

    output_dir = PROJECT_ROOT / "data" / "legal" / "cross_law_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 법령 목록
    with open(output_dir / "our_laws.json", 'w', encoding='utf-8') as f:
        json.dump(our_laws, f, ensure_ascii=False, indent=2)

    # 2. 매칭 가능한 참조
    with open(output_dir / "matchable_references.json", 'w', encoding='utf-8') as f:
        json.dump(analysis['matchable'], f, ensure_ascii=False, indent=2)

    # 3. 매칭 불가능한 참조
    with open(output_dir / "unmatchable_references.json", 'w', encoding='utf-8') as f:
        json.dump(analysis['unmatchable'], f, ensure_ascii=False, indent=2)

    # 4. 법령명 매핑 테이블
    with open(output_dir / "law_name_mapping.json", 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 분석 결과 저장: {output_dir}")
    print(f"  - our_laws.json: {len(our_laws)}개 법령")
    print(f"  - matchable_references.json: {len(analysis['matchable'])}개")
    print(f"  - unmatchable_references.json: {len(analysis['unmatchable'])}개")
    print(f"  - law_name_mapping.json: {len(mapping)}개 매핑")


def main():
    """메인 실행"""

    print("타법 참조 매칭 가능성 분석 시작...\n")

    # 1. 우리 법령 목록
    our_laws = get_our_laws()

    # 2. 타법 참조 분석
    analysis = analyze_cross_law_references(our_laws)

    # 3. 법령명 매핑 테이블
    mapping = create_law_mapping(our_laws, analysis)

    # 4. 결과 출력
    print_analysis(our_laws, analysis, mapping)

    # 5. 결과 저장
    save_results(our_laws, analysis, mapping)

    print("\n" + "=" * 80)
    print("분석 완료")
    print("=" * 80)


if __name__ == "__main__":
    main()
