"""HIRA 암질환 데이터 - 약제명 추출 및 매칭 v2 (영문명 별칭 포함)

개선사항:
1. 영문명 별칭 사전 추가 (paclitaxel → 파클리탁셀)
2. 매칭 순서: 직접 매칭 → 영문명 별칭 → 미매칭

입력:
- data/hira_cancer/parsed/{announcement,pre_announcement,faq}/*.json
- data/hira_master/drug_dictionary.json
- data/hira_master/drug_aliases_eng.json (NEW!)

출력:
- data/hira_cancer/drug_matching_results_v2.json
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

PARSED_DIR = Path('data/hira_cancer/parsed')
DRUG_DICT_FILE = Path('data/hira_master/drug_dictionary.json')
ENG_ALIASES_FILE = Path('data/hira_master/drug_aliases_eng.json')
OUTPUT_FILE = Path('data/hira_cancer/drug_matching_results_v2.json')

print('=' * 100)
print('HIRA 암질환 데이터 - 약제명 매칭 v2 (영문명 별칭 포함)')
print('=' * 100)

# 1. 사전 로드
print('\n[1] 사전 로드')
print('-' * 100)

with open(DRUG_DICT_FILE, 'r', encoding='utf-8') as f:
    drug_dict = json.load(f)
print(f'약가 사전: {len(drug_dict):,}개 검색 키')

with open(ENG_ALIASES_FILE, 'r', encoding='utf-8') as f:
    eng_aliases_data = json.load(f)
    eng_aliases = eng_aliases_data['mappings']
print(f'영문명 별칭: {len(eng_aliases):,}개 매핑')

# 2. 파일 수집
print('\n[2] 파싱 파일 수집')
print('-' * 100)

all_files = []
for board in ['announcement', 'pre_announcement', 'faq']:
    board_dir = PARSED_DIR / board
    files = list(board_dir.glob('*.json'))
    all_files.extend([(board, f) for f in files])
    print(f'{board}: {len(files)}개 파일')

print(f'\n총 {len(all_files)}개 파일')

# 3. 약제명 추출 함수 (v1과 동일)
def extract_drug_candidates(text):
    """텍스트에서 약제명 후보 추출"""
    candidates = set()

    if not text:
        return candidates

    # 패턴 1: 제형 패턴
    form_pattern = r'([가-힣A-Za-z][가-힣A-Za-z0-9]*)(주|정|캡슐|시럽|액|연고|크림|겔|산|과립)\b'
    for match in re.finditer(form_pattern, text):
        full_name = match.group(0)
        base_name = match.group(1)

        if len(full_name) >= 3:
            candidates.add(full_name)
            if len(base_name) >= 2:
                candidates.add(base_name)

    # 패턴 2: 괄호 안 성분명
    paren_pattern = r'\(([가-힣A-Za-z][가-힣A-Za-z0-9]*)\)'
    for match in re.finditer(paren_pattern, text):
        ingredient = match.group(1)
        if len(ingredient) >= 3 and not re.match(r'\d', ingredient):
            candidates.add(ingredient)

    return candidates

# 4. 매칭 함수 (v2 - 영문명 별칭 추가)
def match_drug(candidate, drug_dict, eng_aliases):
    """
    약제명 매칭 (우선순위)
    1. 직접 매칭 (약가 사전)
    2. 영문명 별칭 매칭
    3. 미매칭

    Returns: (matched, korean_name, match_type)
    """
    # 1. 직접 매칭
    if candidate in drug_dict:
        return (True, candidate, 'direct')

    # 2. 영문명 별칭 매칭
    candidate_lower = candidate.lower()
    if candidate_lower in eng_aliases:
        korean_name = eng_aliases[candidate_lower]
        # 한글명이 약가 사전에 있는지 확인
        if korean_name in drug_dict:
            return (True, korean_name, 'english_alias')

    # 3. 미매칭
    return (False, candidate, 'unmatched')

# 5. 전체 파일 처리
print('\n[3] 약제명 추출 및 매칭 (영문명 별칭 포함)')
print('-' * 100)

stats = {
    'total_files': len(all_files),
    'total_candidates_raw': 0,
    'total_candidates_unique': 0,
    'matched_direct': 0,
    'matched_english': 0,
    'unmatched': 0,
    'matched_direct_occurrences': 0,
    'matched_english_occurrences': 0,
    'unmatched_occurrences': 0,
}

all_candidates_counter = Counter()
matched_drugs = defaultdict(lambda: {'count': 0, 'match_type': '', 'sources': []})
matched_via_english = defaultdict(lambda: {'count': 0, 'english_name': '', 'korean_name': ''})
unmatched_drugs = Counter()

for board, file_path in all_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        content = data.get('content', '')
        metadata = data.get('attachment_metadata', {})

        # 약제명 후보 추출
        candidates = extract_drug_candidates(content)

        for candidate in candidates:
            all_candidates_counter[candidate] += 1
            stats['total_candidates_raw'] += 1

            # 매칭 시도
            is_matched, result_name, match_type = match_drug(candidate, drug_dict, eng_aliases)

            if is_matched:
                if match_type == 'direct':
                    matched_drugs[result_name]['count'] += 1
                    matched_drugs[result_name]['match_type'] = 'direct'
                    stats['matched_direct_occurrences'] += 1
                elif match_type == 'english_alias':
                    matched_drugs[result_name]['count'] += 1
                    matched_drugs[result_name]['match_type'] = 'english_alias'
                    matched_via_english[candidate]['count'] += 1
                    matched_via_english[candidate]['english_name'] = candidate
                    matched_via_english[candidate]['korean_name'] = result_name
                    stats['matched_english_occurrences'] += 1
            else:
                unmatched_drugs[candidate] += 1
                stats['unmatched_occurrences'] += 1

    except Exception as e:
        print(f'오류 ({file_path.name}): {e}')
        continue

# 고유 약제명 수
stats['total_candidates_unique'] = len(all_candidates_counter)
stats['matched_direct'] = len([d for d in matched_drugs.values() if d['match_type'] == 'direct'])
stats['matched_english'] = len(matched_via_english)
stats['unmatched'] = len(unmatched_drugs)

total_matched_unique = stats['matched_direct'] + stats['matched_english']
total_matched_occurrences = stats['matched_direct_occurrences'] + stats['matched_english_occurrences']

print(f'\n✅ 처리 완료!')
print(f'\n전체 통계:')
print(f'  총 후보 추출: {stats["total_candidates_raw"]:,}개 (중복 포함)')
print(f'  고유 후보: {stats["total_candidates_unique"]:,}개')
print(f'\n매칭 결과:')
print(f'  매칭 성공 (고유): {total_matched_unique:,}개 ({total_matched_unique/stats["total_candidates_unique"]*100:.1f}%)')
print(f'    - 직접 매칭: {stats["matched_direct"]:,}개')
print(f'    - 영문명 별칭: {stats["matched_english"]:,}개')
print(f'  매칭 실패 (고유): {stats["unmatched"]:,}개 ({stats["unmatched"]/stats["total_candidates_unique"]*100:.1f}%)')
print(f'\n출현 빈도 기준:')
print(f'  매칭 성공: {total_matched_occurrences:,}회')
print(f'    - 직접 매칭: {stats["matched_direct_occurrences"]:,}회')
print(f'    - 영문명 별칭: {stats["matched_english_occurrences"]:,}회')
print(f'  매칭 실패: {stats["unmatched_occurrences"]:,}회')

# 6. 영문명 별칭 효과 분석
print('\n[4] 영문명 별칭 매칭 효과')
print('-' * 100)

print('\n영문명 별칭으로 매칭된 약제 (Top 20):')
for i, (eng, info) in enumerate(sorted(matched_via_english.items(), key=lambda x: x[1]['count'], reverse=True)[:20], 1):
    kor = info['korean_name']
    count = info['count']
    print(f'{i:2d}. {eng:30s} → {kor:20s} ({count:3d}회)')

# 7. v1 vs v2 비교
print('\n[5] v1 vs v2 비교')
print('-' * 100)

# v1 결과 (하드코딩 - 이전 실행 결과)
v1_matched_unique = 317
v1_match_rate = 23.5

print(f'\nv1 (영문명 별칭 없음):')
print(f'  매칭 성공: {v1_matched_unique}개 ({v1_match_rate:.1f}%)')

print(f'\nv2 (영문명 별칭 포함):')
print(f'  매칭 성공: {total_matched_unique}개 ({total_matched_unique/stats["total_candidates_unique"]*100:.1f}%)')
print(f'    - 직접 매칭: {stats["matched_direct"]}개')
print(f'    - 영문명 별칭: {stats["matched_english"]}개 ⭐')

improvement = total_matched_unique - v1_matched_unique
improvement_rate = (total_matched_unique/stats["total_candidates_unique"]*100) - v1_match_rate
print(f'\n개선 효과:')
print(f'  증가: +{improvement}개 (+{improvement_rate:.1f}%p)')

# 8. 미매칭 분석
print('\n[6] 여전히 미매칭된 약제 (Top 30)')
print('-' * 100)

for i, (drug, count) in enumerate(unmatched_drugs.most_common(30), 1):
    print(f'{i:2d}. {drug:30s} ({count:3d}회)')

# 9. 결과 저장
print('\n[7] 결과 저장')
print('-' * 100)

result = {
    'summary': {
        'version': 'v2',
        'total_files': stats['total_files'],
        'total_candidates_unique': stats['total_candidates_unique'],
        'matched_total': total_matched_unique,
        'matched_direct': stats['matched_direct'],
        'matched_english': stats['matched_english'],
        'unmatched': stats['unmatched'],
        'match_rate': total_matched_unique / stats['total_candidates_unique'] * 100,
        'improvement_from_v1': {
            'v1_matched': v1_matched_unique,
            'v1_rate': v1_match_rate,
            'v2_matched': total_matched_unique,
            'v2_rate': total_matched_unique / stats['total_candidates_unique'] * 100,
            'increase': improvement,
            'increase_rate': improvement_rate
        }
    },
    'matched_via_english': [
        {'english': eng, 'korean': info['korean_name'], 'count': info['count']}
        for eng, info in sorted(matched_via_english.items(), key=lambda x: x[1]['count'], reverse=True)[:50]
    ],
    'top_unmatched': [
        {'drug': drug, 'count': count}
        for drug, count in unmatched_drugs.most_common(100)
    ]
}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'저장 완료: {OUTPUT_FILE}')
print(f'파일 크기: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB')

# 10. 최종 요약
print('\n' + '=' * 100)
print('✅ 약제명 매칭 v2 완료 (영문명 별칭 포함)')
print('=' * 100)

print(f'''
주요 결과:
- v1 매칭률: {v1_match_rate:.1f}% ({v1_matched_unique}개)
- v2 매칭률: {total_matched_unique/stats["total_candidates_unique"]*100:.1f}% ({total_matched_unique}개)
- 개선 효과: +{improvement}개 (+{improvement_rate:.1f}%p)

영문명 별칭 기여:
- 영문명으로 추가 매칭: {stats["matched_english"]}개
- 대표 사례: paclitaxel→파클리탁셀, docetaxel→도세탁셀

다음 단계:
1. 미매칭 약제 검토
2. 추가 별칭 필요 시 수동 입력
3. 최종 매칭 결과 활용
''')
