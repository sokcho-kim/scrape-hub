"""대용량 PDF 분할 및 파싱

전략:
1. PDF를 10-20페이지씩 분할
2. 각 부분을 Upstage API로 파싱
3. 결과를 병합하여 전체 문서 생성
"""
import sys
import codecs
from pathlib import Path
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.parsers import UpstageParser

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()


class PDFSplitParser:
    """PDF 분할 파서"""

    def __init__(self, output_dir: str = 'data/hira_master/parsed', chunk_pages: int = 20):
        """
        Args:
            output_dir: 출력 디렉토리
            chunk_pages: 한 번에 처리할 페이지 수
        """
        api_key = os.getenv('UPSTAGE_API_KEY')
        if not api_key:
            raise ValueError('UPSTAGE_API_KEY not found in .env')

        self.parser = UpstageParser(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.chunk_pages = chunk_pages

        # 임시 분할 파일 저장 위치
        self.temp_dir = self.output_dir / 'temp_chunks'
        self.temp_dir.mkdir(exist_ok=True)

    def split_pdf(self, pdf_path: Path) -> list[Path]:
        """PDF를 여러 파일로 분할

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            분할된 PDF 파일 경로 리스트
        """
        print(f'\n📄 PDF 분할: {pdf_path.name}')

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        print(f'  총 페이지: {total_pages}p')
        print(f'  분할 단위: {self.chunk_pages}p')
        print(f'  예상 파일: {(total_pages + self.chunk_pages - 1) // self.chunk_pages}개')

        chunks = []

        for start_page in range(0, total_pages, self.chunk_pages):
            end_page = min(start_page + self.chunk_pages, total_pages)

            # 새 PDF 생성
            writer = PdfWriter()
            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])

            # 저장
            chunk_filename = f'{pdf_path.stem}_pages_{start_page+1}-{end_page}.pdf'
            chunk_path = self.temp_dir / chunk_filename
            writer.write(chunk_path)

            chunks.append(chunk_path)
            print(f'  ✅ {chunk_filename} ({end_page - start_page}p)')

        return chunks

    def parse_chunks(self, chunk_paths: list[Path]) -> list[dict]:
        """분할된 PDF 파일들 파싱

        Args:
            chunk_paths: 분할된 PDF 경로 리스트

        Returns:
            파싱 결과 리스트
        """
        print(f'\n🔄 청크 파싱: {len(chunk_paths)}개')

        results = []

        for i, chunk_path in enumerate(chunk_paths, 1):
            print(f'\n[{i}/{len(chunk_paths)}] {chunk_path.name}')

            try:
                result = self.parser.parse(chunk_path)

                if result:
                    print(f'  ✅ 성공: {result.get("pages")}p, {len(result.get("content", ""))}자')
                    results.append(result)
                else:
                    print(f'  ❌ 실패')
                    results.append(None)

            except Exception as e:
                print(f'  ❌ 에러: {e}')
                results.append(None)

        return results

    def merge_results(self, results: list[dict], source_file: str) -> dict:
        """파싱 결과 병합

        Args:
            results: 파싱 결과 리스트
            source_file: 원본 파일명

        Returns:
            병합된 결과
        """
        print(f'\n🔗 결과 병합')

        # None 필터링
        valid_results = [r for r in results if r is not None]

        if not valid_results:
            return None

        # Markdown 병합
        merged_content = '\n\n---\n\n'.join([
            r.get('content', '') for r in valid_results
        ])

        # HTML 병합
        merged_html = '\n<hr>\n'.join([
            r.get('html', '') for r in valid_results
        ])

        # 총 페이지 수
        total_pages = sum(r.get('pages', 0) for r in valid_results)

        merged = {
            'source_file': source_file,
            'total_pages': total_pages,
            'chunks_parsed': len(valid_results),
            'chunks_failed': len(results) - len(valid_results),
            'content': merged_content,
            'html': merged_html,
            'model': valid_results[0].get('model') if valid_results else None,
            'parsed_at': datetime.now().isoformat()
        }

        print(f'  ✅ 병합 완료: {total_pages}p, {len(merged_content)}자')

        return merged

    def cleanup_temp_files(self):
        """임시 파일 삭제"""
        print(f'\n🧹 임시 파일 정리')

        for file in self.temp_dir.glob('*.pdf'):
            file.unlink()
            print(f'  삭제: {file.name}')

    def parse_large_pdf(self, pdf_path: Path) -> dict:
        """대용량 PDF 전체 파싱 프로세스

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            병합된 파싱 결과
        """
        print(f'\n{"="*80}')
        print(f'📚 대용량 PDF 파싱: {pdf_path.name}')
        print(f'{"="*80}')

        # 1. PDF 분할
        chunks = self.split_pdf(pdf_path)

        # 2. 각 청크 파싱
        results = self.parse_chunks(chunks)

        # 3. 결과 병합
        merged = self.merge_results(results, pdf_path.name)

        # 4. 저장
        if merged:
            output_file = self.output_dir / f'{pdf_path.stem}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            print(f'\n💾 저장: {output_file}')

            # 미리보기
            print(f'\n[Markdown 미리보기 (처음 500자)]')
            print('-' * 80)
            print(merged['content'][:500])
            print('-' * 80)

        # 5. 임시 파일 정리
        self.cleanup_temp_files()

        return merged


def main():
    """메인 실행"""
    print('=' * 80)
    print('🏥 HIRA 마스터 데이터 PDF 분할 파싱')
    print('=' * 80)

    parser = PDFSplitParser(chunk_pages=20)  # 20페이지씩 분할

    # 파싱할 PDF 목록
    master_dir = Path('data/hira_master')
    pdfs = [
        master_dir / 'KCD-8 1권_220630_20220630034856.pdf',
        master_dir / 'KDRG 분류집(신포괄지불제도용 ver1.4).pdf',
    ]

    results_summary = {}

    for pdf_path in pdfs:
        if not pdf_path.exists():
            print(f'⚠️ 파일 없음: {pdf_path}')
            continue

        try:
            result = parser.parse_large_pdf(pdf_path)

            if result:
                results_summary[pdf_path.stem] = {
                    'pages': result.get('total_pages'),
                    'chunks': result.get('chunks_parsed'),
                    'failed': result.get('chunks_failed'),
                    'success': True
                }
            else:
                results_summary[pdf_path.stem] = {
                    'success': False,
                    'error': 'Parsing failed'
                }

        except Exception as e:
            print(f'❌ 전체 에러: {e}')
            import traceback
            traceback.print_exc()
            results_summary[pdf_path.stem] = {
                'success': False,
                'error': str(e)
            }

    # 최종 요약
    print('\n\n' + '=' * 80)
    print('📊 파싱 요약')
    print('=' * 80)

    for name, info in results_summary.items():
        if info.get('success'):
            print(f'✅ {name}:')
            print(f'   페이지: {info.get("pages")}p')
            print(f'   청크: {info.get("chunks")}개 성공, {info.get("failed")}개 실패')
        else:
            print(f'❌ {name}: {info.get("error")}')

    # 통계 저장
    summary_file = parser.output_dir / '_parsing_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'parsed_at': datetime.now().isoformat(),
            'results': results_summary
        }, f, ensure_ascii=False, indent=2)

    print(f'\n💾 요약 저장: {summary_file}')

    print('\n' + '=' * 80)
    print('✅ 전체 파싱 완료')
    print('=' * 80)


if __name__ == '__main__':
    main()
