import pandas as pd
import json
import os
from pathlib import Path

def analyze_file(filepath):
    """파일을 분석해서 메타정보 반환"""
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    ext = filepath.suffix

    info = {
        'filename': filename,
        'size': f"{filesize / 1024:.1f} KB",
        'type': None,
        'rows': None,
        'columns': None,
        'description': None
    }

    try:
        if ext == '.csv':
            df = pd.read_csv(filepath, encoding='utf-8-sig')
            info['type'] = 'CSV'
            info['rows'] = len(df)
            info['columns'] = list(df.columns)
            info['column_count'] = len(df.columns)
        elif ext == '.json':
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)
            info['type'] = 'JSON'
            if isinstance(data, list):
                info['rows'] = len(data)
                if len(data) > 0 and isinstance(data[0], dict):
                    info['columns'] = list(data[0].keys())
                    info['column_count'] = len(data[0].keys())
            elif isinstance(data, dict):
                info['rows'] = len(data)
                info['structure'] = 'Dictionary'
    except Exception as e:
        info['error'] = str(e)

    return info

# bridges 폴더의 모든 데이터 파일 분석
bridge_files = sorted(Path('.').glob('*.csv')) + sorted(Path('.').glob('*.json'))

print("=" * 100)
print("BRIDGES 폴더 데이터 색인")
print("=" * 100)

data_files = []
script_files = []

for filepath in bridge_files:
    if 'sample' in filepath.name:
        continue  # 샘플 파일은 나중에 따로 처리
    info = analyze_file(filepath)
    data_files.append(info)

# 파일별 상세 정보 출력
print("\n## 📊 데이터 파일 목록\n")

categories = {
    'master': [],
    'clean': [],
    'normalized': [],
    'sample': []
}

# 파일 분류
for f in data_files:
    if 'sample' in f['filename']:
        categories['sample'].append(f)
    elif 'normalized' in f['filename']:
        categories['normalized'].append(f)
    elif 'clean' in f['filename']:
        categories['clean'].append(f)
    elif 'master' in f['filename']:
        categories['master'].append(f)

# 1. Master 파일 (원본 통합)
print("### 1️⃣ MASTER - 원본 통합 데이터")
print("여러 소스에서 수집한 항암제 데이터를 ATC 코드 기반으로 통합한 1차 결과물")
print("-" * 100)
for f in categories['master']:
    print(f"\n📄 **{f['filename']}** ({f['size']})")
    print(f"   - 형식: {f['type']}")
    print(f"   - 행 수: {f['rows']:,}개")
    if f.get('columns'):
        print(f"   - 컬럼: {f['column_count']}개")
        print(f"     {', '.join(f['columns'][:8])}")
        if len(f['columns']) > 8:
            print(f"     {', '.join(f['columns'][8:])}")

# 2. Clean 파일 (정제)
print("\n\n### 2️⃣ CLEAN - 정제 데이터")
print("브랜드명, 성분명 추출 및 정제가 완료된 데이터 (Phase 1)")
print("-" * 100)
for f in categories['clean']:
    print(f"\n📄 **{f['filename']}** ({f['size']})")
    print(f"   - 형식: {f['type']}")
    print(f"   - 행 수: {f['rows']:,}개")
    if f.get('columns'):
        print(f"   - 컬럼: {f['column_count']}개")
        print(f"     {', '.join(f['columns'][:8])}")
        if len(f['columns']) > 8:
            print(f"     {', '.join(f['columns'][8:])}")

# 3. Normalized 파일 (정규화)
print("\n\n### 3️⃣ NORMALIZED - 정규화 데이터 (최종)")
print("1 제품 = 1 행 구조로 정규화, HIRA dictionary와 조인하여 제조사/약가 정보 추가")
print("-" * 100)
for f in categories['normalized']:
    print(f"\n📄 **{f['filename']}** ({f['size']})")
    print(f"   - 형식: {f['type']}")
    print(f"   - 행 수: {f['rows']:,}개")
    if f.get('columns'):
        print(f"   - 컬럼: {f['column_count']}개")
        print(f"     {', '.join(f['columns'][:8])}")
        if len(f['columns']) > 8:
            print(f"     {', '.join(f['columns'][8:])}")

# 샘플 파일
sample_files = sorted(Path('.').glob('*sample*.json'))
if sample_files:
    print("\n\n### 4️⃣ SAMPLE - 샘플 파일")
    print("데이터 구조 확인용 샘플 (5-10개 레코드)")
    print("-" * 100)
    for filepath in sample_files:
        info = analyze_file(filepath)
        print(f"\n📄 **{info['filename']}** ({info['size']})")
        print(f"   - 원본: {info['filename'].replace('_sample.json', '')}")

# 스크립트 파일
script_files = sorted(Path('.').glob('*.py'))
if script_files:
    print("\n\n## 🔧 스크립트 파일 목록\n")
    for script in script_files:
        size = os.path.getsize(script) / 1024
        print(f"📜 **{script.name}** ({size:.1f} KB)")
        # 첫 줄 docstring 읽기
        try:
            with open(script, encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if '"""' in line or "'''" in line:
                        desc_line = line.strip().strip('"""').strip("'''")
                        if desc_line:
                            print(f"   - {desc_line}")
                        break
                    elif line.strip().startswith('#') and 'coding' not in line:
                        print(f"   - {line.strip().lstrip('#').strip()}")
                        break
        except:
            pass

print("\n\n" + "=" * 100)
print("색인 생성 완료!")
print("=" * 100)

# 권장 사용 파일
print("\n## ✅ 권장 사용 파일\n")
print("🎯 **anticancer_normalized_v2.csv** (또는 .json)")
print("   - 가장 최신이며 완전한 데이터")
print("   - HIRA dictionary 조인 완료")
print("   - 제조사, 약가, 투여경로 정보 포함")
print("   - 1,001개 제품, 154개 성분")
print("\n💡 **사용 예시**:")
print("   - 항암제 검색/조회 시스템")
print("   - 약가 비교 분석")
print("   - 제조사별 제품 현황")
print("   - ATC 코드 기반 분류")
