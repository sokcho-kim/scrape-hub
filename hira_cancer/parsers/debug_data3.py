"""HIRA 데이터 JSON 파일로 저장"""
import json
from pathlib import Path

# HIRA 데이터 로드
hira_file = Path("data/hira_cancer/raw/hira_cancer_20251023_184848.json")
with open(hira_file, 'r', encoding='utf-8') as f:
    hira_data = json.load(f)

announcements = hira_data['data']['announcement']

# 가장 긴 content 찾기
content_lengths = [len(a.get('content', '')) for a in announcements]
longest_idx = content_lengths.index(max(content_lengths))
longest = announcements[longest_idx]

# 처음 5개 공고 저장
output = {
    'total': len(announcements),
    'samples': []
}

for i in range(min(5, len(announcements))):
    ann = announcements[i]
    output['samples'].append({
        'index': i + 1,
        'title': ann.get('title', ''),
        'announcement_no': ann.get('announcement_no', ''),
        'created_date': ann.get('created_date', ''),
        'content_length': len(ann.get('content', '')),
        'content': ann.get('content', '')
    })

# 가장 긴 것도 추가
output['longest'] = {
    'index': longest_idx + 1,
    'title': longest.get('title', ''),
    'announcement_no': longest.get('announcement_no', ''),
    'created_date': longest.get('created_date', ''),
    'content_length': len(longest.get('content', '')),
    'content': longest.get('content', '')
}

# 저장
output_file = Path("hira_cancer/parsers/debug_announcements.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"저장 완료: {output_file}")
print(f"  총 공고 수: {output['total']}")
print(f"  샘플 수: {len(output['samples'])}")
print(f"  가장 긴 공고 index: {output['longest']['index']}")
print(f"  가장 긴 공고 길이: {output['longest']['content_length']} 자")

# 첨부파일 정보도 저장
attachments = hira_data['data']['attachment']
att_output = {
    'total': len(attachments),
    'samples': attachments[:10]  # 처음 10개만
}

att_file = Path("hira_cancer/parsers/debug_attachments.json")
with open(att_file, 'w', encoding='utf-8') as f:
    json.dump(att_output, f, ensure_ascii=False, indent=2)

print(f"\n첨부파일 저장 완료: {att_file}")
print(f"  총 첨부파일 수: {att_output['total']}")
