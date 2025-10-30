"""NCC 암정보 사전 규칙 기반 분류기 v2 (5가지 개선)"""
import json
import re
from pathlib import Path
from collections import Counter


class ImprovedClassifier:
    """개선된 규칙 기반 분류기

    개선 사항:
    1. NCC 100개 암종 화이트리스트 (핵심!)
    2. 임상시험 우선순위 최상위
    3. 요법/레짐명 정규식 사전
    4. 약제 패턴 강화
    5. HTML 전처리 개선
    """

    def __init__(self):
        # 1. NCC 100개 암종 화이트리스트 로드
        self.cancer_whitelist = self._load_cancer_whitelist()

        # 3. 요법/레짐명 사전
        self.regimen_patterns = [
            r'\b(ABVD|ABVE|AC|AC-T|FOLFOX|FOLFIRI|R-CHOP|CHOP|CVP|BEP|EP|VIP)\s*요법',
            r'\b(ABVD|ABVE|AC|AC-T|FOLFOX|FOLFIRI|R-CHOP|CHOP|CVP|BEP|EP|VIP)\b',
        ]

        # 카테고리별 패턴 정의 (우선순위 재조정)
        self.category_patterns = {
            '임상시험/연구': {
                'priority': 1,  # 최우선!
                'keywords': [
                    '임상시험', '임상연구', '1상', '2상', '3상', '4상',
                    '일상', '이상', '삼상', '사상',  # 한글 표기
                    '대조군', '무작위', '이중맹검', '단일기관', '다기관',
                    '환자군', '코호트', '프로토콜', '시험군', '연구 단계',
                    '첫 번째 연구', '시험하는 연구'
                ],
                'negative_keywords': [],  # 임상시험은 다른 것과 절대 혼동 안 됨
            },
            '치료법': {
                'priority': 2,
                'keywords': [
                    '요법', '수술', '방사선', '화학요법', '면역치료', '표적치료',
                    '절제술', '적출', '이식', '조사', '투여법', '병용요법', '단독요법',
                    '고식적요법', '보조요법', '수술적', '비수술적', '시술', '처치',
                    '치료법', '치료 방법', '치료에 쓰이는'
                ],
                'suffix': ['요법', '술', '치료'],
                'negative_keywords': [],
            },
            '약제': {
                'priority': 3,
                'keywords': [
                    '약제', '약물', '투여', '복용', '주사', '정제', '캡슐', '시럽',
                    '연질캡슐', '경질캡슐', '연고', '크림', '겔', '로션', '패치',
                    '용량', '처방', '투약', '제제', '성분', '상품명',
                    '억제제', '길항제', '대항제', '항생제', 'inhibitor', 'antagonist',
                    '치료에 사용되는 약', '치료에 쓰이는 약', '투여하는'
                ],
                'suffix': ['주', '정', '캡슐', '시럽', '액', '산', '크림', '염'],
                'negative_keywords': [],
            },
            '검사/진단': {
                'priority': 3,
                'keywords': [
                    '검사', '촬영', '진단', '영상', '생검', '조직검사', '스캔',
                    '엑스선', 'X선', 'CT', 'MRI', 'PET', '초음파', '내시경',
                    '조영', '영상법', '검진', '선별검사', '판정', '확진',
                    '조영술', '조영제', '판독', '소견'
                ],
                'suffix': ['검사', '촬영', '술', '법'],
                'negative_keywords': [],
            },
            '유전자/분자': {
                'priority': 4,
                'keywords': [
                    '유전자', '염색체', 'DNA', 'RNA', '단백질', '효소', '수용체',
                    '항원', '항체', '분자', '돌연변이', '변이', '발현',
                    '활성', '결합', '신호전달', '경로', '바이오마커', '표지자',
                    '세포주기', '세포사멸', '아폽토시스', '리간드', '인자'
                ],
                'suffix': ['제', '체', '자', '소', '질', '인자'],
                # 약제와 구분: '투여', '복용', '사용되는 약' 없으면 분자
                'negative_keywords': ['투여', '복용', '치료에 사용', '투약'],
            },
            '증상/부작용': {
                'priority': 5,
                'keywords': [
                    '증상', '징후', '통증', '부작용', '합병증', '무감각', '따끔거림',
                    '부종', '발열', '구토', '설사', '피로', '출혈', '감염',
                    '독성', '이상반응', '불편', '손상', '장애'
                ],
                'suffix': ['증', '증상', '통'],
                'negative_keywords': [],
            },
            '해부/생리': {
                'priority': 5,
                'keywords': [
                    '부위', '장기', '조직', '세포', '혈관', '신경', '근육',
                    '뼈', '피부', '점막', '상피', '기관', '계통', '구조',
                    '해부', '생리', '기능', '분비', '순환', '호흡'
                ],
                'suffix': ['부', '계', '조직', '세포'],
                'negative_keywords': [],
            },
        }

    def _load_cancer_whitelist(self):
        """NCC 100개 암종 화이트리스트 로드"""
        cancer_file = Path("ncc/cancer_dictionary/ncc_cancer_list.json")

        if not cancer_file.exists():
            print("[경고] NCC 암종 리스트 파일이 없습니다. 암종 분류가 부정확할 수 있습니다.")
            return set()

        with open(cancer_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cancer_names = set(data['cancer_names'])

        # 동의어/별칭 추가 (일반적인 표현)
        aliases = set()
        for name in cancer_names:
            # "소아청소년 뇌종양" -> "뇌종양"도 추가
            if ' ' in name:
                parts = name.split()
                for part in parts:
                    if '암' in part or '종양' in part or '종' in part:
                        aliases.add(part)

        cancer_names.update(aliases)

        print(f"[로드] NCC 암종 화이트리스트: {len(cancer_names)}개")
        return cancer_names

    def _preprocess_content(self, content):
        """HTML 전처리 개선"""
        if not content:
            return ""

        # HTML 태그 제거 (더 강력하게)
        content = re.sub(r'<[^>]+>', ' ', content)

        # HTML 엔티티 제거
        content = re.sub(r'&[a-z]+;', ' ', content)
        content = re.sub(r'&#\d+;', ' ', content)

        # 유니코드 정규화 (작은따옴표, 하이픈 등)
        content = content.replace('\u2018', "'").replace('\u2019', "'")
        content = content.replace('\u201c', '"').replace('\u201d', '"')
        content = content.replace('\u2013', '-').replace('\u2014', '-')
        content = content.replace('&nbsp;', ' ')

        # 연속 공백 제거
        content = re.sub(r'\s+', ' ', content)

        return content.strip()

    def classify_term(self, keyword, content):
        """단일 용어 분류 (개선된 로직)"""
        # None 체크
        if not keyword or not content:
            return ['기타'], 0.0

        # 전처리
        clean_content = self._preprocess_content(content)
        combined_text = f"{keyword} {clean_content}".lower()

        # ========================================
        # 우선순위 1: 임상시험 (최우선!)
        # ========================================
        clinical_keywords = ['임상시험', '1상', '2상', '3상', '4상', '일상', '이상', '삼상', '사상',
                            '임상연구', '대조군', '무작위', '이중맹검', '코호트']
        if any(kw in combined_text for kw in clinical_keywords):
            return ['임상시험/연구'], 0.95

        # ========================================
        # 우선순위 2: 요법/레짐명 (정규식 사전)
        # ========================================
        for pattern in self.regimen_patterns:
            if re.search(pattern, keyword, re.IGNORECASE):
                return ['치료법'], 0.95

        # ========================================
        # 우선순위 3: NCC 암종 화이트리스트
        # ========================================
        if keyword in self.cancer_whitelist:
            # 키워드 자체가 암종명이면 무조건 암종
            return ['암종'], 1.0

        # 내용에 암종명이 포함되어도 "~암 치료에 사용" 같은 문맥이면 제외
        is_cancer_in_content = any(cancer in combined_text for cancer in self.cancer_whitelist)
        is_treatment_context = any(phrase in clean_content for phrase in [
            '치료에 사용', '치료에 쓰이는', '투여', '복용', '주사', '약제', '약물'
        ])

        if is_cancer_in_content and not is_treatment_context:
            # 암종명이 언급되지만 치료 문맥이 아니면 암종
            return ['암종'], 0.8

        # ========================================
        # 우선순위 4: 약제 패턴 강화
        # ========================================
        # "억제제", "길항제", "항생제" 등은 약제
        drug_indicators = ['억제제', '길항제', '대항제', '항생제', 'inhibitor', 'antagonist']
        if any(ind in combined_text for ind in drug_indicators):
            # 단, "투여", "복용" 문맥이 없으면 유전자/분자일 수도
            if any(word in clean_content for word in ['투여', '복용', '치료에 사용', '투약']):
                return ['약제'], 0.9

        # 약제 접미사 ("주", "정", "캡슐", "염")
        drug_suffix = ['주', '정', '캡슐', '시럽', '액', '크림', '염', '산']
        if any(keyword.endswith(suf) for suf in drug_suffix):
            return ['약제'], 0.85

        # ========================================
        # 일반 규칙 기반 점수 계산
        # ========================================
        scores = {}

        for category, patterns in self.category_patterns.items():
            score = 0

            # 키워드 매칭
            for kw in patterns['keywords']:
                count = combined_text.count(kw.lower())
                score += count * 2

            # 접미사 매칭
            for suffix in patterns.get('suffix', []):
                if keyword.endswith(suffix):
                    score += 5

            # 네거티브 키워드 (점수 감소)
            for neg_kw in patterns.get('negative_keywords', []):
                if neg_kw in combined_text:
                    score -= 3

            # 우선순위 보정
            scores[category] = score / patterns['priority']

        # 점수가 0보다 큰 카테고리들
        if not scores or max(scores.values()) == 0:
            return ['기타'], 0.1

        # 최고 점수 카테고리
        max_score = max(scores.values())
        top_categories = [cat for cat, score in scores.items() if score == max_score]

        # 동점이면 우선순위 고려
        if len(top_categories) > 1:
            top_categories.sort(key=lambda x: self.category_patterns[x]['priority'])

        # 신뢰도 계산 (간단히 정규화)
        confidence = min(max_score / 10, 1.0)  # 0-1 사이로 정규화

        return [top_categories[0]], confidence

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
        low_confidence_count = 0

        for term in all_terms:
            keyword = term['keyword']
            content = term['content']

            categories, confidence = self.classify_term(keyword, content)

            classified_terms.append({
                'keyword': keyword,
                'content': content[:200],  # 미리보기용
                'categories': categories,
                'confidence': confidence
            })

            # 통계
            for cat in categories:
                category_counts[cat] += 1

            if confidence < 0.7:
                low_confidence_count += 1

        print(f"[완료] 낮은 신뢰도 (<0.7): {low_confidence_count}개 ({low_confidence_count/len(all_terms)*100:.1f}%)\n")

        return classified_terms, category_counts


def main():
    """메인 실행"""
    classifier = ImprovedClassifier()

    print("=" * 60)
    print("NCC 암정보 사전 규칙 기반 분류 v2 (개선)")
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
    output_file = Path("data/ncc/cancer_dictionary/classified_terms_v2.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    result = {
        'summary': {
            'total_terms': total,
            'category_distribution': dict(category_counts),
            'version': 'v2_improved'
        },
        'classified_terms': classified_terms
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[완료] 분류 결과 저장: {output_file}")

    # 샘플 출력
    samples_by_category = {}
    for term in classified_terms:
        cat = term['categories'][0]
        if cat not in samples_by_category:
            samples_by_category[cat] = []
        if len(samples_by_category[cat]) < 5:
            samples_by_category[cat].append(term)

    sample_file = Path("ncc/cancer_dictionary/classification_samples_v2.json")
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(samples_by_category, f, ensure_ascii=False, indent=2)

    print(f"[완료] 샘플 저장: {sample_file}")

    print("\n\n[카테고리별 샘플 (각 5개)]")
    print("=" * 60)
    for category in sorted(samples_by_category.keys()):
        print(f"\n[{category}]")
        for i, term in enumerate(samples_by_category[category][:5], 1):
            confidence = term.get('confidence', 0)
            print(f"  {i}. {term['keyword']} (신뢰도: {confidence:.2f})")


if __name__ == '__main__':
    main()
