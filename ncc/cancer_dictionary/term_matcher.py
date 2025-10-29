"""
NCC 암정보 사전 활용 도구

방금 수집한 3,543개 암 관련 의학 용어를 다른 데이터와 연계하여 활용
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class TermMatcher:
    """암정보 사전 매칭 도구"""

    def __init__(self, dictionary_dir: str = "data/ncc/cancer_dictionary/parsed"):
        self.dictionary_dir = Path(dictionary_dir)
        self.terms = self._load_all_terms()
        self.term_index = self._build_index()

    def _load_all_terms(self) -> List[Dict[str, Any]]:
        """모든 배치 파일에서 용어 로드"""
        all_terms = []

        for batch_file in sorted(self.dictionary_dir.glob("batch_*.json")):
            with open(batch_file, 'r', encoding='utf-8') as f:
                terms = json.load(f)
                all_terms.extend(terms)

        print(f"[OK] {len(all_terms)}개 암 용어 로드 완료")
        return all_terms

    def _build_index(self) -> Dict[str, Dict[str, Any]]:
        """빠른 검색을 위한 인덱스 구축"""
        index = {}

        for term in self.terms:
            # 용어명으로 인덱싱 (대소문자 무시)
            key = term['title'].lower()
            index[key] = term

            # 키워드가 다른 경우 추가
            if term.get('keyword') and term['keyword'].lower() != key:
                index[term['keyword'].lower()] = term

        print(f"[OK] {len(index)}개 검색 키 생성")
        return index

    def search_term(self, query: str) -> Optional[Dict[str, Any]]:
        """정확한 용어 검색"""
        return self.term_index.get(query.lower())

    def fuzzy_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """부분 매칭 검색"""
        query_lower = query.lower()
        matches = []

        for term in self.terms:
            if query_lower in term['title'].lower():
                matches.append(term)
                if len(matches) >= top_k:
                    break

        return matches

    def extract_terms_from_text(self, text: str) -> List[Dict[str, Any]]:
        """텍스트에서 암 관련 용어 추출 (NER)"""
        found_terms = []

        # 각 용어가 텍스트에 있는지 확인
        for term in self.terms:
            if term['title'] in text:
                found_terms.append({
                    'term': term['title'],
                    'definition': term['content'],
                    'position': text.index(term['title'])
                })

        # 위치 순으로 정렬
        found_terms.sort(key=lambda x: x['position'])
        return found_terms

    def enrich_hira_document(self, hira_doc: Dict[str, Any]) -> Dict[str, Any]:
        """HIRA 문서에 용어 설명 추가"""
        content = hira_doc.get('content', '')

        # 문서에서 용어 추출
        found_terms = self.extract_terms_from_text(content)

        # 원본 문서 복사
        enriched = hira_doc.copy()
        enriched['medical_terms'] = found_terms
        enriched['term_count'] = len(found_terms)

        return enriched

    def get_drug_related_terms(self, drug_name: str) -> List[Dict[str, Any]]:
        """약제명과 관련된 용어 검색"""
        # 약제명 포함 용어 검색
        related = []

        for term in self.terms:
            if drug_name.lower() in term['title'].lower() or \
               drug_name.lower() in term['content'].lower():
                related.append(term)

        return related


def demo_hira_enrichment():
    """HIRA 데이터 보강 데모"""
    print("=" * 80)
    print("HIRA 암질환 데이터 + NCC 용어 사전 연계 데모")
    print("=" * 80)

    # 1. 용어 매칭 도구 초기화
    matcher = TermMatcher()

    # 2. HIRA 데이터 로드
    hira_file = Path("data/hira_cancer/raw/hira_cancer_20251023_184848.json")
    with open(hira_file, 'r', encoding='utf-8') as f:
        hira_data = json.load(f)

    # 3. 첫 번째 공고 문서 분석
    first_post = hira_data['data']['announcement'][0]
    print(f"\n[문서] {first_post['title']}")
    print(f"   내용 길이: {len(first_post['content'])}자")

    # 4. 용어 추출
    enriched = matcher.enrich_hira_document(first_post)

    print(f"\n[용어 추출] 발견된 의학 용어: {enriched['term_count']}개")
    for i, term_info in enumerate(enriched['medical_terms'][:5], 1):
        print(f"\n   [{i}] {term_info['term']}")
        print(f"       정의: {term_info['definition'][:100]}...")

    # 5. 약제명 검색 예시
    print("\n" + "=" * 80)
    print("약제명 기반 관련 용어 검색")
    print("=" * 80)

    drugs = ["Dostarlimab", "Paclitaxel", "Carboplatin", "면역"]

    for drug in drugs:
        related_terms = matcher.get_drug_related_terms(drug)
        if related_terms:
            print(f"\n[약제] '{drug}' 관련 용어: {len(related_terms)}개")
            for term in related_terms[:3]:
                print(f"   - {term['title']}: {term['content'][:80]}...")

    # 6. 저장
    output_file = Path("data/ncc/cancer_dictionary/enriched_demo.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"\n[저장] 보강된 문서 저장: {output_file}")


def demo_term_search():
    """용어 검색 데모"""
    print("\n" + "=" * 80)
    print("암 용어 검색 데모")
    print("=" * 80)

    matcher = TermMatcher()

    # 검색 예시
    queries = [
        "면역",
        "항암제",
        "화학요법",
        "세포"
    ]

    for query in queries:
        print(f"\n[검색] 검색어: '{query}'")
        results = matcher.fuzzy_search(query, top_k=3)

        if results:
            print(f"   결과: {len(results)}개")
            for i, term in enumerate(results, 1):
                print(f"   [{i}] {term['title']}")
                print(f"       {term['content'][:100]}...")
        else:
            print("   결과 없음")


if __name__ == "__main__":
    # HIRA 데이터 보강 데모
    demo_hira_enrichment()

    # 용어 검색 데모
    demo_term_search()
