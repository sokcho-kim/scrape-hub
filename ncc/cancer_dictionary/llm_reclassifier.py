"""LLM 기반 재분류기 - 낮은 신뢰도 항목 재심사"""
import json
import os
import time
from pathlib import Path
from collections import Counter
import openai

# .env 파일 로드 (있으면)
try:
    from dotenv import load_dotenv
    load_dotenv()  # .env 파일에서 환경변수 로드
    print("[INFO] .env 파일 로드 완료")
except ImportError:
    print("[INFO] python-dotenv 없음, 환경변수에서 직접 읽음")


class LLMReclassifier:
    """OpenAI GPT를 사용한 의학 용어 재분류기"""

    def __init__(self, api_key=None):
        """초기화

        Args:
            api_key: OpenAI API 키. None이면 환경변수에서 읽음
        """
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')

        if not self.api_key:
            raise ValueError("OpenAI API 키가 필요합니다. 환경변수 OPENAI_API_KEY를 설정하거나 직접 입력해주세요.")

        # OpenAI 클라이언트 설정 (v1.0.0+ API)
        self.client = openai.OpenAI(api_key=self.api_key)

        # 카테고리 정의
        self.categories = [
            "약제",
            "암종",
            "치료법",
            "검사/진단",
            "증상/부작용",
            "유전자/분자",
            "임상시험/연구",
            "해부/생리",
            "기타"
        ]

    def create_prompt(self, keyword, content):
        """분류를 위한 프롬프트 생성"""

        prompt = f"""당신은 의학 용어 분류 전문가입니다.

다음 의학 용어를 정확히 분류해주세요.

**용어**: {keyword}
**정의**: {content[:500]}

**분류 카테고리**:
1. 약제 - 치료에 사용되는 약물, 약제, 억제제, 길항제 등
2. 암종 - 암의 종류 (갑상선암, 위암, 백혈병 등)
3. 치료법 - 수술, 방사선, 화학요법, ~요법, ~술 등
4. 검사/진단 - 검사, 촬영, 진단 방법 등
5. 증상/부작용 - 증상, 징후, 부작용, 합병증 등
6. 유전자/분자 - 유전자, 단백질, 수용체, 바이오마커 등
7. 임상시험/연구 - 1상/2상/3상 임상시험, 연구 방법 등
8. 해부/생리 - 장기, 조직, 세포, 해부학적 구조 등
9. 기타 - 위 카테고리에 해당하지 않는 경우

**중요 규칙**:
- "~암 치료에 사용되는 약제"는 **약제**입니다 (암종 아님)
- "1상 임상시험", "2상 임상시험"은 **임상시험/연구**입니다
- "ABVD 요법", "AC 요법" 같은 레짐명은 **치료법**입니다
- "억제제", "길항제"가 포함되면 대부분 **약제**입니다

다음 JSON 형식으로만 응답하세요:
{{
  "category": "카테고리명",
  "confidence": 0.95,
  "reasoning": "간단한 이유 (1-2문장)"
}}
"""
        return prompt

    def classify_single(self, keyword, content, model="gpt-4o-mini"):
        """단일 용어 분류"""
        try:
            prompt = self.create_prompt(keyword, content)

            # OpenAI v1.0.0+ API 사용
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "당신은 의학 용어 분류 전문가입니다. 항상 JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 일관성을 위해 낮게
                max_tokens=200
            )

            # JSON 파싱
            result_text = response.choices[0].message.content.strip()

            # JSON 블록 추출 (```json ... ``` 제거)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)

            return {
                'category': result.get('category', '기타'),
                'confidence': result.get('confidence', 0.5),
                'reasoning': result.get('reasoning', ''),
                'model': model,
                'status': 'success'
            }

        except json.JSONDecodeError as e:
            print(f"[오류] JSON 파싱 실패 ({keyword}): {result_text}")
            return {
                'category': '기타',
                'confidence': 0.0,
                'reasoning': f'JSON 파싱 오류: {str(e)}',
                'model': model,
                'status': 'error'
            }

        except Exception as e:
            print(f"[오류] 분류 실패 ({keyword}): {str(e)}")
            return {
                'category': '기타',
                'confidence': 0.0,
                'reasoning': f'오류: {str(e)}',
                'model': model,
                'status': 'error'
            }

    def reclassify_batch(self, terms, batch_size=10, delay=1.0, model="gpt-4o-mini"):
        """배치 재분류

        Args:
            terms: 재분류할 용어 리스트
            batch_size: 중간 저장 단위
            delay: API 요청 간 대기 시간 (초)
            model: 사용할 모델 (gpt-4o-mini 추천)
        """
        results = []
        total = len(terms)

        print(f"\n총 {total}개 항목 재분류 시작...")
        print(f"모델: {model}")
        print(f"배치 크기: {batch_size}개")
        print(f"예상 비용: ${total * 0.0003:.2f} (GPT-4o-mini 기준)\n")

        for i, term in enumerate(terms, 1):
            keyword = term['keyword']
            content = term['content']

            # LLM 재분류
            llm_result = self.classify_single(keyword, content, model)

            # 결과 저장
            result = {
                'keyword': keyword,
                'content': content[:200],
                'rule_based': {
                    'categories': term.get('categories', ['기타']),
                    'confidence': term.get('confidence', 0.0)
                },
                'llm': llm_result,
                'final_category': llm_result['category']
            }

            results.append(result)

            # 진행 상황 출력
            if i % 10 == 0 or i == total:
                print(f"진행: {i}/{total} ({i/total*100:.1f}%) - 마지막: {keyword} -> {llm_result['category']}")

            # 중간 저장 (배치 단위)
            if i % batch_size == 0:
                self._save_intermediate(results, batch_num=i//batch_size)

            # API Rate Limit 방지
            if i < total:
                time.sleep(delay)

        return results

    def _save_intermediate(self, results, batch_num):
        """중간 결과 저장"""
        output_dir = Path("ncc/cancer_dictionary/llm_results")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"batch_{batch_num:04d}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"  [중간저장] {output_file}")


def main():
    """메인 실행"""
    import sys

    print("=" * 70)
    print("NCC 암정보 사전 LLM 재분류")
    print("=" * 70)

    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n[오류] OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("\n다음과 같이 설정해주세요:")
        print("  export OPENAI_API_KEY='sk-proj-xxxxx...'")
        print("\n또는 직접 입력:")
        api_key = input("OpenAI API Key: ").strip()

        if not api_key:
            print("[중단] API 키가 필요합니다.")
            sys.exit(1)

    # 재분류기 초기화
    try:
        classifier = LLMReclassifier(api_key=api_key)
        print("\n[완료] OpenAI API 연결 성공")
    except Exception as e:
        print(f"\n[오류] API 초기화 실패: {e}")
        sys.exit(1)

    # 낮은 신뢰도 항목 로드
    v2_file = Path("data/ncc/cancer_dictionary/classified_terms_v2.json")

    if not v2_file.exists():
        print(f"\n[오류] 파일을 찾을 수 없습니다: {v2_file}")
        sys.exit(1)

    with open(v2_file, 'r', encoding='utf-8') as f:
        v2_data = json.load(f)

    # 낮은 신뢰도 (<0.3) 항목 필터링
    low_confidence = [
        term for term in v2_data['classified_terms']
        if term.get('confidence', 0) < 0.3
    ]

    print(f"\n[대상] 낮은 신뢰도 항목: {len(low_confidence)}개 (신뢰도 < 0.3)")
    print(f"[예상 비용] ${len(low_confidence) * 0.0003:.2f} (GPT-4o-mini)")
    print("\n[시작] 재분류 시작...")

    # 재분류 실행
    start_time = time.time()
    results = classifier.reclassify_batch(
        low_confidence,
        batch_size=50,  # 50개마다 중간 저장
        delay=0.5,      # 0.5초 대기
        model="gpt-4o-mini"
    )

    elapsed = time.time() - start_time
    print(f"\n\n[완료] 총 소요 시간: {elapsed/60:.1f}분")

    # 최종 결과 저장
    output_file = Path("data/ncc/cancer_dictionary/llm_reclassified.json")

    # 통계
    category_counts = Counter()
    for result in results:
        category_counts[result['final_category']] += 1

    output_data = {
        'summary': {
            'total_reclassified': len(results),
            'model': 'gpt-4o-mini',
            'elapsed_time': elapsed,
            'category_distribution': dict(category_counts)
        },
        'results': results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n[저장] 최종 결과: {output_file}")

    # 통계 출력
    print("\n[재분류 통계]")
    print("-" * 70)
    for cat, count in category_counts.most_common():
        print(f"  {cat:20s}: {count:5d}개 ({count/len(results)*100:5.1f}%)")


if __name__ == '__main__':
    main()
