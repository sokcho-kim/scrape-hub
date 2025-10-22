"""
Upstage Document Parse API 테스트 - Option A vs B 비교

Option A: 전체 문서 업로드 (858p, ~$8.58)
Option B: 샘플 페이지만 분할 업로드 (10p, ~$0.10)
"""
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter

# .env 파일 로드
load_dotenv()

# Upstage API 설정
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")
UPSTAGE_DOCUMENT_PARSE_URL = "https://api.upstage.ai/v1/document-ai/document-parse"


def split_pdf_pages(pdf_path: Path, pages: List[int], output_dir: Path) -> List[Path]:
    """
    PDF에서 특정 페이지들만 추출하여 개별 PDF 파일로 저장

    Args:
        pdf_path: 원본 PDF 경로
        pages: 추출할 페이지 번호 리스트 (1-based)
        output_dir: 출력 디렉토리

    Returns:
        생성된 PDF 파일 경로 리스트
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(pdf_path)
    output_files = []

    print(f"\nSplitting PDF into {len(pages)} individual files...")

    for page_num in pages:
        writer = PdfWriter()
        # pypdf는 0-based index
        writer.add_page(reader.pages[page_num - 1])

        output_path = output_dir / f"page_{page_num}.pdf"
        with open(output_path, 'wb') as f:
            writer.write(f)

        output_files.append(output_path)
        print(f"  Created: {output_path.name}")

    return output_files


def parse_pdf_upstage(pdf_path: Path, api_key: str) -> Dict[str, Any]:
    """
    Upstage Document Parse API로 PDF 파싱

    Args:
        pdf_path: PDF 파일 경로
        api_key: Upstage API 키

    Returns:
        API 응답 결과
    """
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    with open(pdf_path, 'rb') as f:
        files = {
            'document': (pdf_path.name, f, 'application/pdf')
        }

        data = {
            'ocr': 'force'
        }

        print(f"  Calling Upstage API...")
        response = requests.post(
            UPSTAGE_DOCUMENT_PARSE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=300  # 5분 타임아웃
        )

    if response.status_code != 200:
        print(f"  ERROR: API returned status {response.status_code}")
        print(f"  Response: {response.text}")
        return None

    return response.json()


def extract_tables_from_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Upstage 응답에서 표 정보 추출
    """
    tables = []

    if not response or 'elements' not in response:
        return tables

    for element in response.get('elements', []):
        if element.get('category') == 'table':
            # 올바른 경로: element['content']['html']
            content = element.get('content', {})
            html = content.get('html', '')
            text = content.get('text', '')

            table_info = {
                'id': element.get('id'),
                'page': element.get('page'),
                'bbox': element.get('coordinates'),  # 'bounding_box' -> 'coordinates'
                'html': html,
                'text': text,
                'rows': 0,
                'cols': 0
            }

            # HTML에서 행/열 수 추정
            if html:
                table_info['rows'] = html.count('<tr>')
                # 첫 번째 tr에서 td/th 개수
                import re
                first_row = re.search(r'<tr>.*?</tr>', html, re.DOTALL)
                if first_row:
                    table_info['cols'] = first_row.group().count('<td>') + first_row.group().count('<th>')

            tables.append(table_info)

    return tables


