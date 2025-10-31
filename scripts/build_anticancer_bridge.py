#!/usr/bin/env python3
"""
약가 마스터에서 항암제 브리지 구축

입력: data/pharmalex_unity/merged_pharma_data_20250915_102415.csv
출력: bridges/anticancer_master.parquet

필터: ATC L01 (항암제) + L02 (호르몬 요법)
정제: 성분명 기준 중복 제거, 브랜드명 집계
"""

import pandas as pd
from pathlib import Path
import json

def main():
    print("=" * 80)
    print("항암제 브리지 구축 (Code-based Ground Truth)")
    print("=" * 80)

    # 1. 약가 마스터 로드
    print("\n[1/4] Loading pharma master...")
    df = pd.read_csv(
        'data/pharmalex_unity/merged_pharma_data_20250915_102415.csv',
        encoding='utf-8-sig',
        low_memory=False
    )
    print(f"  Total records: {len(df):,}")

    # 2. L01/L02 항암제 필터링
    print("\n[2/4] Filtering anticancer drugs (L01/L02)...")
    anticancer = df[
        df['ATC코드'].str.startswith('L01', na=False) |
        df['ATC코드'].str.startswith('L02', na=False)
    ].copy()
    print(f"  Anticancer records: {len(anticancer):,}")

    # 3. 필요한 컬럼만 선택
    keep_cols = [
        'ATC코드', 'ATC코드 명칭',
        '일반명', '제품명', '업체명',
        '제품코드', '주성분코드'
    ]
    anticancer = anticancer[keep_cols].copy()

    # 4. 성분명 기준 집계
    print("\n[3/4] Aggregating by ingredient...")

    # 성분명별 그룹화
    grouped = anticancer.groupby('일반명').agg({
        'ATC코드': 'first',  # 첫 번째 ATC 코드 (동일 성분은 같은 코드)
        'ATC코드 명칭': 'first',
        '제품명': lambda x: list(x.unique()),  # 모든 브랜드명
        '업체명': lambda x: list(x.unique()),  # 모든 제조사
        '제품코드': lambda x: list(x.unique()),
        '주성분코드': 'first'
    }).reset_index()

    grouped.columns = [
        'ingredient_ko',  # 일반명 (한글)
        'atc_code',
        'atc_name_en',
        'brand_names',  # 브랜드명 리스트
        'manufacturers',
        'product_codes',
        'ingredient_code'
    ]

    print(f"  Unique ingredients: {len(grouped)}")
    print(f"  L01: {len(grouped[grouped['atc_code'].str.startswith('L01', na=False)])}")
    print(f"  L02: {len(grouped[grouped['atc_code'].str.startswith('L02', na=False)])}")

    # 5. 브랜드명 수 계산
    grouped['brand_count'] = grouped['brand_names'].apply(len)

    # 6. 저장
    print("\n[4/4] Saving...")

    # JSON으로 저장
    output_dir = Path('bridges')
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / 'anticancer_master.json'
    data = grouped.to_dict(orient='records')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {json_path} ({len(grouped)} ingredients)")

    # CSV 백업
    csv_path = output_dir / 'anticancer_master.csv'
    grouped.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  CSV: {csv_path}")

    # JSON 샘플 저장 (검증용)
    sample_path = output_dir / 'anticancer_master_sample.json'
    sample = grouped.head(10).to_dict(orient='records')
    with open(sample_path, 'w', encoding='utf-8') as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    print(f"  Sample: {sample_path}")

    # 7. 통계
    print("\n[Statistics]")
    print(f"  Total ingredients: {len(grouped)}")
    print(f"  Total brands: {grouped['brand_count'].sum()}")
    print(f"  Avg brands per ingredient: {grouped['brand_count'].mean():.1f}")
    print(f"  Max brands: {grouped['brand_count'].max()}")

    # ATC 2자리 분포
    grouped['atc_class'] = grouped['atc_code'].str[:3]
    print(f"\n  ATC class distribution:")
    for atc_class, count in grouped['atc_class'].value_counts().head(10).items():
        print(f"    {atc_class}: {count} ingredients")

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
