"""
Upstage Document Parse API 테스트 - 약제 기준 PDF

목적:
- 약제 사용 기준 PDF의 표 파싱 성능 평가
- pdfplumber vs Upstage 비교
- 복잡한 표 (병합셀, 중첩) 처리 능력 확인
"""
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import requests

# Upstage API 설정
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")
UPSTAGE_DOCUMENT_PARSE_URL = "https://api.upstage.ai/v1/document-ai/document-parse"


def parse_pdf_page_upstage(pdf_path: Path, page_num: int) -> Dict[str, Any]:
    """
    Upstage Document Parse API로 특정 페이지 파싱

    Args:
        pdf_path: PDF 파일 경로
        page_num: 파싱할 페이지 번호 (1-based)

    Returns:
        API 응답 결과
    """
    if not UPSTAGE_API_KEY:
        raise ValueError("UPSTAGE_API_KEY environment variable not set")

    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}"
    }

    # PDF 파일 읽기
    with open(pdf_path, 'rb') as f:
        files = {
            'document': (pdf_path.name, f, 'application/pdf')
        }

        # API 파라미터
        data = {
            'ocr': 'force',  # OCR 강제 (표 감지 향상)
            'page': str(page_num)  # 특정 페이지만
        }

        print(f"  Calling Upstage API for page {page_num}...")
        response = requests.post(
            UPSTAGE_DOCUMENT_PARSE_URL,
            headers=headers,
            files=files,
            data=data
        )

    if response.status_code != 200:
        print(f"  ERROR: API returned status {response.status_code}")
        print(f"  Response: {response.text}")
        return None

    return response.json()


def extract_tables_from_upstage_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Upstage 응답에서 표 정보 추출

    Args:
        response: Upstage API 응답

    Returns:
        표 리스트
    """
    tables = []

    if not response or 'elements' not in response:
        return tables

    for element in response['elements']:
        if element.get('category') == 'table':
            table_info = {
                'id': element.get('id'),
                'page': element.get('page'),
                'bbox': element.get('bounding_box'),
                'html': element.get('html'),
                'text': element.get('text'),
                'rows': 0,
                'cols': 0
            }

            # HTML에서 행/열 수 추정
            html = element.get('html', '')
            if html:
                table_info['rows'] = html.count('<tr>')
                # 첫 번째 tr에서 td/th 개수
                import re
                first_row = re.search(r'<tr>.*?</tr>', html, re.DOTALL)
                if first_row:
                    table_info['cols'] = first_row.group().count('<td>') + first_row.group().count('<th>')

            tables.append(table_info)

    return tables


def test_upstage_pharma(pdf_path: Path, sample_pages: List[int], output_dir: Path):
    """
    약제 PDF Upstage 파싱 테스트

    Args:
        pdf_path: PDF 경로
        sample_pages: 테스트할 페이지 목록
        output_dir: 결과 저장 디렉토리
    """
    print("="*60)
    print("Upstage Document Parse API - Pharma Test")
    print("="*60)
    print(f"\nPDF: {pdf_path.name}")
    print(f"Sample pages: {sample_pages}")
    print(f"Output: {output_dir}")

    if not UPSTAGE_API_KEY:
        print("\nERROR: UPSTAGE_API_KEY not set")
        print("Please set the environment variable:")
        print("  export UPSTAGE_API_KEY='your-api-key'")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_cost = 0.0
    cost_per_page = 0.01  # $0.01 per page (estimated)

    for page_num in sample_pages:
        print(f"\n{'='*60}")
        print(f"Page {page_num}")
        print('='*60)

        try:
            # API 호출
            start_time = time.time()
            response = parse_pdf_page_upstage(pdf_path, page_num)
            elapsed = time.time() - start_time

            if not response:
                results.append({
                    'page': page_num,
                    'status': 'failed',
                    'error': 'API call failed'
                })
                continue

            # 표 추출
            tables = extract_tables_from_upstage_response(response)

            result = {
                'page': page_num,
                'status': 'success',
                'elapsed_seconds': elapsed,
                'tables_found': len(tables),
                'tables': tables,
                'raw_response': response
            }

            results.append(result)
            total_cost += cost_per_page

            # 결과 출력
            print(f"  Status: OK")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Tables: {len(tables)}")

            for i, table in enumerate(tables):
                print(f"    Table {i+1}: {table['rows']}x{table['cols']} rows/cols")
                if table.get('text'):
                    preview = table['text'][:100].replace('\n', ' ')
                    print(f"      Preview: {preview}...")

            # 개별 페이지 결과 저장
            page_output_path = output_dir / f"page_{page_num}_upstage.json"
            with open(page_output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"  Saved: {page_output_path.name}")

            # Rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'page': page_num,
                'status': 'error',
                'error': str(e)
            })

    # 전체 요약
    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    successful = sum(1 for r in results if r.get('status') == 'success')
    total_tables = sum(r.get('tables_found', 0) for r in results if r.get('status') == 'success')
    total_rows = sum(
        sum(t.get('rows', 0) for t in r.get('tables', []))
        for r in results if r.get('status') == 'success'
    )

    print(f"Pages tested: {len(sample_pages)}")
    print(f"Successful: {successful}/{len(sample_pages)} ({successful/len(sample_pages)*100:.1f}%)")
    print(f"Total tables: {total_tables}")
    print(f"Total rows: {total_rows}")
    print(f"Avg rows/table: {total_rows/total_tables if total_tables > 0 else 0:.1f}")
    print(f"\nEstimated cost: ${total_cost:.2f}")

    # 전체 결과 저장
    summary_path = output_dir / "upstage_test_summary.json"
    summary = {
        "pdf_name": pdf_path.name,
        "sample_pages": sample_pages,
        "total_pages_tested": len(sample_pages),
        "successful": successful,
        "total_tables": total_tables,
        "total_rows": total_rows,
        "estimated_cost_usd": total_cost,
        "results": results
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nSummary saved: {summary_path}")


def main():
    """메인 실행"""
    base_dir = Path(__file__).parent.parent.parent

    # 약제 PDF 경로
    pdf_path = base_dir / "data" / "hira" / "ebook" / "요양급여의 적용기준 및 방법에 관한 세부사항(약제) - 2025년 7월판(G000DB5-2025-94).pdf"

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    # 샘플 페이지 선택 (전략적 분산)
    sample_pages = [
        10,   # 초반
        50,   # 약제 목록 시작
        100,  # 중간
        200,  # 중간
        300,  # 중간
        400,  # 중간
        500,  # 후반
        600,  # 후반
        700,  # 후반
        800   # 말미
    ]

    # 출력 디렉토리
    output_dir = base_dir / "data" / "pharma" / "parsed" / "upstage_test"

    # 테스트 실행
    test_upstage_pharma(pdf_path, sample_pages, output_dir)


if __name__ == "__main__":
    main()
