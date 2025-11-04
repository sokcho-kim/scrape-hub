import json
import pprint

# HIRA dictionary 로드
with open('../data/hira_master/drug_dictionary_normalized.json', encoding='utf-8') as f:
    data = json.load(f)

print(f'총 데이터 수: {len(data)}')

# 샘플 키 확인
keys = list(data.keys())[:5]
print(f'샘플 키들: {keys}')

# 제품코드로 매핑 생성
print('\n제품코드 → 제조사 매핑 생성 중...')
product_code_map = {}

for key, value in data.items():
    for record in value.get('records', []):
        pc = record.get('product_code')
        if pc:
            product_code_map[pc] = {
                'company': record.get('company'),
                'product_name': record.get('product_name'),
                'ingredient_code': record.get('ingredient_code'),
                'price': record.get('price')
            }

print(f'총 매핑된 제품코드 수: {len(product_code_map)}')

# 항암제 제품코드 테스트
test_codes = ['644303333', '644303341', '644902301', '653602530']
print('\n=== 항암제 제품코드 조회 테스트 ===')
for code in test_codes:
    result = product_code_map.get(code)
    if result:
        print(f'\n제품코드 {code}:')
        pprint.pprint(result)
    else:
        print(f'\n제품코드 {code}: 데이터 없음')
