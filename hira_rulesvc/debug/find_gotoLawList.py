"""
gotoLawList 함수가 정의된 위치 찾기
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = 'http://rulesvc.hira.or.kr/lmxsrv/main/main.srv'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page()

    # 메인 페이지 접속
    print(f"메인 페이지 접속: {BASE_URL}")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # 고시정보 탭 클릭
    print("고시정보 탭 클릭")
    page.evaluate("menu_go('1')")
    time.sleep(2)

    # 모든 frame 나열
    print("\n=== 모든 Frame 목록 ===")
    frames = page.frames
    for i, frame in enumerate(frames):
        name = frame.name or "(no name)"
        url = frame.url[:80]
        print(f"{i}. {name} - {url}")

    # 각 frame에서 gotoLawList 함수 확인
    print("\n=== gotoLawList 함수 찾기 ===")
    for i, frame in enumerate(frames):
        name = frame.name or "(no name)"
        try:
            has_function = frame.evaluate("typeof gotoLawList !== 'undefined'")
            if has_function:
                print(f"[O] {name} (frame {i}) - gotoLawList 함수 있음!")
            else:
                print(f"[X] {name} (frame {i}) - 없음")
        except Exception as e:
            print(f"[X] {name} (frame {i}) - 오류: {str(e)[:50]}")

    print("\n브라우저를 20초간 열어둡니다...")
    time.sleep(20)
    browser.close()
