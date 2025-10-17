"""
파일 크기 기반으로 HWP 페이지 수 추정
"""
from pathlib import Path
import sys
import codecs

if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def estimate_pages_from_size(size_kb):
    """
    파일 크기로 페이지 수 추정
    HWP 파일은 대략 30-50KB당 1페이지로 추정 (평균 40KB)
    """
    # 평균: 40KB/page
    return max(1, round(size_kb / 40))

def main():
    docs_dir = Path('data/hira_rulesvc/documents')

    results = []
    total_pages = 0
    total_size_kb = 0

    print("=" * 100)
    print(f"{'파일명':<65} {'크기(KB)':>10} {'예상페이지':>10} {'카테고리':<15}")
    print("=" * 100)

    for file_path in sorted(docs_dir.glob('*')):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in ['.hwp', '.pdf']:
            continue

        size_kb = file_path.stat().st_size / 1024

        # PDF는 4페이지로 확인됨
        if file_path.suffix.lower() == '.pdf':
            pages = 4
        else:
            pages = estimate_pages_from_size(size_kb)

        # 카테고리 판단
        name = file_path.name
        if '법' in name and ('시행' in name or '법률' in name or '령' in name):
            category = '법령'
        elif name.startswith(('1-', '2-', '3-', '4-', '5-', '6-', '7-', '8-')):
            category = '행정해석'
        else:
            category = '고시'

        total_pages += pages
        total_size_kb += size_kb

        # 파일명 제한
        display_name = name
        if len(display_name) > 60:
            display_name = display_name[:57] + "..."

        print(f"{display_name:<65} {size_kb:>10.1f} {pages:>10} {category:<15}")

        results.append({
            'name': name,
            'size_kb': size_kb,
            'pages': pages,
            'category': category
        })

    print("=" * 100)

    # 카테고리별 통계
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'count': 0, 'pages': 0, 'size_kb': 0}
        categories[cat]['count'] += 1
        categories[cat]['pages'] += r['pages']
        categories[cat]['size_kb'] += r['size_kb']

    print("\n[카테고리별 통계]")
    print("-" * 80)
    print(f"{'카테고리':<15} {'파일수':>10} {'예상페이지':>15} {'평균/파일':>15} {'총크기(KB)':>15}")
    print("-" * 80)
    for cat, stats in sorted(categories.items()):
        avg_pages = stats['pages'] / stats['count']
        print(f"{cat:<15} {stats['count']:>10} {stats['pages']:>15} {avg_pages:>15.1f} {stats['size_kb']:>15.1f}")

    print("-" * 80)
    print(f"{'합계':<15} {len(results):>10} {total_pages:>15} {total_pages/len(results):>15.1f} {total_size_kb:>15.1f}")

    print("\n" + "=" * 80)
    print("[비용 산정]")
    print("-" * 80)
    print(f"{'총 파일 수:':<40} {len(results)}개")
    print(f"{'총 파일 크기:':<40} {total_size_kb/1024:.2f} MB")
    print(f"{'예상 총 페이지 수:':<40} {total_pages} 페이지")
    print(f"{'파일당 평균 페이지:':<40} {total_pages/len(results):.1f} 페이지")
    print("-" * 80)
    print(f"{'Upstage API 비용 (페이지당 $0.01):':<40} ${total_pages * 0.01:.2f}")
    print(f"{'환율 적용 (1,300원):':<40} ₩{int(total_pages * 0.01 * 1300):,}원")
    print("-" * 80)

    # 시나리오별 비용
    print("\n[시나리오별 비용 추정]")
    print("-" * 80)
    scenarios = [
        ("현재 추정 (40KB/page)", total_pages, 1.0),
        ("보수적 추정 (50KB/page)", int(total_size_kb / 50), 0.8),
        ("적극적 추정 (30KB/page)", int(total_size_kb / 30), 1.33),
    ]

    for scenario, pages, factor in scenarios:
        cost_usd = pages * 0.01
        cost_krw = int(cost_usd * 1300)
        print(f"{scenario:<30} {pages:>6} 페이지  ${cost_usd:>6.2f}  ₩{cost_krw:>7,}원")

    print("=" * 80)

if __name__ == '__main__':
    main()
