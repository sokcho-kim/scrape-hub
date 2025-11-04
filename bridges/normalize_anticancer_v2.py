import pandas as pd
import ast
import json
from pathlib import Path

def load_hira_product_mapping(hira_json_path):
    """HIRA dictionary에서 제품코드 → 제조사 매핑 생성"""
    print(f"HIRA dictionary 로드 중: {hira_json_path}")

    with open(hira_json_path, encoding='utf-8') as f:
        data = json.load(f)

    product_code_map = {}

    for key, value in data.items():
        for record in value.get('records', []):
            pc = record.get('product_code')
            if pc:
                product_code_map[pc] = {
                    'company': record.get('company'),
                    'product_name': record.get('product_name'),
                    'ingredient_code': record.get('ingredient_code'),
                    'price': record.get('price'),
                    'route': record.get('route'),
                    'specification': record.get('specification')
                }

    print(f"총 {len(product_code_map)}개 제품코드 매핑 완료")
    return product_code_map


def normalize_anticancer_data(input_file, output_file, hira_mapping=None):
    """
    항암 CSV 데이터를 정규화합니다.
    - 문자열로 저장된 리스트를 파싱
    - 각 제품(product_code)별로 행을 분리
    - HIRA dictionary와 조인하여 정확한 제조사 정보 추가
    - 1 product = 1 row 구조로 변환
    """

    # CSV 읽기 (UTF-8 with BOM)
    df = pd.read_csv(input_file, encoding='utf-8-sig')

    print(f"\n원본 데이터: {len(df)} rows")
    print(f"컬럼: {df.columns.tolist()}")

    # 정규화된 데이터를 저장할 리스트
    normalized_rows = []
    missing_products = []

    for idx, row in df.iterrows():
        try:
            # 문자열로 저장된 리스트를 파이썬 리스트로 변환
            brand_names = ast.literal_eval(row['brand_names']) if pd.notna(row['brand_names']) else []
            product_codes = ast.literal_eval(row['product_codes']) if pd.notna(row['product_codes']) else []

            # 각 제품별로 행 생성
            for i, product_code in enumerate(product_codes):
                normalized_row = {
                    'product_code': product_code,
                    'ingredient_ko_original': row['ingredient_ko'],
                    'ingredient_code_original': row['ingredient_code'],
                    'atc_code': row['atc_code'],
                    'atc_name_en': row['atc_name_en'],
                    'brand_name_full': brand_names[i] if i < len(brand_names) else None,
                }

                # HIRA dictionary에서 제품 정보 조회
                if hira_mapping and product_code in hira_mapping:
                    hira_info = hira_mapping[product_code]
                    normalized_row['company'] = hira_info['company']
                    normalized_row['product_name_hira'] = hira_info['product_name']
                    normalized_row['ingredient_code_hira'] = hira_info['ingredient_code']
                    normalized_row['price'] = hira_info['price']
                    normalized_row['route'] = hira_info['route']
                    normalized_row['specification_hira'] = hira_info['specification']
                else:
                    normalized_row['company'] = None
                    normalized_row['product_name_hira'] = None
                    normalized_row['ingredient_code_hira'] = None
                    normalized_row['price'] = None
                    normalized_row['route'] = None
                    normalized_row['specification_hira'] = None

                    if product_code not in missing_products:
                        missing_products.append(product_code)

                # 브랜드명에서 추가 정보 추출
                if normalized_row['brand_name_full']:
                    brand_full = normalized_row['brand_name_full']

                    # 괄호 안의 성분명 추출
                    if '(' in brand_full and ')' in brand_full:
                        start_idx = brand_full.find('(')
                        end_idx = brand_full.find(')')
                        ingredient_in_brand = brand_full[start_idx+1:end_idx]
                        brand_name_short = brand_full[:start_idx]
                    else:
                        ingredient_in_brand = None
                        brand_name_short = brand_full.split('_')[0] if '_' in brand_full else brand_full

                    # 규격/용량 정보 추출 (밑줄 뒤)
                    if '_(' in brand_full:
                        spec = brand_full.split('_(')[1].rstrip(')')
                    else:
                        spec = None

                    normalized_row['brand_name_short'] = brand_name_short
                    normalized_row['ingredient_in_brand'] = ingredient_in_brand
                    normalized_row['specification_brand'] = spec

                normalized_rows.append(normalized_row)

        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            print(f"Row data: {row.to_dict()}")
            continue

    # DataFrame 생성
    normalized_df = pd.DataFrame(normalized_rows)

    print(f"\n정규화된 데이터: {len(normalized_df)} rows")
    print(f"컬럼: {normalized_df.columns.tolist()}")

    if missing_products:
        print(f"\n경고: {len(missing_products)}개 제품코드가 HIRA dictionary에 없습니다.")
        print(f"샘플: {missing_products[:10]}")

    # 컬럼 순서 정리
    column_order = [
        'product_code',
        'brand_name_short',
        'brand_name_full',
        'specification_brand',
        'specification_hira',
        'company',
        'price',
        'route',
        'ingredient_ko_original',
        'ingredient_in_brand',
        'ingredient_code_original',
        'ingredient_code_hira',
        'atc_code',
        'atc_name_en',
        'product_name_hira'
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
    print(f"고유 성분 수: {normalized_df['ingredient_ko_original'].nunique()}")
    print(f"고유 제조사 수: {normalized_df['company'].nunique()}")
    print(f"고유 ATC 코드 수: {normalized_df['atc_code'].nunique()}")
    print(f"제조사 정보 있음: {normalized_df['company'].notna().sum()}")
    print(f"약가 정보 있음: {normalized_df['price'].notna().sum()}")

    # 샘플 데이터 출력
    print("\n=== 샘플 데이터 (처음 5행) ===")
    print(normalized_df.head(5).to_string())

    return normalized_df


if __name__ == "__main__":
    # HIRA dictionary 로드
    hira_json_path = "../data/hira_master/drug_dictionary_normalized.json"
    hira_mapping = load_hira_product_mapping(hira_json_path)

    # 정규화 실행
    input_file = "anticancer_master.csv"
    output_file = "anticancer_normalized_v2.csv"

    df = normalize_anticancer_data(input_file, output_file, hira_mapping)

    # JSON으로도 저장 (옵션)
    json_file = "anticancer_normalized_v2.json"
    df.to_json(json_file, orient='records', force_ascii=False, indent=2)
    print(f"\nJSON 저장 완료: {json_file}")
