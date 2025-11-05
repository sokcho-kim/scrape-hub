"""
질병코딩사례집 PDF 지능형 분할 파싱
- 균등하게 50페이지씩 분할
- Upstage API로 각 청크 파싱
"""
import sys
import codecs
from pathlib import Path
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter
import requests
import time

# UTF-8 출력
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()


class SmartPDFSplitParser:
    """균등 분할 PDF 파서"""

    def __init__(self, output_dir: str = 'data/hira_master/parsed_smart', target_chunk_pages: int = 50):
        """
        Args:
            output_dir: 출력 디렉토리
            target_chunk_pages: 목표 청크 크기 (페이지 수)
        """
        self.api_key = os.getenv('UPSTAGE_API_KEY')
        if not self.api_key:
            raise ValueError('UPSTAGE_API_KEY not found in .env')

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.target_chunk_pages = target_chunk_pages
        self.base_url = "https://api.upstage.ai/v1/document-ai/document-parse"

        # 임시 분할 파일 저장 위치
        self.temp_dir = self.output_dir / 'temp_chunks'
        self.temp_dir.mkdir(exist_ok=True)

    def analyze_structure(self, pdf_path: Path) -> dict:
        """PDF 구조 분석 - 균등 분할"""
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        # 균등하게 target_chunk_pages씩 분할
        major_sections = []
        current_page = 1
        chunk_num = 1

        while current_page <= total_pages:
            end_page = min(current_page + self.target_chunk_pages - 1, total_pages)
            major_sections.append({
                'name': f'섹션 {chunk_num} (p.{current_page}-{end_page})',
                'start': current_page,
                'end': end_page
            })
            current_page = end_page + 1
            chunk_num += 1

        return {
            'total_pages': total_pages,
            'major_sections': major_sections
        }

    def calculate_smart_splits(self, structure: dict) -> list:
        """분할 지점 계산 - major_sections를 그대로 사용"""
        major_sections = structure['major_sections']
        splits = []

        for section in major_sections:
            splits.append({
                'start': section['start'],
                'end': section['end'],
                'pages': section['end'] - section['start'] + 1,
                'sections': [section['name']]
            })

        return splits

    def split_pdf(self, pdf_path: Path, splits: list) -> list:
        """계산된 분할 지점에 따라 PDF 분할"""
        print(f'\n📄 지능형 PDF 분할: {pdf_path.name}')

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        print(f'  총 페이지: {total_pages}p')
        print(f'  분할 계획: {len(splits)}개 청크')

        for i, split in enumerate(splits, 1):
            print(f'    청크{i}: p.{split["start"]}-{split["end"]} ({split["pages"]}p)')

        chunks = []

        for i, split in enumerate(splits, 1):
            start_page = split['start'] - 1  # 0-indexed
            end_page = split['end']

            # 새 PDF 생성
            writer = PdfWriter()
            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])

            # 저장
            chunk_filename = f'{pdf_path.stem}_smart_chunk{i:02d}_p{split["start"]:04d}-{split["end"]:04d}.pdf'
            chunk_path = self.temp_dir / chunk_filename
            writer.write(chunk_path)

            chunks.append({
                'path': chunk_path,
                'start': split['start'],
                'end': split['end'],
                'pages': split['pages'],
                'sections': split['sections']
            })
            print(f'  ✅ {chunk_filename}')

        return chunks

    def parse_chunk(self, chunk: dict, output_format: str = "html") -> dict:
        """단일 청크 파싱"""
        chunk_path = chunk['path']
        print(f'\n[파싱] {chunk_path.name}')

        with open(chunk_path, 'rb') as f:
            files = {'document': (chunk_path.name, f, 'application/pdf')}
            data = {
                'ocr': 'true',
                'output_formats': f'["{output_format}"]',
            }

            start_time = time.time()
            try:
                response = requests.post(
                    self.base_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    data=data,
                    timeout=300
                )
                elapsed = time.time() - start_time

                if response.status_code != 200:
                    error_msg = f"API Error {response.status_code}: {response.text}"
                    print(f'  ❌ 실패: {error_msg}')
                    return {'error': error_msg, 'chunk': chunk}

                result = response.json()

                # content 추출
                content_dict = result.get('content', {})
                if isinstance(content_dict, dict):
                    content_text = content_dict.get(output_format, '')
                else:
                    content_text = str(content_dict)

                result['chunk_metadata'] = {
                    'chunk_info': {
                        'start_page': chunk['start'],
                        'end_page': chunk['end'],
                        'pages': chunk['pages'],
                        'sections': chunk['sections']
                    },
                    'chunk_file': str(chunk_path),
                    'elapsed_seconds': elapsed,
                    'content_length': len(content_text),
                    'api_pages': result.get('usage', {}).get('pages', 0)
                }

                print(f'  ✅ 성공: {elapsed:.1f}초, {len(content_text):,}자')
                return result

            except Exception as e:
                print(f'  ❌ 에러: {e}')
                return {'error': str(e), 'chunk': chunk}

    def parse_chunks(self, chunks: list) -> list:
        """분할된 PDF 파일들 파싱"""
        print(f'\n🔄 청크 파싱: {len(chunks)}개')

        results = []

        for i, chunk in enumerate(chunks, 1):
            print(f'\n[{i}/{len(chunks)}]')
            result = self.parse_chunk(chunk)
            results.append(result)

            # Rate limit 방지
            if i < len(chunks):
                time.sleep(1)

        return results

    def merge_results(self, results: list, source_file: str, output_format: str = 'html') -> dict:
        """파싱 결과 병합"""
        print(f'\n🔗 결과 병합')

        # 에러가 없는 결과만 필터링
        valid_results = [r for r in results if 'error' not in r]

        if not valid_results:
            print('  ❌ 모든 청크 파싱 실패')
            return None

        # Content 병합
        merged_content = []
        for r in valid_results:
            content_dict = r.get('content', {})
            if isinstance(content_dict, dict):
                content_text = content_dict.get(output_format, '')
            else:
                content_text = str(content_dict)
            merged_content.append(content_text)

        merged_content_str = '\n\n<hr>\n\n'.join(merged_content)

        # Elements 병합
        merged_elements = []
        for r in valid_results:
            if 'elements' in r:
                merged_elements.extend(r['elements'])

        # 총 페이지 수
        total_pages = sum(r.get('chunk_metadata', {}).get('api_pages', 0) for r in valid_results)

        # 청크 메타데이터
        chunks_metadata = []
        for r in valid_results:
            if 'chunk_metadata' in r:
                chunks_metadata.append(r['chunk_metadata'])

        merged = {
            'source_file': source_file,
            'total_pages': total_pages,
            'chunks_parsed': len(valid_results),
            'chunks_failed': len(results) - len(valid_results),
            'content': merged_content_str,
            'elements': merged_elements,
            'output_format': output_format,
            'parsing_method': 'uniform_split',
            'parsed_at': datetime.now().isoformat(),
            'chunks_metadata': chunks_metadata
        }

        print(f'  ✅ 병합 완료: {total_pages}p, {len(merged_content_str):,}자')
        print(f'  ✅ Elements: {len(merged_elements)}개')

        # 섹션별 요약
        print(f'\n  📋 섹션별 분할:')
        for i, meta in enumerate(chunks_metadata, 1):
            chunk_info = meta['chunk_info']
            print(f'     청크{i}: p.{chunk_info["start_page"]}-{chunk_info["end_page"]} '
                  f'({chunk_info["pages"]}p)')

        return merged

    def cleanup_temp_files(self):
        """임시 파일 삭제"""
        print(f'\n🧹 임시 파일 정리')

        for file in self.temp_dir.glob('*.pdf'):
            file.unlink()
            print(f'  삭제: {file.name}')

    def parse_large_pdf(self, pdf_path: Path, output_format: str = 'html') -> dict:
        """대용량 PDF 전체 파싱 프로세스 (지능형 분할)"""
        print(f'\n{"="*80}')
        print(f'📚 지능형 PDF 파싱: {pdf_path.name}')
        print(f'{"="*80}')

        # 1. 구조 분석
        print('\n[단계 1] PDF 구조 분석')
        structure = self.analyze_structure(pdf_path)
        print(f'  총 페이지: {structure["total_pages"]}p')
        print(f'  분할 계획: {len(structure["major_sections"])}개 청크')

        # 2. 분할 계획 수립
        print('\n[단계 2] 지능형 분할 계획 수립')
        splits = self.calculate_smart_splits(structure)

        # 3. PDF 분할
        print('\n[단계 3] PDF 분할')
        chunks = self.split_pdf(pdf_path, splits)

        # 4. 각 청크 파싱
        print('\n[단계 4] 청크 파싱')
        results = self.parse_chunks(chunks)

        # 5. 결과 병합
        print('\n[단계 5] 결과 병합')
        merged = self.merge_results(results, pdf_path.name, output_format)

        # 6. 저장
        if merged:
            # JSON 저장
            output_file = self.output_dir / f'{pdf_path.stem}_smart.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            print(f'\n💾 JSON 저장: {output_file}')

            # Raw content 저장 (HTML)
            raw_file = self.output_dir / f'{pdf_path.stem}_smart.{output_format}'
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(merged['content'])

            print(f'💾 Raw 저장: {raw_file}')

            # 미리보기
            print(f'\n[{output_format.upper()} 미리보기 (처음 500자)]')
            print('-' * 80)
            print(merged['content'][:500])
            print('-' * 80)

        # 7. 임시 파일 정리
        self.cleanup_temp_files()

        return merged


