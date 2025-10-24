"""파싱된 샘플 확인 스크립트"""
import json
import sys
import codecs
from pathlib import Path

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 파싱된 파일 목록
PARSED_DIR = Path("data/hira_cancer/parsed")

def view_sample(filepath: Path):
    """파싱된 파일 내용 출력"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print('=' * 80)
    print(f'파일: {filepath.name}')
    print('=' * 80)

    # 메타데이터 출력
    att_meta = data.get('attachment_metadata', {})
    print(f'게시판: {att_meta.get("board_name")}')
    print(f'게시글 번호: {att_meta.get("post_number")}')

    title = att_meta.get("post_title", "")
    if len(title) > 60:
        title = title[:60] + "..."
    print(f'게시글 제목: {title}')
    print(f'첨부파일명: {att_meta.get("filename")}')
    print()

    # 파싱 결과
    print(f'페이지 수: {data.get("pages")}p')
    print(f'모델: {data.get("model")}')
    print(f'텍스트 길이: {len(data.get("content", ""))}자')
    print(f'HTML 길이: {len(data.get("html", ""))}자')
    print()

    # 본문 미리보기 (처음 800자)
    content = data.get('content', '')
    print('[본문 미리보기 (처음 800자)]')
    print('-' * 80)
    print(content[:800])
    print('-' * 80)
    print()


def main():
    """모든 파싱된 샘플 출력"""
    # 게시판별로 1개씩 선택
    samples = {
        'announcement': '217_0_첨부파일 다운로드.json',
        'pre_announcement': '9579_0_주요공고개정내역(예정)_20251001.hwpx.json',
        'faq': '117_0_첨부파일 다운로드.json',
    }

    for board, filename in samples.items():
        filepath = PARSED_DIR / board / filename
        if filepath.exists():
            view_sample(filepath)
        else:
            print(f'[경고] 파일 없음: {filepath}')
            print()


if __name__ == '__main__':
    main()
