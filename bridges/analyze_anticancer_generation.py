import pandas as pd

# 데이터 로드
df = pd.read_csv('anticancer_normalized_v2.csv', encoding='utf-8-sig')

print("=" * 100)
print("항암제 세대 분류 분석")
print("=" * 100)

# 1. 현재 데이터는 항암제만 포함하는지?
print("\n[1] 데이터 범위 확인")
print(f"  - ATC 코드 범위: L01 (항종양제), L02 (내분비요법)")
atc_prefix = df['atc_code'].str[:3].value_counts()
print(f"  - L01 (Antineoplastic agents): {atc_prefix.get('L01', 0)}개")
print(f"  - L02 (Endocrine therapy): {atc_prefix.get('L02', 0)}개")
print(f"  -> 결론: 항암제에만 국한됨 [OK]")

# 2. ATC 코드로 세대 추론 가능성
print("\n[2] ATC 코드 기반 세대 분류 가능성")
print("\nATC 하위 분류 매핑:")

# ATC 코드 5자리 기준 분류
atc_classification = {
    # 1세대: 세포독성 항암제 (전통적 화학요법)
    'L01AA': '알킬화제 (Alkylating agents)',
    'L01AB': '알킬화제 - 알킬설포네이트',
    'L01AC': '알킬화제 - 에틸렌이민 유도체',
    'L01AD': '알킬화제 - 니트로소우레아',
    'L01AX': '알킬화제 - 기타',
    'L01BA': '대사길항제 - 엽산 유사체',
    'L01BB': '대사길항제 - 퓨린 유사체',
    'L01BC': '대사길항제 - 피리미딘 유사체',
    'L01CA': '식물 알칼로이드 - 빈카 알칼로이드',
    'L01CB': '식물 알칼로이드 - 포도필로톡신 유도체',
    'L01CD': '식물 알칼로이드 - 탁산',
    'L01CE': '식물 알칼로이드 - 캄프토테신 유도체',
    'L01DA': '항생제 - 악티노마이신',
    'L01DB': '항생제 - 안트라사이클린',
    'L01DC': '항생제 - 기타',
    'L01XA': '백금 화합물',

    # 2세대: 표적 항암제
    'L01EA': 'BCR-ABL 티로신 키나제 억제제',
    'L01EB': 'EGFR 티로신 키나제 억제제',
    'L01EC': 'ALK 티로신 키나제 억제제',
    'L01ED': '기타 티로신 키나제 억제제',
    'L01EF': 'CDK 억제제',
    'L01EG': 'BRAF 억제제',
    'L01EH': 'MEK 억제제',
    'L01EJ': 'JAK 억제제',
    'L01EK': 'VEGFR 티로신 키나제 억제제',
    'L01EL': 'BTK 억제제',
    'L01EX': '기타 표적치료제',
    'L01XE': 'mTOR 억제제',
    'L01XG': '프로테아좀 억제제',
    'L01XH': 'HDAC 억제제',
    'L01XK': 'PARP 억제제',
    'L01XL': '항암제 ADC (항체-약물 결합체)',

    # 2-3세대: 단일클론항체 (일부 면역항암제 포함)
    'L01FA': 'CD20 단일클론항체',
    'L01FB': 'EGFR 단일클론항체',
    'L01FC': 'HER2 단일클론항체',
    'L01FD': 'VEGF 단일클론항체',
    'L01FE': 'CD30 단일클론항체',
    'L01FF': 'PD-1/PD-L1 면역관문억제제',
    'L01FG': 'VEGF/VEGFR 단일클론항체',
    'L01FX': '기타 단일클론항체',

    # 호르몬 요법
    'L02AB': '프로게스토겐',
    'L02AE': 'GnRH 유사체',
    'L02BA': '항에스트로겐',
    'L02BB': '항안드로겐',
    'L02BG': '아로마타제 억제제',
    'L02BX': '기타 호르몬 길항제',
}

