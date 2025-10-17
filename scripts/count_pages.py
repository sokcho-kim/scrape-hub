"""
HWP 파일의 페이지 수를 확인하는 스크립트
"""
import os
import struct
from pathlib import Path
import zipfile

def count_hwp_pages(file_path):
    """
    HWP 파일의 페이지 수를 추출
    HWP 5.0 형식 (zip 기반)을 파싱
    """
    try:
        # HWP 파일은 내부적으로 zip 파일
        with zipfile.ZipFile(file_path, 'r') as zf:
            # DocInfo.xml에서 페이지 정보 추출
            if 'DocInfo.xml' in zf.namelist():
                doc_info = zf.read('DocInfo.xml').decode('utf-8')

                # <PAGECNT> 태그에서 페이지 수 추출
                if '<PAGECNT>' in doc_info:
                    start = doc_info.find('<PAGECNT>') + len('<PAGECNT>')
                    end = doc_info.find('</PAGECNT>')
                    page_count = int(doc_info[start:end])
                    return page_count

            # PrvText에서 페이지 카운트 추출 (대안)
            if 'PrvText' in zf.namelist():
                prv_text = zf.read('PrvText')
                # 간단한 페이지 추정 (텍스트 길이 기반)
                text_length = len(prv_text)
                # 대략 2000자당 1페이지로 추정
                return max(1, text_length // 2000)

    except Exception as e:
        return None

    return None

def count_pdf_pages(file_path):
    """
    PDF 파일의 페이지 수를 추출
    """
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            return len(pdf_reader.pages)
    except ImportError:
        # PyPDF2가 없으면 간단한 파싱
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                # /Count 태그에서 페이지 수 추출
                if b'/Count' in content:
                    idx = content.find(b'/Count')
                    substr = content[idx:idx+50]
                    # 숫자 추출
                    import re
                    match = re.search(rb'/Count\s+(\d+)', substr)
                    if match:
                        return int(match.group(1))
        except:
            pass

    return None

def main():
    import sys
    import codecs

    # UTF-8 출력 설정
    if sys.platform == 'win32':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    docs_dir = Path('data/hira_rulesvc/documents')

    results = []
    total_pages = 0
    total_files = 0

    print("=" * 80)
    print(f"{'파일명':<60} {'페이지':<10} {'크기(KB)':<10}")
    print("=" * 80)

    for file_path in sorted(docs_dir.glob('*')):
        if file_path.is_file():
            file_size_kb = file_path.stat().st_size / 1024

            if file_path.suffix.lower() == '.hwp':
                pages = count_hwp_pages(file_path)
            elif file_path.suffix.lower() == '.pdf':
                pages = count_pdf_pages(file_path)
            else:
                continue

            if pages is not None:
                total_pages += pages
                total_files += 1
                status = "✓"
            else:
                pages = "?"
                status = "✗"

            # 파일명을 50자로 제한
            display_name = file_path.name
            if len(display_name) > 55:
                display_name = display_name[:52] + "..."

            print(f"{display_name:<60} {str(pages):<10} {file_size_kb:>8.1f}")

            results.append({
                'name': file_path.name,
                'pages': pages,
                'size_kb': file_size_kb
            })

    print("=" * 80)
    print(f"\n{'총 파일 수:':<30} {total_files}개")
    print(f"{'총 페이지 수:':<30} {total_pages}페이지")
    print(f"{'페이지 확인 실패:':<30} {len([r for r in results if r['pages'] == '?'])}개")
    print(f"\n{'예상 비용 (페이지당 $0.01):':<30} ${total_pages * 0.01:.2f}")
    print(f"{'예상 비용 (환율 1,300원):':<30} ₩{int(total_pages * 0.01 * 1300):,}원")

if __name__ == '__main__':
    main()
