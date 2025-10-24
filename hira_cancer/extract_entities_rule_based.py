"""규칙 기반 엔티티 추출 (Rule-based Entity Extraction)

Markdown 파싱 결과에서 구조화된 데이터 추출
- LLM 없이 정규식 + 패턴 매칭
- 완전 무료, 빠름
"""
import json
import re
import sys
import codecs
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class RuleBasedEntityExtractor:
    """규칙 기반 엔티티 추출기"""

    def __init__(self):
        self.entities = defaultdict(list)
        self.relations = []

    def extract_from_file(self, parsed_json_path: Path) -> Dict[str, Any]:
        """단일 파싱 파일에서 엔티티 추출"""
        with open(parsed_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        content = data.get('content', '')
        metadata = data.get('attachment_metadata', {})

        result = {
            'metadata': metadata,
            'entities': {},
            'relations': []
        }

        # 1. 암종류 추출
        cancers = self.extract_cancers(content)
        result['entities']['cancers'] = cancers

        # 2. 약제 정보 추출 (표에서)
        drugs = self.extract_drugs_from_tables(content)
        result['entities']['drugs'] = drugs

        # 3. 제한사항 추출
        restrictions = self.extract_restrictions(content)
        result['entities']['restrictions'] = restrictions

        # 4. Q&A 추출
        qas = self.extract_qas(content)
        result['entities']['qas'] = qas

        # 5. 관계 생성
        result['relations'] = self.generate_relations(result['entities'], metadata)

        return result

    def extract_cancers(self, content: str) -> List[Dict[str, str]]:
        """암종류 추출

        패턴: [숫자] 암종류명(영문명)
        예: [28] 비호지킨림프종(Non-Hodgkin's Lymphoma)
        """
        cancers = []
        pattern = r'\[(\d+)\]\s*([^\(]+)\(([^\)]+)\)'

        for match in re.finditer(pattern, content):
            cancer_id = match.group(1)
            korean_name = match.group(2).strip()
            english_name = match.group(3).strip()

            cancers.append({
                'id': cancer_id,
                'korean_name': korean_name,
                'english_name': english_name,
                'code': f'CANCER_{cancer_id}'
            })

        return cancers

    def extract_drugs_from_tables(self, content: str) -> List[Dict[str, Any]]:
        """Markdown 표에서 약제 정보 추출

        표 형식:
        | 연번 | 항암요법 | 투여대상 | 투여단계 |
        | 18 | tisagenlecleucel주 | ... | 3차 이상 |
        """
        drugs = []

        # 개선된 표 파싱: 줄 단위로 처리
        lines = content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 표 헤더 찾기
            if line.startswith('|') and '항암요법' in line:
                headers = [h.strip() for h in line.split('|')[1:-1]]

                # 구분선 건너뛰기
                i += 1
                if i >= len(lines):
                    break

                # 데이터 행 파싱
                i += 1
                while i < len(lines):
                    data_line = lines[i].strip()

                    if not data_line.startswith('|'):
                        break

                    # 빈 행 체크
                    if data_line == '|':
                        i += 1
                        continue

                    cells = [c.strip() for c in data_line.split('|')[1:-1]]

                    # 셀 개수 체크 (유연하게 처리)
                    if len(cells) < len(headers):
                        # 빈 셀 추가
                        cells.extend([''] * (len(headers) - len(cells)))
                    elif len(cells) > len(headers):
                        # 초과 셀 제거
                        cells = cells[:len(headers)]

                    row_data = dict(zip(headers, cells))

                    # 약제명 추출
                    drug_raw = row_data.get('항암요법', '').strip()

                    if drug_raw and drug_raw != '---':
                        # 주석 번호 제거 (예: "tisagenlecleucel주 6주 7" → "tisagenlecleucel주")
                        # 패턴: 숫자 + "주" 반복 제거
                        drug_clean = re.sub(r'\s+\d+(?:주\s*\d+)*$', '', drug_raw).strip()

                        drug_info = {
                            'name': drug_clean,
                            'indication': row_data.get('투여대상', ''),
                            'line': row_data.get('투여단계', ''),
                            'regimen': row_data.get('투여요법', '-'),
                            'raw_name': drug_raw
                        }

                        drugs.append(drug_info)

                    i += 1

            i += 1

        return drugs

    def extract_restrictions(self, content: str) -> List[Dict[str, str]]:
        """제한사항 추출

        패턴:
        - ▪ 급여인정 기간: ...
        - 주6. CAR-T 세포치료제...
        """
        restrictions = []

        # ▪ 패턴 (bullet point)
        bullet_pattern = r'▪\s*([^:]+):\s*([^\n]+(?:\n(?!▪)[^\n]+)*)'
        for match in re.finditer(bullet_pattern, content):
            category = match.group(1).strip()
            description = match.group(2).strip()

            restrictions.append({
                'type': 'guideline',
                'category': category,
                'description': description
            })

        # 주석 패턴
        note_pattern = r'주(\d+)\.\s*([^\n]+(?:\n(?!주\d)[^\n]+)*)'
        for match in re.finditer(note_pattern, content):
            note_id = match.group(1)
            description = match.group(2).strip()

            restrictions.append({
                'type': 'note',
                'note_id': f'주{note_id}',
                'description': description
            })

        return restrictions

    def extract_qas(self, content: str) -> List[Dict[str, str]]:
        """Q&A 추출

        패턴:
        # 질문 1 투여대상 기준 시점은...
        # <답변>
        ○ 약물 투입 전이...
        """
        qas = []

        # 질문 패턴
        qa_pattern = r'질문\s*(\d+)\s+([^\n]+)\n+#\s*<답변>\s*\n+(○\s*[^\n]+(?:\n[^\n#]+)*)'

        for match in re.finditer(qa_pattern, content):
            question_id = match.group(1)
            question = match.group(2).strip()
            answer = match.group(3).strip()

            # 답변에서 ○ 제거
            answer_clean = re.sub(r'^○\s*', '', answer).strip()

            qas.append({
                'question_id': question_id,
                'question': question,
                'answer': answer_clean
            })

        return qas

    def generate_relations(self, entities: Dict[str, List], metadata: Dict) -> List[Dict[str, str]]:
        """엔티티 간 관계 생성"""
        relations = []

        # Drug → Cancer (TREATS)
        for drug in entities.get('drugs', []):
            for cancer in entities.get('cancers', []):
                # 간단한 휴리스틱: 같은 문서에 있으면 관련
                relations.append({
                    'type': 'TREATS',
                    'source': drug['name'],
                    'source_type': 'Drug',
                    'target': cancer['korean_name'],
                    'target_type': 'Cancer',
                    'properties': {
                        'indication': drug['indication'],
                        'line': drug['line']
                    }
                })

        # Drug → Document (MENTIONED_IN)
        for drug in entities.get('drugs', []):
            relations.append({
                'type': 'MENTIONED_IN',
                'source': drug['name'],
                'source_type': 'Drug',
                'target': metadata.get('post_number', 'UNKNOWN'),
                'target_type': 'Document',
                'properties': {
                    'board': metadata.get('board'),
                    'title': metadata.get('post_title', '')
                }
            })

        return relations


def main():
    """샘플 테스트"""
    extractor = RuleBasedEntityExtractor()

    # 샘플 파일 경로
    sample_file = Path('data/hira_cancer/parsed_preview/faq_117.txt')

    if not sample_file.exists():
        print(f"❌ 샘플 파일 없음: {sample_file}")
        return

    # 텍스트 파일을 JSON 형식으로 변환 (임시)
    with open(sample_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Markdown 내용만 추출
    markdown_start = content.find('[파싱된 Markdown 내용]')
    if markdown_start != -1:
        markdown_content = content[markdown_start + len('[파싱된 Markdown 내용]'):].strip()
    else:
        markdown_content = content

    # 임시 데이터 구조
    temp_data = {
        'content': markdown_content,
        'attachment_metadata': {
            'board': 'faq',
            'post_number': '117',
            'post_title': 'Tisagenlecleucel(품명: 킴리아주) 관련 질의 응답'
        }
    }

    # 임시 JSON 저장
    temp_json = Path('temp_test.json')
    with open(temp_json, 'w', encoding='utf-8') as f:
        json.dump(temp_data, f, ensure_ascii=False, indent=2)

    # 추출 실행
    result = extractor.extract_from_file(temp_json)

    # 결과 출력
    print('=' * 80)
    print('🔍 규칙 기반 엔티티 추출 결과')
    print('=' * 80)

    print('\n📌 암종류 (Cancers):')
    for cancer in result['entities']['cancers']:
        print(f"  - [{cancer['id']}] {cancer['korean_name']} ({cancer['english_name']})")

    print('\n💊 약제 정보 (Drugs):')
    for drug in result['entities']['drugs']:
        print(f"  - {drug['name']}")
        print(f"    투여대상: {drug['indication'][:50]}...")
        print(f"    투여단계: {drug['line']}")

    print('\n⚠️ 제한사항 (Restrictions):')
    for i, restriction in enumerate(result['entities']['restrictions'][:5], 1):
        print(f"  {i}. [{restriction['type']}] {restriction.get('category', restriction.get('note_id', ''))}")
        print(f"     {restriction['description'][:60]}...")

    print('\n❓ Q&A:')
    for qa in result['entities']['qas']:
        print(f"  Q{qa['question_id']}: {qa['question']}")
        print(f"  A: {qa['answer'][:80]}...")

    print('\n🔗 관계 (Relations):')
    for i, rel in enumerate(result['relations'][:5], 1):
        print(f"  {i}. ({rel['source']}) -[{rel['type']}]-> ({rel['target']})")

    print(f"\n✅ 총 추출: {len(result['entities']['cancers'])}개 암종류, "
          f"{len(result['entities']['drugs'])}개 약제, "
          f"{len(result['entities']['restrictions'])}개 제한사항, "
          f"{len(result['entities']['qas'])}개 Q&A, "
          f"{len(result['relations'])}개 관계")

    # 결과 저장
    output_file = Path('data/hira_cancer/extracted_entities_sample.json')
    output_file.parent.mkdir(exist_ok=True, parents=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 저장: {output_file}")

    # 임시 파일 삭제
    temp_json.unlink()


if __name__ == '__main__':
    main()
