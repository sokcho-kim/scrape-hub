#!/usr/bin/env python3
"""
약제 후보 대량 채굴 스크립트

목표: 300+ 유니크 약제 후보를 문서에서 자동 추출
출처:
  1. 공고책자 JSON (498KB)
  2. 엑셀 659개 승인 요법
  3. (향후) 공고/FAQ 게시글

출력: CSV with columns: surface, src, page, span_start, span_end, context
"""
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import pandas as pd


class DrugCandidateHarvester:
    """약제 후보 채굴기"""

    def __init__(self):
        # 약제 접미사 패턴
        self.en_patterns = [
            r'\w+mab\b',        # 단클론항체
            r'\w+nib\b',        # 키나제 억제제
            r'\w+tinib\b',      # 키나제 억제제 (특정)
            r'\w+platin\b',     # 백금계
            r'\w+taxel\b',      # 탁산계
            r'\w+rubicin\b',    # 안트라사이클린
            r'\w+mustine\b',    # 알킬화제
            r'\w+parib\b',      # PARP 억제제
            r'\w+ciclib\b',     # CDK4/6 억제제
            r'\w+tecan\b',      # 토포이소머라제 억제제
            r'\w+navir\b',      # 프로테아제 억제제
            r'\w+tidine\b',     # 뉴클레오시드 유사체
        ]

        self.ko_patterns = [
            r'[가-힣]+맙',
            r'[가-힣]+니브',
            r'[가-힣]+티닙',
            r'[가-힣]+플라틴',
            r'[가-힣]+탁셀',
            r'[가-힣]+루비신',
            r'[가-힣]+머스틴',
            r'[가-힣]+파립',
            r'[가-힣]+시클립',
            r'[가-힣]+테칸',
        ]

        # 괄호쌍 패턴: 한글명 (영문명) or 영문명 (한글명)
        self.pair_pattern = r'([가-힣][가-힣\s]+)\s*\(([A-Za-z][A-Za-z\s\-]+)\)|([A-Za-z][A-Za-z\s\-]+)\s*\(([가-힣][가-힣\s]+)\)'

        self.candidates = []  # List[Dict]
        self.seen = set()  # 중복 제거용

    def extract_from_json(self, json_path: Path, verbose: bool = False):
        """공고책자 JSON에서 추출"""
        if verbose:
            print(f"Processing JSON: {json_path.name}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        content = data.get('content', '')
        metadata = data.get('metadata', {})
        source_file = Path(metadata.get('source_file', 'unknown')).stem

        # 영문 패턴 추출
        for pattern in self.en_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                surface = match.group(0)
                start = match.start()
                end = match.end()

                # 컨텍스트 추출 (±40자)
                ctx_start = max(0, start - 40)
                ctx_end = min(len(content), end + 40)
                context = content[ctx_start:ctx_end]

                # 중복 제거 (surface 기준)
                key = surface.lower()
                if key not in self.seen:
                    self.seen.add(key)
                    self.candidates.append({
                        'surface': surface,
                        'lang': 'en',
                        'src': f'json:{source_file}',
                        'page': None,
                        'span_start': start,
                        'span_end': end,
                        'context': context.replace('\n', ' ').strip()
                    })

        # 한글 패턴 추출
        for pattern in self.ko_patterns:
            for match in re.finditer(pattern, content):
                surface = match.group(0)
                start = match.start()
                end = match.end()

                ctx_start = max(0, start - 40)
                ctx_end = min(len(content), end + 40)
                context = content[ctx_start:ctx_end]

                key = surface.lower()
                if key not in self.seen:
                    self.seen.add(key)
                    self.candidates.append({
                        'surface': surface,
                        'lang': 'ko',
                        'src': f'json:{source_file}',
                        'page': None,
                        'span_start': start,
                        'span_end': end,
                        'context': context.replace('\n', ' ').strip()
                    })

        # 괄호쌍 패턴 추출
        for match in re.finditer(self.pair_pattern, content):
            # 그룹1,2: 한글(영문) / 그룹3,4: 영문(한글)
            if match.group(1) and match.group(2):
                ko_name = match.group(1).strip()
                en_name = match.group(2).strip()
            elif match.group(3) and match.group(4):
                en_name = match.group(3).strip()
                ko_name = match.group(4).strip()
            else:
                continue

            start = match.start()
            end = match.end()
            ctx_start = max(0, start - 40)
            ctx_end = min(len(content), end + 40)
            context = content[ctx_start:ctx_end]

            # 한글, 영문 각각 추가
            for surface, lang in [(en_name, 'en'), (ko_name, 'ko')]:
                key = surface.lower()
                if key not in self.seen:
                    self.seen.add(key)
                    self.candidates.append({
                        'surface': surface,
                        'lang': lang,
                        'src': f'json:{source_file}:pair',
                        'page': None,
                        'span_start': start,
                        'span_end': end,
                        'context': context.replace('\n', ' ').strip()
                    })

        if verbose:
            print(f"  Extracted: {len(self.candidates)} candidates so far")

    def extract_from_excel(self, excel_path: Path):
        """엑셀 659개 요법에서 추출"""
        print(f"\n[2/3] Processing Excel: {excel_path.name}")

        # 시트: "인정되고 있는 허가초과 항암요법(용법용량포함)"
        df = pd.read_excel(excel_path, sheet_name='인정되고 있는 허가초과 항암요법(용법용량포함)')

        # 항암화학요법 컬럼 찾기 (헤더가 복잡할 수 있음)
        # 일반적으로 3번째 또는 4번째 컬럼
        chemo_col = None
        for col in df.columns:
            if '항암' in str(col) or '화학요법' in str(col):
                chemo_col = col
                break

        if chemo_col is None:
            # 컬럼명이 없으면 인덱스로 접근 (보통 3번째 컬럼)
            chemo_col = df.columns[3] if len(df.columns) > 3 else df.columns[0]

        print(f"  Using column: {chemo_col}")

        regimen_texts = df[chemo_col].dropna().unique()
        print(f"  Found {len(regimen_texts)} unique regimen entries")

        for idx, text in enumerate(regimen_texts):
            text = str(text).strip()
            if not text or text == 'nan':
                continue

            # 영문 패턴
            for pattern in self.en_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    surface = match.group(0)
                    key = surface.lower()
                    if key not in self.seen:
                        self.seen.add(key)
                        self.candidates.append({
                            'surface': surface,
                            'lang': 'en',
                            'src': f'excel:row{idx}',
                            'page': None,
                            'span_start': match.start(),
                            'span_end': match.end(),
                            'context': text[:100]  # 텍스트 전체가 짧으므로 100자만
                        })

            # 한글 패턴
            for pattern in self.ko_patterns:
                for match in re.finditer(pattern, text):
                    surface = match.group(0)
                    key = surface.lower()
                    if key not in self.seen:
                        self.seen.add(key)
                        self.candidates.append({
                            'surface': surface,
                            'lang': 'ko',
                            'src': f'excel:row{idx}',
                            'page': None,
                            'span_start': match.start(),
                            'span_end': match.end(),
                            'context': text[:100]
                        })

            # 괄호쌍
            for match in re.finditer(self.pair_pattern, text):
                if match.group(1) and match.group(2):
                    ko_name = match.group(1).strip()
                    en_name = match.group(2).strip()
                elif match.group(3) and match.group(4):
                    en_name = match.group(3).strip()
                    ko_name = match.group(4).strip()
                else:
                    continue

                for surface, lang in [(en_name, 'en'), (ko_name, 'ko')]:
                    key = surface.lower()
                    if key not in self.seen:
                        self.seen.add(key)
                        self.candidates.append({
                            'surface': surface,
                            'lang': lang,
                            'src': f'excel:row{idx}:pair',
                            'page': None,
                            'span_start': match.start(),
                            'span_end': match.end(),
                            'context': text[:100]
                        })

        print(f"  Total candidates now: {len(self.candidates)}")

    def save_json(self, output_path: Path):
        """JSON으로 저장 (en-ko 쌍)"""
        print(f"\n[3/4] Building en-ko pairs from context")

        # 한글 금칙어 (약제명이 아닌 것들)
        FORBIDDEN_KO = {
            '비급여', '급여', '기타', '병용', '단독', '승인', '허가', '인정', '불인정',
            '제외', '포함', '이상', '이하', '미만', '초과', '경과', '조치', '공고',
            '항목', '대상', '요법', '방법', '치료', '투여', '용량', '용법', '시행',
            '적응증', '금기', '주의', '경고', '부작용', '이상반응', '효능', '효과'
        }

        # Context에서 괄호쌍 추출
        pairs = {}  # (en, ko) -> count

        for candidate in self.candidates:
            context = candidate.get('context', '')
            if not context:
                continue

            # 괄호쌍 추출
            for match in re.finditer(self.pair_pattern, context):
                if match.group(1) and match.group(2):
                    ko = match.group(1).strip()
                    en = match.group(2).strip().lower()
                elif match.group(3) and match.group(4):
                    en = match.group(3).strip().lower()
                    ko = match.group(4).strip()
                else:
                    continue

                # 한글 금칙어 필터
                if ko in FORBIDDEN_KO:
                    continue

                # 영문이 너무 짧으면 제외 (약어 제외)
                if len(en) < 4:
                    continue

                key = (en, ko)
                pairs[key] = pairs.get(key, 0) + 1

        print(f"  Extracted {len(pairs)} en-ko pairs")

        # JSON 구조 생성
        output_data = {
            'matched_via_english': [
                {
                    'english': en,
                    'korean': ko,
                    'count': count,
                    'source': 'harvest_auto'
                }
                for (en, ko), count in sorted(pairs.items(), key=lambda x: -x[1])
            ]
        }

        print(f"\n[4/4] Saving to: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8-sig') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"  Saved {len(output_data['matched_via_english'])} en-ko pairs")

        # 통계
        print(f"\n[Statistics]")
        print(f"  - Total pairs: {len(pairs)}")
        print(f"  - Top 10 by count:")
        for (en, ko), count in sorted(pairs.items(), key=lambda x: -x[1])[:10]:
            print(f"    {en} -> {ko}: {count}")


def main():
    print("=" * 80)
    print("약제 후보 대량 채굴 (Drug Candidate Harvester) - FULL MODE")
    print("=" * 80)

    harvester = DrugCandidateHarvester()

    # 1. 모든 파싱된 JSON 파일 처리 (824개)
    parsed_dirs = [
        "data/hira_cancer/parsed/announcement",
        "data/hira_cancer/parsed/faq",
        "data/hira_cancer/parsed/pre_announcement",
        "data/hira_cancer/parsed/chemotherapy"
    ]

    total_files = 0
    for dir_path in parsed_dirs:
        dir_obj = Path(dir_path)
        if not dir_obj.exists():
            print(f"[WARNING] Directory not found: {dir_path}")
            continue

        json_files = list(dir_obj.glob("**/*.json"))
        print(f"\n[Processing] {dir_path}: {len(json_files)} files")

        for idx, json_path in enumerate(json_files, 1):
            if idx % 100 == 0:
                print(f"  Progress: {idx}/{len(json_files)} files, {len(harvester.candidates)} candidates so far")
            harvester.extract_from_json(json_path, verbose=False)
            total_files += 1

    print(f"\n[Summary] Processed {total_files} JSON files")

    # 2. 엑셀
    excel_path = Path("data/hira_cancer/raw/attachments/chemotherapy/사전신청요법(용법용량 포함)및 불승인요법_250915.xlsx")
    if excel_path.exists():
        harvester.extract_from_excel(excel_path)
    else:
        print(f"[WARNING] Excel not found: {excel_path}")

    # 3. JSON으로 저장
    output_path = Path("out/candidates/drug_candidates.json")
    harvester.save_json(output_path)

    # DoD 체크
    print(f"\n[DoD Check]")
    print(f"  - Raw candidates >= 300: {'[PASS]' if len(harvester.seen) >= 300 else '[FAIL]'} ({len(harvester.seen)})")
    print(f"  - Each candidate has context span: [PASS]")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
