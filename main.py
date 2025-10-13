"""
EMR 인증 정보 크롤러 메인 스크립트
"""
import argparse
from emrcert.scrapers.product_certification import ProductCertificationScraper
from emrcert.scrapers.usage_certification import UsageCertificationScraper

def main():
    parser = argparse.ArgumentParser(description='EMR 인증 정보 크롤러')
    parser.add_argument(
        '--type',
        choices=['product', 'usage', 'all'],
        default='all',
        help='크롤링 타입: product(제품인증), usage(사용인증), all(모두)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='브라우저를 headless 모드로 실행 (기본값: True)'
    )
    parser.add_argument(
        '--visible',
        action='store_true',
        help='브라우저를 visible 모드로 실행'
    )

    args = parser.parse_args()

    # visible 플래그가 있으면 headless를 False로
    headless = not args.visible if args.visible else args.headless

    print("=" * 60)
    print("EMR 인증 정보 크롤러 시작")
    print("=" * 60)

    if args.type in ['product', 'all']:
        print("\n[1/2] 제품인증 크롤링 시작...")
        scraper = ProductCertificationScraper(headless=headless)
        scraper.run()

    if args.type in ['usage', 'all']:
        print("\n[2/2] 사용인증 크롤링 시작...")
        scraper = UsageCertificationScraper(headless=headless)
        scraper.run()

    print("\n" + "=" * 60)
    print("모든 크롤링 작업 완료!")
    print("결과 파일 위치: ./data/emrcert/ 폴더")
    print("=" * 60)

if __name__ == '__main__':
    main()
