#!/usr/bin/env python3
"""엑셀 파일 구조 분석"""
import pandas as pd
from pathlib import Path


def analyze_excel(xlsx_path: Path, output_path: Path):
    """엑셀 파일 분석 후 텍스트로 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    xl_file = pd.ExcelFile(xlsx_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'=== Excel File: {xlsx_path.name} ===\n\n')
        f.write(f'Total sheets: {len(xl_file.sheet_names)}\n')
        f.write(f'Sheet names: {xl_file.sheet_names}\n\n')

        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

            separator = '=' * 80
            f.write(f'{separator}\n')
            f.write(f'Sheet: {sheet_name}\n')
            f.write(f'{separator}\n')
            f.write(f'Shape: {df.shape[0]} rows x {df.shape[1]} columns\n\n')

            # 컬럼명
            f.write(f'Columns:\n')
            for i, col in enumerate(df.columns, 1):
                f.write(f'  {i}. {col}\n')

            # 처음 5행
            f.write(f'\nFirst 5 rows:\n')
            f.write(df.head(5).to_string(index=True))
            f.write(f'\n\n')

    print(f'Analysis saved to: {output_path}')


if __name__ == '__main__':
    xlsx_path = Path('data/hira_cancer/raw/attachments/chemotherapy/사전신청요법(용법용량 포함)및 불승인요법_250915.xlsx')
    output_path = Path('data/hira_cancer/parsed/chemotherapy/excel_analysis.txt')

    analyze_excel(xlsx_path, output_path)
