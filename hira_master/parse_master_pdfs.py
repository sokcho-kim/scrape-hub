"""HIRA 마스터 PDF 파싱

파일:
1. KCD-8 1권 - 한국표준질병사인분류 (질환 코드 마스터)
2. KDRG 분류집 - 진단군 분류 (신포괄지불제도)

목적:
- Upstage Parser로 PDF 파싱
- Graph RAG 엔티티 매칭용 마스터 데이터 구축
"""
import sys
import codecs
from pathlib import Path
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트를 Python path에 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.parsers import UpstageParser

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# .env 로드
load_dotenv()


class MasterPDFParser:
    """마스터 PDF 파서"""

    def __init__(self, output_dir: str = 'data/hira_master/parsed'):
        api_key = os.getenv('UPSTAGE_API_KEY')
        if not api_key:
            raise ValueError('UPSTAGE_API_KEY not found in .env')

        self.parser = UpstageParser(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def parse_pdf(self, pdf_path: Path, sample_pages: int = None) -> dict:
        """단일 PDF 파싱

        Args:
            pdf_path: PDF 파일 경로
            sample_pages: 샘플 페이지 수 (None이면 전체)
        """
        print(f'\n{"="*80}')
        print(f'📄 파싱: {pdf_path.name}')
        print(f'{"="*80}')

        # 파싱 실행 (Path 객체 그대로 전달)
        result = self.parser.parse(pdf_path)

        if result:
            # 메타데이터 추가
            result['source_file'] = pdf_path.name
            result['parsed_at'] = datetime.now().isoformat()

            # 통계 출력
            print(f'✅ 파싱 성공')
            print(f'  - 페이지: {result.get("pages", 0)}p')
            print(f'  - 모델: {result.get("model")}')
            print(f'  - Markdown 길이: {len(result.get("content", ""))}자')
            print(f'  - HTML 길이: {len(result.get("html", ""))}자')

            # 샘플 출력
            content = result.get('content', '')
            print(f'\n[Markdown 미리보기 (처음 500자)]')
            print('-' * 80)
            print(content[:500])
            print('-' * 80)

            # 저장
            output_file = self.output_dir / f'{pdf_path.stem}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f'\n💾 저장: {output_file}')

            return result
        else:
            print(f'❌ 파싱 실패')
            return None


def main():
    """메인 실행"""
    print('=' * 80)
    print('🏥 HIRA 마스터 데이터 PDF 파싱')
    print('=' * 80)

    parser = MasterPDFParser()

    # 파싱할 PDF 목록
    master_dir = Path('data/hira_master')
    pdfs = [
        master_dir / 'KCD-8 1권_220630_20220630034856.pdf',
        master_dir / 'KDRG 분류집(신포괄지불제도용 ver1.4).pdf',
    ]

    results = {}

    for pdf_path in pdfs:
        if not pdf_path.exists():
            print(f'⚠️ 파일 없음: {pdf_path}')
            continue

        try:
            result = parser.parse_pdf(pdf_path)
            if result:
                results[pdf_path.stem] = {
                    'pages': result.get('pages'),
                    'success': True
                }
            else:
                results[pdf_path.stem] = {
                    'success': False,
                    'error': 'Parsing failed'
                }
        except Exception as e:
            print(f'❌ 에러: {e}')
            results[pdf_path.stem] = {
                'success': False,
                'error': str(e)
            }

    # 최종 요약
    print('\n\n' + '=' * 80)
    print('📊 파싱 요약')
    print('=' * 80)

    for name, info in results.items():
        if info.get('success'):
            print(f'✅ {name}: {info.get("pages")}p')
        else:
            print(f'❌ {name}: {info.get("error")}')

    # 통계 저장
    summary_file = parser.output_dir / '_parsing_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'parsed_at': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f'\n💾 요약 저장: {summary_file}')

    print('\n' + '=' * 80)
    print('✅ 파싱 완료')
    print('=' * 80)


if __name__ == '__main__':
    main()
