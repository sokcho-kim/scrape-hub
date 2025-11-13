"""
법령 조문 파싱 스크립트

법령 텍스트에서 조/항/호/목 구조를 추출하고 구조화합니다.

입력: data/likms/laws/*.json (법령 원문)
출력: data/legal/parsed/*.json (파싱된 조문 구조)
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib


# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_DIR = PROJECT_ROOT / "data" / "likms" / "laws"
OUTPUT_DIR = PROJECT_ROOT / "data" / "legal" / "parsed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ArticleParser:
    """법령 조문 파서"""

    # 조문 패턴
    ARTICLE_PATTERN = r'^제(\d+)조(?:의(\d+))?\s*\(([^)]+)\)\s*$'  # 제1조(목적), 제3조의2(난민에 대한 특례)

    # 항 패턴 (원문자: ①②③...)
    CLAUSE_PATTERN = r'^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮])\s+'

    # 호 패턴 (1. 또는 1호)
    SUBCLAUSE_PATTERN = r'^(\d+)\.\s+'

    # 목 패턴 (가. 또는 가목)
    ITEM_PATTERN = r'^([가-힣])\.\s+'

    # 조문 참조 패턴
    REFERENCE_PATTERNS = [
        r'제(\d+)조(?:의(\d+))?(?:제(\d+)항)?(?:제(\d+)호)?(?:([가-힣])목)?',  # 제1조, 제3조의2, 제1조제1항
        r'「([^」]+)」\s*제(\d+)조',  # 타법 참조: 「국민건강보험법」 제1조
        r'같은\s+(법|조|항|호)\s*제(\d+)[조항호목]',  # 같은 법 제1조
        r'(이|그|동)\s*(법|조|항|호|목)',  # 이 법, 그 조
    ]

    def __init__(self):
        self.current_law_id = None
        self.current_article_number = None
        self.current_clause_number = None
        self.current_subclause_number = None
        self.articles = []

    def generate_article_id(self, law_id: str, article_num: str,
                          clause: Optional[str] = None,
                          subclause: Optional[str] = None,
                          item: Optional[str] = None) -> str:
        """조문 고유 ID 생성"""
        parts = [f"ART_{law_id}", article_num]
        if clause:
            parts.append(f"C{clause}")
        if subclause:
            parts.append(f"S{subclause}")
        if item:
            parts.append(f"I{item}")
        return "_".join(parts)

    def normalize_article_number(self, main_num: str, sub_num: Optional[str] = None) -> str:
        """조문 번호 정규화: 제1조, 제3조의2 등"""
        if sub_num:
            return f"{int(main_num):03d}_{int(sub_num):02d}"
        return f"{int(main_num):03d}"

    def parse_law_content(self, law_data: Dict) -> List[Dict]:
        """법령 전문에서 조문 추출"""
        law_name = law_data.get("title", "Unknown")
        law_type = law_data.get("type", "법률")
        content = law_data.get("content", "")

        # law_id 생성 (파일명 기반)
        law_id = self._generate_law_id(law_name, law_type)
        self.current_law_id = law_id

        print(f"\n{'='*60}")
        print(f"법령 파싱: {law_name} ({law_type})")
        print(f"Law ID: {law_id}")
        print(f"{'='*60}\n")

        # 줄 단위로 분리
        lines = content.split('\n')

        articles = []
        current_article = None
        current_clause = None
        current_subclause = None
        current_item = None

        buffer = []  # 현재 조문의 텍스트 버퍼

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # 1. 조 매칭
            article_match = re.match(self.ARTICLE_PATTERN, line)
            if article_match:
                # 이전 조문 저장
                if current_article:
                    current_article['full_text'] = '\n'.join(buffer).strip()
                    articles.append(current_article)
                    buffer = []

                main_num, sub_num, title = article_match.groups()
                article_number = self.normalize_article_number(main_num, sub_num)
                article_id = self.generate_article_id(law_id, article_number)

                current_article = {
                    'article_id': article_id,
                    'law_id': law_id,
                    'law_name': law_name,
                    'article_number': f"제{main_num}조" + (f"의{sub_num}" if sub_num else ""),
                    'article_number_normalized': article_number,
                    'article_title': title,
                    'depth': 0,
                    'parent_article_id': None,
                    'clause_number': None,
                    'subclause_number': None,
                    'item_number': None,
                    'full_text': '',
                    'line_start': line_num,
                    'line_end': None,
                    'children': []
                }

                self.current_article_number = article_number
                current_clause = None
                current_subclause = None
                current_item = None

                print(f"  조문 발견: {current_article['article_number']} ({title})")
                continue

            # 현재 조문이 없으면 스킵 (전문, 부칙 등)
            if not current_article:
                continue

            # 2. 항 매칭
            clause_match = re.match(self.CLAUSE_PATTERN, line)
            if clause_match:
                clause_symbol = clause_match.group(1)
                clause_number = self._clause_symbol_to_number(clause_symbol)

                # 항을 별도 article로 저장
                clause_id = self.generate_article_id(
                    law_id, article_number, str(clause_number)
                )

                clause_article = {
                    'article_id': clause_id,
                    'law_id': law_id,
                    'law_name': law_name,
                    'article_number': current_article['article_number'],
                    'article_number_normalized': article_number,
                    'article_title': current_article['article_title'],
                    'depth': 1,
                    'parent_article_id': current_article['article_id'],
                    'clause_number': clause_number,
                    'subclause_number': None,
                    'item_number': None,
                    'full_text': line[len(clause_match.group(0)):],  # 항 기호 제거
                    'line_start': line_num,
                    'line_end': line_num,
                    'children': []
                }

                articles.append(clause_article)
                current_article['children'].append(clause_id)
                current_clause = clause_article
                current_subclause = None
                current_item = None
                continue

            # 3. 호 매칭
            subclause_match = re.match(self.SUBCLAUSE_PATTERN, line)
            if subclause_match and current_clause:
                subclause_number = int(subclause_match.group(1))

                subclause_id = self.generate_article_id(
                    law_id, article_number,
                    str(current_clause['clause_number']),
                    str(subclause_number)
                )

                subclause_article = {
                    'article_id': subclause_id,
                    'law_id': law_id,
                    'law_name': law_name,
                    'article_number': current_article['article_number'],
                    'article_number_normalized': article_number,
                    'article_title': current_article['article_title'],
                    'depth': 2,
                    'parent_article_id': current_clause['article_id'],
                    'clause_number': current_clause['clause_number'],
                    'subclause_number': subclause_number,
                    'item_number': None,
                    'full_text': line[len(subclause_match.group(0)):],
                    'line_start': line_num,
                    'line_end': line_num,
                    'children': []
                }

                articles.append(subclause_article)
                current_clause['children'].append(subclause_id)
                current_subclause = subclause_article
                current_item = None
                continue

            # 4. 목 매칭
            item_match = re.match(self.ITEM_PATTERN, line)
            if item_match and current_subclause:
                item_letter = item_match.group(1)

                item_id = self.generate_article_id(
                    law_id, article_number,
                    str(current_clause['clause_number']),
                    str(current_subclause['subclause_number']),
                    item_letter
                )

                item_article = {
                    'article_id': item_id,
                    'law_id': law_id,
                    'law_name': law_name,
                    'article_number': current_article['article_number'],
                    'article_number_normalized': article_number,
                    'article_title': current_article['article_title'],
                    'depth': 3,
                    'parent_article_id': current_subclause['article_id'],
                    'clause_number': current_clause['clause_number'],
                    'subclause_number': current_subclause['subclause_number'],
                    'item_number': item_letter,
                    'full_text': line[len(item_match.group(0)):],
                    'line_start': line_num,
                    'line_end': line_num,
                    'children': []
                }

                articles.append(item_article)
                current_subclause['children'].append(item_id)
                current_item = item_article
                continue

            # 5. 일반 텍스트 (버퍼에 추가)
            buffer.append(line)

        # 마지막 조문 저장
        if current_article and buffer:
            current_article['full_text'] = '\n'.join(buffer).strip()
            articles.append(current_article)

        print(f"\n총 {len(articles)}개 조문 추출 완료")
        return articles

    def _generate_law_id(self, law_name: str, law_type: str) -> str:
        """법령 ID 생성"""
        # 법령명 해시 사용
        name_hash = hashlib.md5(law_name.encode('utf-8')).hexdigest()[:8]
        return f"LAW_{name_hash.upper()}"

    def _clause_symbol_to_number(self, symbol: str) -> int:
        """항 기호를 숫자로 변환"""
        clause_symbols = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮'
        return clause_symbols.index(symbol) + 1

    def extract_references(self, text: str) -> List[Dict]:
        """조문에서 참조 추출"""
        references = []

        for pattern in self.REFERENCE_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                ref = {
                    'reference_text': match.group(0),
                    'match_position': match.span(),
                    'groups': match.groups()
                }
                references.append(ref)

        return references

    def save_parsed_articles(self, articles: List[Dict], law_name: str):
        """파싱된 조문 저장"""
        # 파일명 정규화
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', law_name)
        output_file = OUTPUT_DIR / f"{safe_name}_parsed.json"

        output_data = {
            'law_name': law_name,
            'total_articles': len(articles),
            'parsed_at': datetime.now().isoformat(),
            'articles': articles
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 저장 완료: {output_file}")
        print(f"   - 조문 수: {len(articles)}개")

        # 통계 출력
        depth_counts = {}
        for article in articles:
            depth = article['depth']
            depth_counts[depth] = depth_counts.get(depth, 0) + 1

        print(f"\n   [조문 구조]")
        print(f"   - 조: {depth_counts.get(0, 0)}개")
        print(f"   - 항: {depth_counts.get(1, 0)}개")
        print(f"   - 호: {depth_counts.get(2, 0)}개")
        print(f"   - 목: {depth_counts.get(3, 0)}개")


def main():
    """메인 실행"""
    parser = ArticleParser()

    # 모든 법령 파일 처리
    law_files = list(INPUT_DIR.glob("*.json"))

    print(f"발견된 법령 파일: {len(law_files)}개\n")

    total_articles = 0

    for law_file in law_files:
        try:
            with open(law_file, 'r', encoding='utf-8') as f:
                law_data = json.load(f)

            # 조문 파싱
            articles = parser.parse_law_content(law_data)
            total_articles += len(articles)

            # 저장
            parser.save_parsed_articles(articles, law_data.get('title', law_file.stem))

        except Exception as e:
            print(f"[ERROR] 오류 ({law_file.name}): {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"전체 처리 완료")
    print(f"{'='*60}")
    print(f"- 처리 법령: {len(law_files)}개")
    print(f"- 총 조문: {total_articles}개")
    print(f"- 출력 디렉토리: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
