"""HIRA 암질환 파싱 데이터에서 약제명 표기 패턴 분석

목적:
1. 약제명이 어떻게 표현되는지 파악 (제형 포함 여부, 괄호 사용 등)
2. 약제명 출현 위치 파악 (표, 본문, 제목)
3. 문맥 패턴 파악 (주변 단어, 표현 방식)

입력: data/hira_cancer/parsed/{announcement,pre_announcement,faq}/*.json
출력: data/hira_cancer/drug_mention_analysis.json
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import re
import sys

# UTF-8 출력
sys.stdout.reconfigure(encoding='utf-8')

PARSED_DIR = Path('data/hira_cancer/parsed')
OUTPUT_FILE = Path('data/hira_cancer/drug_mention_analysis.json')

print('=' * 100)
print('HIRA 암질환 데이터 - 약제명 표기 패턴 분석')
print('=' * 100)

# 1. 파일 목록 수집
print('\n[1] 파싱 파일 수집')
print('-' * 100)

all_files = []
for board in ['announcement', 'pre_announcement', 'faq']:
    board_dir = PARSED_DIR / board
    files = list(board_dir.glob('*.json'))
    all_files.extend([(board, f) for f in files])
    print(f'{board}: {len(files)}개 파일')

print(f'\n총 {len(all_files)}개 파일')

# 2. 약제명 후보 추출 함수
def extract_drug_candidates(text):
    """
    텍스트에서 약제명 후보 추출

    패턴:
    1. X주, X정, X캡슐 (제형 패턴)
    2. X(Y) - 괄호 패턴 (제품명(성분명))
    3. 표 내 약제명 컬럼
    """
    candidates = []

    if not text:
        return candidates

    # 패턴 1: 제형 패턴 (한글 + 제형)
    # 예: "옵디보주", "키트루다주", "타세바정"
    form_pattern = r'([가-힣A-Za-z]+)(주|정|캡슐|시럽|액|연고|크림|겔)\b'
    for match in re.finditer(form_pattern, text):
        full_name = match.group(0)  # "옵디보주"
        base_name = match.group(1)  # "옵디보"
        form = match.group(2)       # "주"

        candidates.append({
            'text': full_name,
            'base_name': base_name,
            'form': form,
            'type': '제형_패턴',
            'context': text[max(0, match.start()-20):min(len(text), match.end()+20)]
        })

    # 패턴 2: 괄호 패턴
    # 예: "옵디보(니볼루맙)", "키트루다주(펨브롤리주맙)"
    paren_pattern = r'([가-힣A-Za-z0-9]+(?:주|정|캡슐)?)\s*\(([^)]+)\)'
    for match in re.finditer(paren_pattern, text):
        product = match.group(1)
        ingredient = match.group(2)

        candidates.append({
            'text': match.group(0),
            'product': product,
            'ingredient': ingredient,
            'type': '괄호_패턴',
            'context': text[max(0, match.start()-20):min(len(text), match.end()+20)]
        })

    # 패턴 3: Markdown 표 감지
    # | 약제명 | ... | 형식
    if '|' in text and ('약제명' in text or '성분명' in text or '제품명' in text):
        candidates.append({
            'text': '(표 감지)',
            'type': '표_형식',
            'context': 'Markdown table detected'
        })

    return candidates

# 3. 전체 파일 분석
print('\n[2] 약제명 후보 추출')
print('-' * 100)

all_candidates = []
board_stats = defaultdict(lambda: {'files': 0, 'candidates': 0})
pattern_counter = Counter()

for board, file_path in all_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        content = data.get('content', '')
        candidates = extract_drug_candidates(content)

        for candidate in candidates:
            candidate['source_file'] = file_path.name
            candidate['board'] = board
            all_candidates.append(candidate)
            pattern_counter[candidate['type']] += 1

        board_stats[board]['files'] += 1
        board_stats[board]['candidates'] += len(candidates)

    except Exception as e:
        print(f'오류 ({file_path.name}): {e}')
        continue

print(f'\n총 약제명 후보: {len(all_candidates)}개')
print(f'\n게시판별 통계:')
for board, stats in board_stats.items():
    avg = stats['candidates'] / stats['files'] if stats['files'] > 0 else 0
    print(f'  {board}: {stats["candidates"]:,}개 (평균 {avg:.1f}개/파일)')

print(f'\n패턴별 통계:')
for pattern, count in pattern_counter.most_common():
    print(f'  {pattern}: {count:,}개 ({count/len(all_candidates)*100:.1f}%)')

# 4. 빈도 분석
print('\n[3] 약제명 후보 빈도 분석')
print('-' * 100)

# 제형 패턴 빈도
form_pattern_counter = Counter()
for c in all_candidates:
    if c['type'] == '제형_패턴':
        form_pattern_counter[c['text']] += 1

print('\n가장 많이 출현한 제형 패턴 (Top 30):')
for i, (name, count) in enumerate(form_pattern_counter.most_common(30), 1):
    print(f'{i:2d}. {name:30s} ({count:3d}회)')

# 괄호 패턴 빈도
paren_pattern_counter = Counter()
for c in all_candidates:
    if c['type'] == '괄호_패턴':
        paren_pattern_counter[c['text']] += 1

print('\n가장 많이 출현한 괄호 패턴 (Top 30):')
for i, (name, count) in enumerate(paren_pattern_counter.most_common(30), 1):
    print(f'{i:2d}. {name:50s} ({count:3d}회)')

# 5. 샘플 출력
print('\n[4] 문맥 샘플 (제형 패턴)')
print('-' * 100)

for candidate in all_candidates[:10]:
    if candidate['type'] == '제형_패턴':
        print(f"\n약제: {candidate['text']}")
        print(f"파일: {candidate['source_file']}")
        print(f"문맥: ...{candidate['context']}...")

# 6. JSON 저장
print('\n[5] 결과 저장')
print('-' * 100)

result = {
    'total_files': len(all_files),
    'total_candidates': len(all_candidates),
    'board_stats': dict(board_stats),
    'pattern_stats': dict(pattern_counter),
    'top_form_patterns': [
        {'name': name, 'count': count}
        for name, count in form_pattern_counter.most_common(50)
    ],
    'top_paren_patterns': [
        {'name': name, 'count': count}
        for name, count in paren_pattern_counter.most_common(50)
    ],
    'sample_candidates': all_candidates[:100]  # 샘플 100개만
}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'저장 완료: {OUTPUT_FILE}')
print(f'파일 크기: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB')

print('\n' + '=' * 100)
print('✅ 약제명 패턴 분석 완료')
print('=' * 100)

print(f'''
주요 발견:
- 총 {len(all_candidates):,}개 약제명 후보 추출
- 제형 패턴: {pattern_counter.get("제형_패턴", 0):,}개
- 괄호 패턴: {pattern_counter.get("괄호_패턴", 0):,}개
- 표 형식: {pattern_counter.get("표_형식", 0):,}개

다음 단계:
1. 약제명 추출 규칙 개발 (패턴 기반)
2. 약가 사전과 매칭 테스트
''')
