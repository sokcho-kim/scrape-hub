"""
KCD-9 Master file 분석
"""
import sys
import codecs
from pathlib import Path
import pandas as pd

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def analyze_masterfile():
    """Master file 분석"""

    file_path = Path('data/kssc/kcd-9th/제9차 한국표준질병ㆍ사인분류 2차 정오 DB masterfile_251031_20251103085142.xlsx')

    print('='*80)
    print('📊 KCD-9 Master File 분석')
    print('='*80)
    print(f'\n파일: {file_path.name}\n')

    xl_file = pd.ExcelFile(file_path)

    print(f'📁 시트 목록: {len(xl_file.sheet_names)}개\n')
    for i, sheet in enumerate(xl_file.sheet_names, 1):
        print(f'  {i}. {sheet}')

    # 각 시트 분석
    for sheet_name in xl_file.sheet_names:
        print(f'\n\n{"="*80}')
        print(f'📄 Sheet: {sheet_name}')
        print(f'{"="*80}\n')

        # 헤더 확인 (처음 10행)
        df_preview = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=10)
        print(f'[처음 10행 미리보기]')
        print(df_preview.to_string())

        # 실제 데이터 읽기 (헤더 추정)
        print(f'\n[데이터 구조 분석]')

        # 헤더가 1행에 있다고 가정
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)

        print(f'  총 행 수: {len(df):,}')
        print(f'  총 열 수: {len(df.columns)}')
        print(f'\n  컬럼명:')
        for i, col in enumerate(df.columns, 1):
            print(f'    {i}. {col}')

        print(f'\n  첫 5행 샘플:')
        print(df.head(5).to_string(max_colwidth=50))

        # 기본 통계
        print(f'\n  결측치 확인:')
        null_counts = df.isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                print(f'    {col}: {count:,}개 ({count/len(df)*100:.1f}%)')


def main():
    analyze_masterfile()

    print('\n\n' + '='*80)
    print('✅ 분석 완료')
    print('='*80)


if __name__ == '__main__':
    main()
