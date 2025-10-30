"""전체 3,543개 NCC 암정보 사전 LLM 분류 (개선된 프롬프트)"""
import json
import os
import time
from pathlib import Path
from collections import Counter
import openai

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[INFO] .env 파일 로드 완료")
except ImportError:
    print("[INFO] python-dotenv 없음, 환경변수에서 직접 읽음")


class ImprovedLLMClassifier:
    """개선된 프롬프트를 사용한 LLM 분류기"""

    def __init__(self, api_key=None):
        """초기화"""
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')

        if not self.api_key:
            raise ValueError("OpenAI API 키가 필요합니다.")

        self.client = openai.OpenAI(api_key=self.api_key)

        # NCC 암종 화이트리스트 로드
        self.cancer_whitelist = self._load_cancer_whitelist()

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

    def _load_cancer_whitelist(self):
        """NCC 100개 암종 화이트리스트 로드"""
        cancer_file = Path("ncc/cancer_dictionary/ncc_cancer_list.json")

        if not cancer_file.exists():
            print("[경고] NCC 암종 리스트 파일이 없습니다.")
            return []

        with open(cancer_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data['cancer_names'][:20]  # 프롬프트에는 상위 20개만 포함

    def create_system_message(self):
        """시스템 메시지 생성 (역할 정의)"""
        return """역할: 한국어 암 관련 의학 용어를 아래 9개 카테고리 중 정확히 하나로 분류하는 분류기.

카테고리(폐집합): ["약제","암종","치료법","검사/진단","증상/부작용","유전자/분자","임상시험/연구","해부/생리","기타"]

필수 규칙:
1. 반드시 위 9개 중 1개만 선택.
2. 분류 대상은 '용어' 자체. '정의'는 보조 근거로만 사용.
3. 모호할 때는 더 좁고 임상적으로 유의미한 범주 선택.
4. 임상시험 키워드(1상/2상/3상/무작위/대조군/프로토콜) → 임상시험/연구
5. 레짐명(ABVD,R-CHOP,FOLFOX) + ~요법/~술/수술/방사선 → 치료법
6. 약제 단서(투여/복용/용량/정/주/캡슐/억제제/길항제/-mab/-nib/platin) → 약제
7. 암종 단서(~암/종/백혈병/carcinoma/lymphoma/leukemia) → 암종
8. 유전자/분자 단서(EGFR/BRAF/PD-L1/수용체/단백질/바이오마커/변이) → 유전자/분자
9. "기타"는 정말 분류 불가능할 때만 사용.

자체 검증(위반 시 재생성):
- category는 위 9개 중 하나만.
- 암종 선택 시: 용어/정의에 암종 단서 직접 등장 필수.
- 임상시험 키워드 있으면 암종/약제/치료법 금지.
- evidence는 입력에서 직접 발췌한 3~30자만(창작 금지).

출력 스키마(키 고정):
{
  "term": "입력 용어 원문",
  "category": "9개 중 1개",
  "confidence": 0.0~1.0,
  "reason": "한 줄 근거",
  "evidence": "입력에서 발췌한 핵심 구절 3~30자"
}

출력은 JSON만. 중괄호 밖 문자 금지."""

    def create_user_prompt(self, keyword, content):
        """개선된 사용자 프롬프트 생성 (Few-shot 포함)"""

        # NCC 암종 리스트 샘플
        cancer_examples = ", ".join(self.cancer_whitelist[:10])

        prompt = f"""용어: "{keyword}"
정의: {content[:800] if content else "(정의 없음)"}

참고: NCC 주요 암종 - {cancer_examples}, ...

Few-shot 예시:

1) 용어: "타목시펜"
   정의: "에스트로겐 수용체 길항제. 유방암 치료에 경구 투여."
   출력: {{"term":"타목시펜","category":"약제","confidence":0.96,"reason":"치료용 약물, 투여 단서","evidence":"치료에 경구 투여"}}

2) 용어: "R-CHOP"
   정의: "비호지킨림프종 치료 레짐. 리툭시맙, 사이클로포스파마이드, 독소루비신, 빈크리스틴, 프레드니손 병용."
   출력: {{"term":"R-CHOP","category":"치료법","confidence":0.97,"reason":"레짐명","evidence":"치료 레짐"}}

3) 용어: "BRAF V600E"
   정의: "BRAF 유전자의 600번째 코돈 돌연변이. 흑색종의 표적."
   출력: {{"term":"BRAF V600E","category":"유전자/분자","confidence":0.97,"reason":"유전자 변이","evidence":"유전자의 600번째 코돈 돌연변이"}}

4) 용어: "2상 임상시험"
   정의: "약물의 유효성을 평가하는 연구 단계."
   출력: {{"term":"2상 임상시험","category":"임상시험/연구","confidence":0.98,"reason":"임상시험 단계","evidence":"연구 단계"}}

5) 용어: "급성림프모구백혈병"
   정의: "림프모구가 골수와 혈액에서 비정상적으로 증식하는 암."
   출력: {{"term":"급성림프모구백혈병","category":"암종","confidence":0.98,"reason":"백혈병 명칭","evidence":"암"}}

6) 용어: "PET-CT"
   정의: "양전자방출단층촬영과 컴퓨터단층촬영을 결합한 영상검사."
   출력: {{"term":"PET-CT","category":"검사/진단","confidence":0.98,"reason":"영상검사","evidence":"영상검사"}}

위 형식으로 아래 용어를 분류하세요."""

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
                temperature=0.0,  # 결정적 출력
                max_tokens=200,
                response_format={"type": "json_object"}  # JSON 모드 강제
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
                print(f"[경고] 잘못된 카테고리 ({keyword}): {category} -> 기타로 변경")
                category = '기타'

            return {
                'term': result.get('term', keyword),
                'category': category,
                'confidence': result.get('confidence', 0.5),
                'reason': result.get('reason', result.get('reasoning', '')),
                'evidence': result.get('evidence', '')[:50],  # 최대 50자
                'model': model,
                'status': 'success'
            }

        except json.JSONDecodeError as e:
            print(f"[오류] JSON 파싱 실패 ({keyword}): {result_text[:100]}")
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

    def classify_all(self, batch_size=50, delay=0.5, model="gpt-4o-mini"):
        """전체 3,543개 항목 분류"""
        # 모든 배치 파일 로드
        data_dir = Path("data/ncc/cancer_dictionary/parsed")
        all_terms = []

        for i in range(1, 13):
            batch_file = data_dir / f"batch_{i:04d}.json"
            with open(batch_file, 'r', encoding='utf-8') as f:
                all_terms.extend(json.load(f))

        total = len(all_terms)
        print(f"\n총 {total}개 항목 LLM 분류 시작...")
        print(f"모델: {model}")
        print(f"배치 크기: {batch_size}개")
        print(f"예상 비용: ${total * 0.0003:.2f} (GPT-4o-mini 기준)")
        print(f"예상 소요 시간: {total * (delay + 1) / 60:.1f}분\n")

        results = []
        start_time = time.time()

        for i, term in enumerate(all_terms, 1):
            keyword = term['keyword']
            content = term['content']

            # LLM 분류
            llm_result = self.classify_single(keyword, content, model)

            # 결과 저장
            result = {
                'keyword': keyword,
                'content': content[:200],
                'llm': llm_result,
                'final_category': llm_result['category']
            }

            results.append(result)

            # 진행 상황 출력
            if i % 10 == 0 or i == total:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / rate if rate > 0 else 0
                print(f"진행: {i}/{total} ({i/total*100:.1f}%) | "
                      f"속도: {rate:.1f}건/초 | "
                      f"남은 시간: {eta/60:.1f}분 | "
                      f"마지막: {keyword} -> {llm_result['category']}")

            # 중간 저장 (배치 단위)
            if i % batch_size == 0:
                self._save_intermediate(results, batch_num=i//batch_size)

            # API Rate Limit 방지
            if i < total:
                time.sleep(delay)

        elapsed = time.time() - start_time
        print(f"\n[완료] 총 소요 시간: {elapsed/60:.1f}분")

        return results

    def _save_intermediate(self, results, batch_num):
        """중간 결과 저장"""
        output_dir = Path("ncc/cancer_dictionary/llm_full_results")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"batch_{batch_num:04d}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"  [중간저장] {output_file}")


def main():
    """메인 실행"""
    import sys

    print("=" * 70)
    print("NCC 암정보 사전 전체 LLM 분류 (개선된 프롬프트)")
    print("=" * 70)

    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n[오류] OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("\n다음과 같이 설정해주세요:")
        print("  export OPENAI_API_KEY='sk-proj-xxxxx...'")
        sys.exit(1)

    # 분류기 초기화
    try:
        classifier = ImprovedLLMClassifier(api_key=api_key)
        print("\n[완료] OpenAI API 연결 성공")
        print(f"[완료] NCC 암종 화이트리스트 {len(classifier.cancer_whitelist)}개 로드")
    except Exception as e:
        print(f"\n[오류] API 초기화 실패: {e}")
        sys.exit(1)

    # 전체 분류 실행
    start_time = time.time()
    results = classifier.classify_all(
        batch_size=50,
        delay=0.5,
        model="gpt-4o-mini"
    )

    elapsed = time.time() - start_time
    print(f"\n[완료] 총 소요 시간: {elapsed/60:.1f}분")

    # 최종 결과 저장
    output_file = Path("data/ncc/cancer_dictionary/llm_classified_full.json")

    # 통계
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

    # 평균 신뢰도 계산
    avg_confidence = {}
    for cat in category_counts.keys():
        avg_confidence[cat] = confidence_sum[cat] / confidence_count[cat]

    output_data = {
        'summary': {
            'total_classified': len(results),
            'model': 'gpt-4o-mini',
            'elapsed_time': elapsed,
            'category_distribution': dict(category_counts),
            'avg_confidence_by_category': avg_confidence
        },
        'results': results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n[저장] 최종 결과: {output_file}")

    # 통계 출력
    print("\n[LLM 분류 통계]")
    print("-" * 70)
    for cat, count in category_counts.most_common():
        avg_conf = avg_confidence[cat]
        print(f"  {cat:20s}: {count:5d}개 ({count/len(results)*100:5.1f}%) | "
              f"평균 신뢰도: {avg_conf:.2f}")

    print(f"\n  {'총계':20s}: {len(results):5d}개 (100.0%)")


if __name__ == '__main__':
    main()
