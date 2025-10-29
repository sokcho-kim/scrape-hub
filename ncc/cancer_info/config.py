"""
NCC (국립암센터) 스크래퍼 설정 v2

전체 100개 암종 수집
태그 시스템: 주요암, 성인, 소아청소년
"""

BASE_URL = "https://www.cancer.go.kr"

# Phase 1: 항암화학요법 정보 (우선순위)
CHEMOTHERAPY_PAGES = [
    {
        "url": "/lay1/S1T289C290/contents.do",
        "category": "치료 > 항암화학요법",
        "title": "항암화학요법의 이해",
        "filename": "chemotherapy_overview"
    },
    {
        "url": "/lay1/S1T289C291/contents.do",
        "category": "치료 > 항암화학요법",
        "title": "세포독성 항암제",
        "filename": "cytotoxic_drugs"
    },
    {
        "url": "/lay1/S1T289C292/contents.do",
        "category": "치료 > 항암화학요법",
        "title": "표적치료제",
        "filename": "targeted_therapy"
    },
    {
        "url": "/lay1/S1T289C293/contents.do",
        "category": "치료 > 항암화학요법",
        "title": "면역관문억제제",
        "filename": "immune_checkpoint_inhibitors"
    },
    {
        "url": "/lay1/S1T289C294/contents.do",
        "category": "치료 > 항암화학요법",
        "title": "면역세포치료",
        "filename": "immune_cell_therapy"
    }
]

# Phase 2: 전체 암종 목록 (100개)
# 태그: "주요암" (12대 주요 암), "성인", "소아청소년"

# 주요 12대 암 목록 (사이트 상단 메뉴 기준)
MAJOR_CANCERS = {
    "갑상선암", "위암", "대장암", "폐암", "간암", "유방암",
    "전립선암", "췌장암", "담낭암", "담도암", "신장암", "방광암"
}

