"""
건강보험요양급여비용 PDF 구조 분석

목적:
1. PDF 구조 파악 (표, 텍스트, 이미지)
2. EDI 코드 패턴 분석
3. 파싱 전략 수립
"""

import pdfplumber
import json
from pathlib import Path

pdf_path = Path("data/hira/ebook/2025년 1월판 건강보험요양급여비용-(G000A37-2025-16).pdf")
output_dir = Path("data/hira/analysis")
output_dir.mkdir(parents=True, exist_ok=True)

def analyze_pdf_structure():
    """PDF 구조 분석"""

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"총 페이지: {total_pages}")

        # 샘플 페이지 분석 (50, 100, 200, 500페이지)
        sample_pages = [50, 100, 200, 500]

        analysis = {
            'total_pages': total_pages,
            'samples': []
        }

        for page_num in sample_pages:
            if page_num >= total_pages:
                continue

            print(f"\n{'='*80}")
            print(f"Page {page_num + 1} 분석")
            print(f"{'='*80}")

            page = pdf.pages[page_num]

            # 텍스트 추출
            text = page.extract_text()

            # 표 추출
            tables = page.extract_tables()

            # 페이지 정보
            page_info = {
                'page_number': page_num + 1,
                'has_text': text is not None and len(text) > 0,
                'text_length': len(text) if text else 0,
                'text_sample': text[:500] if text else None,
                'table_count': len(tables) if tables else 0,
                'tables': []
            }

            print(f"텍스트 길이: {page_info['text_length']}")
            print(f"표 개수: {page_info['table_count']}")

            # 표 구조 분석
            if tables:
                for i, table in enumerate(tables[:2]):  # 처음 2개 표만
                    if table and len(table) > 0:
                        table_info = {
                            'index': i,
                            'rows': len(table),
                            'cols': len(table[0]) if table[0] else 0,
                            'sample_rows': table[:3]  # 처음 3행
                        }
                        page_info['tables'].append(table_info)

                        print(f"\n표 {i+1}:")
                        print(f"  행: {table_info['rows']}, 열: {table_info['cols']}")
                        # 표 내용은 파일에만 저장

            # 텍스트 샘플 (파일에만 저장, 화면 출력 안 함)

            analysis['samples'].append(page_info)

        # 결과 저장
        output_file = output_dir / "suga_structure_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        print(f"\n\n분석 결과 저장: {output_file}")

        return analysis


def search_edi_patterns():
    """EDI 코드 패턴 검색"""

    print(f"\n\n{'='*80}")
    print("EDI 코드 패턴 검색 (샘플 100페이지)")
    print(f"{'='*80}")

    edi_patterns = []

    with pdfplumber.open(pdf_path) as pdf:
        # 50-150페이지에서 샘플 검색
        for page_num in range(50, min(150, len(pdf.pages)), 10):
            page = pdf.pages[page_num]
            text = page.extract_text()

            if not text:
                continue

            # EDI 코드 패턴 찾기 (영문자+숫자 조합)
            import re

            # 패턴 1: A1234 형태
            pattern1 = re.findall(r'\b[A-Z]\d{4}\b', text)

            # 패턴 2: AA123 형태
            pattern2 = re.findall(r'\b[A-Z]{2}\d{3}\b', text)

            # 패턴 3: 123456 형태 (6자리 숫자)
            pattern3 = re.findall(r'\b\d{6}\b', text)

            if pattern1 or pattern2 or pattern3:
                edi_patterns.append({
                    'page': page_num + 1,
                    'pattern1': pattern1[:5],
                    'pattern2': pattern2[:5],
                    'pattern3': pattern3[:5]
                })

                print(f"\nPage {page_num + 1}:")
                if pattern1:
                    print(f"  패턴1 (A1234): {pattern1[:5]}")
                if pattern2:
                    print(f"  패턴2 (AA123): {pattern2[:5]}")
                if pattern3:
                    print(f"  패턴3 (123456): {pattern3[:5]}")

    # 결과 저장
    output_file = output_dir / "edi_patterns.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(edi_patterns, f, ensure_ascii=False, indent=2)

    print(f"\n\nEDI 패턴 저장: {output_file}")


if __name__ == "__main__":
    print("건강보험요양급여비용 PDF 구조 분석 시작\n")

    # 1. 구조 분석
    analysis = analyze_pdf_structure()

    # 2. EDI 패턴 검색
    search_edi_patterns()

    print("\n\n분석 완료!")
