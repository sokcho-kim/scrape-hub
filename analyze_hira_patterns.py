"""
HIRA 고시 데이터 패턴 분석
- 수술/처치 코드 패턴 (자XXX, 차XXX 등)
- 약제명 패턴
- 질병코드 패턴
- 검사명/수치 패턴
"""

import pandas as pd
import re
from collections import Counter, defaultdict
import json

# Excel 파일 읽기
df = pd.read_excel('C:/Jimin/scrape-hub/data/hira/hiradata_ver2.xlsx')

print(f"총 데이터: {len(df):,}개")
print(f"\n컬럼: {list(df.columns)}")

# 카테고리 분포 (인코딩 문제 해결)
print("\n" + "="*80)
print("카테고리 분포")
print("="*80)
print(df['category'].value_counts())

# 1. 수술/처치 코드 패턴 추출
print("\n" + "="*80)
print("1. 수술/처치 코드 패턴 분석")
print("="*80)

procedure_pattern = re.compile(r'[자차저나마바사아][가-힣]?\d{3,4}[가-힣]?')
all_procedure_codes = []
sample_contexts = defaultdict(list)

for idx, row in df.iterrows():
    content = str(row['content'])
    codes = procedure_pattern.findall(content)
    if codes:
        all_procedure_codes.extend(codes)
        # 샘플 문맥 저장 (처음 5개만)
        for code in codes[:3]:
            if len(sample_contexts[code]) < 3:
                # 코드 주변 50자 추출
                match = re.search(re.escape(code), content)
                if match:
                    start = max(0, match.start() - 30)
                    end = min(len(content), match.end() + 30)
                    context = content[start:end].replace('\n', ' ')
                    sample_contexts[code].append({
                        'title': row['title'],
                        'context': context
                    })

procedure_counter = Counter(all_procedure_codes)
print(f"\n발견된 총 수술/처치 코드: {len(all_procedure_codes):,}개")
print(f"고유 코드: {len(procedure_counter):,}개")
print(f"\n코드 접두어 분포:")

prefix_counter = Counter([code[0] for code in all_procedure_codes])
for prefix, count in prefix_counter.most_common():
    print(f"  {prefix}: {count:,}개")

print(f"\n가장 많이 언급된 수술/처치 코드 Top 20:")
for code, count in procedure_counter.most_common(20):
    print(f"  {code}: {count}회")

# 2. 약제명 패턴 분석
print("\n" + "="*80)
print("2. 약제명 패턴 분석")
print("="*80)

# 일반적인 약제명 패턴
# - 영문 대문자로 시작
# - -zole, -prazole, -mab, -nib, -statin, -lol, -pril, -sartan 등 접미사
# - 일반명은 소문자, 상품명은 대문자로 시작하는 경향

drug_suffixes = [
    'prazole', 'zole', 'mab', 'nib', 'statin', 'lol', 'pril', 'sartan',
    'cycline', 'mycin', 'cillin', 'floxacin', 'vir', 'dipine', 'caine',
    'ide', 'ine', 'ole', 'one', 'ate', 'pam', 'zepam'
]

# 패턴: 영문 약제명 (대소문자 시작, 3글자 이상)
drug_pattern = re.compile(r'\b[A-Z][a-z]{2,}(?:' + '|'.join(drug_suffixes) + r')\b')

all_drug_names = []
drug_contexts = defaultdict(list)

for idx, row in df.iterrows():
    content = str(row['content'])
    drugs = drug_pattern.findall(content)
    if drugs:
        all_drug_names.extend(drugs)
        for drug in drugs[:3]:
            if len(drug_contexts[drug]) < 2:
                match = re.search(re.escape(drug), content)
                if match:
                    start = max(0, match.start() - 30)
                    end = min(len(content), match.end() + 30)
                    context = content[start:end].replace('\n', ' ')
                    drug_contexts[drug].append({
                        'title': row['title'],
                        'context': context
                    })

drug_counter = Counter(all_drug_names)
print(f"\n발견된 총 약제명 (패턴 매칭): {len(all_drug_names):,}개")
print(f"고유 약제명: {len(drug_counter):,}개")
print(f"\n가장 많이 언급된 약제명 Top 30:")
for drug, count in drug_counter.most_common(30):
    print(f"  {drug}: {count}회")

# 3. 질병코드 (ICD) 패턴 분석
print("\n" + "="*80)
print("3. 질병코드 (KCD/ICD) 패턴 분석")
print("="*80)

# ICD 코드 패턴: A00-Z99, A00.0-Z99.9 형식
icd_pattern = re.compile(r'\b[A-Z]\d{2}(?:\.\d{1,2})?\b')

