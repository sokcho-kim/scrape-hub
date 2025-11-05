"""
KDRG HTML에서 수술/처치 코드 테이블 추출
- 한글코드(자751) → 영문코드(Q7511) → 명칭 매핑
"""
import sys
import codecs
from pathlib import Path
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def extract_procedure_codes(html_path: Path):
    """KDRG HTML에서 수술/처치 코드 추출"""

    print('='*80)
    print('🔍 KDRG 수술/처치 코드 추출')
    print('='*80)
    print(f'\n입력: {html_path.name}\n')

    # HTML 로드
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    print('[1] HTML 파싱 완료')
    print(f'  총 HTML 크기: {len(html_content):,}자\n')

    # 테이블 찾기
    tables = soup.find_all('table')
    print(f'[2] 테이블 검색')
    print(f'  발견된 테이블: {len(tables)}개\n')

    # 코드 패턴
    # 한글코드: 자751, 차94, 나850 등
    korean_code_pattern = re.compile(r'^[가-힣]+\d+[가-힣]*(\(.*?\))*$')
    # 영문코드: Q7511, U4940, S5711 등
    english_code_pattern = re.compile(r'^[A-Z]+\d+$')

    procedures = []
    code_count = 0
    table_with_codes = 0

    print('[3] 코드 추출 중...')

    for table_idx, table in enumerate(tables):
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all('td')

            # 3컬럼 구조 확인: 한글코드 | 영문코드 | 명칭
            if len(cells) >= 3:
                col1 = cells[0].get_text(strip=True)
                col2 = cells[1].get_text(strip=True)
                col3 = cells[2].get_text(strip=True)

                # 한글코드와 영문코드 패턴 확인
                if korean_code_pattern.match(col1) and english_code_pattern.match(col2):
                    procedure = {
                        'korean_code': col1,
                        'english_code': col2,
                        'name': col3,
                        'table_index': table_idx
                    }
                    procedures.append(procedure)
                    code_count += 1

        if any(korean_code_pattern.match(cell.get_text(strip=True)) for row in rows for cell in row.find_all('td')):
            table_with_codes += 1

    print(f'  ✅ 추출 완료: {code_count:,}개 코드')
    print(f'  📊 코드 포함 테이블: {table_with_codes}개\n')

    # 중복 제거 (같은 한글코드가 여러 번 나올 수 있음)
    unique_codes = {}
    for proc in procedures:
        key = proc['korean_code']
        if key not in unique_codes:
            unique_codes[key] = proc
        else:
            # 이미 있으면 명칭이 더 긴 것을 선택 (더 상세함)
            if len(proc['name']) > len(unique_codes[key]['name']):
                unique_codes[key] = proc

    procedures_unique = list(unique_codes.values())

    print(f'[4] 중복 제거')
    print(f'  원본: {len(procedures):,}개')
    print(f'  고유: {len(procedures_unique):,}개\n')

    # 코드 prefix별 통계
    print(f'[5] 코드 유형별 통계')

    prefix_stats = {}
    for proc in procedures_unique:
        prefix = proc['korean_code'][0]  # 첫 글자
        prefix_stats[prefix] = prefix_stats.get(prefix, 0) + 1

    for prefix, count in sorted(prefix_stats.items(), key=lambda x: -x[1]):
        print(f'  {prefix}: {count:,}개')

    # 샘플 출력
    print(f'\n[6] 샘플 코드 (처음 20개)')
    print('-'*80)
    for i, proc in enumerate(procedures_unique[:20], 1):
        print(f'{i:2d}. {proc["korean_code"]:15s} {proc["english_code"]:10s} {proc["name"][:50]}')
    print('-'*80)

    # 특정 코드 검색 (고시 예시)
    print(f'\n[7] 고시 예시 코드 검색')
    test_codes = ['자722', '자751', '자752', '자754', '자756', '자757', '자758', '자759', '자816']

    found_codes = {}
    for code in test_codes:
        for proc in procedures_unique:
            if proc['korean_code'].startswith(code):
                found_codes[code] = proc
                break

    print('  고시: "췌장수술(자751, 자752, 자754, 자756, 자757, 자758, 자759, 자816)"\n')
    for code in test_codes:
        if code in found_codes:
            proc = found_codes[code]
            print(f'  ✅ {code:10s} → {proc["english_code"]:10s} → {proc["name"]}')
        else:
            print(f'  ❌ {code:10s} → 코드 없음')

    return procedures_unique


