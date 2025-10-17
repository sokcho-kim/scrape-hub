"""실패한 파일 목록과 크기 확인"""
from pathlib import Path

docs_dir = Path("data/hira_rulesvc/documents")
parsed_dir = Path("data/hira_rulesvc/parsed")

# 전체 파일
all_files = sorted(list(docs_dir.glob("*.hwp")) + list(docs_dir.glob("*.pdf")))

# 파싱 성공 파일
parsed_files = {f.stem for f in parsed_dir.glob("*.json") if f.name not in ["_summary.json", "_failed_files.txt"]}

# 실패 파일
failed_files = [f for f in all_files if f.stem not in parsed_files]

print("=" * 100)
print(f"{'파일명':<70} {'크기':>10} {'에러 추정':>15}")
print("=" * 100)

for f in failed_files:
    size_kb = f.stat().st_size / 1024

    # 에러 유형 추정
    if size_kb > 400:
        error_type = "413 (크기)"
    else:
        error_type = "500 (서버)"

    name = f.name
    if len(name) > 65:
        name = name[:62] + "..."

    print(f"{name:<70} {size_kb:>9.1f}K {error_type:>15}")

print("=" * 100)
print(f"\n총 {len(failed_files)}개 실패 파일")

# 에러별 통계
err_413 = [f for f in failed_files if f.stat().st_size / 1024 > 400]
err_500 = [f for f in failed_files if f.stat().st_size / 1024 <= 400]

print(f"- 413 Request Too Large: {len(err_413)}개")
print(f"- 500 Server Error: {len(err_500)}개")
