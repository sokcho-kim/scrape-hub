"""NCC 암정보 사전 샘플 분석"""
import json
import random
from pathlib import Path

def analyze_samples():
    """랜덤 샘플 추출 및 패턴 분석"""

    # 모든 배치 파일 로드
    data_dir = Path("data/ncc/cancer_dictionary/parsed")
    all_terms = []

    for i in range(1, 13):
        batch_file = data_dir / f"batch_{i:04d}.json"
        with open(batch_file, 'r', encoding='utf-8') as f:
            all_terms.extend(json.load(f))

    print(f"총 용어 수: {len(all_terms)}")

    # 랜덤 샘플 50개
    samples = random.sample(all_terms, 50)

    # 샘플 정보 추출
    sample_info = []
    for term in samples:
        keyword = term['keyword']
        content = term['content']

        # 간단한 패턴 매칭으로 카테고리 추정
        category_hints = []

        # 약제 관련
        if any(word in content for word in ['약제', '약물', '투여', '복용', '주사', '정제', '캡슐']):
            category_hints.append('약제')

        # 암종 관련
        if any(word in content for word in ['암', '종양', '악성', '암세포', '림프종', '백혈병', '육종']):
            category_hints.append('암종')

        # 치료법 관련
        if any(word in content for word in ['치료', '요법', '수술', '방사선', '화학요법', '면역치료']):
            category_hints.append('치료법')

        # 검사/진단 관련
        if any(word in content for word in ['검사', '촬영', '진단', '영상', '생검', '조직검사']):
            category_hints.append('검사/진단')

        # 증상 관련
        if any(word in content for word in ['증상', '징후', '통증', '부작용']):
            category_hints.append('증상')

        # 임상시험 관련
        if any(word in content for word in ['임상시험', '임상연구', '연구', '시험']):
            category_hints.append('임상시험')

        # 유전자/분자 관련
        if any(word in content for word in ['유전자', '염색체', 'DNA', 'RNA', '단백질', '효소']):
            category_hints.append('유전자/분자')

        sample_info.append({
            'keyword': keyword,
            'content_preview': content[:150],
            'content_length': len(content),
            'category_hints': category_hints
        })

    # JSON 파일로 저장
    output_file = Path("ncc/cancer_dictionary/sample_analysis.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_info, f, ensure_ascii=False, indent=2)

    print(f"샘플 분석 완료: {output_file}")

    # 카테고리 통계
    category_counts = {}
    for sample in sample_info:
        for cat in sample['category_hints']:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    print("\n카테고리 힌트 통계 (50개 샘플 기준):")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}개")

    # 통계 저장
    stats = {
        'total_terms': len(all_terms),
        'sample_size': len(samples),
        'category_distribution': category_counts
    }

    stats_file = Path("ncc/cancer_dictionary/sample_stats.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n통계 저장 완료: {stats_file}")

if __name__ == '__main__':
    analyze_samples()
