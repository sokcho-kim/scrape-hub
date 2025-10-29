"""약가파일을 검색 가능한 사전(Dictionary)으로 변환

목적:
1. 다양한 형태의 검색 키 생성 (제품명, 성분명, 정규화된 키)
2. 빠른 Exact Match를 위한 사전 구조
3. JSON 파일로 저장하여 재사용

입력: data/hira_master/20221101_20251101 적용약가파일_사전제공 1부.xlsx
출력: data/hira_master/drug_dictionary.json
"""

import pandas as pd
import json
import re
from pathlib import Path
from collections import defaultdict
import sys
import codecs

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

MASTER_DIR = Path('data/hira_master')
OUTPUT_FILE = MASTER_DIR / 'drug_dictionary.json'

print('=' * 100)
print('약가파일 → 검색 사전 변환')
print('=' * 100)

# 1. 약가파일 읽기
print('\n[1] 약가파일 로드')
print('-' * 100)

drug_file = MASTER_DIR / '20221101_20251101 적용약가파일_사전제공 1부.xlsx'
df = pd.read_excel(drug_file)

print(f'총 {len(df):,}개 행 로드')
print(f'컬럼: {list(df.columns[:10])}...')

# 2. 키 추출 함수
def extract_search_keys(product_name):
    """
    제품명에서 다양한 검색 키 추출

    예시 입력: "옵디보주100mg(니볼루맙,유전자재조합)_(0.1g/10mL)"

    출력 키:
    1. "옵디보주100mg" - 전체 제품명 (괄호 앞)
    2. "옵디보주" - 숫자/단위 제거
    3. "옵디보" - 제형도 제거 (NEW!)
    4. "니볼루맙" - 성분명 (괄호 안 첫 번째)

    정규화 키 (소문자, 공백/특수문자 제거):
    - "opdivoju100mg"
    - "opdivoju"
    - "opdivo"  (NEW!)
    - "nivolumab"
    """
    keys = []

    if pd.isna(product_name):
        return keys

    # 1. 괄호 앞부분 = 제품명 추출
    match = re.match(r'([^(]+)', product_name)
    if not match:
        return keys

    full_product_name = match.group(1).strip()
    keys.append(full_product_name)  # "옵디보주100mg" 또는 "킴리아주"

    # 2. 숫자 + 단위 제거
    # 패턴: 숫자(소수점 포함) + 단위(mg, g, mL, 밀리그램, 그램 등)
    without_dosage = re.sub(r'\d+(\.\d+)?(mg|g|mL|L|밀리그램|그램|킬로그램|밀리리터|리터|μg|mcg|IU|I\.U|KI\.U).*$', '', full_product_name, flags=re.IGNORECASE)
    without_dosage = without_dosage.strip()

    # 숫자가 제거됐으면 키 추가
    if without_dosage and without_dosage != full_product_name:
        keys.append(without_dosage)  # "옵디보주"

    # 3. 제형 제거 (숫자 제거 여부와 무관하게 항상 시도)
    # 제형 패턴: 주, 정, 캡슐, 시럽, 액, 연고, 크림, 겔, 패치, 좌제, 산, 과립 등
    dosage_forms = [
        '주', '정', '캡슐', '연질캡슐', '경질캡슐', '서방정', '서방캡슐',
        '시럽', '액', '현탁액', '용액', '주사', '주사액',
        '연고', '크림', '겔', '로션', '패치', '좌제', '좌약',
        '산', '과립', '세립', '분말', '산제',
        '점안액', '점비액', '점이액', '안연고',
        '흡입제', '스프레이', '에어로졸',
        '필름', '트로키', '츄정', '발포정'
    ]

    # without_dosage가 없으면 full_product_name에서 제형 제거 시도
    base_name = without_dosage if without_dosage else full_product_name
    without_form = base_name

    for form in dosage_forms:
        if base_name.endswith(form):
            without_form = base_name[:-len(form)].strip()
            break

    # 제형이 제거됐고, 아직 키에 없으면 추가
    if without_form and without_form != base_name and without_form not in keys:
        keys.append(without_form)  # "옵디보" 또는 "킴리아"

    # 4. 괄호 안 성분명
    match = re.search(r'\(([^)]+)\)', product_name)
    if match:
        ingredients = match.group(1)
        # 쉼표로 구분된 첫 번째 성분만 추출
        first_ingredient = ingredients.split(',')[0].strip()
        if first_ingredient:
            keys.append(first_ingredient)  # "니볼루맙"

    return keys

def normalize_key(key):
    """
    검색 키 정규화
    - 소문자 변환
    - 공백, 하이픈, 언더스코어 제거
    - 특수문자 제거
    """
    if not key:
        return ''

    # 소문자 변환
    normalized = key.lower()

    # 공백, 특수문자 제거
    normalized = re.sub(r'[\s\-_·]', '', normalized)

    # 한글, 영문, 숫자만 남김
    normalized = re.sub(r'[^\w가-힣]', '', normalized)

    return normalized

