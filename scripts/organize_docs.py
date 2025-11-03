#!/usr/bin/env python3
"""문서 파일 정리 스크립트"""
from pathlib import Path
import shutil

def organize_docs():
    """docs 폴더로 문서 파일 정리"""

    # 이동할 파일 매핑
    moves = {
        # 모듈 README들 -> docs/modules/
        'emrcert/README.md': 'docs/modules/emrcert/README.md',
        'hira_cancer/README.md': 'docs/modules/hira_cancer/README.md',
        'hira_rulesvc/README.md': 'docs/modules/hira_rulesvc/README.md',
        'likms/README.md': 'docs/modules/likms/README.md',
        'ncc/README.md': 'docs/modules/ncc/README.md',
        'pharma/README.md': 'docs/modules/pharma/README.md',

        # logs의 md 파일들 -> docs/reports/logs/
        'logs/drug_gate_report_pass2.md': 'docs/reports/logs/drug_gate_report_pass2.md',
        'logs/drug_gate_report_pass3.md': 'docs/reports/logs/drug_gate_report_pass3.md',
        'logs/drug_gate_report_pass3_fixed.md': 'docs/reports/logs/drug_gate_report_pass3_fixed.md',
        'logs/drug_gate_report_pass4.md': 'docs/reports/logs/drug_gate_report_pass4.md',

        # temp 파일 -> docs/temp/
        'temp_master_explore.txt': 'docs/temp/temp_master_explore.txt',
    }

    print('Document Reorganization')
    print('='*60)

    moved = 0
    skipped = 0

    for src_str, dst_str in moves.items():
        src = Path(src_str)
        dst = Path(dst_str)

        if not src.exists():
            print(f'SKIP (not found): {src}')
            skipped += 1
            continue

        # 대상 디렉토리 생성
        dst.parent.mkdir(parents=True, exist_ok=True)

        # 파일 이동
        try:
            shutil.move(str(src), str(dst))
            print(f'MOVED: {src} -> {dst}')
            moved += 1
        except Exception as e:
            print(f'ERROR: {src} - {e}')

    print()
    print(f'Summary: {moved} moved, {skipped} skipped')

    # reports 폴더의 파일들 확인
    reports_root = Path('reports')
    if reports_root.exists():
        print()
        print('Checking reports/ folder...')
        for f in reports_root.rglob('*'):
            if f.is_file():
                rel_path = f.relative_to(reports_root)
                dst = Path('docs/reports') / rel_path

                if not dst.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(dst))
                    print(f'MOVED: {f} -> {dst}')
                    moved += 1

    print()
    print(f'Final: {moved} files organized')
    print('='*60)


if __name__ == '__main__':
    organize_docs()
