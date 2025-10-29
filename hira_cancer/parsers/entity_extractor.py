"""
HIRA 암질환 공고 문서 엔티티 추출기

목표: 약제-암종-요법 관계를 구조화된 JSON으로 추출
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class HIRAEntityExtractor:
    """HIRA 공고 문서에서 약제, 암종, 요법 정보 추출"""

    def __init__(self):
        # NCC 암종 목록 로드 (100개)
        self.cancer_types = self._load_cancer_types()

        # 약제 패턴 (U+2018/U+2019 작은따옴표 안의 약제명 추출)
        self.drug_pattern = re.compile(r"[\u2018\u201c]([A-Z][a-zA-Z0-9\s\+\-\(\)]+?)[\u2019\u201d]")
        # 요법 패턴
        self.regimen_patterns = {
            'type': re.compile(r'(병용요법|단독요법|복합요법)'),
            'line': re.compile(r'(\d+차|차\s*이상)'),
            'purpose': re.compile(r'(고식적요법|보조요법|adjuvant|neoadjuvant)'),
        }

        # 변경 유형 패턴
        self.action_pattern = re.compile(r'(신설|변경|삭제|추가|개정)')

    def _load_cancer_types(self) -> List[str]:
        """NCC 암종 목록 로드"""
        # 하드코딩 (나중에 파일에서 로드로 변경 가능)
        cancer_types = [
            "갑상선암", "위암", "대장암", "폐암", "간암", "유방암", "전립선암",
            "췌장암", "담낭암", "담도암", "신장암", "방광암", "자궁암", "난소암",
            "식도암", "구강암", "후두암", "인두암", "비인두암", "침샘암",
            "흑색종", "피부암", "골육종", "연부조직육종", "뇌종양", "뇌하수체종양",
            "갑상선수질암", "부갑상선암", "부신암", "신경내분비종양", "카르시노이드",
            "백혈병", "급성골수성백혈병", "급성림프구성백혈병", "만성골수성백혈병",
            "만성림프구성백혈병", "골수이형성증후군", "골수증식종양",
            "림프종", "호지킨림프종", "비호지킨림프종", "다발골수종",
            "소세포폐암", "비소세포폐암", "간내담도암", "간외담도암",
            "자궁경부암", "자궁내막암", "난관암", "복막암",
            "전이성뇌종양", "원발불명암", "소아암", "소아청소년암",
            "갑상선여포암", "갑상선유두암", "미분화갑상선암"
        ]
        return cancer_types

    def extract_cancer_type(self, text: str) -> Optional[str]:
        """텍스트에서 암종 추출"""
        for cancer in self.cancer_types:
            # "자궁암에", "폐암에서", "유방암의" 등 패턴
            if cancer in text:
                return cancer
        return None

    def extract_drugs(self, text: str) -> List[str]:
        """약제명 추출 (작은따옴표 안의 영문)"""
        matches = self.drug_pattern.findall(text)

        drugs = []
        for match in matches:
            # '+' 로 구분된 경우 분리
            if '+' in match:
                parts = [d.strip() for d in match.split('+')]
                drugs.extend(parts)
            else:
                drugs.append(match.strip())

        # 중복 제거
        return list(set(drugs))

    def extract_regimen_info(self, text: str) -> Dict[str, Optional[str]]:
        """요법 정보 추출 (병용/단독, 1차/2차, 목적)"""
        info = {
            'type': None,  # 병용요법, 단독요법
            'line': None,  # 1차, 2차, 3차 이상
            'purpose': None  # 고식적요법, 보조요법
        }

        for key, pattern in self.regimen_patterns.items():
            match = pattern.search(text)
            if match:
                info[key] = match.group(1)

        return info

    def extract_action(self, text: str) -> Optional[str]:
        """변경 유형 추출 (신설, 변경, 삭제 등)"""
        match = self.action_pattern.search(text)
        return match.group(1) if match else None

    def parse_announcement(self, announcement: Dict[str, Any]) -> List[Dict[str, Any]]:
        """단일 공고 문서 파싱"""
        content = announcement.get('content', '')

        # 신설/변경 섹션별로 분리
        sections = self._split_sections(content)

        relations = []

        for section_text in sections:
            # 암종 추출
            cancer = self.extract_cancer_type(section_text)
            if not cancer:
                continue

            # 약제 추출
            drugs = self.extract_drugs(section_text)
            if not drugs:
                continue

            # 요법 정보
            regimen = self.extract_regimen_info(section_text)

            # 변경 유형
            action = self.extract_action(section_text)

            # 관계 생성
            relation = {
                'cancer': cancer,
                'drugs': drugs,
                'regimen_type': regimen['type'],
                'line': regimen['line'],
                'purpose': regimen['purpose'],
                'action': action,
                'source_text': section_text.strip(),
                'announcement_no': announcement.get('announcement_no'),
                'date': announcement.get('created_date'),
                'board': announcement.get('board')
            }

            relations.append(relation)

        return relations

    def _split_sections(self, content: str) -> List[str]:
        """공고 내용을 섹션별로 분리"""
        # '- ' 로 시작하는 항목들로 분리
        lines = content.split('\n')
        sections = []
        current_section = []

        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('ㆍ'):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            elif current_section:
                current_section.append(line)

        # 마지막 섹션
        if current_section:
            sections.append('\n'.join(current_section))

        return sections

    def parse_all_announcements(self, hira_file: str) -> List[Dict[str, Any]]:
        """전체 공고 문서 파싱"""
        print(f"HIRA 공고 문서 파싱 시작: {hira_file}")

        # HIRA 데이터 로드
        with open(hira_file, 'r', encoding='utf-8') as f:
            hira_data = json.load(f)

        all_relations = []
        announcement_count = 0

        # 공고만 처리
        announcements = hira_data['data']['announcement']

        print(f"총 {len(announcements)}개 공고 처리 중...")

        for announcement in announcements:
            relations = self.parse_announcement(announcement)

            if relations:
                all_relations.extend(relations)
                announcement_count += 1

                if announcement_count % 20 == 0:
                    print(f"  진행: {announcement_count}개 공고, {len(all_relations)}개 관계 추출")

        print(f"\n완료!")
        print(f"  처리된 공고: {announcement_count}개")
        print(f"  추출된 관계: {len(all_relations)}개")

        return all_relations

    def save_results(self, relations: List[Dict[str, Any]], output_file: str):
        """결과 저장"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 요약 통계
        summary = {
            'total_relations': len(relations),
            'unique_cancers': len(set(r['cancer'] for r in relations if r['cancer'])),
            'unique_drugs': len(set(drug for r in relations for drug in r['drugs'])),
            'by_action': {},
            'by_regimen_type': {},
            'extracted_at': datetime.now().isoformat()
        }

        # 변경 유형별
        for r in relations:
            action = r['action'] or 'unknown'
            summary['by_action'][action] = summary['by_action'].get(action, 0) + 1

            regimen = r['regimen_type'] or 'unknown'
            summary['by_regimen_type'][regimen] = summary['by_regimen_type'].get(regimen, 0) + 1

        # 저장
        result = {
            'summary': summary,
            'relations': relations
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n저장 완료: {output_path}")
        print(f"\n통계:")
        print(f"  총 관계: {summary['total_relations']}개")
        print(f"  암종: {summary['unique_cancers']}개")
        print(f"  약제: {summary['unique_drugs']}개")
        print(f"  변경 유형별:")
        for action, count in summary['by_action'].items():
            print(f"    - {action}: {count}개")


def main():
    """메인 실행"""
    extractor = HIRAEntityExtractor()

    # HIRA 데이터 파일
    hira_file = "data/hira_cancer/raw/hira_cancer_20251023_184848.json"

    # 파싱
    relations = extractor.parse_all_announcements(hira_file)

    # 결과 저장
    output_file = "data/hira_cancer/parsed/drug_cancer_relations.json"
    extractor.save_results(relations, output_file)

    # 샘플 저장 (콘솔 출력 대신 JSON으로 저장하여 인코딩 에러 방지)
    sample_file = Path("data/hira_cancer/parsed/drug_cancer_relations_samples.json")
    samples = []
    for i, rel in enumerate(relations[:10], 1):
        samples.append({
            'index': i,
            'cancer': rel['cancer'],
            'drugs': rel['drugs'][:5],
            'regimen_type': rel['regimen_type'],
            'line': rel['line'],
            'action': rel['action'],
            'source_preview': rel['source_text'][:150]
        })

    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump({'samples': samples, 'total': len(relations)}, f, ensure_ascii=False, indent=2)

    print(f"\n샘플 저장: {sample_file}")


if __name__ == "__main__":
    main()
