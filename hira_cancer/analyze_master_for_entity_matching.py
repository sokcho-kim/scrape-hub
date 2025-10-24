"""마스터 데이터 분석 - 엔티티 매칭 가능성 평가

목적:
1. 약가파일 → 약제명 추출
2. 상병마스터 → 질환명 추출
3. 암질환 파싱 데이터와 매칭 가능성 분석
"""
import pandas as pd
import json
import sys
import codecs
from pathlib import Path
from collections import defaultdict

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

MASTER_DIR = Path('data/hira_master')
PARSED_DIR = Path('data/hira_cancer/parsed_preview')

print('=' * 80)
print('🔍 마스터 데이터 분석 - Graph RAG 엔티티 매칭')
print('=' * 80)

# 1. 약가파일 분석
print('\n1️⃣ 적용 약가파일 분석')
print('-' * 80)

drug_file = Path('data/hira_master/20221101_20251101 적용약가파일_사전제공 1부.xlsx')
df_drug = pd.read_excel(drug_file)

print(f'총 행 수: {len(df_drug):,}개')
print(f'컬럼 수: {len(df_drug.columns)}개')
print(f'\n주요 컬럼:')
for col in df_drug.columns[:15]:
    print(f'  - {col}')

# 제품명 추출
product_col = df_drug.columns[6]  # 7번째 컬럼이 제품명인 것 같음
print(f'\n제품명 컬럼: "{product_col}"')
print(f'고유 제품 수: {df_drug[product_col].nunique():,}개')

# 샘플
print(f'\n제품명 샘플 (10개):')
samples = df_drug[product_col].drop_duplicates().head(10).tolist()
for i, name in enumerate(samples, 1):
    print(f'  {i}. {name}')

# 2. 암질환 파싱 데이터에서 약제명 추출
print('\n\n2️⃣ 암질환 파싱 데이터 약제명 추출')
print('-' * 80)

# FAQ #117 예시
faq_file = PARSED_DIR / 'faq_117.txt'
with open(faq_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Markdown 내용만 추출
markdown_start = content.find('[파싱된 Markdown 내용]')
if markdown_start != -1:
    markdown = content[markdown_start:].lower()
else:
    markdown = content.lower()

# 약제명 매칭 테스트
matched_drugs = []
for drug_name in samples:
    # 간단한 이름 추출 (괄호 앞부분)
    simple_name = drug_name.split('(')[0].strip().lower()

    if len(simple_name) > 3 and simple_name in markdown:
        matched_drugs.append((drug_name, simple_name))

print(f'샘플 10개 중 매칭: {len(matched_drugs)}개')
for drug, simple in matched_drugs:
    print(f'  ✅ {drug} (검색어: {simple})')

# 3. Tisagenlecleucel 매칭 테스트
print('\n\n3️⃣ 특정 약제 매칭 테스트')
print('-' * 80)

target_drug = 'tisagenlecleucel'
print(f'검색 약제: {target_drug}')

# 약가파일에서 검색
matches = df_drug[df_drug[product_col].str.contains(target_drug, case=False, na=False)]
print(f'\n약가파일 매칭 결과: {len(matches)}건')
if len(matches) > 0:
    print('매칭된 제품:')
    for idx, row in matches.head().iterrows():
        print(f'  - {row[product_col]}')
else:
    print('  매칭 없음')

    # 영문명으로 다시 검색
    print('\n영문 성분명으로 재검색 시도...')
    # 컬럼명 확인 필요

# 4. 매칭 전략 제안
print('\n\n4️⃣ 엔티티 매칭 전략 분석')
print('-' * 80)

print('''
**결론**:

✅ 약가파일 활용 가능:
  - {0:,}개 약제 정보 보유
  - 제품명으로 매칭 가능
  - 문제: 성분명 vs 제품명 차이
  - 해결: 다중 매칭 (성분명, 제품명, 영문명)

❓ 상병마스터 확인 필요:
  - 현재 파일은 변경내역 문서
  - 전체 질환 마스터 파일 필요
  - 또는 암 관련 ICD-10 코드 사전 필요

🎯 최종 추천 전략:

1. **규칙 기반 + 마스터 매칭** (1차)
   - Markdown 표에서 약제명 추출
   - 약가파일과 매칭 (부분 일치 허용)
   - 매칭률: 60-80% 예상

2. **NER 모델 보완** (2차)
   - 규칙으로 못 찾은 약제명 추출
   - 의학 용어 인식
   - 매칭률: 80-95% 예상

3. **수동 검증** (3차)
   - 미매칭 약제 수동 확인
   - 사전 업데이트
   - 매칭률: 95-100%

💡 NER 모델이 있다면:
  - 규칙 기반 (빠름, 70%)
  + NER 모델 (정확, 25%)
  + 수동 (5%)
  = 100% 커버리지 달성 가능!
'''.format(df_drug[product_col].nunique()))

# 5. 다음 단계 제안
print('\n\n5️⃣ 다음 단계')
print('-' * 80)
print('''
[선택 A] 규칙 기반 + 마스터 매칭으로 시작
  ├─ 약가파일 전처리 (성분명 추출)
  ├─ 암질환 데이터 약제명 추출
  ├─ Fuzzy matching (유사도 매칭)
  └─ 매칭 결과 확인

[선택 B] NER 모델 우선 사용
  ├─ NER 모델로 약제명 추출
  ├─ 약가파일과 검증
  └─ 미매칭만 규칙 적용

[선택 C] 하이브리드 (추천!)
  ├─ 1단계: 규칙 기반 (표 데이터 - 빠름)
  ├─ 2단계: NER 모델 (서술형 텍스트 - 정확)
  └─ 3단계: 약가파일 검증 (마스터 매칭)

어떤 방식을 선택하시겠습니까?
''')

print('=' * 80)
