import pandas as pd
import ast
import json
from pathlib import Path

def normalize_anticancer_data(input_file, output_file):
    """
    항암 CSV 데이터를 정규화합니다.
    - 문자열로 저장된 리스트를 파싱
    - 각 제품(product_code)별로 행을 분리
    - 1 product = 1 row 구조로 변환
    """

    # CSV 읽기 (UTF-8 with BOM)
    df = pd.read_csv(input_file, encoding='utf-8-sig')

    print(f"원본 데이터: {len(df)} rows")
    print(f"컬럼: {df.columns.tolist()}")

    # 정규화된 데이터를 저장할 리스트
    normalized_rows = []

    for idx, row in df.iterrows():
        try:
            # 문자열로 저장된 리스트를 파이썬 리스트로 변환
            brand_names = ast.literal_eval(row['brand_names']) if pd.notna(row['brand_names']) else []
            manufacturers = ast.literal_eval(row['manufacturers']) if pd.notna(row['manufacturers']) else []
            product_codes = ast.literal_eval(row['product_codes']) if pd.notna(row['product_codes']) else []

            # 각 제품별로 행 생성
            for i, product_code in enumerate(product_codes):
                normalized_row = {
                    'ingredient_ko': row['ingredient_ko'],
                    'ingredient_code': row['ingredient_code'],
                    'atc_code': row['atc_code'],
                    'atc_name_en': row['atc_name_en'],
                    'product_code': product_code,
                    'brand_name': brand_names[i] if i < len(brand_names) else None,
                    'manufacturer': manufacturers[i] if i < len(manufacturers) else None,
                }

                # 브랜드명에서 추가 정보 추출
                if normalized_row['brand_name']:
                    # 브랜드명과 용량/규격 분리
                    # 예: "유토랄주250밀리그람(플루오로우라실)_(0.25g/5mL)"
                    brand_full = normalized_row['brand_name']

                    # 괄호 안의 성분명 추출
                    if '(' in brand_full and ')' in brand_full:
                        start_idx = brand_full.find('(')
                        end_idx = brand_full.find(')')
                        ingredient_in_brand = brand_full[start_idx+1:end_idx]
                        brand_name_only = brand_full[:start_idx]
                    else:
                        ingredient_in_brand = None
                        brand_name_only = brand_full.split('_')[0] if '_' in brand_full else brand_full

                    # 규격/용량 정보 추출 (밑줄 뒤)
                    if '_(' in brand_full:
                        spec = brand_full.split('_(')[1].rstrip(')')
                    else:
                        spec = None

                    normalized_row['brand_name_full'] = brand_full
                    normalized_row['brand_name_short'] = brand_name_only
                    normalized_row['ingredient_in_brand'] = ingredient_in_brand
                    normalized_row['specification'] = spec

                normalized_rows.append(normalized_row)

        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            print(f"Row data: {row.to_dict()}")
            continue

    # DataFrame 생성
    normalized_df = pd.DataFrame(normalized_rows)

    print(f"\n정규화된 데이터: {len(normalized_df)} rows")
    print(f"컬럼: {normalized_df.columns.tolist()}")

    # 컬럼 순서 정리
    column_order = [
        'product_code',
        'brand_name_short',
        'brand_name_full',
        'specification',
        'ingredient_ko',
        'ingredient_in_brand',
        'ingredient_code',
        'atc_code',
        'atc_name_en',
        'manufacturer'
    ]

    # 존재하는 컬럼만 선택
    existing_columns = [col for col in column_order if col in normalized_df.columns]
    normalized_df = normalized_df[existing_columns]

    # CSV 저장
    normalized_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n저장 완료: {output_file}")

    # 통계 출력
    print("\n=== 통계 ===")
    print(f"총 제품 수: {len(normalized_df)}")
    print(f"고유 성분 수: {normalized_df['ingredient_ko'].nunique()}")
    print(f"고유 제조사 수: {normalized_df['manufacturer'].nunique()}")
    print(f"고유 ATC 코드 수: {normalized_df['atc_code'].nunique()}")

    # 샘플 데이터 출력
    print("\n=== 샘플 데이터 (처음 3행) ===")
    print(normalized_df.head(3).to_string())

    return normalized_df


if __name__ == "__main__":
    input_file = "anticancer_master.csv"
    output_file = "anticancer_normalized.csv"

    df = normalize_anticancer_data(input_file, output_file)

    # JSON으로도 저장 (옵션)
    json_file = "anticancer_normalized.json"
    df.to_json(json_file, orient='records', force_ascii=False, indent=2)
    print(f"\nJSON 저장 완료: {json_file}")
