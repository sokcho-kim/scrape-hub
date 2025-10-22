"""
pdfplumber로 동일한 10페이지 테스트 - Upstage와 비교
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber


def extract_tables_pdfplumber(pdf_path: Path, pages: List[int], output_dir: Path):
    """
    pdfplumber로 지정된 페이지들의 표 추출

    Args:
        pdf_path: PDF 파일 경로
        pages: 추출할 페이지 번호 리스트 (1-based)
        output_dir: 출력 디렉토리
    """
    print("="*80)
    print("pdfplumber Table Extraction Test")
    print("="*80)
    print(f"PDF: {pdf_path.name}")
    print(f"Pages: {pages}")

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    start_time = time.time()

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in pages:
            print(f"\n{'='*80}")
            print(f"Processing Page {page_num}")
            print('='*80)

            try:
                # pdfplumber는 0-based index
                page = pdf.pages[page_num - 1]
                tables = page.find_tables()

                page_tables = []

                for i, table in enumerate(tables):
                    # 표 추출
                    table_data = table.extract()

                    # 유효한 행만 카운트 (모두 None이 아닌 행)
                    valid_rows = [row for row in table_data if any(cell for cell in row)]

                    table_info = {
                        'table_id': i,
                        'bbox': table.bbox,
                        'rows': len(valid_rows),
                        'cols': len(table_data[0]) if table_data else 0,
                        'data_preview': valid_rows[:3] if valid_rows else []  # 처음 3행만
                    }

                    page_tables.append(table_info)

                    print(f"  Table {i+1}:")
                    print(f"    BBox: {table.bbox}")
                    print(f"    Size: {table_info['rows']}x{table_info['cols']}")
                    if valid_rows:
                        print(f"    Preview (row 1): {valid_rows[0][:2]}")  # 처음 2셀만

                result = {
                    'page': page_num,
                    'status': 'success',
                    'tables_found': len(tables),
                    'tables': page_tables
                }

                results.append(result)

                print(f"  Total tables: {len(tables)}")

            except Exception as e:
                print(f"  ERROR: {str(e)}")
                results.append({
                    'page': page_num,
                    'status': 'error',
                    'error': str(e)
                })

    elapsed = time.time() - start_time

    # 요약 통계
    successful = sum(1 for r in results if r.get('status') == 'success')
    total_tables = sum(r.get('tables_found', 0) for r in results if r.get('status') == 'success')
    total_rows = sum(
        sum(t.get('rows', 0) for t in r.get('tables', []))
        for r in results if r.get('status') == 'success'
    )

    summary = {
        'method': 'pdfplumber',
        'pdf_name': pdf_path.name,
        'sample_pages': pages,
        'total_pages_tested': len(pages),
        'successful': successful,
        'total_tables': total_tables,
        'total_rows': total_rows,
        'elapsed_seconds': elapsed,
        'cost_usd': 0.0,  # 무료
        'results': results
    }

    # 저장
    summary_path = output_dir / "pdfplumber_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*80}")
    print("pdfplumber SUMMARY")
    print('='*80)
    print(f"Pages tested: {len(pages)}")
    print(f"Successful: {successful}/{len(pages)} ({successful/len(pages)*100:.1f}%)")
    print(f"Total tables: {total_tables}")
    print(f"Total rows: {total_rows}")
    print(f"Avg rows/table: {total_rows/total_tables if total_tables > 0 else 0:.1f}")
    print(f"Time elapsed: {elapsed:.1f}s")
    print(f"Cost: $0.00 (free)")
    print(f"\nSaved: {summary_path}")

    return summary


def compare_with_upstage(pdfplumber_summary: Dict, upstage_summary: Dict, output_dir: Path):
    """
    pdfplumber vs Upstage 비교 분석
    """
    print("\n" + "="*80)
    print("COMPARISON: pdfplumber vs Upstage")
    print("="*80)

    # 전체 비교
    comparison = {
        'pdfplumber': {
            'cost': pdfplumber_summary['cost_usd'],
            'time': pdfplumber_summary['elapsed_seconds'],
            'tables': pdfplumber_summary['total_tables'],
            'rows': pdfplumber_summary['total_rows'],
            'avg_rows_per_table': pdfplumber_summary['total_rows'] / pdfplumber_summary['total_tables'] if pdfplumber_summary['total_tables'] > 0 else 0
        },
        'upstage': {
            'cost': upstage_summary['cost_usd'],
            'time': upstage_summary['elapsed_seconds'],
            'tables': upstage_summary['total_tables'],
            'rows': upstage_summary['total_rows'],
            'avg_rows_per_table': upstage_summary['total_rows'] / upstage_summary['total_tables'] if upstage_summary['total_tables'] > 0 else 0
        }
    }

    # 페이지별 비교
    page_comparison = []
    for page_num in pdfplumber_summary['sample_pages']:
        pdf_result = next((r for r in pdfplumber_summary['results'] if r['page'] == page_num), None)
        up_result = next((r for r in upstage_summary['results'] if r['page'] == page_num), None)

        if pdf_result and up_result:
            pdf_tables = pdf_result.get('tables_found', 0)
            pdf_rows = sum(t.get('rows', 0) for t in pdf_result.get('tables', []))

            up_tables = up_result.get('tables_found', 0)
            up_rows = sum(t.get('rows', 0) for t in up_result.get('tables', []))

            page_comparison.append({
                'page': page_num,
                'pdfplumber_tables': pdf_tables,
                'pdfplumber_rows': pdf_rows,
                'upstage_tables': up_tables,
                'upstage_rows': up_rows,
                'table_match': pdf_tables == up_tables,
                'row_diff': up_rows - pdf_rows
            })

    comparison['page_by_page'] = page_comparison

    # 저장
    comparison_path = output_dir / "pdfplumber_vs_upstage_comparison.json"
    with open(comparison_path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    # 출력
    print("\nOverall Comparison:")
    print(f"\n{'Metric':<20} {'pdfplumber':>15} {'Upstage':>15} {'Difference':>15}")
    print("-" * 70)
    print(f"{'Cost':<20} ${comparison['pdfplumber']['cost']:>14.2f} ${comparison['upstage']['cost']:>14.2f} ${comparison['upstage']['cost'] - comparison['pdfplumber']['cost']:>14.2f}")
    print(f"{'Time (s)':<20} {comparison['pdfplumber']['time']:>15.1f} {comparison['upstage']['time']:>15.1f} {comparison['upstage']['time'] - comparison['pdfplumber']['time']:>15.1f}")
    print(f"{'Tables':<20} {comparison['pdfplumber']['tables']:>15} {comparison['upstage']['tables']:>15} {comparison['upstage']['tables'] - comparison['pdfplumber']['tables']:>15}")
    print(f"{'Rows':<20} {comparison['pdfplumber']['rows']:>15} {comparison['upstage']['rows']:>15} {comparison['upstage']['rows'] - comparison['pdfplumber']['rows']:>15}")
    print(f"{'Avg rows/table':<20} {comparison['pdfplumber']['avg_rows_per_table']:>15.1f} {comparison['upstage']['avg_rows_per_table']:>15.1f} {comparison['upstage']['avg_rows_per_table'] - comparison['pdfplumber']['avg_rows_per_table']:>15.1f}")

    print("\nPage-by-Page Comparison:")
    print(f"\n{'Page':>5} {'PDF Tables':>12} {'PDF Rows':>10} {'UP Tables':>11} {'UP Rows':>9} {'Row Diff':>10} {'Match':>8}")
    print("-" * 75)

    for p in page_comparison:
        match_str = "YES" if p['table_match'] else "NO"
        print(f"{p['page']:>5} {p['pdfplumber_tables']:>12} {p['pdfplumber_rows']:>10} {p['upstage_tables']:>11} {p['upstage_rows']:>9} {p['row_diff']:>+10} {match_str:>8}")

    # 매칭 통계
    table_matches = sum(1 for p in page_comparison if p['table_match'])
    print(f"\nTable detection agreement: {table_matches}/{len(page_comparison)} ({table_matches/len(page_comparison)*100:.1f}%)")

    # 행 수 차이 분석
    total_row_diff = sum(p['row_diff'] for p in page_comparison)
    print(f"Total row difference: {total_row_diff:+d} (Upstage extracted {abs(total_row_diff)} {'more' if total_row_diff > 0 else 'fewer'} rows)")

    print(f"\nComparison saved: {comparison_path}")

    return comparison


def main():
    """메인 실행"""
    base_dir = Path(__file__).parent.parent.parent

    pdf_path = base_dir / "data" / "hira" / "ebook" / "요양급여의 적용기준 및 방법에 관한 세부사항(약제) - 2025년 7월판(G000DB5-2025-94).pdf"

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    sample_pages = [10, 50, 100, 200, 300, 400, 500, 600, 700, 800]
    output_dir = base_dir / "data" / "pharma" / "parsed" / "upstage_test"

    # pdfplumber 테스트
    pdfplumber_summary = extract_tables_pdfplumber(pdf_path, sample_pages, output_dir)

    # Upstage 결과 로드
    upstage_summary_path = output_dir / "option_b_summary.json"
    if upstage_summary_path.exists():
        with open(upstage_summary_path, 'r', encoding='utf-8') as f:
            upstage_summary = json.load(f)

        # 비교
        compare_with_upstage(pdfplumber_summary, upstage_summary, output_dir)
    else:
        print("\nWARNING: Upstage results not found. Skipping comparison.")

    print("\n" + "="*80)
    print("pdfplumber TEST COMPLETED")
    print("="*80)


if __name__ == "__main__":
    main()
