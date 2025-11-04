import json

print("=" * 100)
print("KCD-8 1권 데이터 확인")
print("=" * 100)

# JSON 로드
with open('data/hira_master/parsed/KCD-8 1권_220630_20220630034856.json', encoding='utf-8') as f:
    data = json.load(f)

print(f"\n데이터 타입: {type(data)}")

if isinstance(data, dict):
    print(f"Keys: {list(data.keys())}")
    for key in list(data.keys())[:5]:
        print(f"\n[{key}]")
        print(f"  타입: {type(data[key])}")
        if isinstance(data[key], (list, dict)):
            print(f"  크기: {len(data[key])}")

elif isinstance(data, list):
    print(f"리스트 길이: {len(data)}")
    if len(data) > 0:
        print(f"\n첫 항목 타입: {type(data[0])}")
        if isinstance(data[0], dict):
            print(f"첫 항목 Keys: {list(data[0].keys())}")
            print(f"\n첫 항목 샘플:")
            for k, v in list(data[0].items())[:3]:
                print(f"  {k}: {str(v)[:100]}")

print("\n" + "=" * 100)
