"""
조문 간 참조 추출 스크립트

파싱된 조문에서 다른 조문에 대한 참조를 추출합니다.

입력: data/legal/parsed/*_parsed.json (파싱된 조문)
출력: data/legal/references/*_references.json (참조 관계)
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict


# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_DIR = PROJECT_ROOT / "data" / "legal" / "parsed"
OUTPUT_DIR = PROJECT_ROOT / "data" / "legal" / "references"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ReferenceExtractor:
    """조문 참조 추출기"""

    # 참조 패턴들
    PATTERNS = {
        # 1. 같은 법 내 조문 참조: 제1조, 제3조의2, 제1조제1항제1호
        'same_law_article': re.compile(
            r'제(\d+)조(?:의(\d+))?'
            r'(?:제(\d+)항)?'
            r'(?:제(\d+)호)?'
            r'(?:([가-힣])목)?'
        ),

        # 2. 타법 참조: 「국민건강보험법」 제1조
        'other_law_article': re.compile(
            r'「([^」]+)」\s*'
            r'제(\d+)조(?:의(\d+))?'
            r'(?:제(\d+)항)?'
            r'(?:제(\d+)호)?'
            r'(?:([가-힣])목)?'
        ),

        # 3. 같은 법/조/항 참조: 같은 법 제1조, 같은 조 제1항
        'same_reference': re.compile(
            r'같은\s+(법|조|항|호|목)\s*'
            r'제(\d+)[조항호]?'
        ),

        # 4. 이 법/그 조 등 대명사 참조
        'pronoun_reference': re.compile(
            r'(이|그|동)\s*(법|조|항|호|목)'
        ),

        # 5. 준용 패턴: "~을 준용한다"
        'apply_mutatis_mutandis': re.compile(
            r'([을를])\s*준용한다'
        ),

        # 6. 위임 패턴: "~에 따라", "~에서 정하는 바에 따라"
        'delegation': re.compile(
            r'(에\s*따라|에서\s*정하는\s*바에\s*따라)'
        ),

        # 7. 예외 패턴: "~에도 불구하고"
        'exception': re.compile(
            r'에도\s*불구하고'
        ),
    }

    # 참조 유형
    REFERENCE_TYPES = {
        'apply_mutatis_mutandis': '준용',
        'delegation': '위임',
        'exception': '예외',
        'definition': '정의',
        'requirement': '요건',
        'procedure': '절차',
        'general': '일반참조'
    }

    def __init__(self):
        self.current_law_id = None
        self.current_law_name = None
        self.article_map = {}  # article_number_normalized -> article_id

    def extract_from_parsed_law(self, parsed_file: Path) -> Dict:
        """파싱된 법령 파일에서 참조 추출"""
        with open(parsed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.current_law_name = data['law_name']
        articles = data['articles']

        # 조문 맵 구축 (빠른 검색용)
        self.article_map = {}
        for article in articles:
            if article['depth'] == 0:  # 조 레벨만
                norm_num = article['article_number_normalized']
                self.article_map[norm_num] = article['article_id']

        print(f"\n{'='*60}")
        print(f"참조 추출: {self.current_law_name}")
        print(f"조문 수: {len(articles)}개")
        print(f"{'='*60}\n")

        references = []
        stats = defaultdict(int)

        for article in articles:
            article_refs = self.extract_references_from_article(article)
            references.extend(article_refs)

            for ref in article_refs:
                stats[ref['reference_type']] += 1
                if ref['is_cross_law']:
                    stats['cross_law_references'] += 1

        print(f"\n[참조 통계]")
        print(f"  - 총 참조: {len(references)}개")
        for ref_type, count in sorted(stats.items()):
            print(f"  - {ref_type}: {count}개")

        return {
            'law_name': self.current_law_name,
            'total_references': len(references),
            'extracted_at': datetime.now().isoformat(),
            'statistics': dict(stats),
            'references': references
        }

    def extract_references_from_article(self, article: Dict) -> List[Dict]:
        """단일 조문에서 참조 추출"""
        text = article['full_text']
        if not text:
            return []

        references = []

        # 1. 타법 참조 추출
        for match in self.PATTERNS['other_law_article'].finditer(text):
            law_name, art_num, art_sub, clause, subclause, item = match.groups()

            ref_type = self._determine_reference_type(text, match.span())

            ref = {
                'source_article_id': article['article_id'],
                'source_article_number': article['article_number'],
                'source_full_path': self._get_full_path(article),
                'reference_text': match.group(0),
                'reference_type': ref_type,
                'is_cross_law': True,
                'target_law_name': law_name,
                'target_article_number': f"제{art_num}조" + (f"의{art_sub}" if art_sub else ""),
                'target_clause': int(clause) if clause else None,
                'target_subclause': int(subclause) if subclause else None,
                'target_item': item,
                'match_position': match.span(),
                'context': self._extract_context(text, match.span())
            }
            references.append(ref)

        # 2. 같은 법 내 조문 참조
        for match in self.PATTERNS['same_law_article'].finditer(text):
            # 타법 참조와 중복 제거 (앞에 「」가 있는 경우)
            if text[max(0, match.start()-10):match.start()].find('」') != -1:
                continue

            art_num, art_sub, clause, subclause, item = match.groups()

            # 타겟 조문 ID 찾기
            target_article_id = self._find_target_article(
                art_num, art_sub, clause, subclause, item
            )

            ref_type = self._determine_reference_type(text, match.span())

            ref = {
                'source_article_id': article['article_id'],
                'source_article_number': article['article_number'],
                'source_full_path': self._get_full_path(article),
                'reference_text': match.group(0),
                'reference_type': ref_type,
                'is_cross_law': False,
                'target_law_name': self.current_law_name,
                'target_article_id': target_article_id,
                'target_article_number': f"제{art_num}조" + (f"의{art_sub}" if art_sub else ""),
                'target_clause': int(clause) if clause else None,
                'target_subclause': int(subclause) if subclause else None,
                'target_item': item,
                'match_position': match.span(),
                'context': self._extract_context(text, match.span())
            }
            references.append(ref)

        # 3. "같은 법/조/항" 참조
        for match in self.PATTERNS['same_reference'].finditer(text):
            unit, number = match.groups()

            ref = {
                'source_article_id': article['article_id'],
                'source_article_number': article['article_number'],
                'source_full_path': self._get_full_path(article),
                'reference_text': match.group(0),
                'reference_type': '상대참조',
                'is_cross_law': False,
                'target_law_name': self.current_law_name,
                'same_unit': unit,
                'target_number': int(number),
                'match_position': match.span(),
                'context': self._extract_context(text, match.span())
            }
            references.append(ref)

        return references

    def _find_target_article(self, art_num: str, art_sub: Optional[str],
                            clause: Optional[str], subclause: Optional[str],
                            item: Optional[str]) -> Optional[str]:
        """타겟 조문 ID 찾기"""
        # 정규화된 조문 번호 생성
        if art_sub:
            norm_num = f"{int(art_num):03d}_{int(art_sub):02d}"
        else:
            norm_num = f"{int(art_num):03d}"

        # 조 레벨 ID 찾기
        base_id = self.article_map.get(norm_num)
        if not base_id:
            return None

        # 하위 조항까지 지정된 경우 ID 생성
        if clause:
            parts = [base_id, f"C{clause}"]
            if subclause:
                parts.append(f"S{subclause}")
            if item:
                parts.append(f"I{item}")
            return "_".join(parts)

        return base_id

    def _determine_reference_type(self, text: str, span: Tuple[int, int]) -> str:
        """참조 유형 판단"""
        # 참조 전후 문맥 확인 (앞뒤 50자)
        start, end = span
        context = text[max(0, start-50):min(len(text), end+50)]

        # 준용
        if self.PATTERNS['apply_mutatis_mutandis'].search(context):
            return '준용'

        # 위임
        if self.PATTERNS['delegation'].search(context):
            return '위임'

        # 예외
        if self.PATTERNS['exception'].search(context):
            return '예외'

        # 정의 (제2조 정의 조항 참조)
        if '정의' in context or '말한다' in context:
            return '정의'

        return '일반참조'

    def _get_full_path(self, article: Dict) -> str:
        """조문의 전체 경로 생성"""
        parts = [article['article_number']]

        if article['clause_number']:
            parts.append(f"제{article['clause_number']}항")
        if article['subclause_number']:
            parts.append(f"제{article['subclause_number']}호")
        if article['item_number']:
            parts.append(f"{article['item_number']}목")

        if article.get('article_title'):
            parts[0] += f"({article['article_title']})"

        return " ".join(parts)

    def _extract_context(self, text: str, span: Tuple[int, int], window: int = 30) -> str:
        """참조 주변 문맥 추출"""
        start, end = span
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)

        context = text[context_start:context_end]

        # 앞뒤 생략 표시
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."

        return context.strip()

    def save_references(self, references_data: Dict, law_name: str):
        """참조 데이터 저장"""
        # 파일명 정규화
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', law_name)
        output_file = OUTPUT_DIR / f"{safe_name}_references.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(references_data, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 저장 완료: {output_file}")


def main():
    """메인 실행"""
    extractor = ReferenceExtractor()

    # 파싱된 법령 파일 목록
    parsed_files = list(INPUT_DIR.glob("*_parsed.json"))

    print(f"발견된 파싱 파일: {len(parsed_files)}개\n")

    total_references = 0

    for parsed_file in parsed_files:
        try:
            # 참조 추출
            references_data = extractor.extract_from_parsed_law(parsed_file)
            total_references += references_data['total_references']

            # 저장
            extractor.save_references(
                references_data,
                references_data['law_name']
            )

        except Exception as e:
            print(f"[ERROR] 오류 ({parsed_file.name}): {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"전체 처리 완료")
    print(f"{'='*60}")
    print(f"- 처리 법령: {len(parsed_files)}개")
    print(f"- 총 참조: {total_references}개")
    print(f"- 출력 디렉토리: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
