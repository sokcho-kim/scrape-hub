import json
from pathlib import Path

print("=" * 100)
print("NCC 암정보 사전에서 약물 정보 추출")
print("=" * 100)

# 1. LLM 분류 결과 로드
print("\n[1] LLM 분류 결과 로드...")
llm_results_dir = Path('../ncc/cancer_dictionary/llm_dynamic_results')
all_terms = []

batch_files = sorted(llm_results_dir.glob('batch_*.json'))
print(f"  - 배치 파일: {len(batch_files)}개")

for batch_file in batch_files:
    with open(batch_file, encoding='utf-8') as f:
        terms = json.load(f)
        all_terms.extend(terms)

print(f"  - 전체 용어: {len(all_terms):,}개")

# 2. 카테고리별 분류
print("\n[2] 카테고리별 분류...")
categories = {}
for term in all_terms:
    category = term.get('final_category', 'unknown')
    if category not in categories:
        categories[category] = []
    categories[category].append(term)

print(f"  - 카테고리 수: {len(categories)}개")
for category, items in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"    {category}: {len(items)}개")

# 3. 약물 추출
print("\n[3] 약물 정보 추출...")
drugs = categories.get('약물', [])
print(f"  - 약물 수: {len(drugs)}개")

# 4. bridges 항암제와 매칭
print("\n[4] bridges 항암제와 매칭...")
import pandas as pd

bridges_df = pd.read_csv('anticancer_normalized_v2.csv', encoding='utf-8-sig')

# bridges 약물명 추출
bridges_names = set()
for col in ['brand_name_short', 'brand_name_full', 'ingredient_ko_original', 'ingredient_in_brand']:
    if col in bridges_df.columns:
        bridges_names.update(bridges_df[col].dropna().unique())

print(f"  - bridges 약물명: {len(bridges_names)}개")

# NCC 약물명과 매칭
matched_drugs = []
unmatched_drugs = []

for drug in drugs:
    keyword = drug['keyword']

    # 부분 매칭 (NCC 용어가 bridges 약물명에 포함되는지)
    is_matched = False
    matched_with = None

    for bridge_name in bridges_names:
        if pd.notna(bridge_name) and (
            keyword.lower() in str(bridge_name).lower() or
            str(bridge_name).lower() in keyword.lower()
        ):
            is_matched = True
            matched_with = bridge_name
            break

    if is_matched:
        drug['matched'] = True
        drug['matched_with'] = matched_with
        matched_drugs.append(drug)
    else:
        drug['matched'] = False
        unmatched_drugs.append(drug)

print(f"  - 매칭 성공: {len(matched_drugs)}개")
print(f"  - 미매칭: {len(unmatched_drugs)}개")

# 5. 결과 출력
print("\n[5] 매칭된 약물 (샘플 20개)")
print("-" * 100)
for drug in matched_drugs[:20]:
    print(f"\nNCC: {drug['keyword']}")
    print(f"  → bridges: {drug['matched_with']}")
    print(f"  설명: {drug['content'][:100]}...")

print("\n\n[6] 미매칭 약물 (샘플 20개)")
print("-" * 100)
for drug in unmatched_drugs[:20]:
    print(f"\nNCC: {drug['keyword']}")
    print(f"  설명: {drug['content'][:100]}...")

# 6. 저장
print("\n[7] 결과 저장...")

# 전체 약물 저장
with open('ncc_drugs_all.json', 'w', encoding='utf-8') as f:
    json.dump(drugs, f, ensure_ascii=False, indent=2)
print(f"  - 전체 약물: ncc_drugs_all.json ({len(drugs)}개)")

# 매칭된 약물
with open('ncc_drugs_matched.json', 'w', encoding='utf-8') as f:
    json.dump(matched_drugs, f, ensure_ascii=False, indent=2)
print(f"  - 매칭 성공: ncc_drugs_matched.json ({len(matched_drugs)}개)")

# 미매칭 약물
with open('ncc_drugs_unmatched.json', 'w', encoding='utf-8') as f:
    json.dump(unmatched_drugs, f, ensure_ascii=False, indent=2)
print(f"  - 미매칭: ncc_drugs_unmatched.json ({len(unmatched_drugs)}개)")

# CSV로도 저장 (간단 버전)
import pandas as pd

drugs_simple = []
for drug in drugs:
    drugs_simple.append({
        '용어': drug['keyword'],
        '설명': drug['content'],
        '매칭여부': 'O' if drug.get('matched', False) else 'X',
        'bridges약물': drug.get('matched_with', '')
    })

df_drugs = pd.DataFrame(drugs_simple)
df_drugs.to_csv('ncc_drugs_summary.csv', index=False, encoding='utf-8-sig')
print(f"  - 요약 CSV: ncc_drugs_summary.csv ({len(drugs)}개)")

print("\n" + "=" * 100)
print("[완료]")
print("=" * 100)

print(f"\n통계:")
print(f"  - NCC 전체 용어: {len(all_terms):,}개")
print(f"  - 약물 분류: {len(drugs)}개 ({len(drugs)/len(all_terms)*100:.1f}%)")
print(f"  - bridges 매칭: {len(matched_drugs)}개 ({len(matched_drugs)/len(drugs)*100:.1f}%)")
print(f"  - 미매칭: {len(unmatched_drugs)}개 ({len(unmatched_drugs)/len(drugs)*100:.1f}%)")
