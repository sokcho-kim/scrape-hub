"""
NCC 암정보 사전 스크래퍼 설정
"""

BASE_URL = "https://www.cancer.go.kr"

# 암정보 사전 목록 페이지
DICTIONARY_LIST_URL = f"{BASE_URL}/lay1/program/S1T523C837/dictionaryworks/list.do"

# 암정보 사전 상세 Ajax URL
DICTIONARY_DETAIL_URL = f"{BASE_URL}/inc/searchWorks/search.do"

# 스크래핑 설정
SCRAPING_CONFIG = {
    "delay_between_requests": 1.0,  # 1초 간격
    "timeout": 30000,  # 30초
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (Research/Education)",
    "headless": True,
    "rows_per_page": 30,  # 페이지당 항목 수 (기본값 10 → 30으로 증가)
}

# 출력 디렉토리
OUTPUT_DIRS = {
    "parsed": "data/ncc/cancer_dictionary/parsed",
    "logs": "data/ncc/cancer_dictionary/logs"
}

# 정렬 옵션
SORT_OPTIONS = {
    "latest": "최신순",
    "alphabetical": "가나다순",
    "views": "조회순"
}

# 색인 옵션
INDEX_OPTIONS = [
    "전체",
    "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    "0-9", "A-Z"
]