def test_option_b(pdf_path: Path, sample_pages: List[int], output_dir: Path):
    """
    Option B: 샘플 페이지만 분할하여 개별 업로드
    """
    print("="*80)
    print("OPTION B: Split Pages & Individual Upload")
    print("="*80)
    print(f"PDF: {pdf_path.name}")
    print(f"Sample pages: {sample_pages}")
    print(f"Expected cost: ${len(sample_pages) * 0.01:.2f}")

    if not UPSTAGE_API_KEY:
        print("\nERROR: UPSTAGE_API_KEY not set")
        return None

    # 페이지 분할
    split_dir = output_dir / "split_pdfs"
    split_files = split_pdf_pages(pdf_path, sample_pages, split_dir)

    # 각 페이지 파싱
    results = []
    start_time = time.time()

    for i, (page_num, split_file) in enumerate(zip(sample_pages, split_files)):
        print(f"\n{'='*80}")
        print(f"Processing Page {page_num} ({i+1}/{len(sample_pages)})")
        print('='*80)

        try:
            response = parse_pdf_upstage(split_file, UPSTAGE_API_KEY)

            if not response:
                results.append({
                    'page': page_num,
                    'status': 'failed',
                    'error': 'API call failed'
                })
                continue

            tables = extract_tables_from_response(response)

            result = {
                'page': page_num,
                'status': 'success',
                'tables_found': len(tables),
                'tables': tables
            }

            results.append(result)

            print(f"  Status: OK")
            print(f"  Tables: {len(tables)}")
            for j, table in enumerate(tables):
                print(f"    Table {j+1}: {table['rows']}x{table['cols']} rows/cols")

            # Rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'page': page_num,
                'status': 'error',
                'error': str(e)
            })

    elapsed = time.time() - start_time

    # 요약
    successful = sum(1 for r in results if r.get('status') == 'success')
    total_tables = sum(r.get('tables_found', 0) for r in results if r.get('status') == 'success')
    total_rows = sum(
        sum(t.get('rows', 0) for t in r.get('tables', []))
        for r in results if r.get('status') == 'success'
    )

    summary = {
        'method': 'Option B - Split Pages',
        'pdf_name': pdf_path.name,
        'sample_pages': sample_pages,
        'total_pages_tested': len(sample_pages),
        'successful': successful,
        'total_tables': total_tables,
        'total_rows': total_rows,
        'elapsed_seconds': elapsed,
        'cost_usd': len(sample_pages) * 0.01,
        'results': results
    }

    # 저장
    summary_path = output_dir / "option_b_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*80}")
    print("OPTION B SUMMARY")
    print('='*80)
    print(f"Pages tested: {len(sample_pages)}")
    print(f"Successful: {successful}/{len(sample_pages)} ({successful/len(sample_pages)*100:.1f}%)")
    print(f"Total tables: {total_tables}")
    print(f"Total rows: {total_rows}")
    print(f"Avg rows/table: {total_rows/total_tables if total_tables > 0 else 0:.1f}")
    print(f"Time elapsed: {elapsed:.1f}s")
    print(f"Actual cost: ${summary['cost_usd']:.2f}")
    print(f"\nSaved: {summary_path}")

    return summary


