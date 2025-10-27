"""마스터 데이터 구조 확인 - 프로젝트 적용 가능성 검토"""
import pandas as pd
from pathlib import Path
import json
import sys
import codecs

# UTF-8 출력 설정
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

MASTER_DIR = Path('data/hira_master')

print('=' * 100)
print('HIRA 마스터 데이터 구조 분석')
print('=' * 100)

# 1. 약가파일 분석
print('\n[1] 약가파일 (20221101_20251101 적용약가파일_사전제공 1부.xlsx)')
print('-' * 100)

drug_file = MASTER_DIR / '20221101_20251101 적용약가파일_사전제공 1부.xlsx'
try:
    df_drug = pd.read_excel(drug_file, nrows=10)
    print(f'[SUCCESS] 파일 읽기 성공')
    print(f'   총 컬럼: {len(df_drug.columns)}개')
    print(f'\n   컬럼 목록:')
    for i, col in enumerate(df_drug.columns, 1):
        print(f'      {i:2d}. {col}')

    print(f'\n   샘플 데이터 (첫 3행):')
    print(df_drug.head(3).to_string(index=False))

    # 전체 행 수 확인
    df_drug_full = pd.read_excel(drug_file)
    print(f'\n   전체 약제 수: {len(df_drug_full):,}개')

    # 제품명 컬럼 확인 (보통 6-7번째 컬럼)
    if len(df_drug.columns) > 6:
        product_col = df_drug.columns[6]
        print(f'\n   제품명 컬럼 추정: "{product_col}"')
        unique_products = df_drug_full[product_col].nunique()
        print(f'   고유 제품 수: {unique_products:,}개')

        print(f'\n   제품명 샘플 (10개):')
        samples = df_drug_full[product_col].dropna().drop_duplicates().head(10).tolist()
        for i, name in enumerate(samples, 1):
            print(f'      {i}. {name}')

except Exception as e:
    print(f'[ERROR] 에러: {e}')

# 2. 상병마스터 분석
print('\n\n[2] 상병마스터 (배포용 상병마스터_250908(2).xlsx)')
print('-' * 100)

disease_file = MASTER_DIR / '배포용 상병마스터_250908(2).xlsx'
try:
    df_disease = pd.read_excel(disease_file, nrows=10)
    print(f'[SUCCESS] 파일 읽기 성공')
    print(f'   총 컬럼: {len(df_disease.columns)}개')
    print(f'\n   컬럼 목록:')
    for i, col in enumerate(df_disease.columns, 1):
        print(f'      {i:2d}. {col}')

    print(f'\n   샘플 데이터 (첫 3행):')
    print(df_disease.head(3).to_string(index=False))

    # 전체 행 수 확인
    df_disease_full = pd.read_excel(disease_file)
    print(f'\n   전체 상병 수: {len(df_disease_full):,}개')

    # KCD 코드 컬럼 찾기
    kcd_cols = [col for col in df_disease.columns if 'KCD' in str(col).upper() or 'CODE' in str(col).upper() or '코드' in str(col)]
    if kcd_cols:
        print(f'\n   KCD 관련 컬럼:')
        for col in kcd_cols:
            print(f'      - {col}')

except Exception as e:
    print(f'[ERROR] 에러: {e}')

# 3. 수가반영내역 분석
print('\n\n[3] 수가반영내역 (수가반영내역(25.10.1.기준)_전체판.xlsb)')
print('-' * 100)

try:
    # xlsb 파일은 pyxlsb 엔진 필요
    import pyxlsb
    fee_file = MASTER_DIR / '★수가반영내역(25.10.1.기준)_전체판.xlsb'
    df_fee = pd.read_excel(fee_file, engine='pyxlsb', nrows=10)
    print(f'✅ 파일 읽기 성공 (pyxlsb 엔진 사용)')
    print(f'   총 컬럼: {len(df_fee.columns)}개')
    print(f'\n   컬럼 목록:')
    for i, col in enumerate(df_fee.columns, 1):
        print(f'      {i:2d}. {col}')

    print(f'\n   샘플 데이터 (첫 3행):')
    print(df_fee.head(3).to_string(index=False))

    # 전체 행 수 확인
    df_fee_full = pd.read_excel(fee_file, engine='pyxlsb')
    print(f'\n   전체 수가 항목 수: {len(df_fee_full):,}개')

