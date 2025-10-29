"""HIRA 암질환 데이터에서 약제명 추출 및 약가 사전 매칭

목적:
1. 파싱 데이터에서 약제명 후보 추출
2. 약가 사전과 매칭 (노이즈 자동 제거)
3. 매칭률 계산 및 미매칭 분석

입력:
- data/hira_cancer/parsed/{announcement,pre_announcement,faq}/*.json
- data/hira_master/drug_dictionary.json

출력:
- data/hira_cancer/drug_matching_results.json
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

PARSED_DIR = Path('data/hira_cancer/parsed')
DRUG_DICT_FILE = Path('data/hira_master/drug_dictionary.json')
OUTPUT_FILE = Path('data/hira_cancer/drug_matching_results.json')

print('=' * 100)
print('HIRA 암질환 데이터 - 약제명 추출 및 약가 사전 매칭')
print('=' * 100)

# 1. 약가 사전 로드
print('\n[1] 약가 사전 로드')
print('-' * 100)

with open(DRUG_DICT_FILE, 'r', encoding='utf-8') as f:
    drug_dict = json.load(f)

print(f'약가 사전 로드 완료')
print(f'  총 검색 키: {len(drug_dict):,}개')
print(f'  파일 크기: {DRUG_DICT_FILE.stat().st_size / (1024*1024):.2f} MB')

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

# 3. 약제명 추출 함수
def extract_drug_candidates(text):
    """
    텍스트에서 약제명 후보 추출

    패턴:
    1. 제형 패턴: [한글/영문]주, [한글/영문]정, [한글/영문]캡슐
    2. 괄호 패턴: X(Y)

    필터링:
    - 최소 길이 2자 이상
    - 숫자로 시작하는 것 제외
    """
    candidates = set()

    if not text:
        return candidates

    # 패턴 1: 제형 패턴
    form_pattern = r'([가-힣A-Za-z][가-힣A-Za-z0-9]*)(주|정|캡슐|시럽|액|연고|크림|겔|산|과립)\b'
    for match in re.finditer(form_pattern, text):
        full_name = match.group(0)
        base_name = match.group(1)

        # 길이 체크 (전체가 3자 이상)
        if len(full_name) >= 3:
            candidates.add(full_name)
            # 베이스명도 추가 (제형 없이)
            if len(base_name) >= 2:
                candidates.add(base_name)

    # 패턴 2: 괄호 안 성분명
    # "옵디보주(니볼루맙)" → "니볼루맙"
    paren_pattern = r'\(([가-힣A-Za-z][가-힣A-Za-z0-9]*)\)'
    for match in re.finditer(paren_pattern, text):
        ingredient = match.group(1)
        if len(ingredient) >= 3 and not re.match(r'\d', ingredient):
            candidates.add(ingredient)

    return candidates

# 4. 전체 파일 처리
print('\n[3] 약제명 추출 및 약가 사전 매칭')
print('-' * 100)

stats = {
    'total_files': len(all_files),
    'total_candidates_raw': 0,
    'total_candidates_unique': 0,
    'matched_unique': 0,
    'unmatched_unique': 0,
    'matched_occurrences': 0,
    'unmatched_occurrences': 0,
    'board_stats': defaultdict(lambda: {
        'files': 0,
        'candidates_raw': 0,
        'matched': 0,
        'unmatched': 0
    })
}

all_candidates_counter = Counter()
matched_drugs = defaultdict(lambda: {'count': 0, 'sources': []})
unmatched_drugs = Counter()

file_results = []

for board, file_path in all_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        content = data.get('content', '')
        metadata = data.get('attachment_metadata', {})

        # 약제명 후보 추출
        candidates = extract_drug_candidates(content)

        file_matched = []
        file_unmatched = []

        for candidate in candidates:
            all_candidates_counter[candidate] += 1
            stats['total_candidates_raw'] += 1

            # 약가 사전 매칭
            if candidate in drug_dict:
                matched_drugs[candidate]['count'] += 1
                matched_drugs[candidate]['sources'].append({
                    'file': file_path.name,
                    'board': board,
                    'post_title': metadata.get('post_title', '')
                })
                file_matched.append(candidate)
                stats['matched_occurrences'] += 1
            else:
                unmatched_drugs[candidate] += 1
                file_unmatched.append(candidate)
                stats['unmatched_occurrences'] += 1

        # 파일별 결과
        file_results.append({
            'file': file_path.name,
            'board': board,
            'post_title': metadata.get('post_title', ''),
            'total_candidates': len(candidates),
            'matched_count': len(file_matched),
            'unmatched_count': len(file_unmatched),
            'matched_drugs': list(set(file_matched)),
            'unmatched_drugs': list(set(file_unmatched))
        })

        # 게시판별 통계
        stats['board_stats'][board]['files'] += 1
        stats['board_stats'][board]['candidates_raw'] += len(candidates)
        stats['board_stats'][board]['matched'] += len(file_matched)
        stats['board_stats'][board]['unmatched'] += len(file_unmatched)

    except Exception as e:
        print(f'오류 ({file_path.name}): {e}')
        continue

# 고유 약제명 수
stats['total_candidates_unique'] = len(all_candidates_counter)
stats['matched_unique'] = len(matched_drugs)
stats['unmatched_unique'] = len(unmatched_drugs)

print(f'\n✅ 처리 완료!')
print(f'\n전체 통계:')
print(f'  총 후보 추출: {stats["total_candidates_raw"]:,}개 (중복 포함)')
print(f'  고유 후보: {stats["total_candidates_unique"]:,}개')
print(f'\n매칭 결과:')
print(f'  매칭 성공 (고유): {stats["matched_unique"]:,}개 ({stats["matched_unique"]/stats["total_candidates_unique"]*100:.1f}%)')
print(f'  매칭 실패 (고유): {stats["unmatched_unique"]:,}개 ({stats["unmatched_unique"]/stats["total_candidates_unique"]*100:.1f}%)')
print(f'\n출현 빈도 기준:')
print(f'  매칭 성공: {stats["matched_occurrences"]:,}회')
print(f'  매칭 실패: {stats["unmatched_occurrences"]:,}회')

# 5. 게시판별 통계
print('\n[4] 게시판별 통계')
print('-' * 100)

for board, board_stat in stats['board_stats'].items():
    total = board_stat['matched'] + board_stat['unmatched']
    match_rate = board_stat['matched'] / total * 100 if total > 0 else 0
    print(f'\n{board}:')
    print(f'  파일 수: {board_stat["files"]}개')
    print(f'  후보 추출: {board_stat["candidates_raw"]}개')
    print(f'  매칭 성공: {board_stat["matched"]}개 ({match_rate:.1f}%)')
    print(f'  매칭 실패: {board_stat["unmatched"]}개')

# 6. 빈도 분석
print('\n[5] 빈도 분석')
print('-' * 100)

print('\n가장 많이 매칭된 약제명 (Top 30):')
matched_sorted = sorted(matched_drugs.items(), key=lambda x: x[1]['count'], reverse=True)
for i, (drug, info) in enumerate(matched_sorted[:30], 1):
    print(f'{i:2d}. {drug:30s} ({info["count"]:3d}회)')

print('\n가장 많이 미매칭된 후보 (Top 30):')
for i, (drug, count) in enumerate(unmatched_drugs.most_common(30), 1):
    print(f'{i:2d}. {drug:30s} ({count:3d}회)')

# 7. 노이즈 제거 효과
print('\n[6] 노이즈 제거 효과')
print('-' * 100)

noise_examples = ['개정', '인정', '예정', '공고개정', '급여인정', '설정', '배정']
removed_noise = []
for noise in noise_examples:
    if noise in unmatched_drugs:
        removed_noise.append((noise, unmatched_drugs[noise]))

if removed_noise:
    print('\n제거된 노이즈 (일반 명사):')
    for noise, count in removed_noise:
        print(f'  ❌ "{noise}" ({count}회) → 약가 사전에 없음 → 자동 제거')
else:
    print('노이즈 예시가 미매칭 목록에 없습니다.')

# 8. 결과 저장
print('\n[7] 결과 저장')
print('-' * 100)

result = {
    'summary': {
        'total_files': stats['total_files'],
        'total_candidates_raw': stats['total_candidates_raw'],
        'total_candidates_unique': stats['total_candidates_unique'],
        'matched_unique': stats['matched_unique'],
        'unmatched_unique': stats['unmatched_unique'],
        'match_rate_unique': stats['matched_unique'] / stats['total_candidates_unique'] * 100,
        'matched_occurrences': stats['matched_occurrences'],
        'unmatched_occurrences': stats['unmatched_occurrences']
    },
    'board_stats': dict(stats['board_stats']),
    'top_matched_drugs': [
        {'drug': drug, 'count': info['count']}
        for drug, info in matched_sorted[:100]
    ],
    'top_unmatched': [
        {'drug': drug, 'count': count}
        for drug, count in unmatched_drugs.most_common(100)
    ],
    'file_results': file_results[:50]  # 샘플 50개
}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'저장 완료: {OUTPUT_FILE}')
print(f'파일 크기: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB')

# 9. 최종 요약
print('\n' + '=' * 100)
print('✅ 약제명 추출 및 매칭 완료')
print('=' * 100)

match_rate = stats['matched_unique'] / stats['total_candidates_unique'] * 100
print(f'''
주요 결과:
- 총 추출: {stats["total_candidates_unique"]:,}개 고유 약제명 후보
- 매칭 성공: {stats["matched_unique"]:,}개 ({match_rate:.1f}%)
- 매칭 실패: {stats["unmatched_unique"]:,}개

노이즈 제거:
- 약가 사전 매칭으로 일반 명사 자동 제거
- 예: "개정", "인정", "예정" 등

다음 단계:
1. 미매칭 약제 검토 (실제 약제인지 확인)
2. 별칭 사전 구축 (필요 시)
3. 최종 매칭률 향상 방안 검토
''')
