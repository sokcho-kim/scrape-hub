"""pharmalex_unity CSV에서 영문명-한글명 매핑 추출

목적:
1. merged_pharma_data CSV에서 영문 성분명 → 한글 성분명 매핑 추출
2. JSON 별칭 사전 생성
3. 약가 사전과 통합하여 영문명 검색 가능하게

입력: data/pharmalex_unity/merged_pharma_data_20250915_102415.csv
출력: data/hira_master/drug_aliases_eng.json
"""

import pandas as pd
import json
import re
from pathlib import Path
from collections import defaultdict
import sys

sys.stdout.reconfigure(encoding='utf-8')

CSV_FILE = Path('data/pharmalex_unity/merged_pharma_data_20250915_102415.csv')
OUTPUT_FILE = Path('data/hira_master/drug_aliases_eng.json')
DRUG_DICT_FILE = Path('data/hira_master/drug_dictionary.json')

print('=' * 100)
print('영문명-한글명 별칭 사전 구축')
print('=' * 100)

# 1. CSV 파일 읽기
print('\n[1] pharmalex_unity CSV 로드')
print('-' * 100)

df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
print(f'총 {len(df):,}개 행 로드')

# 2. 약가 사전 로드 (검증용)
print('\n[2] 약가 사전 로드 (검증용)')
print('-' * 100)

with open(DRUG_DICT_FILE, 'r', encoding='utf-8') as f:
    drug_dict = json.load(f)

print(f'약가 사전: {len(drug_dict):,}개 검색 키')

# 3. 영문명-한글명 매핑 추출
print('\n[3] 영문명-한글명 매핑 추출')
print('-' * 100)

eng_to_kor = defaultdict(set)  # 영문명 → 한글명들 (여러 개 가능)
stats = {
    'total_rows': len(df),
    'rows_with_eng': 0,
    'rows_with_kor': 0,
    'valid_mappings': 0
}

for idx, row in df.iterrows():
    product_name = row['제품명']
    eng_name = row['일반명']

    # 영문명이 있는지 확인
    if pd.isna(eng_name) or not isinstance(eng_name, str) or not eng_name.strip():
        continue

    stats['rows_with_eng'] += 1

    # 제품명 괄호 안에서 한글 성분명 추출
    # 예: "옵디보주100mg(니볼루맙,유전자재조합)" → "니볼루맙"
    match = re.search(r'\(([^)]+)\)', product_name)
    if not match:
        continue

    kor_ingredients = match.group(1)
    # 쉼표로 분리된 첫 번째만 추출
    kor_ingredient = kor_ingredients.split(',')[0].strip()

    if not kor_ingredient or len(kor_ingredient) < 2:
        continue

    # ⭐ NEW: 규격 필터링 - 숫자/단위 패턴이 있으면 제외
    # 예: "1mg/1정", "10mL", "5g" 등은 규격이지 성분명이 아님
    if re.search(r'\d+\s*(?:mg|g|kg|ml|mL|L|μg|mcg|IU|/|%)', kor_ingredient, re.IGNORECASE):
        continue  # 규격이므로 건너뜀

    # 추가 필터: 숫자로 시작하는 것도 제외
    if re.match(r'^\d', kor_ingredient):
        continue

    stats['rows_with_kor'] += 1

    # 영문명 정규화
    eng_lower = eng_name.lower().strip()

    # 한글명 정규화
    kor_normalized = kor_ingredient

    # 매핑 추가
    eng_to_kor[eng_lower].add(kor_normalized)

    if (idx + 1) % 100000 == 0:
        print(f'  처리 중: {idx + 1:,} / {len(df):,}')

print(f'\n처리 완료!')
print(f'  총 행: {stats["total_rows"]:,}개')
print(f'  영문명 있는 행: {stats["rows_with_eng"]:,}개')
print(f'  한글명 추출 성공: {stats["rows_with_kor"]:,}개')
print(f'  고유 영문명: {len(eng_to_kor):,}개')