CANCER_TYPES_ALL = [
    # 성인 암 (92개)
    {"name": "가성점액종", "cancer_seq": "7573253", "tags": ["성인"]},
    {"name": "간내 담도암", "cancer_seq": "3293", "tags": ["성인"]},
    {"name": "간모세포종", "cancer_seq": "8676000", "tags": ["성인"]},
    {"name": "간암", "cancer_seq": "3317", "tags": ["주요암", "성인"]},
    {"name": "갑상선암", "cancer_seq": "3341", "tags": ["주요암", "성인"]},
    {"name": "결장암", "cancer_seq": "3365", "tags": ["성인"]},
    {"name": "고환암", "cancer_seq": "3389", "tags": ["성인"]},
    {"name": "골수이형성증후군", "cancer_seq": "3413", "tags": ["성인"]},
    {"name": "교모세포종", "cancer_seq": "3437", "tags": ["성인"]},
    {"name": "구강암", "cancer_seq": "3461", "tags": ["성인"]},
    {"name": "구순암", "cancer_seq": "7408109", "tags": ["성인"]},
    {"name": "구인두-편도암(HPV 관련)", "cancer_seq": "8723939", "tags": ["성인"]},
    {"name": "구인두-하인두암(HPV 비관련)", "cancer_seq": "8723940", "tags": ["성인"]},
    {"name": "균상식육종", "cancer_seq": "3485", "tags": ["성인"]},
    {"name": "급성 골수성백혈병", "cancer_seq": "3509", "tags": ["성인"]},
    {"name": "급성 림프구성백혈병", "cancer_seq": "3533", "tags": ["성인"]},
    {"name": "기저세포암", "cancer_seq": "3557", "tags": ["성인"]},
    {"name": "난소상피암", "cancer_seq": "3581", "tags": ["성인"]},
    {"name": "난소생식세포종양", "cancer_seq": "3605", "tags": ["성인"]},
    {"name": "남성 유방암", "cancer_seq": "3629", "tags": ["성인"]},
    {"name": "뇌종양", "cancer_seq": "3653", "tags": ["성인"]},
    {"name": "뇌하수체선종", "cancer_seq": "3677", "tags": ["성인"]},
    {"name": "다발골수종", "cancer_seq": "3701", "tags": ["성인"]},
    {"name": "담낭·담도암", "cancer_seq": "8723938", "tags": ["성인"]},
    {"name": "담낭암", "cancer_seq": "3749", "tags": ["주요암", "성인"]},
    {"name": "담도암", "cancer_seq": "3773", "tags": ["주요암", "성인"]},
    {"name": "대장암", "cancer_seq": "3797", "tags": ["주요암", "성인"]},
    {"name": "만성 골수성백혈병", "cancer_seq": "3821", "tags": ["성인"]},
    {"name": "만성 림프구성백혈병", "cancer_seq": "3845", "tags": ["성인"]},
    {"name": "망막모세포종", "cancer_seq": "3869", "tags": ["성인"]},
    {"name": "맥락막흑색종", "cancer_seq": "3917", "tags": ["성인"]},
    {"name": "미만성 거대B세포림프종", "cancer_seq": "3507338", "tags": ["성인"]},
    {"name": "바터팽대부암", "cancer_seq": "3941", "tags": ["성인"]},
    {"name": "방광암", "cancer_seq": "3965", "tags": ["주요암", "성인"]},
    {"name": "복막암", "cancer_seq": "3989", "tags": ["성인"]},
    {"name": "부갑상선암", "cancer_seq": "4013", "tags": ["성인"]},
    {"name": "부신암", "cancer_seq": "4037", "tags": ["성인"]},
    {"name": "비부비동암", "cancer_seq": "7406371", "tags": ["성인"]},
    {"name": "비소세포폐암", "cancer_seq": "4061", "tags": ["성인"]},
    {"name": "비호지킨림프종", "cancer_seq": "114462", "tags": ["성인"]},
    {"name": "설암", "cancer_seq": "4085", "tags": ["성인"]},
    {"name": "성기삭 간질성 종양", "cancer_seq": "8723942", "tags": ["성인"]},
    {"name": "성상세포종", "cancer_seq": "4109", "tags": ["성인"]},
    {"name": "소세포폐암", "cancer_seq": "4133", "tags": ["성인"]},
    {"name": "소장암", "cancer_seq": "4229", "tags": ["성인"]},
    {"name": "수막종", "cancer_seq": "4253", "tags": ["성인"]},
    {"name": "식도암", "cancer_seq": "4277", "tags": ["성인"]},
    {"name": "신경교종", "cancer_seq": "4301", "tags": ["성인"]},
    {"name": "신경모세포종", "cancer_seq": "4325", "tags": ["성인"]},
    {"name": "신우암", "cancer_seq": "7880257", "tags": ["성인"]},
    {"name": "신장암", "cancer_seq": "4373", "tags": ["주요암", "성인"]},
    {"name": "심장암", "cancer_seq": "3723316", "tags": ["성인"]},
    {"name": "십이지장암", "cancer_seq": "7405045", "tags": ["성인"]},
    {"name": "악성 골종양", "cancer_seq": "4421", "tags": ["성인"]},
    {"name": "악성 림프종", "cancer_seq": "4445", "tags": ["성인"]},
    {"name": "악성 연부조직종양", "cancer_seq": "4397", "tags": ["성인"]},
    {"name": "악성 중피종", "cancer_seq": "4493", "tags": ["성인"]},
    {"name": "악성 흑색종", "cancer_seq": "4517", "tags": ["성인"]},
    {"name": "안종양", "cancer_seq": "4541", "tags": ["성인"]},
    {"name": "외음부암", "cancer_seq": "4565", "tags": ["성인"]},
    {"name": "요관암", "cancer_seq": "7882456", "tags": ["성인"]},
    {"name": "요도암", "cancer_seq": "4589", "tags": ["성인"]},
    {"name": "원발부위불명암", "cancer_seq": "4613", "tags": ["성인"]},
    {"name": "위림프종", "cancer_seq": "4637", "tags": ["성인"]},
    {"name": "위암", "cancer_seq": "4661", "tags": ["주요암", "성인"]},
    {"name": "위유암종", "cancer_seq": "4685", "tags": ["성인"]},
    {"name": "위장관 기질종양", "cancer_seq": "4709", "tags": ["성인"]},
    {"name": "윌름스종양", "cancer_seq": "4733", "tags": ["성인"]},
    {"name": "유방암", "cancer_seq": "4757", "tags": ["주요암", "성인"]},
    {"name": "육종", "cancer_seq": "4781", "tags": ["성인"]},
    {"name": "음경암", "cancer_seq": "4805", "tags": ["성인"]},
    {"name": "임신융모질환", "cancer_seq": "4853", "tags": ["성인"]},
    {"name": "자궁경부암", "cancer_seq": "4877", "tags": ["성인"]},
    {"name": "자궁내막암", "cancer_seq": "4901", "tags": ["성인"]},
    {"name": "자궁육종", "cancer_seq": "4925", "tags": ["성인"]},
    {"name": "전립선암", "cancer_seq": "4949", "tags": ["주요암", "성인"]},
    {"name": "전이성 골종양", "cancer_seq": "4473465", "tags": ["성인"]},
    {"name": "전이성 뇌종양", "cancer_seq": "4973", "tags": ["성인"]},
    {"name": "종격동암", "cancer_seq": "8467636", "tags": ["성인"]},
    {"name": "직장 신경내분비종양", "cancer_seq": "5021", "tags": ["성인"]},
    {"name": "직장암", "cancer_seq": "4997", "tags": ["성인"]},
    {"name": "질암", "cancer_seq": "5045", "tags": ["성인"]},
    {"name": "척수종양", "cancer_seq": "5069", "tags": ["성인"]},
    {"name": "청신경초종", "cancer_seq": "5093", "tags": ["성인"]},
    {"name": "췌장암", "cancer_seq": "5117", "tags": ["주요암", "성인"]},
    {"name": "침샘암", "cancer_seq": "5141", "tags": ["성인"]},
    {"name": "카포시 육종", "cancer_seq": "7403619", "tags": ["성인"]},
    {"name": "파제트병", "cancer_seq": "7771357", "tags": ["성인"]},
    {"name": "편평상피세포암", "cancer_seq": "5189", "tags": ["성인"]},
    {"name": "폐선암", "cancer_seq": "5213", "tags": ["성인"]},
    {"name": "폐암", "cancer_seq": "5237", "tags": ["주요암", "성인"]},
    {"name": "폐편평상피세포암", "cancer_seq": "5261", "tags": ["성인"]},
    {"name": "피부암", "cancer_seq": "5285", "tags": ["성인"]},
    {"name": "항문암", "cancer_seq": "5309", "tags": ["성인"]},
    {"name": "횡문근육종", "cancer_seq": "8687522", "tags": ["성인"]},
    {"name": "후두암", "cancer_seq": "5333", "tags": ["성인"]},
    {"name": "흉선암", "cancer_seq": "154771", "tags": ["성인"]},

    # 소아청소년 암 (8개)
    {"name": "소아청소년 뇌종양", "cancer_seq": "4157", "tags": ["소아청소년"]},
    {"name": "소아청소년 림프종", "cancer_seq": "4181", "tags": ["소아청소년"]},
    {"name": "소아청소년 백혈병", "cancer_seq": "4205", "tags": ["소아청소년"]},
]

# 스크래핑 설정
SCRAPING_CONFIG = {
    "delay_between_requests": 2.0,
    "timeout": 60000,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (Research/Education)",
    "headless": True
}

# 출력 디렉토리
OUTPUT_DIRS = {
    "raw": "data/ncc/raw",
    "parsed": "data/ncc/parsed",
    "logs": "data/ncc/logs"
}