except ImportError:
    print(f'❌ pyxlsb 라이브러리 필요: pip install pyxlsb')
except Exception as e:
    print(f'[ERROR] 에러: {e}')

# 4. 프로젝트 적용 가능성 평가
print('\n\n[4] 프로젝트 적용 가능성 평가')
print('-' * 100)

print('''
[데이터 특성 분석]

1. 약가파일 (약제 정보)
   [O] 제품명, 성분명, 가격 등 상세 정보 포함
   [O] HIRA 암질환 데이터의 약제명과 매칭 가능
   [!] 정확한 매칭을 위해서는 다음이 필요:
      - 약제명 정규화 (대소문자, 공백, 특수문자 제거)
      - 성분명 vs 제품명 구분
      - 영문명 vs 한글명 매칭

2. 상병마스터 (질환 코드)
   [O] KCD 코드 및 질환명 포함
   [O] 암질환 데이터의 질환명과 매칭 가능
   [!] 정확한 매칭을 위해서는:
      - KCD 코드 추출 (예: C34.1, C50.9)
      - 질환명 표준화
      - 암 관련 코드만 필터링 (C00-C97)

3. 수가반영내역 (의료행위 코드)
   [O] 의료행위 코드, 명칭, 수가 포함
   [?] 암질환 데이터와의 직접적인 연관성 확인 필요

[정확한 매칭 전략 - Fuzzy Matching 제외]

**규칙 1: 정규화 후 Exact Match**
   - 약제명: 공백 제거, 대소문자 통일, 괄호 제거
   - 질환명: KCD 코드 기준 매칭
   예시: "Tisagenlecleucel(킴리아주)" → "tisagenlecleucel" (exact match)

**규칙 2: 복수 키 매칭**
   - 약제명의 성분명과 제품명 모두 비교
   - 영문명과 한글명 모두 비교
   예시: "Tisagenlecleucel" OR "킴리아주"

**규칙 3: 표준 코드 매칭**
   - KCD 코드: C34.1 (exact match)
   - 약제 코드: 보험코드 기준 (exact match)

[매칭 성공 조건]
   [O] 정규화된 문자열의 완전 일치
   [O] 표준 코드의 완전 일치
   [X] 유사도 기반 매칭 (Fuzzy) 제외
   [X] 부분 문자열 매칭 (Substring) 제외 (단, 괄호 제거는 허용)

[권장 사항]
   1. 약가파일과 상병마스터는 **사전(Dictionary)** 형태로 변환
   2. 암질환 데이터에서 약제명/질환명 추출 후 사전에서 **Exact Lookup**
   3. 미매칭 항목은 수동 검증 후 사전 업데이트

[Fuzzy Matching이 필요 없는 이유]
   - 의료 데이터는 표준화된 명칭 사용
   - 오타/변형보다는 표준명 vs 별칭 문제
   - 별칭 사전을 구축하면 Exact Match로 충분
''')

print('\n' + '=' * 100)
print('[분석 완료]')
print('=' * 100)

# 5. 다음 단계 제안
print('\n\n[5] 다음 단계 제안')
print('-' * 100)
print('''
[Step 1] 마스터 데이터 전처리
   ├─ 약가파일: 성분명, 제품명 추출 → JSON 사전
   ├─ 상병마스터: KCD 코드, 질환명 추출 → JSON 사전
   └─ 별칭 사전 구축 (영문명 ↔ 한글명)

[Step 2] 암질환 데이터 전처리
   ├─ PDF/HWP 파싱 결과에서 약제명 추출
   ├─ 약제명 정규화 (공백, 괄호, 대소문자)
   └─ 질환명/KCD 코드 추출

[Step 3] Exact Matching
   ├─ 정규화된 약제명 → 약가사전 Lookup
   ├─ KCD 코드 → 상병사전 Lookup
   └─ 매칭률 계산

[Step 4] 검증 및 보완
   ├─ 미매칭 항목 확인
   ├─ 별칭 추가 또는 수동 매칭
   └─ 최종 매칭 결과 저장

작업을 진행하시겠습니까?
''')
