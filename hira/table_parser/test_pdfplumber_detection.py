"""
pdfplumber.find_tables() 표 감지 테스트
- Camelot lattice vs pdfplumber 비교
"""
import json
from pathlib import Path
import pdfplumber

def test_pdfplumber_detection(pdf_path: Path, sample_pages: list):
    """pdfplumber 표 감지 테스트"""

    print("="*60)
    print("pdfplumber.find_tables() Detection Test")
    print("="*60)

    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in sample_pages:
            if page_num > len(pdf.pages):
                continue

            page = pdf.pages[page_num - 1]

            # pdfplumber 표 감지
            tables = page.find_tables()

            result = {
                "page": page_num,
                "tables_found": len(tables),
                "tables_info": []
            }

            for i, table in enumerate(tables):
                # 표 정보
                bbox = table.bbox

                # 실제 데이터 추출 시도
                extracted = table.extract()
                row_count = len(extracted) if extracted else 0
                col_count = len(extracted[0]) if extracted and len(extracted) > 0 else 0

                table_info = {
                    "table_id": f"t{page_num}_{i+1}",
                    "bbox": bbox,
                    "rows": row_count,
                    "cols": col_count,
                    "has_data": extracted is not None and len(extracted) > 0
                }

                result["tables_info"].append(table_info)

            results.append(result)

            print(f"\nPage {page_num}:")
            print(f"  Tables found: {len(tables)}")
            if tables:
                for info in result["tables_info"]:
                    print(f"    - {info['table_id']}: {info['rows']}x{info['cols']} rows/cols, bbox={info['bbox']}")

    # 요약
    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    total_tables = sum(r["tables_found"] for r in results)
    total_rows = sum(
        sum(t["rows"] for t in r["tables_info"])
        for r in results
    )
    pages_with_tables = sum(1 for r in results if r["tables_found"] > 0)

    print(f"Total pages tested: {len(sample_pages)}")
    print(f"Pages with tables: {pages_with_tables}/{len(sample_pages)} ({pages_with_tables/len(sample_pages)*100:.1f}%)")
    print(f"Total tables detected: {total_tables}")
    print(f"Total rows extracted: {total_rows}")
    print(f"Avg rows/table: {total_rows/total_tables if total_tables > 0 else 0:.1f}")

    # 결과 저장
    output_dir = Path(__file__).parent.parent.parent / "data" / "hira" / "table_parser" / "mvp_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "pdfplumber_detection_test.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "sample_pages": sample_pages,
            "results": results,
            "summary": {
                "total_tables": total_tables,
                "total_rows": total_rows,
                "pages_with_tables": pages_with_tables,
                "detection_rate": pages_with_tables / len(sample_pages)
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved: {output_path}")

    return results


def main():
    """메인 실행"""
    base_dir = Path(__file__).parent.parent.parent
    pdf_path = base_dir / "data" / "hira" / "ebook" / "2025년 1월판 건강보험요양급여비용-(G000A37-2025-16).pdf"

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    print(f"PDF: {pdf_path.name}\n")

    # 동일한 샘플 페이지
    sample_pages = [10, 15, 20, 100, 105, 110, 200, 250, 300, 500]

    results = test_pdfplumber_detection(pdf_path, sample_pages)

    print("\n" + "="*60)
    print("Comparison with Camelot lattice")
    print("="*60)
    print("Camelot lattice:")
    print("  - Detection rate: 60% (6/10 pages)")
    print("  - Total rows: 6 (avg 1 row/table)")
    print("\npdfplumber.find_tables():")

    total_tables = sum(r["tables_found"] for r in results)
    total_rows = sum(sum(t["rows"] for t in r["tables_info"]) for r in results)
    pages_with_tables = sum(1 for r in results if r["tables_found"] > 0)

    print(f"  - Detection rate: {pages_with_tables/len(sample_pages)*100:.0f}% ({pages_with_tables}/10 pages)")
    print(f"  - Total rows: {total_rows} (avg {total_rows/total_tables if total_tables > 0 else 0:.1f} rows/table)")

    if pages_with_tables > 6:
        print("\nOK: pdfplumber is BETTER at detection!")
    elif pages_with_tables == 6:
        print("\n~: Similar detection rate")
    else:
        print("\nX: pdfplumber is worse")


if __name__ == "__main__":
    main()
