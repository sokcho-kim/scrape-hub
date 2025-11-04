import pandas as pd
import re

print("=" * 100)
print("ATC 없는 항암제 교차 확인 v2 (개선된 키워드)")
print("=" * 100)

# 1. 약가 마스터 로드
print("\n[1] 약가 마스터 로드...")
df_all = pd.read_csv(
    '../data/pharmalex_unity/merged_pharma_data_20250915_102415.csv',
    encoding='utf-8-sig',
    low_memory=False
)
print(f"  - 전체: {len(df_all):,}개")
print(f"  - ATC 없음: {df_all['ATC코드'].isna().sum():,}개")

# 2. ATC 없는 약제
no_atc = df_all[df_all['ATC코드'].isna()].copy()
no_atc_unique = no_atc.drop_duplicates(subset='제품코드').copy()
print(f"  - 고유 제품: {len(no_atc_unique):,}개")

# 3. 개선된 키워드 (false positive 제거)
print("\n[2] 개선된 항암제 키워드 검색...")

# 제외할 약물명 (false positive)
exclude_patterns = [
    r'암로디핀|amlodipine',  # 고혈압약
    r'암브록솔|ambroxol',    # 기침약
    r'암페낙|amfenac',       # 소염진통제
    r'암포테리신|amphotericin',  # 항진균제
    r'트리암시놀론|triamcinolone',  # 스테로이드
    r'암시노나이드|amcinonide',  # 스테로이드
    r'세포티암|cefotiam',    # 항생제
    r'디클로페낙|diclofenac'  # 소염진통제
]

# 진짜 항암제 키워드 (더 구체적)
anticancer_patterns = [
    r'항암',                  # 명시적 항암
    r'백혈병',                # 혈액암
    r'림프종',                # 림프암
    r'육종',                  # 육종
    r'chemotherapy',          # 화학요법
    r'leukemia',              # 백혈병
    r'lymphoma',              # 림프종
    r'sarcoma',               # 육종
    r'oncology',              # 종양학
    r'carcinoma',             # 암종
    r'neoplasm',              # 신생물
    r'malignant',             # 악성
]

def is_anticancer_candidate(row):
    """진짜 항암제인지 확인"""
    text = f"{row['제품명']} {row['일반명']}".lower()

    # 제외 패턴 확인
    for pattern in exclude_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    # 항암 패턴 확인
    for pattern in anticancer_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False

candidates = no_atc_unique[no_atc_unique.apply(is_anticancer_candidate, axis=1)].copy()
print(f"  - 항암제 후보: {len(candidates)}개 (false positive 제거 후)")

# 4. bridges 비교
print("\n[3] bridges 데이터와 비교...")
bridges_df = pd.read_csv('anticancer_normalized_v2.csv', encoding='utf-8-sig')
bridges_codes = set(bridges_df['product_code'].unique())

new_candidates = candidates[~candidates['제품코드'].isin(bridges_codes)].copy()
print(f"  - 신규 항암제 후보: {len(new_candidates)}개")

# 5. 결과 출력
print("\n" + "=" * 100)
print("[결과]")
print("=" * 100)

if len(new_candidates) > 0:
    print(f"\n신규 항암제 후보 {len(new_candidates)}개 발견:")
    print("-" * 100)

    for idx, row in new_candidates.iterrows():
        print(f"\n제품코드: {row['제품코드']}")
        print(f"  제품명: {row['제품명']}")
        print(f"  일반명: {row['일반명']}")
        print(f"  제조사: {row['업체명']}")
        print(f"  주성분코드: {row['주성분코드']}")

    # CSV 저장
    output_path = 'anticancer_candidates_filtered.csv'
    new_candidates.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n[OK] 저장 완료: {output_path}")
else:
    print("\n[OK] ATC 없는 신규 항암제를 찾지 못했습니다.")
    print("  -> 현재 bridges 데이터가 완전함")
    print("  -> 또는 ATC 없는 항암제가 실제로 없음")

print("\n[통계]")
print(f"  - 전체 약제: {len(df_all):,}개")
print(f"  - ATC 없음: {len(no_atc_unique):,}개")
print(f"  - 항암제 후보: {len(candidates)}개")
print(f"  - 신규 발견: {len(new_candidates)}개")

print("\n" + "=" * 100)
