#!/usr/bin/env python3
"""
성분별 약제 그룹화 도구

기능:
- ingredient_code로 동일 성분 약품 그룹화
- 제네릭 약품 목록 확인
- 가격 비교
- 제조사 비교
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


def load_drug_dictionary(dict_path: Path) -> Dict:
    """약가 사전 로드"""
    with open(dict_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def group_by_ingredient(drug_dict: Dict) -> Dict[str, List]:
    """
    성분코드로 약제 그룹화

    Returns:
        {
            'ingredient_code': [
                {
                    'product_name': '...',
                    'company': '...',
                    'price': ...,
                    'product_code': '...',
                    'route': '...'
                },
                ...
            ]
        }
    """
    grouped = defaultdict(list)

    for key, value in drug_dict.items():
        for rec in value.get('records', []):
            ing_code = rec.get('ingredient_code')
            if ing_code:
                grouped[ing_code].append({
                    'product_name': rec.get('product_name', ''),
                    'company': rec.get('company', ''),
                    'price': rec.get('price', 0),
                    'product_code': rec.get('product_code', ''),
                    'route': rec.get('route', '')
                })

    # 중복 제거 (제품명 기준)
    for ing_code in grouped:
        unique = {}
        for product in grouped[ing_code]:
            name = product['product_name']
            if name not in unique:
                unique[name] = product
        grouped[ing_code] = list(unique.values())

    return dict(grouped)


def get_ingredient_stats(grouped: Dict[str, List]) -> List[Dict]:
    """
    성분별 통계 생성

    Returns:
        [
            {
                'ingredient_code': '...',
                'product_count': ...,
                'company_count': ...,
                'min_price': ...,
                'max_price': ...,
                'sample_product': '...'
            },
            ...
        ]
    """
    stats = []

    for ing_code, products in grouped.items():
        companies = set(p['company'] for p in products)
        prices = [p['price'] for p in products if p['price'] > 0]

        stats.append({
            'ingredient_code': ing_code,
            'product_count': len(products),
            'company_count': len(companies),
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'sample_product': products[0]['product_name'] if products else ''
        })

    return stats


def search_ingredient(grouped: Dict[str, List], query: str) -> List[Dict]:
    """
    성분명으로 검색

    Args:
        grouped: 성분별 그룹화된 데이터
        query: 검색어 (성분명 일부)

    Returns:
        매칭되는 성분 목록
    """
    results = []
    query_lower = query.lower()

    for ing_code, products in grouped.items():
        # 샘플 제품명에서 검색
        sample = products[0]['product_name'].lower() if products else ''

        if query_lower in sample or query_lower in ing_code.lower():
            results.append({
                'ingredient_code': ing_code,
                'products': products,
                'sample_product': products[0]['product_name'] if products else ''
            })

    return results


def main():
    """실행"""
    import argparse

    parser = argparse.ArgumentParser(description='성분별 약제 그룹화 및 검색')
    parser.add_argument('--dict', default='data/hira_master/drug_dictionary.json',
                        help='약가 사전 파일')
    parser.add_argument('--search', '-s', type=str,
                        help='검색어 (성분명 일부)')
    parser.add_argument('--code', '-c', type=str,
                        help='성분코드로 직접 검색')
    parser.add_argument('--top', '-t', type=int, default=10,
                        help='제네릭 많은 순 TOP N (기본: 10)')
    parser.add_argument('--output', '-o', type=str,
                        help='결과를 JSON으로 저장할 경로')

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent.parent
    dict_path = base_dir / args.dict

    if not dict_path.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {dict_path}")
        return 1

    print("=" * 80)
    print("성분별 약제 그룹화 도구")
    print("=" * 80)
    print()

    # 약가 사전 로드
    print(f"[LOAD] {dict_path}")
    drug_dict = load_drug_dictionary(dict_path)
    print(f"  → {len(drug_dict):,}개 검색 키 로드")

    # 성분별 그룹화
    print("\n[GROUP] 성분별 그룹화 중...")
    grouped = group_by_ingredient(drug_dict)
    print(f"  → {len(grouped):,}개 성분 그룹 생성")

    # 성분코드로 직접 검색
    if args.code:
        if args.code in grouped:
            products = grouped[args.code]
            print(f"\n=== 성분코드: {args.code} ===")
            print(f"총 제품 수: {len(products)}개")
            print()

            # 가격순 정렬
            products_sorted = sorted(products, key=lambda x: x['price'], reverse=True)

            print("제품 목록 (가격순):")
            for i, p in enumerate(products_sorted, 1):
                print(f"\n{i}. {p['product_name']}")
                print(f"   제조사: {p['company']}")
                print(f"   약가: {p['price']}원")
                print(f"   투여경로: {p['route']}")
        else:
            print(f"\n[ERROR] 성분코드를 찾을 수 없습니다: {args.code}")

        return 0

    # 성분명 검색
    if args.search:
        results = search_ingredient(grouped, args.search)

        if not results:
            print(f"\n[INFO] 검색 결과가 없습니다: {args.search}")
            return 0

        print(f"\n=== 검색 결과: '{args.search}' ===")
        print(f"매칭된 성분: {len(results)}개")
        print()

        for i, result in enumerate(results[:20], 1):
            products = result['products']
            companies = set(p['company'] for p in products)
            prices = [p['price'] for p in products if p['price'] > 0]

            print(f"{i}. 성분코드: {result['ingredient_code']}")
            print(f"   제품 예시: {result['sample_product']}")
            print(f"   제품 수: {len(products)}개")
            print(f"   제조사 수: {len(companies)}개")
            if prices:
                print(f"   가격 범위: {min(prices):,.0f}원 ~ {max(prices):,.0f}원")
            print()

        if len(results) > 20:
            print(f"... 외 {len(results)-20}개 성분")

        return 0

    # TOP N 제네릭 많은 성분
    print(f"\n=== 제네릭이 가장 많은 성분 TOP {args.top} ===")
    stats = get_ingredient_stats(grouped)
    stats_sorted = sorted(stats, key=lambda x: x['company_count'], reverse=True)

    for i, stat in enumerate(stats_sorted[:args.top], 1):
        print(f"\n{i}. 성분코드: {stat['ingredient_code']}")
        print(f"   제품 예시: {stat['sample_product'][:60]}...")
        print(f"   제품 수: {stat['product_count']}개")
        print(f"   제조사 수: {stat['company_count']}개")
        if stat['max_price'] > 0:
            print(f"   가격 범위: {stat['min_price']:,.0f}원 ~ {stat['max_price']:,.0f}원")

    # JSON 저장
    if args.output:
        output_path = base_dir / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_ingredients': len(grouped),
                'stats': stats_sorted[:100],  # TOP 100
                'grouped_data': grouped
            }, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVE] 결과 저장: {output_path}")

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