# 3. 사전 구축
print('\n[2] 검색 키 추출 및 사전 구축')
print('-' * 100)

# 사전 구조
# {
#   "원본키": {
#     "records": [제품 정보들],
#     "normalized_from": "정규화된키"
#   },
#   "정규화된키": {
#     "records": [제품 정보들],
#     "is_normalized": True
#   }
# }

drug_dict = defaultdict(lambda: {"records": [], "normalized_from": None, "is_normalized": False})
key_statistics = defaultdict(int)

for idx, row in df.iterrows():
    product_code = str(row['제품코드'])
    product_name = row['제품명']

    # 제품 정보
    record = {
        'product_code': product_code,
        'product_name': product_name,
        'specification': str(row['규격']) if pd.notna(row['규격']) else '',
        'company': str(row['업체명']) if pd.notna(row['업체명']) else '',
        'ingredient_code': str(row['주성분코드']) if pd.notna(row['주성분코드']) else '',
        'price': float(row['상한가']) if pd.notna(row['상한가']) else 0.0,
        'route': str(row['투여경로']) if pd.notna(row['투여경로']) else '',
    }

    # 검색 키 추출
    search_keys = extract_search_keys(product_name)

    for key in search_keys:
        if not key:
            continue

        # 원본 키로 저장
        drug_dict[key]["records"].append(record)
        key_statistics['원본 키'] += 1

        # 정규화 키로도 저장
        normalized = normalize_key(key)
        if normalized and normalized != key:
            drug_dict[normalized]["records"].append(record)
            drug_dict[normalized]["is_normalized"] = True
            drug_dict[key]["normalized_from"] = normalized
            key_statistics['정규화 키'] += 1

    if (idx + 1) % 10000 == 0:
        print(f'  처리 중: {idx + 1:,} / {len(df):,} ({(idx+1)/len(df)*100:.1f}%)')

print(f'\n완료!')
print(f'  고유 검색 키: {len(drug_dict):,}개')
print(f'  원본 키: {key_statistics["원본 키"]:,}개')
print(f'  정규화 키: {key_statistics["정규화 키"]:,}개')

# 4. 샘플 확인
print('\n[3] 샘플 확인')
print('-' * 100)

sample_keys = list(drug_dict.keys())[:10]
for key in sample_keys:
    info = drug_dict[key]
    print(f'\n검색 키: "{key}"')
    print(f'  정규화 여부: {"Yes" if info["is_normalized"] else "No"}')
    print(f'  매칭 제품 수: {len(info["records"])}개')
    if info["records"]:
        first = info["records"][0]
        print(f'  예시 제품: {first["product_name"]}')
        print(f'           제품코드: {first["product_code"]}')

# 5. 특정 약제 테스트
print('\n[4] 검색 테스트')
print('-' * 100)

test_queries = [
    '옵디보',
    '니볼루맙',
    'opdivo',  # 영문은 아직 미지원
    '킴리아',
    'Tisagenlecleucel',
]

for query in test_queries:
    normalized_query = normalize_key(query)

    # 원본 키 검색
    result_original = drug_dict.get(query)
    # 정규화 키 검색
    result_normalized = drug_dict.get(normalized_query)

    print(f'\n쿼리: "{query}" (정규화: "{normalized_query}")')

    if result_original:
        print(f'  [원본 키 매칭] {len(result_original["records"])}개 제품')
        for rec in result_original["records"][:3]:
            print(f'    - {rec["product_name"]}')
    elif result_normalized:
        print(f'  [정규화 키 매칭] {len(result_normalized["records"])}개 제품')
        for rec in result_normalized["records"][:3]:
            print(f'    - {rec["product_name"]}')
    else:
        print(f'  [매칭 없음]')

# 6. JSON 저장
print('\n[5] JSON 파일로 저장')
print('-' * 100)

# defaultdict를 일반 dict로 변환
final_dict = {k: dict(v) for k, v in drug_dict.items()}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(final_dict, f, ensure_ascii=False, indent=2)

file_size = OUTPUT_FILE.stat().st_size / (1024 * 1024)
print(f'저장 완료: {OUTPUT_FILE}')
print(f'파일 크기: {file_size:.2f} MB')

# 7. 통계 요약
print('\n[6] 통계 요약')
print('-' * 100)

total_records = sum(len(v["records"]) for v in drug_dict.values())
avg_records_per_key = total_records / len(drug_dict) if drug_dict else 0

print(f'''
총 검색 키:           {len(drug_dict):,}개
총 매칭 레코드:       {total_records:,}개
키당 평균 제품 수:    {avg_records_per_key:.2f}개

원본 약가 데이터:     {len(df):,}개
고유 제품명:          {df['제품명'].nunique():,}개
''')

print('\n' + '=' * 100)
print('✅ 약가 사전 구축 완료')
print('=' * 100)

print(f'''
다음 단계:
1. 암질환 파싱 데이터에서 약제명 추출
2. 이 사전으로 Exact Match 수행
3. 매칭률 계산

테스트 명령:
  python hira_cancer/test_drug_matching.py
''')
