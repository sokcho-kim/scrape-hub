"""
KCD-9 Master file 정규화 및 JSON 변환
- 54,126개 질병코드를 구조화된 JSON으로 변환
- 검색 가능한 형태로 정리
"""
import sys
import codecs
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def normalize_masterfile():
    """Master file 정규화"""

    file_path = Path('data/kssc/kcd-9th/제9차 한국표준질병ㆍ사인분류 2차 정오 DB masterfile_251031_20251103085142.xlsx')
    output_dir = Path('data/kssc/kcd-9th/normalized')
    output_dir.mkdir(exist_ok=True, parents=True)

    print('='*80)
    print('🔄 KCD-9 Master File 정규화')
    print('='*80)
    print(f'\n입력: {file_path.name}')
    print(f'출력: {output_dir}\n')

    # Master file 읽기 (2행이 헤더)
    df = pd.read_excel(file_path, sheet_name='KCD-8 DB Masterfile', header=2)

    print(f'총 데이터: {len(df):,}개 행\n')

    # 컬럼명 정리
    df.columns = [
        'is_header',        # 표제어 (1이면 주 코드)
        'classification',   # 분류기준 (대/중/소/세)
        'code',            # 질병분류코드
        'symbol',          # 검별 (+/*)
        'note',            # 주석 (포함/제외/주)
        'name_kr',         # 한글명칭
        'name_en',         # 영문명칭
        'is_lowest',       # 최하위코드 (1이면 실제 사용 가능)
        'is_domestic',     # 국내세분화코드
        'is_oriental',     # 한의병명
        'is_additional',   # 국내추가진단명
        'revision_no',     # 정오차수
        'revision_note',   # 정오내용
        'unused'           # 사용하지 않는 컬럼
    ]

    # 결측치 처리
    df = df.fillna({
        'is_header': 0,
        'classification': '',
        'symbol': '',
        'note': '',
        'is_lowest': 0,
        'is_domestic': 0,
        'is_oriental': 0,
        'is_additional': 0,
    })

    # 데이터 타입 변환
    df['is_header'] = df['is_header'].astype(int)
    df['is_lowest'] = df['is_lowest'].astype(int)
    df['is_domestic'] = df['is_domestic'].astype(int)
    df['is_oriental'] = df['is_oriental'].astype(int)
    df['is_additional'] = df['is_additional'].astype(int)

    print('[데이터 정제 완료]')
    print(f'  - 컬럼명 정리')
    print(f'  - 결측치 처리')
    print(f'  - 데이터 타입 변환\n')

    # 통계
    print('[데이터 통계]')
    print(f'  총 코드 수: {len(df):,}개')
    print(f'  표제어 (주 코드): {df["is_header"].sum():,}개')
    print(f'  최하위 코드 (사용 가능): {df["is_lowest"].sum():,}개')
    print(f'  국내 세분화: {df["is_domestic"].sum():,}개')
    print(f'  한의 병명: {df["is_oriental"].sum():,}개')
    print(f'  국내 추가: {df["is_additional"].sum():,}개')

    # 분류 레벨 통계
    print(f'\n[분류 체계]')
    classification_counts = df[df['classification'] != '']['classification'].value_counts()
    for level, count in classification_counts.items():
        print(f'  {level}: {count:,}개')

    # 검별 통계
    symbol_counts = df[df['symbol'] != '']['symbol'].value_counts()
    print(f'\n[검별 표시]')
    for symbol, count in symbol_counts.items():
        print(f'  {symbol}: {count:,}개')

    # 1. 전체 데이터를 JSON으로 저장
    print(f'\n[1] 전체 데이터 JSON 변환...')

    records = []
    for _, row in df.iterrows():
        record = {
            'code': str(row['code']).strip(),
            'name_kr': str(row['name_kr']).strip() if pd.notna(row['name_kr']) else '',
            'name_en': str(row['name_en']).strip() if pd.notna(row['name_en']) else '',
            'is_header': bool(row['is_header']),
            'classification': str(row['classification']).strip(),
            'symbol': str(row['symbol']).strip(),
            'note': str(row['note']).strip() if pd.notna(row['note']) else '',
            'is_lowest': bool(row['is_lowest']),
            'is_domestic': bool(row['is_domestic']),
            'is_oriental': bool(row['is_oriental']),
            'is_additional': bool(row['is_additional']),
        }

        # 정오 정보 (있는 경우만)
        if pd.notna(row['revision_no']):
            record['revision'] = {
                'no': str(row['revision_no']).strip(),
                'note': str(row['revision_note']).strip() if pd.notna(row['revision_note']) else ''
            }

        records.append(record)

    # 전체 데이터 저장
    full_output = {
        'version': 'KCD-9',
        'release_date': '2025-10-31',
        'revision': '2차 정오',
        'total_codes': len(records),
        'generated_at': datetime.now().isoformat(),
        'codes': records
    }

    full_file = output_dir / 'kcd9_full.json'
    with open(full_file, 'w', encoding='utf-8') as f:
        json.dump(full_output, f, ensure_ascii=False, indent=2)

    print(f'  ✅ 저장: {full_file.name} ({len(records):,}개 코드)')

    # 2. 최하위 코드만 추출 (실제 사용 가능한 코드)
    print(f'\n[2] 최하위 코드만 추출...')

    lowest_df = df[df['is_lowest'] == 1].copy()
    lowest_records = []

    for _, row in lowest_df.iterrows():
        record = {
            'code': str(row['code']).strip(),
            'name_kr': str(row['name_kr']).strip() if pd.notna(row['name_kr']) else '',
            'name_en': str(row['name_en']).strip() if pd.notna(row['name_en']) else '',
            'classification': str(row['classification']).strip(),
            'symbol': str(row['symbol']).strip(),
            'is_domestic': bool(row['is_domestic']),
            'is_oriental': bool(row['is_oriental']),
        }
        lowest_records.append(record)

    lowest_output = {
        'version': 'KCD-9',
        'release_date': '2025-10-31',
        'revision': '2차 정오',
        'description': '최하위 코드만 포함 (실제 진단 시 사용 가능한 코드)',
        'total_codes': len(lowest_records),
        'generated_at': datetime.now().isoformat(),
        'codes': lowest_records
    }

    lowest_file = output_dir / 'kcd9_usable_codes.json'
    with open(lowest_file, 'w', encoding='utf-8') as f:
        json.dump(lowest_output, f, ensure_ascii=False, indent=2)

    print(f'  ✅ 저장: {lowest_file.name} ({len(lowest_records):,}개 코드)')

    # 3. 코드 → 명칭 매핑 딕셔너리 (빠른 검색용)
    print(f'\n[3] 검색용 매핑 딕셔너리 생성...')

    code_map = {}
    for _, row in df.iterrows():
        code = str(row['code']).strip()
        code_map[code] = {
            'name_kr': str(row['name_kr']).strip() if pd.notna(row['name_kr']) else '',
            'name_en': str(row['name_en']).strip() if pd.notna(row['name_en']) else '',
            'is_lowest': bool(row['is_lowest']),
            'is_header': bool(row['is_header']),
        }

    map_output = {
        'version': 'KCD-9',
        'description': '코드 → 명칭 빠른 검색용 매핑',
        'total_codes': len(code_map),
        'generated_at': datetime.now().isoformat(),
        'map': code_map
    }

    map_file = output_dir / 'kcd9_code_map.json'
    with open(map_file, 'w', encoding='utf-8') as f:
        json.dump(map_output, f, ensure_ascii=False, indent=2)

    print(f'  ✅ 저장: {map_file.name} ({len(code_map):,}개 코드)')

    # 4. 대분류별 통계
    print(f'\n[4] 대분류별 통계 생성...')

    major_df = df[df['classification'] == '대'].copy()
    major_stats = []

    for _, row in major_df.iterrows():
        code_range = str(row['code']).strip()
        name_kr = str(row['name_kr']).strip() if pd.notna(row['name_kr']) else ''

        # 해당 대분류에 속하는 코드 수 계산
        # 예: A00-B99 → A, B로 시작하는 코드들
        start_code = code_range.split('-')[0][0] if '-' in code_range else code_range[0]

        count = len(df[df['code'].astype(str).str.startswith(start_code)])

        major_stats.append({
            'code_range': code_range,
            'name_kr': name_kr,
            'total_codes': count
        })

    stats_output = {
        'version': 'KCD-9',
        'description': '대분류(Chapter)별 통계',
        'generated_at': datetime.now().isoformat(),
        'chapters': major_stats
    }

    stats_file = output_dir / 'kcd9_statistics.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_output, f, ensure_ascii=False, indent=2)

    print(f'  ✅ 저장: {stats_file.name} ({len(major_stats)}개 대분류)')

    # 요약
    print(f'\n\n{"="*80}')
    print('📊 정규화 완료 요약')
    print('='*80)
    print(f'\n생성된 파일:')
    print(f'  1. kcd9_full.json - 전체 데이터 ({len(records):,}개)')
    print(f'  2. kcd9_usable_codes.json - 사용 가능한 코드 ({len(lowest_records):,}개)')
    print(f'  3. kcd9_code_map.json - 빠른 검색용 ({len(code_map):,}개)')
    print(f'  4. kcd9_statistics.json - 대분류 통계 ({len(major_stats)}개)')

    print(f'\n💾 저장 위치: {output_dir}')

    return {
        'full': full_file,
        'usable': lowest_file,
        'map': map_file,
        'stats': stats_file
    }


def main():
    files = normalize_masterfile()

    print('\n\n' + '='*80)
    print('✅ 완료')
    print('='*80)

    # 샘플 검색 테스트
    print('\n[검색 테스트]')

    with open(files['map'], 'r', encoding='utf-8') as f:
        data = json.load(f)
        code_map = data['map']

    # 샘플 코드 검색
    test_codes = ['A00', 'A00.0', 'I10', 'C50']

    for code in test_codes:
        if code in code_map:
            info = code_map[code]
            usable = '✅' if info['is_lowest'] else '❌'
            print(f'  {code}: {info["name_kr"]} {usable}')
        else:
            print(f'  {code}: 코드 없음')


if __name__ == '__main__':
    main()
