"""
대화형 페이지 탐색 도구

브라우저를 열어두고 수동으로 페이지를 탐색하면서 HTML을 저장합니다.
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

BASE_URL = 'http://rulesvc.hira.or.kr/lmxsrv/main/main.srv'
DEBUG_DIR = Path('data/hira_rulesvc/debug')
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 60)
    print("HIRA 대화형 탐색 도구")
    print("=" * 60)
    print("\n브라우저가 열립니다. 수동으로 원하는 페이지로 이동하세요.")
    print("준비되면 아무 키나 누르면 현재 페이지를 저장합니다.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 메인 페이지 접속
        print(f"접속 중: {BASE_URL}")
        page.goto(BASE_URL)
        time.sleep(2)

        step = 1
        while True:
            print(f"\n[단계 {step}]")
            print("1. 현재 페이지 저장")
            print("2. contentbody iframe 저장")
            print("3. tree01 iframe 저장")
            print("4. 모든 iframe 저장")
            print("5. 스크린샷 저장")
            print("6. 종료")

            choice = input("\n선택: ").strip()

            if choice == '1':
                # 메인 페이지 저장
                html = page.content()
                file_path = DEBUG_DIR / f'step{step}_main.html'
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"✓ 저장: {file_path}")
                step += 1

            elif choice == '2':
                # contentbody iframe 저장
                frame = page.frame(name="contentbody")
                if frame:
                    html = frame.content()
                    file_path = DEBUG_DIR / f'step{step}_contentbody.html'
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"✓ 저장: {file_path}")
                    step += 1
                else:
                    print("✗ contentbody iframe을 찾을 수 없습니다")

            elif choice == '3':
                # tree01 iframe 저장
                frame = page.frame(name="tree01")
                if frame:
                    html = frame.content()
                    file_path = DEBUG_DIR / f'step{step}_tree01.html'
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"✓ 저장: {file_path}")
                    step += 1
                else:
                    print("✗ tree01 iframe을 찾을 수 없습니다")

            elif choice == '4':
                # 모든 iframe 저장
                frames = page.frames
                print(f"발견된 iframe: {len(frames)}개")
                for idx, frame in enumerate(frames):
                    try:
                        name = frame.name or f"frame{idx}"
                        html = frame.content()
                        file_path = DEBUG_DIR / f'step{step}_{name}.html'
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(html)
                        print(f"  ✓ 저장: {file_path}")
                    except Exception as e:
                        print(f"  ✗ {name} 저장 실패: {e}")
                step += 1

            elif choice == '5':
                # 스크린샷
                file_path = DEBUG_DIR / f'step{step}_screenshot.png'
                page.screenshot(path=str(file_path), full_page=True)
                print(f"✓ 저장: {file_path}")
                step += 1

            elif choice == '6':
                print("\n종료합니다.")
                break

            else:
                print("잘못된 선택입니다.")

        browser.close()

    print(f"\n저장 위치: {DEBUG_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
