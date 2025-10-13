"""
HIRA 고시 SEQ 매핑 테이블

트리 구조의 텍스트를 SEQ 값으로 매핑합니다.
HTML select#lawSeq의 option value를 기반으로 작성되었습니다.
"""

# 고시명 → SEQ 매핑 (HTML에서 추출)
TREE_TO_SEQ_MAPPING = {
    # 요양급여비용 청구방법, 심사청구서·명세서서식 및 작성요령
    "요양급여비용 청구방법(보건복지부 고시)": "2",
    "요양급여비용 청구방법(세부사항)": "200",
    "요양급여비용 청구방법(세부작성요령)": "3",

    # 요양급여비용심사청구소프트웨어의검사등에관한기준
    "요양급여비용심사청구소프트웨어의검사등에관한기준": "12",

    # 자동차보험진료수가 심사업무처리에 관한 규정
    "자동차보험진료수가 심사업무처리에 관한 규정": "204",
    "자동차보험진료수가 심사업무처리에 관한 규정(세부사항)": "205",
    "자동차보험진료수가 청구방법(세부작성요령)": "9",

    # 의료급여법
    "의료급여법": "137",
    "의료급여법 시행규칙": "111",
    "의료급여법 시행령": "112",

    # 고시기준
    "의료급여수가의 기준 및 일반기준": "96",
    "임신,출산 진료비 등의 의료급여기준 및 방법": "99",
    "요양비의 의료급여기준 및 방법": "97",
    "의료급여기관 간 동일성분 의약품 중복투약 관리에 관한 기준": "100",
    "선택의료급여기관 적용 대상자 및 이용 절차 등에 관한 규정": "98",
    "진통,진양,수렴,소염제인 외용제제": "101",
    "코로나바이러스감염증-19 의료급여 절차 예외 인정기준": "206",
    "업무정지처분에 갈음한 과징금 적용기준": "207",
    "급여비용의 예탁 및 지급에 관한 규정": "208",
    "수급권자의 건강유지 및 증진 등을 위한 사업의 지원에 관한 기준": "209",
    "노숙인진료시설 지정 등에 관한 고시": "210",
    "근로능력평가의 기준 등에 관한 규정": "211",
    "의료급여 대상 여부의 확인 방법 및 절차 등에 관한 기준": "216",

    # 행정해석 - 의료급여 수급권자 선정기준 및 관리
    "시설수용자": "160",
    "무연고자 등": "161",
    "행려환자": "162",
    "노숙인": "163",
    "의료급여 자격": "164",

    # 행정해석 - 의료급여체계
    "의료급여의 절차": "165",
    "왕진 관련": "166",
    "회송": "167",
    "선택의료급여기관": "168",

    # 행정해석 - 의료급여의 범위 및 기준
    "의료급여의 범위": "170",
    "의료급여 일반기준": "171",
    "사회복지시설(촉탁의 등) 관련": "180",
    "중증질환 관련": "172",
    "희귀난치성 질환 관련": "173",
    "산정특례 관련": "174",
    "노인 틀니": "177",
    "치과 임플란트": "178",
    "치석 제거": "179",

    # 행정해석 - 의료급여 본인부담
    "급여비용의 부담": "176",
    "직접 조제": "181",
    "식대": "182",
    "경증질환 약제비 본인부담 차등제": "192",
    "의료급여 본인부담 정리": "199",

    # 행정해석 - 의료급여비용의 청구 및 정산
    "급여비용의 청구": "184",
    "급여비용의 정산": "185",
    "대지급금 제도": "186",
    "부당이득금": "187",

    # 행정해석 - 의료급여 정액수가
    "정신질환자": "189",
    "정신과 인력차등제 관련": "190",
    "혈액투석 환자": "191",

    # 행정해석 - 코로나바이러스감염증-19관련
    "코로나바이러스감염증-19관련": "215",

    # 행정해석 - 기타 행정해석
    "세월호 사고 관련": "194",
    "영상수가 인하고시 소송결과 관련": "195",
    "선별급여 관련": "196",
    "메르스(MERS) 관련": "197",
    "응급의료수가 관련": "198",
}

# SEQ → 고시명 역매핑
SEQ_TO_TREE_MAPPING = {v: k for k, v in TREE_TO_SEQ_MAPPING.items()}


def get_seq_by_name(name: str) -> str:
    """
    고시명으로 SEQ 조회 (정확히 일치)

    Args:
        name: 고시명 (예: "요양급여비용 청구방법(보건복지부 고시)")

    Returns:
        SEQ 값 (예: "2")

    Raises:
        ValueError: 고시명을 찾을 수 없을 때
    """
    if name in TREE_TO_SEQ_MAPPING:
        return TREE_TO_SEQ_MAPPING[name]
    raise ValueError(f"고시명 '{name}'을(를) 찾을 수 없습니다.")


def get_seq_by_partial_match(partial_name: str) -> str:
    """
    고시명 부분 일치로 SEQ 조회

    Args:
        partial_name: 고시명 일부 (예: "요양급여비용 청구방법")

    Returns:
        SEQ 값 (여러 개 매칭 시 첫 번째)

    Raises:
        ValueError: 매칭되는 고시명이 없을 때
    """
    matches = [
        (name, seq) for name, seq in TREE_TO_SEQ_MAPPING.items()
        if partial_name in name
    ]

    if not matches:
        raise ValueError(f"'{partial_name}'과(와) 매칭되는 고시가 없습니다.")

    if len(matches) > 1:
        match_names = [name for name, _ in matches]
        print(f"[WARNING] 여러 개 매칭됨: {match_names}")
        print(f"첫 번째 매칭 사용: {matches[0][0]}")

    return matches[0][1]


def get_name_by_seq(seq: str) -> str:
    """
    SEQ로 고시명 조회

    Args:
        seq: SEQ 값 (예: "2")

    Returns:
        고시명 (예: "요양급여비용 청구방법(보건복지부 고시)")

    Raises:
        ValueError: SEQ를 찾을 수 없을 때
    """
    if seq in SEQ_TO_TREE_MAPPING:
        return SEQ_TO_TREE_MAPPING[seq]
    raise ValueError(f"SEQ '{seq}'을(를) 찾을 수 없습니다.")


def list_all_notices():
    """전체 고시 목록 출력"""
    print(f"총 {len(TREE_TO_SEQ_MAPPING)}개 고시:")
    for name, seq in sorted(TREE_TO_SEQ_MAPPING.items(), key=lambda x: int(x[1])):
        print(f"  SEQ {seq:>3}: {name}")


if __name__ == "__main__":
    # 테스트
    print("=== SEQ 매핑 테이블 테스트 ===\n")

    # 1. 정확한 이름으로 조회
    test_name = "요양급여비용 청구방법(보건복지부 고시)"
    seq = get_seq_by_name(test_name)
    print(f"1. 정확 매칭: '{test_name}' → SEQ {seq}")

    # 2. 부분 일치로 조회
    partial = "요양급여비용 청구방법"
    seq = get_seq_by_partial_match(partial)
    print(f"\n2. 부분 매칭: '{partial}' → SEQ {seq}")

    # 3. SEQ로 역조회
    name = get_name_by_seq("2")
    print(f"\n3. 역조회: SEQ 2 → '{name}'")

    # 4. 전체 목록
    print(f"\n4. 전체 목록:")
    list_all_notices()