def test_option_a(pdf_path: Path, sample_pages: List[int], output_dir: Path):
    """
    Option A: 전체 문서 업로드 후 샘플 페이지만 분석
    """
    print("\n" + "="*80)
    print("OPTION A: Full Document Upload")
    print("="*80)
    print(f"PDF: {pdf_path.name}")
    print(f"Total pages: 858")
    print(f"Expected cost: ~$8.58")
    print(f"Will analyze pages: {sample_pages}")

    if not UPSTAGE_API_KEY:
        print("\nERROR: UPSTAGE_API_KEY not set")
        return None

    print("\nUploading full document (this may take a few minutes)...")
    start_time = time.time()

    try:
        response = parse_pdf_upstage(pdf_path, UPSTAGE_API_KEY)

        if not response:
            print("ERROR: Failed to parse full document")
            return None

        # 전체 응답 저장
        full_response_path = output_dir / "option_a_full_response.json"
        with open(full_response_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)

        print(f"  Full response saved: {full_response_path.name}")

        # 샘플 페이지만 필터링
        print(f"\nFiltering for sample pages: {sample_pages}...")

        results = []
        for page_num in sample_pages:
            page_elements = [e for e in response.get('elements', []) if e.get('page') == page_num]
            page_tables = [e for e in page_elements if e.get('category') == 'table']

            tables = extract_tables_from_response({'elements': page_tables})

            result = {
                'page': page_num,
                'status': 'success',
                'tables_found': len(tables),
                'tables': tables
            }

            results.append(result)

            print(f"  Page {page_num}: {len(tables)} tables")

        elapsed = time.time() - start_time

        # 요약
        total_tables = sum(r.get('tables_found', 0) for r in results)
        total_rows = sum(
            sum(t.get('rows', 0) for t in r.get('tables', []))
            for r in results
        )

        # 전체 문서 통계
        all_elements = response.get('elements', [])
        all_tables = [e for e in all_elements if e.get('category') == 'table']

        summary = {
            'method': 'Option A - Full Document',
            'pdf_name': pdf_path.name,
            'total_pages': 858,
            'total_elements': len(all_elements),
            'total_tables_in_doc': len(all_tables),
            'sample_pages': sample_pages,
            'sample_tables': total_tables,
            'sample_rows': total_rows,
            'elapsed_seconds': elapsed,
            'cost_usd': 8.58,
            'results': results
        }

        # 저장
        summary_path = output_dir / "option_a_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*80}")
        print("OPTION A SUMMARY")
        print('='*80)
        print(f"Total pages in PDF: 858")
        print(f"Total tables in document: {len(all_tables)}")
        print(f"\nSample pages analyzed: {len(sample_pages)}")
        print(f"Sample tables: {total_tables}")
        print(f"Sample rows: {total_rows}")
        print(f"Avg rows/table: {total_rows/total_tables if total_tables > 0 else 0:.1f}")
        print(f"Time elapsed: {elapsed:.1f}s")
        print(f"Actual cost: ${summary['cost_usd']:.2f}")
        print(f"\nSaved: {summary_path}")

        return summary

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def compare_options(option_a_summary, option_b_summary, output_dir: Path):
    """
    Option A와 B 비교 분석
    """
    if not option_a_summary or not option_b_summary:
        print("\nCannot compare - one or both options failed")
        return

    print("\n" + "="*80)
    print("COMPARISON: Option A vs Option B")
    print("="*80)

    # 동일 페이지 비교
    comparison = {
        'option_a': {
            'method': 'Full document upload',
            'cost': option_a_summary['cost_usd'],
            'time': option_a_summary['elapsed_seconds'],
            'tables': option_a_summary['sample_tables'],
            'rows': option_a_summary['sample_rows']
        },
        'option_b': {
            'method': 'Split pages upload',
            'cost': option_b_summary['cost_usd'],
            'time': option_b_summary['elapsed_seconds'],
            'tables': option_b_summary['total_tables'],
            'rows': option_b_summary['total_rows']
        }
    }

    # 페이지별 비교
    page_comparison = []
    for page_num in option_b_summary['sample_pages']:
        a_result = next((r for r in option_a_summary['results'] if r['page'] == page_num), None)
        b_result = next((r for r in option_b_summary['results'] if r['page'] == page_num), None)

        if a_result and b_result:
            a_tables = a_result.get('tables_found', 0)
            b_tables = b_result.get('tables_found', 0)

            page_comparison.append({
                'page': page_num,
                'option_a_tables': a_tables,
                'option_b_tables': b_tables,
                'match': a_tables == b_tables
            })

    comparison['page_by_page'] = page_comparison

    # 저장
    comparison_path = output_dir / "option_a_vs_b_comparison.json"
    with open(comparison_path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    # 출력
    print("\nCost Comparison:")
    print(f"  Option A (Full): ${comparison['option_a']['cost']:.2f}")
    print(f"  Option B (Split): ${comparison['option_b']['cost']:.2f}")
    print(f"  Difference: ${comparison['option_a']['cost'] - comparison['option_b']['cost']:.2f}")

    print("\nTime Comparison:")
    print(f"  Option A: {comparison['option_a']['time']:.1f}s")
    print(f"  Option B: {comparison['option_b']['time']:.1f}s")

    print("\nResults Comparison (for sample pages):")
    print(f"  Option A: {comparison['option_a']['tables']} tables, {comparison['option_a']['rows']} rows")
    print(f"  Option B: {comparison['option_b']['tables']} tables, {comparison['option_b']['rows']} rows")

    matches = sum(1 for p in page_comparison if p['match'])
    print(f"\nPage-by-page agreement: {matches}/{len(page_comparison)} ({matches/len(page_comparison)*100:.1f}%)")

    for p in page_comparison:
        status = "✓" if p['match'] else "✗"
        print(f"  {status} Page {p['page']}: A={p['option_a_tables']}, B={p['option_b_tables']}")

    print(f"\nComparison saved: {comparison_path}")


def main():
    """메인 실행"""
    base_dir = Path(__file__).parent.parent.parent

    pdf_path = base_dir / "data" / "hira" / "ebook" / "요양급여의 적용기준 및 방법에 관한 세부사항(약제) - 2025년 7월판(G000DB5-2025-94).pdf"

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    sample_pages = [10, 50, 100, 200, 300, 400, 500, 600, 700, 800]
    output_dir = base_dir / "data" / "pharma" / "parsed" / "upstage_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Option B 먼저 (빠르고 저렴)
    option_b_summary = test_option_b(pdf_path, sample_pages, output_dir)

    # Option A (전체 문서)
    option_a_summary = test_option_a(pdf_path, sample_pages, output_dir)

    # 비교
    compare_options(option_a_summary, option_b_summary, output_dir)

    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)


if __name__ == "__main__":
    main()
