import pandas as pd
import warnings
warnings.filterwarnings('ignore')

print("=" * 100)
print("HIRA 약가 파일 ATC 코드 확인")
print("=" * 100)

# 약가 엑셀 파일 로드
excel_path = '../data/hira_master/20221101_20251101 적용약가파일_사전제공 1부.xlsx'

print(f"\n[1] 파일 로드 중: {excel_path}")

try:
    # 엑셀 파일 시트 확인
    xl = pd.ExcelFile(excel_path)
    print(f"  - 시트 목록: {xl.sheet_names}")

    # 첫 번째 시트 로드
    sheet_name = xl.sheet_names[0]
    print(f"\n[2] 시트 '{sheet_name}' 로드 중...")
    df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=10)

    print(f"\n  컬럼 목록 ({len(df.columns)}개):")
    for i, col in enumerate(df.columns, 1):
        print(f"    {i}. {col}")

    # 전체 데이터 로드
    print(f"\n[3] 전체 데이터 로드 중...")
    df_full = pd.read_excel(excel_path, sheet_name=sheet_name)
    print(f"  - 총 행 수: {len(df_full):,}개")

    # ATC 코드 관련 컬럼 찾기
    print(f"\n[4] ATC 관련 컬럼 검색...")
    atc_cols = [col for col in df_full.columns if 'ATC' in str(col).upper() or 'atc' in str(col).lower()]

    if atc_cols:
        print(f"  - ATC 컬럼 발견: {atc_cols}")

        for col in atc_cols:
            atc_data = df_full[col]
            print(f"\n  [{col}] 통계:")
            print(f"    - 전체: {len(atc_data):,}개")
            print(f"    - 값 있음: {atc_data.notna().sum():,}개 ({atc_data.notna().sum()/len(atc_data)*100:.1f}%)")
            print(f"    - 값 없음: {atc_data.isna().sum():,}개 ({atc_data.isna().sum()/len(atc_data)*100:.1f}%)")

            # 항암제(L01, L02) 필터링
            if atc_data.notna().sum() > 0:
                l01_l02 = atc_data[atc_data.astype(str).str.startswith(('L01', 'L02'), na=False)]
                print(f"    - L01/L02 (항암제): {len(l01_l02):,}개")

                # 샘플 데이터
                print(f"\n  샘플 데이터 (처음 5개):")
                sample = df_full[atc_data.notna()].head(5)
                for idx, row in sample.iterrows():
                    print(f"    - {row[col]}: {row.get('품목명', 'N/A')}")
    else:
        print("  - ATC 컬럼을 찾을 수 없습니다.")
        print("\n  대신 다른 컬럼들을 확인합니다...")
        print(f"\n  샘플 데이터 (처음 3행):")
        print(df_full.head(3).T)

except Exception as e:
    print(f"\n오류 발생: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 100)
print("분석 완료!")
print("=" * 100)