all_icd_codes = []
icd_contexts = defaultdict(list)

for idx, row in df.iterrows():
    content = str(row['content'])
    codes = icd_pattern.findall(content)
    if codes:
        all_icd_codes.extend(codes)
        for code in codes[:3]:
            if len(icd_contexts[code]) < 2:
                match = re.search(re.escape(code), content)
                if match:
                    start = max(0, match.start() - 30)
                    end = min(len(content), match.end() + 30)
                    context = content[start:end].replace('\n', ' ')
                    icd_contexts[code].append({
                        'title': row['title'],
                        'context': context
                    })

icd_counter = Counter(all_icd_codes)
print(f"\n발견된 총 질병코드: {len(all_icd_codes):,}개")
print(f"고유 코드: {len(icd_counter):,}개")

if len(icd_counter) > 0:
    print(f"\n가장 많이 언급된 질병코드 Top 30:")
    for code, count in icd_counter.most_common(30):
        print(f"  {code}: {count}회")
else:
    print("\n질병코드 패턴이 발견되지 않았습니다.")

# 4. 검사명/검사수치 패턴
print("\n" + "="*80)
print("4. 검사명 패턴 분석")
print("="*80)

# 일반적인 검사명 약어
test_patterns = [
    'HbA1C', 'HbA1c', 'eGFR', 'LVEF', 'BMI',
    'NT-proBNP', 'BNP', 'ACE', 'uACR',
    'ALT', 'AST', 'WBC', 'RBC', 'PLT', 'Hb',
    'PT', 'aPTT', 'INR', 'CRP', 'ESR'
]

test_pattern = re.compile(r'\b(?:' + '|'.join(test_patterns) + r')\b', re.IGNORECASE)

all_test_names = []
test_contexts = defaultdict(list)

for idx, row in df.iterrows():
    content = str(row['content'])
    tests = test_pattern.findall(content)
    if tests:
        all_test_names.extend([t.upper() for t in tests])
        for test in tests[:3]:
            if len(test_contexts[test.upper()]) < 2:
                match = re.search(re.escape(test), content, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 40)
                    end = min(len(content), match.end() + 40)
                    context = content[start:end].replace('\n', ' ')
                    test_contexts[test.upper()].append({
                        'title': row['title'],
                        'context': context
                    })

test_counter = Counter(all_test_names)
print(f"\n발견된 총 검사명: {len(all_test_names):,}개")
print(f"고유 검사명: {len(test_counter):,}개")
print(f"\n가장 많이 언급된 검사명 Top 20:")
for test, count in test_counter.most_common(20):
    print(f"  {test}: {count}회")

# 5. 샘플 컨텍스트 출력
print("\n" + "="*80)
print("5. 샘플 컨텍스트")
print("="*80)

print("\n[수술/처치 코드 샘플 컨텍스트]")
for code, contexts in list(sample_contexts.items())[:5]:
    print(f"\n코드: {code}")
    for ctx in contexts[:2]:
        print(f"  - 제목: {ctx['title']}")
        print(f"    컨텍스트: ...{ctx['context']}...")

print("\n[약제명 샘플 컨텍스트]")
for drug, contexts in list(drug_contexts.items())[:5]:
    print(f"\n약제: {drug}")
    for ctx in contexts[:2]:
        print(f"  - 제목: {ctx['title']}")
        print(f"    컨텍스트: ...{ctx['context']}...")

# 6. 결과 저장
output_data = {
    'summary': {
        'total_records': len(df),
        'procedure_codes': {
            'total': len(all_procedure_codes),
            'unique': len(procedure_counter)
        },
        'drug_names': {
            'total': len(all_drug_names),
            'unique': len(drug_counter)
        },
        'icd_codes': {
            'total': len(all_icd_codes),
            'unique': len(icd_counter)
        },
        'test_names': {
            'total': len(all_test_names),
            'unique': len(test_counter)
        }
    },
    'top_procedure_codes': dict(procedure_counter.most_common(50)),
    'top_drug_names': dict(drug_counter.most_common(50)),
    'top_icd_codes': dict(icd_counter.most_common(50)),
    'top_test_names': dict(test_counter.most_common(30)),
    'procedure_code_samples': dict(list(sample_contexts.items())[:10]),
    'drug_name_samples': dict(list(drug_contexts.items())[:10])
}

output_path = 'C:/Jimin/scrape-hub/data/hira/hira_pattern_analysis.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"\n\n분석 결과 저장 완료: {output_path}")