def main():
    """메인 실행"""
    print('=' * 80)
    print('🏥 질병코딩사례집 PDF 지능형 파싱')
    print('=' * 80)

    # 파싱할 PDF
    pdf_path = Path('data/hira_master/제8차 한국표준질병사인분류 질병코딩사례집.pdf')

    if not pdf_path.exists():
        print(f'❌ 파일 없음: {pdf_path}')
        return

    try:
        # 목표 50페이지 청크
        parser = SmartPDFSplitParser(target_chunk_pages=50)
        result = parser.parse_large_pdf(pdf_path, output_format='html')

        # 최종 요약
        print('\n\n' + '=' * 80)
        print('📊 파싱 완료')
        print('=' * 80)

        if result:
            print(f'✅ 총 페이지: {result.get("total_pages")}p')
            print(f'✅ 청크: {result.get("chunks_parsed")}개 성공, {result.get("chunks_failed")}개 실패')
            print(f'✅ Content: {len(result.get("content", "")):,}자')
            print(f'✅ Elements: {len(result.get("elements", []))}개')
            print(f'✅ 파싱 방식: {result.get("parsing_method")}')
        else:
            print('❌ 파싱 실패')

    except Exception as e:
        print(f'❌ 전체 에러: {e}')
        import traceback
        traceback.print_exc()

    print('\n' + '=' * 80)
    print('✅ 완료')
    print('=' * 80)


if __name__ == '__main__':
    main()