def save_results(procedures: list, output_dir: Path):
    """추출 결과 저장"""

    print(f'\n\n[8] 결과 저장')

    output_dir.mkdir(exist_ok=True, parents=True)

    # 1. 전체 데이터 JSON
    full_output = {
        'version': 'KDRG v1.4',
        'description': 'KDRG 분류집 수술/처치 코드',
        'total_codes': len(procedures),
        'generated_at': datetime.now().isoformat(),
        'codes': procedures
    }

    full_file = output_dir / 'kdrg_procedures_full.json'
    with open(full_file, 'w', encoding='utf-8') as f:
        json.dump(full_output, f, ensure_ascii=False, indent=2)

    print(f'  ✅ 전체 데이터: {full_file.name} ({len(procedures):,}개)')

    # 2. 한글코드 → 영문코드 매핑
    korean_to_english = {}
    for proc in procedures:
        korean_to_english[proc['korean_code']] = {
            'english_code': proc['english_code'],
            'name': proc['name']
        }

    map1_output = {
        'version': 'KDRG v1.4',
        'description': '한글코드 → 영문코드 매핑',
        'total_codes': len(korean_to_english),
        'generated_at': datetime.now().isoformat(),
        'map': korean_to_english
    }

    map1_file = output_dir / 'kdrg_korean_to_english.json'
    with open(map1_file, 'w', encoding='utf-8') as f:
        json.dump(map1_output, f, ensure_ascii=False, indent=2)

    print(f'  ✅ 한글→영문 매핑: {map1_file.name} ({len(korean_to_english):,}개)')

    # 3. 영문코드 → 한글코드 매핑
    english_to_korean = {}
    for proc in procedures:
        english_to_korean[proc['english_code']] = {
            'korean_code': proc['korean_code'],
            'name': proc['name']
        }

    map2_output = {
        'version': 'KDRG v1.4',
        'description': '영문코드 → 한글코드 매핑',
        'total_codes': len(english_to_korean),
        'generated_at': datetime.now().isoformat(),
        'map': english_to_korean
    }

    map2_file = output_dir / 'kdrg_english_to_korean.json'
    with open(map2_file, 'w', encoding='utf-8') as f:
        json.dump(map2_output, f, ensure_ascii=False, indent=2)

    print(f'  ✅ 영문→한글 매핑: {map2_file.name} ({len(english_to_korean):,}개)')

    # 4. 검색용 통합 인덱스 (코드 → 명칭)
    search_index = {}
    for proc in procedures:
        # 한글코드로 검색
        search_index[proc['korean_code']] = {
            'type': 'korean_code',
            'english_code': proc['english_code'],
            'name': proc['name']
        }
        # 영문코드로 검색
        search_index[proc['english_code']] = {
            'type': 'english_code',
            'korean_code': proc['korean_code'],
            'name': proc['name']
        }

    search_output = {
        'version': 'KDRG v1.4',
        'description': '통합 검색 인덱스 (한글코드 + 영문코드 모두 검색 가능)',
        'total_entries': len(search_index),
        'generated_at': datetime.now().isoformat(),
        'index': search_index
    }

    search_file = output_dir / 'kdrg_search_index.json'
    with open(search_file, 'w', encoding='utf-8') as f:
        json.dump(search_output, f, ensure_ascii=False, indent=2)

    print(f'  ✅ 통합 검색 인덱스: {search_file.name} ({len(search_index):,}개)')

    print(f'\n💾 저장 위치: {output_dir}')

    return {
        'full': full_file,
        'korean_to_english': map1_file,
        'english_to_korean': map2_file,
        'search': search_file
    }


def main():
    html_path = Path('data/hira_master/kdrg_parsed/kdrg_smart.html')
    output_dir = Path('data/hira_master/kdrg_parsed/codes')

    if not html_path.exists():
        print(f'❌ 파일 없음: {html_path}')
        return

    # 코드 추출
    procedures = extract_procedure_codes(html_path)

    # 결과 저장
    files = save_results(procedures, output_dir)

    # 최종 요약
    print('\n\n' + '='*80)
    print('📊 완료 요약')
    print('='*80)

    print(f'\n추출된 코드: {len(procedures):,}개')

    # 코드 유형별 통계
    prefix_stats = {}
    for proc in procedures:
        prefix = proc['korean_code'][0]
        prefix_stats[prefix] = prefix_stats.get(prefix, 0) + 1

    print(f'\n주요 코드 유형:')
    for prefix, count in sorted(prefix_stats.items(), key=lambda x: -x[1])[:10]:
        print(f'  {prefix}: {count:,}개')

    # 검색 테스트
    print(f'\n[검색 테스트]')
    with open(files['search'], 'r', encoding='utf-8') as f:
        search_data = json.load(f)
        search_index = search_data['index']

    test_codes = ['자722', '자751', 'Q7511', 'N0911']
    for code in test_codes:
        if code in search_index:
            info = search_index[code]
            print(f'  {code:10s} → {info["name"][:50]}')
        else:
            print(f'  {code:10s} → 코드 없음')

    print('\n' + '='*80)
    print('✅ 완료')
    print('='*80)


if __name__ == '__main__':
    main()
