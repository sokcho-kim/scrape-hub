"""NCC 암정보 사전 규칙 기반 분류기"""
import json
import re
from pathlib import Path
from collections import Counter


class RuleBasedClassifier:
    """규칙 기반 의학 용어 분류기"""

    def __init__(self):
        # 카테고리별 키워드 패턴 정의
        self.category_patterns = {
            '약제': {
                'keywords': [
                    '약제', '약물', '투여', '복용', '주사', '정제', '캡슐', '시럽',
                    '연질캡슐', '경질캡슐', '연고', '크림', '겔', '로션', '패치',
                    '용량', '처방', '투약', '제제', '성분', '상품명'
                ],
                'keyword_suffix': ['주', '정', '캡슐', '시럽', '액', '산', '크림'],
                'priority': 2  # 우선순위 (낮을수록 높음)
            },
            '암종': {
                'keywords': [
                    '암', '종양', '악성', '암세포', '림프종', '백혈병', '육종',
                    '선암', '편평세포암', '암종', '악성신생물', '암환자',
                    '신생물', '종괴', '병변', '전이', '재발', '진행암'
                ],
                'keyword_suffix': ['암', '종', '종양'],
                'priority': 3
            },
            '치료법': {
                'keywords': [
                    '치료', '요법', '수술', '방사선', '화학요법', '면역치료',
                    '표적치료', '절제술', '적출', '이식', '조사', '투여법',
                    '병용요법', '단독요법', '고식적요법', '보조요법',
                    '수술적', '비수술적', '시술', '처치'
                ],
                'keyword_suffix': ['요법', '술', '치료', '법'],
                'priority': 4
            },
            '검사/진단': {
                'keywords': [
                    '검사', '촬영', '진단', '영상', '생검', '조직검사', '스캔',
                    '엑스선', 'X선', 'CT', 'MRI', 'PET', '초음파', '내시경',
                    '조영', '영상법', '검진', '선별검사', '판정', '확진',
                    '조영술', '조영제', '판독', '소견'
                ],
                'keyword_suffix': ['검사', '촬영', '술', '법'],
                'priority': 3
            },
            '증상/부작용': {
                'keywords': [
                    '증상', '징후', '통증', '부작용', '합병증', '무감각', '따끔거림',
                    '부종', '발열', '구토', '설사', '피로', '출혈', '감염',
                    '독성', '이상반응', '불편', '손상', '장애'
                ],
                'keyword_suffix': ['증', '증상', '통'],
                'priority': 5
            },
            '유전자/분자': {
                'keywords': [
                    '유전자', '염색체', 'DNA', 'RNA', '단백질', '효소', '수용체',
                    '항원', '항체', '분자', '돌연변이', '변이', '발현', '억제제',
                    '활성', '결합', '신호전달', '경로', '바이오마커', '표지자',
                    '세포주기', '세포사멸', '아폽토시스', '리간드'
                ],
                'keyword_suffix': ['제', '체', '자', '소', '질'],
                'priority': 4
            },
            '임상시험/연구': {
                'keywords': [
                    '임상시험', '임상연구', '연구', '시험', '1상', '2상', '3상',
                    '대조군', '무작위', '이중맹검', '단일기관', '다기관',
                    '환자군', '코호트', '실험', '프로토콜', '시험군'
                ],
                'keyword_suffix': ['상', '시험', '연구'],
                'priority': 3
            },
            '해부/생리': {
                'keywords': [
                    '부위', '장기', '조직', '세포', '혈관', '신경', '근육',
                    '뼈', '피부', '점막', '상피', '기관', '계통', '구조',
                    '해부', '생리', '기능', '분비', '순환', '호흡'
                ],
                'keyword_suffix': ['부', '계', '조직', '세포'],
                'priority': 5
            }
        }

    def classify_term(self, keyword, content):
        """단일 용어 분류"""
        # None 체크
        if not keyword or not content:
            return ['기타']

        # HTML 태그 제거
        clean_content = re.sub(r'<[^>]+>', '', content)
        combined_text = f"{keyword} {clean_content}".lower()

        # 각 카테고리별 점수 계산
        scores = {}

        for category, patterns in self.category_patterns.items():
            score = 0

            # 키워드 매칭
            for kw in patterns['keywords']:
                count = combined_text.count(kw.lower())
                score += count * 2  # 키워드 매칭은 2점

            # 접미사 매칭 (keyword에만 적용)
            for suffix in patterns.get('keyword_suffix', []):
                if keyword.endswith(suffix):
                    score += 5  # 접미사 매칭은 5점

            # 우선순위 보정 (낮은 숫자 = 높은 우선순위)
            scores[category] = score / patterns['priority']

        # 점수가 0보다 큰 카테고리들 반환
        if max(scores.values()) == 0:
            return ['기타']

        # 최고 점수 카테고리 반환
        max_score = max(scores.values())
        top_categories = [cat for cat, score in scores.items() if score == max_score]

        # 동점이면 우선순위 고려
        if len(top_categories) > 1:
            top_categories.sort(key=lambda x: self.category_patterns[x]['priority'])

        return [top_categories[0]]

    def classify_all(self, data_dir='data/ncc/cancer_dictionary/parsed'):
        """전체 용어 분류"""
        data_path = Path(data_dir)
        all_terms = []

        # 모든 배치 파일 로드
        for i in range(1, 13):
            batch_file = data_path / f"batch_{i:04d}.json"
            with open(batch_file, 'r', encoding='utf-8') as f:
                all_terms.extend(json.load(f))

        print(f"총 {len(all_terms)}개 용어 분류 중...\n")

        # 분류 실행
        classified_terms = []
        category_counts = Counter()

        for term in all_terms:
            keyword = term['keyword']
            content = term['content']

            categories = self.classify_term(keyword, content)

            classified_terms.append({
                'keyword': keyword,
                'content': content[:200],  # 미리보기용
                'categories': categories
            })

            # 통계
            for cat in categories:
                category_counts[cat] += 1

        return classified_terms, category_counts


