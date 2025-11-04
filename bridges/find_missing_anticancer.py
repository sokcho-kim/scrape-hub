import pandas as pd
import re
from pathlib import Path

print("=" * 100)
print("ATC 없는 항암제 교차 확인")
print("=" * 100)

# 1. 통합 약가 데이터 로드
print("\n[1] 약가 마스터 로드 중...")
df_all = pd.read_csv(
    '../data/pharmalex_unity/merged_pharma_data_20250915_102415.csv',
    encoding='utf-8-sig',
    low_memory=False
)
print(f"  - 전체 레코드: {len(df_all):,}개")
print(f"  - ATC 있음: {df_all['ATC코드'].notna().sum():,}개 ({df_all['ATC코드'].notna().sum()/len(df_all)*100:.1f}%)")
print(f"  - ATC 없음: {df_all['ATC코드'].isna().sum():,}개 ({df_all['ATC코드'].isna().sum()/len(df_all)*100:.1f}%)")

# 2. ATC 없는 약제 추출
print("\n[2] ATC 없는 약제 추출...")
no_atc = df_all[df_all['ATC코드'].isna()].copy()
print(f"  - ATC 없는 레코드: {len(no_atc):,}개")

# 중복 제거 (제품코드 기준)
no_atc_unique = no_atc.drop_duplicates(subset='제품코드')
print(f"  - 고유 제품: {len(no_atc_unique):,}개")

# 3. 항암제 키워드 검색
print("\n[3] 항암제 키워드 검색...")

keywords = {
    '한글': ['암', '항암', '종양', '백혈병', '림프종', '육종'],
    '영어': ['cancer', 'tumor', 'oncology', 'leukemia', 'lymphoma', 'sarcoma',
             'carcinoma', 'neoplasm', 'malignant', 'chemotherapy']
}

def contains_anticancer_keyword(text):
    """텍스트에 항암 관련 키워드가 있는지 확인"""
    if pd.isna(text):
        return False

    text_lower = str(text).lower()

    # 한글 키워드
    for keyword in keywords['한글']:
        if keyword in text_lower:
            return True

    # 영어 키워드
    for keyword in keywords['영어']:
        if keyword in text_lower:
            return True

    return False

# 품목명, 일반명에서 키워드 검색
no_atc_unique['is_anticancer_candidate'] = (
    no_atc_unique['제품명'].apply(contains_anticancer_keyword) |
    no_atc_unique['일반명'].apply(contains_anticancer_keyword)
)

anticancer_candidates = no_atc_unique[no_atc_unique['is_anticancer_candidate']].copy()
print(f"  - 항암제 후보: {len(anticancer_candidates)}개")

# 4. 현재 bridges 데이터와 비교
print("\n[4] 현재 bridges 데이터와 비교...")
bridges_df = pd.read_csv('anticancer_normalized_v2.csv', encoding='utf-8-sig')
bridges_codes = set(bridges_df['product_code'].unique())
print(f"  - bridges 제품코드: {len(bridges_codes)}개")

# 신규 발견 항목
if len(anticancer_candidates) > 0:
    new_candidates = anticancer_candidates[~anticancer_candidates['제품코드'].isin(bridges_codes)]
    print(f"  - 신규 항암제 후보: {len(new_candidates)}개")
else:
    new_candidates = pd.DataFrame()
    print(f"  - 신규 항암제 후보: 0개")

# 5. 결과 출력
print("\n[5] 결과 분석")
print("-" * 100)

if len(anticancer_candidates) > 0:
    print(f"\n[ATC 없는 항암제 후보] 총 {len(anticancer_candidates)}개")
    print("-" * 100)

    for idx, row in anticancer_candidates.head(20).iterrows():
        print(f"\n{idx+1}. 제품코드: {row['제품코드']}")
        print(f"   제품명: {row['제품명']}")
        print(f"   일반명: {row['일반명']}")
        print(f"   제조사: {row['업체명']}")
        print(f"   주성분코드: {row['주성분코드']}")

        # bridges에 있는지 확인
        if row['제품코드'] in bridges_codes:
            print(f"   상태: [OK] bridges에 이미 포함")
        else:
            print(f"   상태: [NEW] 신규 발견")

    # 신규 항목 요약
    if len(new_candidates) > 0:
        print(f"\n\n[NEW] 신규 발견 항암제 후보 (bridges 미포함)")
        print("=" * 100)
        for idx, row in new_candidates.iterrows():
            print(f"- {row['제품명']} ({row['일반명']}) - {row['제조사']}")
else:
    print("\n[OK] ATC 없는 항암제 후보를 찾지 못했습니다.")
    print("   -> 모든 항암제가 ATC 코드를 가지고 있거나,")
    print("   -> 키워드 기반으로는 탐지되지 않는 항암제일 수 있습니다.")

# 6. 결과 저장
if len(anticancer_candidates) > 0:
    print("\n[6] 결과 저장")
    print("-" * 100)

    output_path = 'anticancer_candidates_no_atc.csv'
    anticancer_candidates.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"  [OK] 저장 완료: {output_path}")

    if len(new_candidates) > 0:
        new_output_path = 'anticancer_candidates_new.csv'
        new_candidates.to_csv(new_output_path, index=False, encoding='utf-8-sig')
        print(f"  [OK] 신규 항목 저장: {new_output_path}")

print("\n" + "=" * 100)
print("분석 완료!")
print("=" * 100)

print("\n[결론]")
print(f"1. 전체 약제: {len(df_all):,}개")
print(f"2. ATC 없음: {len(no_atc_unique):,}개 ({len(no_atc_unique)/len(df_all)*100:.2f}%)")
print(f"3. 항암제 후보 발견: {len(anticancer_candidates)}개")
print(f"4. 신규 (bridges 미포함): {len(new_candidates) if len(new_candidates) > 0 else 0}개")

if len(anticancer_candidates) == 0:
    print("\n[OK] 현재 bridges 데이터가 완전함 (ATC 없는 항암제 없음)")
elif len(new_candidates) == 0:
    print("\n[OK] 신규 항암제 없음 (모두 bridges에 포함)")
else:
    print("\n[WARNING] 신규 항암제 후보가 발견되었습니다!")
    print(f"   -> {len(new_candidates)}개 제품 추가 검토 필요")
