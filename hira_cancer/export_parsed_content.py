"""파싱된 내용을 텍스트 파일로 추출"""
import json
from pathlib import Path

PARSED_DIR = Path("data/hira_cancer/parsed")
OUTPUT_DIR = Path("data/hira_cancer/parsed_preview")
OUTPUT_DIR.mkdir(exist_ok=True)

# 샘플 파일들
samples = [
    ('announcement', '217_0_첨부파일 다운로드.json'),
    ('pre_announcement', '9579_0_주요공고개정내역(예정)_20251001.hwpx.json'),
    ('faq', '117_0_첨부파일 다운로드.json'),
]

for board, filename in samples:
    filepath = PARSED_DIR / board / filename
    if not filepath.exists():
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 메타데이터
    att_meta = data.get('attachment_metadata', {})

    # 텍스트 파일로 저장
    output_filename = f"{board}_{att_meta.get('post_number')}.txt"
    output_path = OUTPUT_DIR / output_filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write(f"게시판: {att_meta.get('board_name')}\n")
        f.write(f"게시글 번호: {att_meta.get('post_number')}\n")
        f.write(f"게시글 제목: {att_meta.get('post_title')}\n")
        f.write(f"첨부파일명: {att_meta.get('filename')}\n")
        f.write(f"페이지 수: {data.get('pages')}p\n")
        f.write('=' * 80 + '\n\n')
        f.write('[파싱된 Markdown 내용]\n\n')
        f.write(data.get('content', ''))

    print(f"저장: {output_path}")

print(f"\n저장 위치: {OUTPUT_DIR.absolute()}")