def main():
    """메인 실행"""
    classifier = RuleBasedClassifier()

    print("=" * 60)
    print("NCC 암정보 사전 규칙 기반 분류")
    print("=" * 60)

    # 전체 분류 실행
    classified_terms, category_counts = classifier.classify_all()

    # 통계 출력
    print("\n[분류 통계]")
    print("-" * 60)
    total = sum(category_counts.values())

    for category, count in category_counts.most_common():
        percentage = (count / total) * 100
        print(f"  {category:20s}: {count:5d}개 ({percentage:5.1f}%)")

    print(f"\n  {'총계':20s}: {total:5d}개 (100.0%)")

    # 결과 저장
    output_file = Path("data/ncc/cancer_dictionary/classified_terms.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    result = {
        'summary': {
            'total_terms': total,
            'category_distribution': dict(category_counts)
        },
        'classified_terms': classified_terms
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[완료] 분류 결과 저장: {output_file}")

    # 샘플 출력 (카테고리별 5개씩)
    print("\n\n[카테고리별 샘플 (각 5개)]")
    print("=" * 60)

    samples_by_category = {}
    for term in classified_terms:
        cat = term['categories'][0]
        if cat not in samples_by_category:
            samples_by_category[cat] = []
        if len(samples_by_category[cat]) < 5:
            samples_by_category[cat].append(term)

    # 샘플 파일로 저장 (콘솔 인코딩 문제 방지)
    sample_file = Path("ncc/cancer_dictionary/classification_samples.json")
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(samples_by_category, f, ensure_ascii=False, indent=2)

    print(f"\n[완료] 샘플 저장: {sample_file}")

    for category in sorted(samples_by_category.keys()):
        print(f"\n[{category}]")
        for i, term in enumerate(samples_by_category[category][:5], 1):
            print(f"  {i}. {term['keyword']}")


if __name__ == '__main__':
    main()
