"""
Phase 2: 그룹 A PDF → Markdown 변환 (pdfplumber)

그룹 A: pdfplumber만으로 충분한 품질의 PDF
- 6개 파일, 4,040페이지
- 비용: $0 (무료)
"""
import pdfplumber
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List


def table_to_markdown(table: List[List[str]]) -> str:
    """
    pdfplumber 표를 Markdown 테이블로 변환

    Args:
        table: pdfplumber extract_tables() 결과

    Returns:
        Markdown 형식 테이블 문자열
    """
    if not table or len(table) == 0:
        return ""

    # None 값 처리
    cleaned_table = []
    for row in table:
        cleaned_row = [str(cell).strip() if cell else "" for cell in row]
        cleaned_table.append(cleaned_row)

    if len(cleaned_table) == 0:
        return ""

    # Markdown 테이블 생성
    lines = []

    # 헤더 (첫 번째 행)
    header = " | ".join(cleaned_table[0])
    lines.append(f"| {header} |")

    # 구분선
    separator = " | ".join(["---"] * len(cleaned_table[0]))
    lines.append(f"| {separator} |")

    # 데이터 행
    for row in cleaned_table[1:]:
        # 컬럼 수 맞추기
        while len(row) < len(cleaned_table[0]):
            row.append("")
        row_str = " | ".join(row[:len(cleaned_table[0])])
        lines.append(f"| {row_str} |")

    return "\n".join(lines)


def process_pdf_to_markdown(pdf_path: Path, file_info: dict) -> dict:
    """
    PDF 파일을 Markdown으로 변환

    Args:
        pdf_path: PDF 파일 경로
        file_info: analysis_report.json의 파일 정보

    Returns:
        변환 결과 (메타데이터 + Markdown 콘텐츠)
    """
    print(f"\nProcessing: {file_info['filename']}")
    print(f"  Pages: {file_info['pages']}")
    print(f"  Expected chars: {file_info['total_chars']:,}")

    result = {
        "metadata": {
            "source_file": file_info['filename'],
            "source_type": "HIRA EBOOK",
            "parsed_at": datetime.now().isoformat(),
            "parser": "pdfplumber",
            "pages": file_info['pages'],
            "file_size_mb": file_info['file_size_mb'],
            "quality_score": file_info['quality_score'],
            "table_count": file_info['table_count']
        },
        "pages": [],
        "full_text": ""
    }

    all_text_parts = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                if page_num % 100 == 0:
                    print(f"    Processing page {page_num}/{file_info['pages']}...")

                page_content = []

                # 1. 텍스트 추출
                text = page.extract_text()
                if text:
                    page_content.append(text)

                # 2. 표 추출 (Markdown 변환)
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables):
                        md_table = table_to_markdown(table)
                        if md_table:
                            page_content.append(f"\n\n**[Table {table_idx + 1}]**\n\n{md_table}\n")

                # 페이지 콘텐츠 결합
                page_text = "\n".join(page_content)

                # 페이지 정보 저장
                result["pages"].append({
                    "page_num": page_num,
                    "char_count": len(page_text),
                    "has_tables": len(tables) > 0 if tables else False,
                    "table_count": len(tables) if tables else 0,
                    "content": page_text
                })

                # 전체 텍스트에 추가
                all_text_parts.append(f"\n\n--- Page {page_num} ---\n\n{page_text}")

        # 전체 텍스트 결합
        result["full_text"] = "".join(all_text_parts)
        result["metadata"]["parsed_chars"] = len(result["full_text"])
        result["metadata"]["parsed_pages"] = len(result["pages"])

        print(f"  OK Completed: {len(result['pages'])} pages, {len(result['full_text']):,} chars")

        return result

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        result["metadata"]["error"] = str(e)
        return result


def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("HIRA EBOOK Phase 2: Group A Processing")
    print("=" * 60)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    ebook_dir = base_dir / "data" / "hira" / "ebook"
    output_dir = base_dir / "data" / "hira" / "parsed" / "group_a"

    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    # analysis_report.json 읽기
    report_path = ebook_dir / "analysis_report.json"
    if not report_path.exists():
        print(f"Error: {report_path} not found!")
        print("Please run analyze_ebooks.py first.")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)

    # 그룹 A 파일 필터링
    group_a_files = [
        file_info for file_info in analysis_data['files']
        if file_info.get('group') == 'A'
    ]

    print(f"\nFound {len(group_a_files)} Group A files:")
    for i, file_info in enumerate(group_a_files, 1):
        print(f"  {i}. {file_info['filename']}")
        print(f"     - {file_info['pages']} pages, {file_info['total_chars']:,} chars")

    print(f"\nOutput directory: {output_dir}")

    # 각 파일 처리
    results_summary = []

    for file_info in group_a_files:
        pdf_path = ebook_dir / file_info['filename']

        if not pdf_path.exists():
            print(f"\nERROR: File not found: {pdf_path}")
            continue

        # PDF -> Markdown 변환
        result = process_pdf_to_markdown(pdf_path, file_info)

        # 결과 저장
        output_filename = pdf_path.stem + ".json"
        output_path = output_dir / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"  OK Saved: {output_path.name}")

        # 요약 정보
        results_summary.append({
            "filename": file_info['filename'],
            "output_file": output_filename,
            "pages": result["metadata"]["parsed_pages"],
            "chars": result["metadata"]["parsed_chars"],
            "tables": result["metadata"]["table_count"],
            "status": "success" if "error" not in result["metadata"] else "failed"
        })

    # 전체 요약 저장
    summary_path = output_dir / "processing_summary.json"
    summary_data = {
        "processed_at": datetime.now().isoformat(),
        "group": "A",
        "files_processed": len(results_summary),
        "total_pages": sum(r["pages"] for r in results_summary),
        "total_chars": sum(r["chars"] for r in results_summary),
        "total_tables": sum(r["tables"] for r in results_summary),
        "files": results_summary
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    # 최종 요약 출력
    print("\n" + "=" * 60)
    print("Processing Summary")
    print("=" * 60)
    print(f"Files processed: {summary_data['files_processed']}")
    print(f"Total pages: {summary_data['total_pages']:,}")
    print(f"Total characters: {summary_data['total_chars']:,}")
    print(f"Total tables: {summary_data['total_tables']:,}")
    print(f"\nOutput directory: {output_dir}")
    print(f"Summary file: {summary_path}")
    print("\nOK Phase 2 completed!")


if __name__ == "__main__":
    main()