# 4. 약가 사전과 검증
print('\n[4] 약가 사전 검증')
print('-' * 100)

validated_mappings = {}
found_in_dict = 0
not_found = 0

for eng, kor_set in eng_to_kor.items():
    # 한글명 중 약가 사전에 있는 것만 선택
    valid_kors = []
    for kor in kor_set:
        if kor in drug_dict:
            valid_kors.append(kor)

    if valid_kors:
        # 여러 개면 첫 번째 (또는 가장 짧은 것)
        validated_mappings[eng] = sorted(valid_kors, key=len)[0]
        found_in_dict += 1
    else:
        # 약가 사전에 없어도 일단 매핑 저장 (나중에 참고용)
        validated_mappings[eng] = list(kor_set)[0]
        not_found += 1

print(f'총 매핑: {len(validated_mappings):,}개')
print(f'  약가 사전에서 검증됨: {found_in_dict:,}개')
print(f'  약가 사전에 없음: {not_found:,}개')

# 5. 샘플 확인
print('\n[5] 매핑 샘플 (약가 사전 검증된 것 30개)')
print('-' * 100)

verified_samples = [(eng, kor) for eng, kor in validated_mappings.items() if kor in drug_dict]
for i, (eng, kor) in enumerate(sorted(verified_samples)[:30], 1):
    print(f'{i:2d}. {eng:35s} → {kor}')

# 6. 미매칭 약제 확인
print('\n[6] HIRA 문서에 나온 영문명 중 매핑 가능한 것 확인')
print('-' * 100)

# 이전 미매칭 목록에서 영문명 추출
common_unmatcheds = [
    'paclitaxel', 'docetaxel', 'gemcitabine', 'fludarabine',
    'capecitabine', 'rituximab', 'anastrozole', 'bortezomib',
    'cisplatin', 'carboplatin', 'oxaliplatin', 'irinotecan',
    'bevacizumab', 'trastuzumab', 'cetuximab', 'erlotinib',
    'gefitinib', 'sorafenib', 'sunitinib', 'imatinib'
]

print('\n주요 항암제 영문명 매핑 가능 여부:')
found_count = 0
for eng in sorted(common_unmatcheds):
    if eng in validated_mappings:
        kor = validated_mappings[eng]
        in_dict = '✅' if kor in drug_dict else '⚠️'
        print(f'  {in_dict} {eng:20s} → {kor}')
        found_count += 1
    else:
        print(f'  ❌ {eng:20s} → 매핑 없음')

print(f'\n매핑 가능: {found_count}/{len(common_unmatcheds)}개 ({found_count/len(common_unmatcheds)*100:.1f}%)')

# 7. JSON 저장
print('\n[7] JSON 파일로 저장')
print('-' * 100)

output_data = {
    'metadata': {
        'source': 'pharmalex_unity/merged_pharma_data_20250915_102415.csv',
        'total_mappings': len(validated_mappings),
        'verified_in_drug_dict': found_in_dict,
        'description': '영문 성분명 → 한글 성분명 매핑'
    },
    'mappings': validated_mappings
}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

file_size = OUTPUT_FILE.stat().st_size / 1024
print(f'저장 완료: {OUTPUT_FILE}')
print(f'파일 크기: {file_size:.2f} KB')

# 8. 최종 요약
print('\n' + '=' * 100)
print('✅ 영문명 별칭 사전 구축 완료')
print('=' * 100)

print(f'''
주요 결과:
- 총 영문명 매핑: {len(validated_mappings):,}개
- 약가 사전 검증: {found_in_dict:,}개 ({found_in_dict/len(validated_mappings)*100:.1f}%)
- 주요 항암제 매핑: {found_count}/{len(common_unmatcheds)}개

예상 효과:
- 이전 매칭률: 23.5%
- 영문명 추가 후: 40-50% 예상

다음 단계:
1. 약가 사전과 통합
2. 재매칭 실행
3. 최종 매칭률 계산
''')
