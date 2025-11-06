"""
HIRA 고시 샘플 확인
"""
import pandas as pd

df = pd.read_excel('C:/Jimin/scrape-hub/data/hira/hiradata_ver2.xlsx')

# 다양한 샘플 추출
print("="*100)
print("랜덤 샘플 3개")
print("="*100)
samples = df.sample(3, random_state=42)
for idx, row in samples.iterrows():
    print(f'\n[샘플 {idx}]')
    print(f'제목: {row["title"]}')
    print(f'카테고리: {row["category"]}')
    print(f'발행일: {row["published_date"]}')
    print(f'고시번호: {row["relevant"]}')
    print(f'내용 (앞 800자):')
    print(str(row["content"])[:800])
    print('-'*100)

# 수술/처치 코드가 많이 포함된 샘플 찾기
print("\n\n" + "="*100)
print("수술/처치 코드 포함 샘플")
print("="*100)

import re
procedure_pattern = re.compile(r'[자차저나마바사아][가-힣]?\d{3,4}[가-힣]?')

code_counts = []
for idx, row in df.iterrows():
    content = str(row['content'])
    codes = procedure_pattern.findall(content)
    if len(codes) >= 5:  # 코드가 5개 이상인 경우
        code_counts.append((idx, len(codes), codes[:10]))  # 상위 10개만

# 상위 3개 출력
code_counts.sort(key=lambda x: x[1], reverse=True)
for idx, count, sample_codes in code_counts[:3]:
    row = df.iloc[idx]
    print(f'\n[코드 {count}개 포함]')
    print(f'제목: {row["title"]}')
    print(f'샘플 코드: {", ".join(sample_codes)}')
    print(f'내용 (앞 600자):')
    print(str(row["content"])[:600])
    print('-'*100)
