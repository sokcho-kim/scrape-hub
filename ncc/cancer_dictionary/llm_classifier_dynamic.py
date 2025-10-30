"""동적 Few-shot 선택을 사용한 LLM 분류기 (v3 - 최종)"""
import json
import os
import time
import re
from pathlib import Path
from collections import Counter
import openai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class DynamicFewShotClassifier:
    """동적 Few-shot 선택 LLM 분류기"""

    def __init__(self, api_key=None):
        """초기화"""
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')

        if not self.api_key:
            raise ValueError("OpenAI API 키가 필요합니다.")

        self.client = openai.OpenAI(api_key=self.api_key)

        # 카테고리 정의
        self.categories = [
            "약제", "암종", "치료법", "검사/진단", "증상/부작용",
            "유전자/분자", "임상시험/연구", "해부/생리", "기타"
        ]

        # Few-shot 예시 풀
        self._init_fewshot_pool()

    def _init_fewshot_pool(self):
        """Few-shot 예시 풀 초기화 (Core 9 + Boundary 10 + Noise 3)"""

        # Core Anchors (9) - 카테고리별 대표 1개
        self.core_examples = [
            {
                "term": "도스타릴리맙",
                "definition": "면역관문억제제, 정맥 주사로 투여",
                "category": "약제",
                "confidence": 0.95,
                "reason": "투여 단서",
                "evidence": "정맥 주사",
                "keywords": ["약제", "투여", "주사", "억제제"]
            },
            {
                "term": "위암",
                "definition": "위에서 발생하는 악성 종양",
                "category": "암종",
                "confidence": 0.99,
                "reason": "암 종명",
                "evidence": "위암",
                "keywords": ["암", "암종", "종양"]
            },
            {
                "term": "R-CHOP",
                "definition": "림프종에서 쓰는 복합 화학요법 레짐",
                "category": "치료법",
                "confidence": 0.96,
                "reason": "레짐명",
                "evidence": "레짐",
                "keywords": ["요법", "레짐", "치료"]
            },
            {
                "term": "PET-CT",
                "definition": "전신 영상 검사",
                "category": "검사/진단",
                "confidence": 0.95,
                "reason": "영상 검사",
                "evidence": "검사",
                "keywords": ["검사", "촬영", "진단"]
            },
            {
                "term": "말초신경병증",
                "definition": "항암제 관련 흔한 부작용",
                "category": "증상/부작용",
                "confidence": 0.94,
                "reason": "부작용 표현",
                "evidence": "부작용",
                "keywords": ["증상", "부작용", "병증"]
            },
            {
                "term": "BRAF V600E",
                "definition": "돌연변이 표적",
                "category": "유전자/분자",
                "confidence": 0.96,
                "reason": "변이 표기",
                "evidence": "돌연변이",
                "keywords": ["유전자", "변이", "분자"]
            },
            {
                "term": "NCT01234567",
                "definition": "3상 무작위배정 임상시험",
                "category": "임상시험/연구",
                "confidence": 0.97,
                "reason": "임상 식별자",
                "evidence": "3상 무작위배정",
                "keywords": ["임상", "NCT", "3상", "무작위"]
            },
            {
                "term": "간",
                "definition": "복강 내 장기",
                "category": "해부/생리",
                "confidence": 0.95,
                "reason": "장기",
                "evidence": "장기",
                "keywords": ["장기", "해부", "조직"]
            },
            {
                "term": "갑년",
                "definition": "흡연량 지표 단위",
                "category": "기타",
                "confidence": 0.94,
                "reason": "단위/지표",
                "evidence": "지표 단위",
                "keywords": ["단위", "지표"]
            }
        ]

        # Boundary Pack (10) - 헷갈리는 경계 케이스
        self.boundary_examples = [
            {
                "term": "키트루다 병용요법",
                "definition": "펨브롤리주맙과 화학요법 병용",
                "category": "치료법",
                "confidence": 0.95,
                "reason": "병용요법",
                "evidence": "병용",
                "keywords": ["요법", "병용", "치료법", "약제"]
            },
            {
                "term": "5-플루오로우라실",
                "definition": "항대사 항암제, 주사로 투여",
                "category": "약제",
                "confidence": 0.98,
                "reason": "항암제/투여",
                "evidence": "항암제",
                "keywords": ["항암제", "투여", "주사", "약제", "치료법"]
            },
            {
                "term": "HER2 양성 유방암",
                "definition": "유방암의 아형",
                "category": "암종",
                "confidence": 0.93,
                "reason": "암 아형",
                "evidence": "유방암",
                "keywords": ["암", "유방암", "HER2", "유전자"]
            },
            {
                "term": "EGFR-TKI",
                "definition": "EGFR 표적 치료제 계열",
                "category": "약제",
                "confidence": 0.9,
                "reason": "치료제 계열",
                "evidence": "치료제",
                "keywords": ["TKI", "EGFR", "약제", "유전자", "억제제"]
            },
            {
                "term": "기관지내시경",
                "definition": "진단 및 시술에 사용",
                "category": "치료법",
                "confidence": 0.9,
                "reason": "시술/처치",
                "evidence": "시술",
                "keywords": ["내시경", "시술", "검사", "치료법"]
            },
            {
                "term": "가슴샘암",
                "definition": "흉선에서 발생하는 암",
                "category": "암종",
                "confidence": 0.98,
                "reason": "암 종명",
                "evidence": "암",
                "keywords": ["암", "샘암", "흉선", "해부"]
            },
            {
                "term": "오심 구토",
                "definition": "항암치료 관련 흔한 증상",
                "category": "증상/부작용",
                "confidence": 0.93,
                "reason": "증상 표현",
                "evidence": "증상",
                "keywords": ["증상", "오심", "구토", "부작용"]
            },
            {
                "term": "beta-galactosidase assay",
                "definition": "효소 활성 측정 검사",
                "category": "검사/진단",
                "confidence": 0.93,
                "reason": "assay=검사",
                "evidence": "assay",
                "keywords": ["assay", "검사", "측정"]
            },
            {
                "term": "FOLFOX 요법",
                "definition": "대장암 표준 화학요법 레짐",
                "category": "치료법",
                "confidence": 0.96,
                "reason": "레짐명",
                "evidence": "레짐",
                "keywords": ["FOLFOX", "요법", "레짐", "화학요법"]
            },
            {
                "term": "트라스투주맙",
                "definition": "HER2 양성 암 치료용 단클론항체",
                "category": "약제",
                "confidence": 0.95,
                "reason": "치료용 항체",
                "evidence": "치료용",
                "keywords": ["mab", "항체", "약제", "HER2"]
            }
        ]

        # Noise Pack (3) - "기타" 유도
        self.noise_examples = [
            {
                "term": "그레이",
                "definition": "방사선 흡수선량 단위 (Gy)",
                "category": "기타",
                "confidence": 0.94,
                "reason": "단위",
                "evidence": "단위",
                "keywords": ["단위", "Gy", "그레이"]
            },
            {
                "term": "환자-년",
                "definition": "역학 연구 단위",
                "category": "기타",
                "confidence": 0.93,
                "reason": "통계 단위",
                "evidence": "단위",
                "keywords": ["단위", "환자-년"]
            },
            {
                "term": "5년 생존율",
                "definition": "예후 지표",
                "category": "기타",
                "confidence": 0.92,
                "reason": "지표",
                "evidence": "지표",
                "keywords": ["생존율", "지표"]
            }
        ]

    def _select_examples(self, keyword, content):
        """동적으로 Few-shot 예시 선택 (Core 3 + Boundary 3 + Noise 1 = 7개)"""

        text = f"{keyword} {content}".lower()

        # 키워드 매칭 점수 계산
        def score_example(example):
            score = 0
            for kw in example['keywords']:
                if kw in text:
                    score += 2
            # 카테고리 관련성도 고려
            if any(pattern in text for pattern in [
                'mab', 'nib', 'tinib', 'platin', '정', '주', '투여', '복용'
            ]) and example['category'] == '약제':
                score += 3
            if any(pattern in text for pattern in [
                '요법', '레짐', '술', '수술', '방사선', '화학요법'
            ]) and example['category'] == '치료법':
                score += 3
            if any(pattern in text for pattern in [
                '암', 'carcinoma', 'lymphoma', 'leukemia', '백혈병', '종양'
            ]) and example['category'] == '암종':
                score += 3
            if any(pattern in text for pattern in [
                'nct', '1상', '2상', '3상', '4상', '무작위', '임상시험'
            ]) and example['category'] == '임상시험/연구':
                score += 3
            if any(pattern in text for pattern in [
                'egfr', 'her2', 'pd-l1', 'kras', 'braf', 'v600e', '변이', '수용체'
            ]) and example['category'] == '유전자/분자':
                score += 3
            return score

        # Core에서 상위 3개
        core_scored = [(ex, score_example(ex)) for ex in self.core_examples]
        core_scored.sort(key=lambda x: x[1], reverse=True)
        selected_core = [ex for ex, score in core_scored[:3]]

        # Boundary에서 상위 3개
        boundary_scored = [(ex, score_example(ex)) for ex in self.boundary_examples]
        boundary_scored.sort(key=lambda x: x[1], reverse=True)
        selected_boundary = [ex for ex, score in boundary_scored[:3]]

        # Noise에서 1개 (무작위 또는 첫 번째)
        selected_noise = [self.noise_examples[0]]

        return selected_core + selected_boundary + selected_noise

    def create_system_message(self):
        """시스템 메시지 생성"""
        return """역할: 한국어 암 관련 의학 용어를 아래 9개 카테고리 중 정확히 하나로 분류하는 분류기.

카테고리(폐집합): ["약제","암종","치료법","검사/진단","증상/부작용","유전자/분자","임상시험/연구","해부/생리","기타"]

필수 규칙:
1. 반드시 위 9개 중 1개만 선택.
2. 분류 대상은 '용어' 자체. '정의'는 보조 근거로만 사용.
3. 모호할 때는 더 좁고 임상적으로 유의미한 범주 선택.
4. 임상시험 키워드(1상/2상/3상/무작위/대조군/NCT) → 임상시험/연구
5. 레짐명(ABVD,R-CHOP,FOLFOX,XELOX) + ~요법/~술/수술/방사선 → 치료법
6. 약제 단서(투여/복용/용량/정/주/캡슐/억제제/길항제/-mab/-nib/platin) → 약제
7. 암종 단서(~암/종/백혈병/carcinoma/lymphoma/leukemia) → 암종
8. 유전자/분자 단서(EGFR/BRAF/PD-L1/수용체/단백질/바이오마커/변이) → 유전자/분자
9. "기타"는 단위/지표/개념만 사용.

자체 검증:
- category는 위 9개 중 하나만.
- 암종 선택 시: 용어/정의에 암종 단서 직접 등장.
- 임상시험 키워드 있으면 암종/약제/치료법 금지.
- evidence는 입력에서 직접 발췌 3~30자만(창작 금지).

출력 스키마:
{
  "term": "입력 용어 원문",
  "category": "9개 중 1개",
  "confidence": 0.0~1.0,
  "reason": "한 줄 근거",
  "evidence": "입력에서 발췌 3~30자"
}

출력은 JSON만. 중괄호 밖 문자 금지."""

    def create_user_prompt(self, keyword, content):
        """동적 Few-shot 프롬프트 생성"""

        # 동적으로 예시 선택
        examples = self._select_examples(keyword, content)

        # Few-shot 예시 포맷팅
        fewshot_text = ""
        for i, ex in enumerate(examples, 1):
            fewshot_text += f"""\n{i}) 용어: "{ex['term']}"
   정의: {ex['definition']}
   출력: {{"term":"{ex['term']}","category":"{ex['category']}","confidence":{ex['confidence']},"reason":"{ex['reason']}","evidence":"{ex['evidence']}"}}
"""

        prompt = f"""용어: "{keyword}"
정의: {content[:800] if content else "(정의 없음)"}

Few-shot 예시 (유사 케이스):{fewshot_text}

위 형식으로 분류하세요."""

        return prompt

    def classify_single(self, keyword, content, model="gpt-4o-mini"):
        """단일 용어 분류"""
        try:
            system_msg = self.create_system_message()
            user_prompt = self.create_user_prompt(keyword, content)

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content.strip()

            # JSON 블록 추출
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)

            # 스키마 검증
            category = result.get('category', '기타')
            if category not in self.categories:
                print(f"[경고] 잘못된 카테고리 ({keyword}): {category} -> 기타")
                category = '기타'

            return {
                'term': result.get('term', keyword),
                'category': category,
                'confidence': result.get('confidence', 0.5),
                'reason': result.get('reason', result.get('reasoning', '')),
                'evidence': result.get('evidence', '')[:50],
                'model': model,
                'status': 'success'
            }

        except json.JSONDecodeError as e:
            print(f"[오류] JSON 파싱 ({keyword}): {str(e)[:50]}")
            return {
                'category': '기타',
                'confidence': 0.0,
                'reason': f'JSON 오류',
                'evidence': '',
                'model': model,
                'status': 'error'
            }

        except Exception as e:
            print(f"[오류] 분류 실패 ({keyword}): {str(e)[:50]}")
            return {
                'category': '기타',
                'confidence': 0.0,
                'reason': f'오류',
                'evidence': '',
                'model': model,
                'status': 'error'
            }

    def classify_all(self, batch_size=50, delay=0.5, model="gpt-4o-mini"):
        """전체 3,543개 항목 분류"""
        data_dir = Path("data/ncc/cancer_dictionary/parsed")
        all_terms = []

        for i in range(1, 13):
            batch_file = data_dir / f"batch_{i:04d}.json"
            with open(batch_file, 'r', encoding='utf-8') as f:
                all_terms.extend(json.load(f))

        total = len(all_terms)
        print(f"\n총 {total}개 항목 동적 Few-shot LLM 분류 시작...")
        print(f"모델: {model}")
        print(f"배치 크기: {batch_size}개")
        print(f"예상 비용: ${total * 0.0003:.2f} (GPT-4o-mini)")
        print(f"예상 시간: {total * (delay + 1) / 60:.1f}분\n")

        results = []
        start_time = time.time()

        for i, term in enumerate(all_terms, 1):
            keyword = term['keyword']
            content = term['content']

            llm_result = self.classify_single(keyword, content, model)

            result = {
                'keyword': keyword,
                'content': content[:200],
                'llm': llm_result,
                'final_category': llm_result['category']
            }

            results.append(result)

            # 진행 상황
            if i % 10 == 0 or i == total:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / rate if rate > 0 else 0
                print(f"진행: {i}/{total} ({i/total*100:.1f}%) | "
                      f"속도: {rate:.1f}건/초 | ETA: {eta/60:.1f}분 | "
                      f"{keyword} → {llm_result['category']}")

            # 중간 저장
            if i % batch_size == 0:
                self._save_intermediate(results, i//batch_size)

            if i < total:
                time.sleep(delay)

        elapsed = time.time() - start_time
        print(f"\n[완료] 총 소요 시간: {elapsed/60:.1f}분")

        return results

    def _save_intermediate(self, results, batch_num):
        """중간 결과 저장"""
        output_dir = Path("ncc/cancer_dictionary/llm_dynamic_results")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"batch_{batch_num:04d}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"  [중간저장] {output_file}")


def main():
    """메인 실행"""
    import sys

    print("=" * 70)
    print("NCC 암정보 사전 동적 Few-shot LLM 분류 (v3)")
    print("=" * 70)

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n[오류] OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    try:
        classifier = DynamicFewShotClassifier(api_key=api_key)
        print("\n[완료] OpenAI API 연결 성공")
        print(f"[완료] Few-shot 풀: Core {len(classifier.core_examples)} + "
              f"Boundary {len(classifier.boundary_examples)} + "
              f"Noise {len(classifier.noise_examples)} = "
              f"{len(classifier.core_examples) + len(classifier.boundary_examples) + len(classifier.noise_examples)}개")
    except Exception as e:
        print(f"\n[오류] 초기화 실패: {e}")
        sys.exit(1)

    start_time = time.time()
    results = classifier.classify_all(
        batch_size=50,
        delay=0.5,
        model="gpt-4o-mini"
    )

    elapsed = time.time() - start_time

    # 최종 결과 저장
    output_file = Path("data/ncc/cancer_dictionary/llm_classified_dynamic.json")

    category_counts = Counter()
    confidence_sum = {}
    confidence_count = {}

    for result in results:
        cat = result['final_category']
        conf = result['llm']['confidence']

        category_counts[cat] += 1

        if cat not in confidence_sum:
            confidence_sum[cat] = 0
            confidence_count[cat] = 0

        confidence_sum[cat] += conf
        confidence_count[cat] += 1

    avg_confidence = {}
    for cat in category_counts.keys():
        avg_confidence[cat] = confidence_sum[cat] / confidence_count[cat]

    output_data = {
        'summary': {
            'total_classified': len(results),
            'model': 'gpt-4o-mini',
            'method': 'dynamic_fewshot',
            'elapsed_time': elapsed,
            'category_distribution': dict(category_counts),
            'avg_confidence_by_category': avg_confidence
        },
        'results': results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n[저장] 최종 결과: {output_file}")

    # 통계
    print("\n[동적 Few-shot LLM 분류 통계]")
    print("-" * 70)
    for cat, count in category_counts.most_common():
        avg_conf = avg_confidence[cat]
        print(f"  {cat:20s}: {count:5d}개 ({count/len(results)*100:5.1f}%) | "
              f"평균 신뢰도: {avg_conf:.2f}")

    print(f"\n  {'총계':20s}: {len(results):5d}개 (100.0%)")


if __name__ == '__main__':
    main()
