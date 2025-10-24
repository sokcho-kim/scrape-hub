"""마스터 데이터 구조 탐색"""
import pandas as pd
import sys
import codecs
from pathlib import Path

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 파일 경로
MASTER_DIR = Path('data/hira_master')

print('=' * 80)
print('📁 HIRA 마스터 데이터 탐색')
print('=' * 80)

# 1. 상병마스터 (질환)
print('\n1️⃣ 배포용 상병마스터')
print('-' * 80)

disease_file = list(MASTER_DIR.glob('*상병마스터*.xlsx'))[0]
print(f'파일: {disease_file.name}')

# 여러 skiprows 시도
for skip in [0, 5, 6, 7]:
    try:
        df = pd.read_excel(disease_file, skiprows=skip, nrows=5)
        print(f'\nskiprows={skip}:')
        print(f'  컬럼: {df.columns.tolist()}')
        print(f'  행 수: {len(df)}')
        if len(df) > 0:
            print(f'  첫 행: {df.iloc[0].tolist()[:5]}')
    except Exception as e:
        print(f'\nskiprows={skip}: 에러 - {e}')

# 전체 데이터 확인
df_disease = pd.read_excel(disease_file)
print(f'\n전체 데이터:')
print(f'  행 수: {len(df_disease)}')
print(f'  컬럼: {df_disease.columns.tolist()}')

# 2. 약가파일
print('\n\n2️⃣ 적용 약가파일')
print('-' * 80)

drug_file = list(MASTER_DIR.glob('*약가*.xlsb'))[0]
print(f'파일: {drug_file.name}')

try:
    df_drug = pd.read_excel(drug_file, engine='pyxlsb', nrows=10)
    print(f'컬럼: {df_drug.columns.tolist()}')
    print(f'\n샘플 데이터 (첫 5행):')
    print(df_drug.head().to_string())

    # 전체 행 수
    df_drug_full = pd.read_excel(drug_file, engine='pyxlsb')
    print(f'\n전체 행 수: {len(df_drug_full)}')
except Exception as e:
    print(f'에러: {e}')

# 3. 수가 반영 내역
print('\n\n3️⃣ 수가 반영 내역')
print('-' * 80)

fee_file = list(MASTER_DIR.glob('*수가*.xlsx'))[0]
print(f'파일: {fee_file.name}')

try:
    df_fee = pd.read_excel(fee_file, nrows=10)
    print(f'컬럼: {df_fee.columns.tolist()}')
    print(f'\n샘플 데이터 (첫 5행):')
    print(df_fee.head().to_string())

    # 전체 행 수
    df_fee_full = pd.read_excel(fee_file)
    print(f'\n전체 행 수: {len(df_fee_full)}')
except Exception as e:
    print(f'에러: {e}')

print('\n' + '=' * 80)
print('✅ 탐색 완료')
print('=' * 80)