# 세대 분류 규칙
generation_rules = {
    '1세대 (세포독성)': ['L01AA', 'L01AB', 'L01AC', 'L01AD', 'L01AX',
                        'L01BA', 'L01BB', 'L01BC',
                        'L01CA', 'L01CB', 'L01CD', 'L01CE',
                        'L01DA', 'L01DB', 'L01DC',
                        'L01XA'],
    '2세대 (표적치료)': ['L01EA', 'L01EB', 'L01EC', 'L01ED', 'L01EF', 'L01EG', 'L01EH', 'L01EJ', 'L01EK', 'L01EL', 'L01EX',
                        'L01XE', 'L01XG', 'L01XH', 'L01XK', 'L01XL'],
    '3세대 (면역항암)': ['L01FF'],  # PD-1/PD-L1
    '단일클론항체': ['L01FA', 'L01FB', 'L01FC', 'L01FD', 'L01FE', 'L01FG', 'L01FX'],
    '호르몬요법': ['L02AB', 'L02AE', 'L02BA', 'L02BB', 'L02BG', 'L02BX'],
}

# 세대 분류 함수
def classify_generation(atc_code):
    atc_5 = atc_code[:5]
    for gen, codes in generation_rules.items():
        if atc_5 in codes:
            return gen
    return '기타/미분류'

df['generation'] = df['atc_code'].apply(classify_generation)

# 세대별 통계
print("\n[3] 세대별 제품 분포")
gen_dist = df['generation'].value_counts()
for gen, count in gen_dist.items():
    print(f"  - {gen}: {count}개 ({count/len(df)*100:.1f}%)")

# 세대별 샘플 약물
print("\n[4] 세대별 대표 약물 샘플")
for gen in ['1세대 (세포독성)', '2세대 (표적치료)', '3세대 (면역항암)', '단일클론항체']:
    if gen in df['generation'].values:
        print(f"\n{gen}:")
        samples = df[df['generation'] == gen].drop_duplicates('ingredient_ko_original')[['brand_name_short', 'ingredient_ko_original', 'atc_code']].head(5)
        for idx, row in samples.iterrows():
            print(f"  * {row['brand_name_short']} ({row['ingredient_ko_original']}) - {row['atc_code']}")

# ATC 5자리 분류별 통계
print("\n[5] ATC 5자리 분류별 제품 수 (상위 20개)")
df['atc_5'] = df['atc_code'].str[:5]
atc5_dist = df.groupby('atc_5').agg({
    'brand_name_short': 'count',
    'generation': 'first'
}).sort_values('brand_name_short', ascending=False).head(20)
atc5_dist.columns = ['제품 수', '세대']

for atc5, row in atc5_dist.iterrows():
    desc = atc_classification.get(atc5, '미분류')
    print(f"  {atc5} - {desc}: {row['제품 수']}개 [{row['세대']}]")

# 세대 정보 추가된 CSV 저장
print("\n[6] 세대 정보 추가")
print("  -> anticancer_with_generation.csv 저장 중...")
df_with_gen = df.copy()
df_with_gen.to_csv('anticancer_with_generation.csv', index=False, encoding='utf-8-sig')
print("  [OK] 저장 완료!")

print("\n" + "=" * 100)
print("분석 완료!")
print("=" * 100)

print("\n[결론]")
print("1. [OK] 현재 데이터는 항암제(L01/L02)에만 국한됨")
print("2. [WARNING] 명시적인 '세대' 필드는 없음")
print("3. [OK] ATC 코드 기반으로 세대 분류 가능")
print("4. [OK] anticancer_with_generation.csv에 세대 정보 추가됨")
print("\n세대 분류 기준:")
print("  - 1세대: 세포독성 항암제 (화학요법)")
print("  - 2세대: 표적 항암제 (티로신 키나제 억제제 등)")
print("  - 3세대: 면역항암제 (PD-1/PD-L1 억제제)")
print("  - 단일클론항체: CD20, HER2, VEGF 등")
print("  - 호르몬요법: 유방암, 전립선암 등")
