"""
NCC 암정보 사전 활용 간단 데모
(인코딩 이슈 없이 JSON 파일로만 출력)
"""
import json
from pathlib import Path
import sys

# UTF-8 출력 설정 (Windows에서도 동작)
sys.stdout.reconfigure(encoding='utf-8')


def load_terms():
    """암 용어 사전 로드"""
    all_terms = []
    parsed_dir = Path("data/ncc/cancer_dictionary/parsed")

    for batch_file in sorted(parsed_dir.glob("batch_*.json")):
        with open(batch_file, 'r', encoding='utf-8') as f:
            all_terms.extend(json.load(f))

    return all_terms


def extract_terms_from_hira():
    """HIRA 문서에서 의학 용어 추출 데모"""
    print("=" * 80)
    print("HIRA 암질환 데이터에서 의학 용어 추출")
    print("=" * 80)

    # 1. 용어 사전 로드
    terms = load_terms()
    print(f"\n1. 암 용어 사전 로드: {len(terms)}개")

    # 용어 인덱스 구축
    term_dict = {term['title']: term for term in terms}

    # 2. HIRA 데이터 로드
    hira_file = Path("data/hira_cancer/raw/hira_cancer_20251023_184848.json")
    with open(hira_file, 'r', encoding='utf-8') as f:
        hira_data = json.load(f)

    print(f"2. HIRA 데이터 로드: {len(hira_data['data']['announcement'])}개 공고")

    # 3. 첫 3개 문서 분석
    results = []

    for i, post in enumerate(hira_data['data']['announcement'][:3], 1):
        title = post['title']
        content = post.get('content', '')

        # 문서에서 용어 찾기
        found_terms = []
        for term_name in term_dict.keys():
            if term_name in content:
                found_terms.append({
                    'term': term_name,
                    'definition': term_dict[term_name]['content']
                })

        results.append({
            'document_num': i,
            'title': title,
            'content_length': len(content),
            'found_terms_count': len(found_terms),
            'found_terms': found_terms[:5]  # 처음 5개만
        })

        print(f"\n[문서 {i}] {title}")
        print(f"  - 길이: {len(content):,}자")
        print(f"  - 발견된 의학 용어: {len(found_terms)}개")

    # 4. 결과 저장
    output_file = Path("data/ncc/cancer_dictionary/hira_term_extraction.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n4. 결과 저장: {output_file}")
    print("   -> 파일 열어서 상세 내용 확인 가능")

    return results


def search_drug_related_terms():
    """약제명 기반 관련 용어 검색"""
    print("\n" + "=" * 80)
    print("약제명 기반 관련 용어 검색")
    print("=" * 80)

    # 용어 로드
    terms = load_terms()

    # 검색할 약제들
    drugs = ["Paclitaxel", "Carboplatin", "Dostarlimab", "면역", "화학요법"]

    results = {}

    for drug in drugs:
        related = []
        for term in terms:
            # 제목이나 내용에 약제명 포함
            if drug.lower() in term['title'].lower() or \
               drug.lower() in term['content'].lower():
                related.append({
                    'title': term['title'],
                    'content': term['content']
                })

        results[drug] = {
            'count': len(related),
            'terms': related[:5]  # 처음 5개만
        }

        print(f"\n[{drug}] 관련 용어: {len(related)}개")

    # 저장
    output_file = Path("data/ncc/cancer_dictionary/drug_related_terms.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장: {output_file}")

    return results


def term_statistics():
    """용어 통계"""
    print("\n" + "=" * 80)
    print("암 용어 사전 통계")
    print("=" * 80)

    terms = load_terms()

    # 길이 통계
    lengths = [len(term['content']) for term in terms]

    # 키워드 통계
    keywords = {}
    for term in terms:
        # 간단한 키워드 추출 (단어 빈도)
        words = term['content'].split()
        for word in words[:10]:  # 처음 10개 단어만
            if len(word) > 2:
                keywords[word] = keywords.get(word, 0) + 1

    # 가장 많이 등장하는 키워드
    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:20]

    stats = {
        'total_terms': len(terms),
        'avg_definition_length': sum(lengths) / len(lengths),
        'min_definition_length': min(lengths),
        'max_definition_length': max(lengths),
        'top_keywords': [{'keyword': k, 'count': c} for k, c in top_keywords]
    }

    print(f"\n총 용어 수: {stats['total_terms']:,}개")
    print(f"평균 정의 길이: {stats['avg_definition_length']:.1f}자")
    print(f"최소 정의 길이: {stats['min_definition_length']}자")
    print(f"최대 정의 길이: {stats['max_definition_length']}자")

    # 저장
    output_file = Path("data/ncc/cancer_dictionary/term_statistics.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n저장: {output_file}")

    return stats


if __name__ == "__main__":
    # 1. HIRA 문서에서 의학 용어 추출
    extract_results = extract_terms_from_hira()

    # 2. 약제명 기반 검색
    drug_results = search_drug_related_terms()

    # 3. 통계
    stats = term_statistics()

    print("\n" + "=" * 80)
    print("완료! 생성된 파일:")
    print("=" * 80)
    print("1. data/ncc/cancer_dictionary/hira_term_extraction.json")
    print("2. data/ncc/cancer_dictionary/drug_related_terms.json")
    print("3. data/ncc/cancer_dictionary/term_statistics.json")
    print("\n이 파일들을 열어서 상세 내용을 확인하세요!")
