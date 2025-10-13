"""
자동 페이지 캡처 도구

브라우저를 열고 주요 페이지들을 자동으로 캡처합니다.
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

BASE_URL = 'http://rulesvc.hira.or.kr/lmxsrv/main/main.srv'
DEBUG_DIR = Path('data/hira_rulesvc/debug')
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

def save_all_frames(page, step_name):
    """모든 프레임 저장"""
    frames = page.frames
    print(f"\n[{step_name}] {len(frames)}개 프레임 발견")

    for idx, frame in enumerate(frames):
        try:
            name = frame.name or f"frame{idx}"
            url = frame.url
            print(f"  - {name}: {url}")

            html = frame.content()
            file_path = DEBUG_DIR / f'{step_name}_{name}.html'
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"    [OK] 저장: {file_path.name}")
        except Exception as e:
            print(f"    [FAIL] {name} 저장 실패: {e}")

def main():
    print("=" * 60)
    print("HIRA 자동 페이지 캡처")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. 메인 페이지
            print(f"\n1. 메인 페이지 접속: {BASE_URL}")
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            save_all_frames(page, "step1_main")

            # 스크린샷
            screenshot_path = DEBUG_DIR / 'step1_main.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  [OK] 스크린샷: {screenshot_path.name}")

            # 2. 서식정보 탭 클릭
            print("\n2. 서식정보 탭 클릭")
            page.evaluate("menu_go('2')")
            time.sleep(3)
            save_all_frames(page, "step2_attach_tab")

            screenshot_path = DEBUG_DIR / 'step2_attach_tab.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  [OK] 스크린샷: {screenshot_path.name}")

            # 3. SEQ=2로 폼 제출
            print("\n3. SEQ=2 폼 제출")
            page.evaluate("""() => {
                document.getElementById('SEQ').value = '2';
                document.getElementById('SEQ_ATTACH_TYPE').value = '0';
                document.getElementById('SEARCH_TYPE').value = 'all';
                document.getElementById('seachForm').action = '/lmxsrv/attach/attachList.srv';
                document.getElementById('seachForm').submit();
            }""")
            time.sleep(3)
            save_all_frames(page, "step3_seq2_submit")

            screenshot_path = DEBUG_DIR / 'step3_seq2_submit.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  [OK] 스크린샷: {screenshot_path.name}")

            # 4. 트리에서 "별표" 클릭 (실제 서식 목록 진입)
            print("\n4. 트리에서 '별표' 클릭")

            # tree01 iframe 접근
            tree_frame = page.frame(name="tree01")
            if not tree_frame:
                print("  [FAIL] tree01 iframe을 찾을 수 없습니다")
            else:
                # 방법: JavaScript로 직접 choiceAttachType 호출
                print("  - 트리 노드 JavaScript 함수 직접 호출...")
                page.evaluate("choiceAttachType(2, 2)")
                time.sleep(3)
                print("    [OK] choiceAttachType(2, 2) 호출됨")

                # contentbody가 변경되었는지 확인
                content_frame = page.frame(name="contentbody")
                if content_frame:
                    content_url = content_frame.url
                    print(f"    [OK] contentbody URL: {content_url}")

            save_all_frames(page, "step4_tree_click_byulpyo")
            screenshot_path = DEBUG_DIR / 'step4_tree_click_byulpyo.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  [OK] 스크린샷: {screenshot_path.name}")

            # 5. 브라우저 유지 (수동 확인용)
            print("\n" + "=" * 60)
            print("캡처 완료! 브라우저를 30초간 유지합니다.")
            print("수동으로 페이지를 탐색해보세요.")
            print(f"결과 저장 위치: {DEBUG_DIR}")
            print("=" * 60)

            time.sleep(30)

        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

    print("\n완료!")


if __name__ == '__main__':
    main()
