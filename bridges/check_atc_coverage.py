import json
import pandas as pd
from collections import Counter

print("=" * 100)
print("HIRA 약가 데이터 ATC 코드 매핑 현황 분석")
print("=" * 100)

# HIRA dictionary 로드
print("\n[1] HIRA drug_dictionary 로드 중...")
with open('../data/hira_master/drug_dictionary_normalized.json', encoding='utf-8') as f:
    hira_data = json.load(f)

print(f"  - 총 제품명(키): {len(hira_data):,}개")

# 제품코드별로 펼치기
print("\n[2] 제품 레코드 추출 중...")
all_records = []
for key, value in hira_data.items():
    for record in value.get('records', []):
        all_records.append(record)

print(f"  - 총 제품 레코드: {len(all_records):,}개")

# DataFrame 생성
df = pd.DataFrame(all_records)

# ATC 코드 존재 여부 확인
print("\n[3] ATC 코드 매핑 현황")

# ingredient_code에서 ATC 패턴 추출 (앞 3자리)
# ingredient_code 형식 예: 161430BIJ (6자리 숫자 + 3자리 영문)
# ATC 코드는 별도 필드가 없으므로 ingredient_code나 다른 방식으로 매핑되어야 함

# ingredient_code 분석
print(f"\n  ingredient_code 분석:")
print(f"  - ingredient_code 있음: {df['ingredient_code'].notna().sum():,}개 ({df['ingredient_code'].notna().sum()/len(df)*100:.1f}%)")
print(f"  - ingredient_code 없음: {df['ingredient_code'].isna().sum():,}개")

# ingredient_code 샘플
print(f"\n  ingredient_code 샘플 (10개):")
sample_codes = df['ingredient_code'].dropna().head(10).tolist()
for code in sample_codes:
    print(f"    - {code}")

# 현재 anticancer 데이터와 비교
print("\n[4] 항암제 데이터 비교")
anticancer_df = pd.read_csv('anticancer_normalized_v2.csv', encoding='utf-8-sig')
anticancer_codes = set(anticancer_df['product_code'].unique())
hira_codes = set(df['product_code'].dropna().unique())

print(f"  - HIRA 전체 제품코드: {len(hira_codes):,}개")
print(f"  - 항암제 제품코드: {len(anticancer_codes):,}개")
print(f"  - 항암제 중 HIRA 매칭: {len(anticancer_codes & hira_codes):,}개")
print(f"  - 항암제 중 HIRA 미매칭: {len(anticancer_codes - hira_codes):,}개")

if len(anticancer_codes - hira_codes) > 0:
    print(f"\n  미매칭 제품코드 샘플:")
    for code in list(anticancer_codes - hira_codes)[:5]:
        product = anticancer_df[anticancer_df['product_code'] == code].iloc[0]
        print(f"    - {code}: {product['brand_name_short']} ({product['company']})")

# ATC 매핑 문제 확인
print("\n[5] ATC 코드 확보 방식 확인")
print("\n  현재 bridges/anticancer_master는:")
print("  1. HIRA 약가 데이터에서 추출")
print("  2. ATC 코드(L01/L02)로 필터링되어 생성됨")
print("  3. 따라서 현재 데이터는 ATC 코드가 있는 항암제만 포함")

print("\n  문제점:")
print("  - HIRA 데이터 자체에 ATC 코드 필드가 명시적으로 없음")
print("  - ingredient_code만 존재 (예: 161430BIJ)")
print("  - ATC 매핑은 별도 작업을 통해 이루어졌을 것으로 추정")

# 원본 데이터 확인
print("\n[6] 원본 데이터 소스 추적")
print("\n  bridges/anticancer_master.csv는 어디서 왔을까?")
print("  가능한 소스:")
print("  1. hira_cancer/ - 항암화학요법 데이터")
print("  2. mfds/ - 의약품 허가 정보")
print("  3. 외부 ATC 매핑 테이블")
print("  4. 수동 매핑")

# hira_cancer 확인
try:
    import os
    cancer_files = []
    for root, dirs, files in os.walk('../hira_cancer'):
        for file in files:
            if file.endswith('.json') or file.endswith('.csv'):
                cancer_files.append(os.path.join(root, file))

    print(f"\n  hira_cancer 폴더 확인:")
    print(f"  - 발견된 파일: {len(cancer_files)}개")
    for f in cancer_files[:10]:
        size = os.path.getsize(f) / 1024
        print(f"    - {os.path.basename(f)} ({size:.1f} KB)")
except Exception as e:
    print(f"\n  hira_cancer 폴더 확인 실패: {e}")

print("\n" + "=" * 100)
print("분석 완료!")
print("=" * 100)

print("\n[결론]")
print("1. HIRA 원천 데이터에는 ATC 코드 필드가 명시적으로 없음")
print("2. 현재 anticancer_master는 ATC 매핑이 완료된 상태")
print("3. ATC 매핑 소스를 추적해야 함")
print("4. ATC 코드 없는 항암제가 누락되었을 가능성 높음")
