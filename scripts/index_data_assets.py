#!/usr/bin/env python3
"""데이터 자산 색인 생성"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def get_directory_stats(path: Path):
    """디렉토리 통계"""
    if not path.exists():
        return None

    files = list(path.rglob('*'))
    files = [f for f in files if f.is_file()]

    total_size = sum(f.stat().st_size for f in files)

    # 파일 타입별 카운트
    extensions = defaultdict(int)
    for f in files:
        ext = f.suffix or '.none'
        extensions[ext] += 1

    return {
        'file_count': len(files),
        'total_size_mb': round(total_size / 1024 / 1024, 2),
        'extensions': dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True))
    }


def index_key_files(base_path: Path):
    """주요 파일 상세 색인"""
    key_files = {}

    # Bridges
    bridges = base_path / 'bridges'
    if bridges.exists():
        for f in bridges.glob('*.json'):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    count = len(data) if isinstance(data, list) else 1
                    key_files[f.name] = {
                        'path': str(f.relative_to(base_path)),
                        'size_mb': round(f.stat().st_size / 1024 / 1024, 2),
                        'record_count': count
                    }
            except:
                pass

    return key_files


def main():
    base = Path(__file__).parent.parent

    data_sources = {
        'HIRA Cancer': 'data/hira_cancer',
        'HIRA RuleSvc': 'data/hira_rulesvc',
        'HIRA Master': 'data/hira_master',
        'MFDS (약전)': 'data/mfds',
        'NCC (암센터)': 'data/ncc',
        'LIKMS (국회법률)': 'data/likms',
        'Pharma': 'data/pharma'
    }

    print("="*80)
    print("DATA ASSET INDEX")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    total_files = 0
    total_size = 0

    index = {}

    for name, path_str in data_sources.items():
        path = base / path_str
        stats = get_directory_stats(path)

        if stats:
            index[name] = stats
            total_files += stats['file_count']
            total_size += stats['total_size_mb']

            print(f"[{name}]")
            print(f"  Files: {stats['file_count']:,}")
            print(f"  Size: {stats['total_size_mb']:.2f} MB")
            print(f"  Top formats: {', '.join(list(stats['extensions'].keys())[:5])}")
            print()

    print("-"*80)
    print(f"TOTAL: {total_files:,} files, {total_size:.2f} MB")
    print("-"*80)
    print()

    # Bridges 파일
    print("[BRIDGE FILES - Master Data]")
    bridges = index_key_files(base)
    for name, info in sorted(bridges.items()):
        print(f"  • {name}")
        print(f"    Records: {info['record_count']:,} | Size: {info['size_mb']:.2f} MB")
    print()

    # Parsed 데이터
    print("[PARSED DATA]")
    parsed_dirs = [
        ('HIRA Cancer Parsed', 'data/hira_cancer/parsed'),
        ('HIRA RuleSvc Parsed', 'data/hira_rulesvc/documents'),
        ('MFDS Parsed (Small)', 'data/mfds/parsed'),
        ('MFDS Parsed (PDF)', 'data/mfds/parsed_pdf'),
        ('NCC Parsed', 'data/ncc/cancer_dictionary')
    ]

    for name, path_str in parsed_dirs:
        path = base / path_str
        if path.exists():
            count = len(list(path.glob('*.json')))
            size = sum(f.stat().st_size for f in path.glob('*.json')) / 1024 / 1024
            print(f"  • {name}: {count} files, {size:.2f} MB")

    print()
    print("="*80)

    # JSON으로 저장
    output = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_files': total_files,
            'total_size_mb': round(total_size, 2)
        },
        'sources': index,
        'bridges': bridges
    }

    output_path = base / 'data_asset_index.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Index saved: {output_path}")


if __name__ == '__main__':
    main()
