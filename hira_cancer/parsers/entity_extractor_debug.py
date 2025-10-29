"""디버그 버전 - 각 단계별 로깅"""
import json
import re
from pathlib import Path
from entity_extractor import HIRAEntityExtractor

# 확장된 디버그 클래스
class HIRAEntityExtractorDebug(HIRAEntityExtractor):
    def parse_all_announcements(self, hira_file: str):
        """전체 공고 문서 파싱 (디버그 버전)"""
        print(f"HIRA 공고 문서 파싱 시작: {hira_file}")

        # HIRA 데이터 로드
        with open(hira_file, 'r', encoding='utf-8') as f:
            hira_data = json.load(f)

        all_relations = []
        announcement_count = 0

        # 통계
        stats = {
            'total_announcements': 0,
            'with_content': 0,
            'with_sections': 0,
            'sections_with_cancer': 0,
            'sections_with_drugs': 0,
            'relations_extracted': 0
        }

        # 공고만 처리
        announcements = hira_data['data']['announcement']
        stats['total_announcements'] = len(announcements)

        print(f"총 {len(announcements)}개 공고 처리 중...")

        for idx, announcement in enumerate(announcements[:10], 1):  # 처음 10개만 테스트
            content = announcement.get('content', '')

            if not content:
                continue

            stats['with_content'] += 1

            # 섹션 분리
            sections = self._split_sections(content)

            if sections:
                stats['with_sections'] += 1
                print(f"\n[공고 {idx}] {announcement.get('announcement_no', 'N/A')}")
                print(f"  섹션: {len(sections)}개")

            for section_idx, section_text in enumerate(sections, 1):
                # 암종 추출
                cancer = self.extract_cancer_type(section_text)

                # 약제 추출
                drugs = self.extract_drugs(section_text)

                if cancer:
                    stats['sections_with_cancer'] += 1
                    print(f"    섹션 {section_idx}: 암종={cancer}, 약제={len(drugs)}개")

                    if drugs:
                        stats['sections_with_drugs'] += 1
                        print(f"      약제: {drugs[:3]}")

                if not cancer or not drugs:
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
                    'source_text': section_text.strip()[:200],
                    'announcement_no': announcement.get('announcement_no'),
                    'date': announcement.get('created_date'),
                    'board': announcement.get('board')
                }

                all_relations.append(relation)
                stats['relations_extracted'] += 1
                announcement_count += 1

        print(f"\n=== 통계 ===")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        return all_relations


# 실행
extractor = HIRAEntityExtractorDebug()
hira_file = "data/hira_cancer/raw/hira_cancer_20251023_184848.json"
relations = extractor.parse_all_announcements(hira_file)

print(f"\n최종 추출: {len(relations)}개 관계")

# 처음 5개 출력
if relations:
    print("\n=== 샘플 결과 ===")
    for i, rel in enumerate(relations[:5], 1):
        print(f"\n[{i}] {rel['cancer']} - {', '.join(rel['drugs'][:3])}")
        print(f"    {rel['source_text'][:100]}...")
