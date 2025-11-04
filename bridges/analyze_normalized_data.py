import pandas as pd
import json

# 정규화된 데이터 로드
df = pd.read_csv('anticancer_normalized_v2.csv', encoding='utf-8-sig')

print("=" * 80)
print("항암제 데이터 정규화 결과 분석")
print("=" * 80)

# 기본 통계
print("\n[1] 기본 통계")
print(f"  - 총 제품 수: {len(df):,}개")
print(f"  - 고유 성분 수: {df['ingredient_ko_original'].nunique()}개")
print(f"  - 고유 제조사 수: {df['company'].nunique()}개")
print(f"  - 고유 ATC 코드 수: {df['atc_code'].nunique()}개")

# 데이터 완전성
print("\n[2] 데이터 완전성")
print(f"  - 제조사 정보 완전성: {df['company'].notna().sum() / len(df) * 100:.1f}% ({df['company'].notna().sum()}/{len(df)})")
print(f"  - 약가 정보 완전성: {df['price'].notna().sum() / len(df) * 100:.1f}% ({df['price'].notna().sum()}/{len(df)})")
print(f"  - 브랜드명 정보 완전성: {df['brand_name_full'].notna().sum() / len(df) * 100:.1f}% ({df['brand_name_full'].notna().sum()}/{len(df)})")

# 약가 통계
print("\n[3] 약가 통계")
price_data = df[df['price'] > 0]['price']
if len(price_data) > 0:
    print(f"  - 평균 약가: {price_data.mean():,.0f}원")
    print(f"  - 중간값: {price_data.median():,.0f}원")
    print(f"  - 최소 약가: {price_data.min():,.0f}원")
    print(f"  - 최고 약가: {price_data.max():,.0f}원")
    print(f"  - 약가 0원 제품: {(df['price'] == 0).sum()}개")

# 투여 경로 분포
print("\n[4] 투여 경로 분포")
route_dist = df['route'].value_counts()
for route, count in route_dist.items():
    print(f"  - {route}: {count}개 ({count/len(df)*100:.1f}%)")

# 제조사별 제품 수 (상위 10개)
print("\n[5] 제조사별 제품 수 (상위 10개)")
company_dist = df['company'].value_counts().head(10)
for company, count in company_dist.items():
    print(f"  - {company}: {count}개")

# ATC 코드별 제품 수 (상위 10개)
print("\n[6] ATC 코드별 제품 수 (상위 10개)")
atc_dist = df['atc_code'].value_counts().head(10)
for atc, count in atc_dist.items():
    atc_name = df[df['atc_code'] == atc]['atc_name_en'].iloc[0]
    print(f"  - {atc} ({atc_name}): {count}개")

# 가장 비싼 항암제 (상위 10개)
print("\n[7] 가장 비싼 항암제 (상위 10개)")
expensive = df.nlargest(10, 'price')[['brand_name_short', 'company', 'price', 'ingredient_ko_original']]
for idx, row in expensive.iterrows():
    print(f"  - {row['brand_name_short'] if pd.notna(row['brand_name_short']) else '(이름없음)'}")
    print(f"    제조사: {row['company']}, 약가: {row['price']:,.0f}원, 성분: {row['ingredient_ko_original']}")

# 데이터 품질 이슈
print("\n[8] 데이터 품질 이슈")
print(f"  - 브랜드명 누락: {df['brand_name_full'].isna().sum()}개")
print(f"  - 제조사 누락: {df['company'].isna().sum()}개")
print(f"  - 약가 누락: {df['price'].isna().sum()}개")

# 성분 코드 불일치
print("\n[9] 성분 코드 불일치")
mismatch = df[df['ingredient_code_original'] != df['ingredient_code_hira']]
print(f"  - 성분 코드 불일치 건수: {len(mismatch)}개")
if len(mismatch) > 0:
    print(f"  - 샘플 (처음 5개):")
    for idx, row in mismatch.head(5).iterrows():
        print(f"    * {row['brand_name_short']}: {row['ingredient_code_original']} → {row['ingredient_code_hira']}")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)
