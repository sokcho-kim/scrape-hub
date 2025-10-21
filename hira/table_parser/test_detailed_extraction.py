"""
pdfplumber 상세 추출 테스트
- 실제 데이터가 어떻게 추출되는지 확인
"""
from pathlib import Path
import pdfplumber
import json

def test_detailed_extraction():
    """상세 추출 테스트"""
    base_dir = Path(__file__).parent.parent.parent
    pdf_path = base_dir / "data" / "hira" / "ebook" / "2025년 1월판 건강보험요양급여비용-(G000A37-2025-16).pdf"

    print("="*60)
    print("Detailed Extraction Test - Page 105")
    print("="*60)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[104]  # page 105

        # 표 찾기
        tables = page.find_tables()
        print(f"\nTables found: {len(tables)}\n")

        if tables:
            table = tables[0]
            extracted = table.extract()

            print(f"Table dimensions: {len(extracted)} rows x {len(extracted[0]) if extracted else 0} cols")
            print(f"\nFirst 5 rows:")
            print("-"*60)

            for i, row in enumerate(extracted[:5]):
                print(f"\nRow {i}:")
                for j, cell in enumerate(row):
                    # 셀 내용 미리보기
                    if cell:
                        cell_preview = cell.replace('\n', '\\n')[:100]
                        print(f"  Col {j}: {cell_preview}...")
                    else:
                        print(f"  Col {j}: [EMPTY]")

            # 병합셀 분석
            print("\n" + "="*60)
            print("Merged Cell Analysis")
            print("="*60)

            for i, row in enumerate(extracted[:5]):
                for j, cell in enumerate(row):
                    if cell and '\n' in cell:
                        lines = cell.split('\n')
                        if len(lines) > 1:
                            print(f"\nRow {i}, Col {j}: {len(lines)} lines in single cell")
                            print(f"  First 3 lines: {lines[:3]}")

            # 실험: 줄바꿈 분할
            print("\n" + "="*60)
            print("Split by Newline Experiment")
            print("="*60)

            # 코드 컬럼(col 1) 분할 시도
            code_column = extracted[1][1] if len(extracted) > 1 else None
            if code_column and '\n' in code_column:
                codes = [c.strip() for c in code_column.split('\n') if c.strip()]
                print(f"\nCode column (before split): 1 cell")
                print(f"Code column (after split): {len(codes)} codes")
                print(f"Sample codes: {codes[:5]}")

            # 점수 컬럼(col 3) 분할 시도
            score_column = extracted[1][3] if len(extracted) > 1 and len(extracted[1]) > 3 else None
            if score_column and '\n' in score_column:
                scores = [s.strip() for s in score_column.split('\n') if s.strip()]
                print(f"\nScore column (before split): 1 cell")
                print(f"Score column (after split): {len(scores)} scores")
                print(f"Sample scores: {scores[:5]}")

            # 예상 행 수
            if code_column and '\n' in code_column:
                codes = [c.strip() for c in code_column.split('\n') if c.strip()]
                print(f"\n" + "="*60)
                print(f"ESTIMATED ACTUAL ROWS: {len(codes)}")
                print(f"CURRENTLY EXTRACTED: {len(extracted)} rows")
                print(f"MISSING: {len(codes) - len(extracted)} rows ({(len(codes) - len(extracted))/len(codes)*100:.1f}%)")
                print("="*60)


if __name__ == "__main__":
    test_detailed_extraction()
