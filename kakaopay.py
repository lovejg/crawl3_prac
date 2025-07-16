import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

def crawl_kakaopay():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={UserAgent().chrome}")

    driver = None
    job_list = []

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        url = 'https://kakaopay.career.greetinghr.com/ko/main?occupations=기술'
        
        print("카카오페이 채용 정보 크롤링을 시작합니다.")
        nowDate = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"현재 날짜: {nowDate}\n")
        
        driver.get(url)

        list_item_selector = "ul.ffGmZN > a"
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, list_item_selector))
            )
        except TimeoutException:
            print("채용 공고를 찾을 수 없습니다. 페이지 구조가 변경되었거나 공고가 없습니다.")
            return []

        # 페이지 끝까지 스크롤
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        html = BeautifulSoup(driver.page_source, 'html.parser')
        
        items = html.select("ul.ffGmZN > a")

        for item in items:
            try:
                base_url = "https://kakaopay.career.greetinghr.com"
                link_suffix = item['href']
                link = f"{base_url}{link_suffix}"

                title = item.select_one('span.gMeHeg').text.strip()
                info_items = item.select('.gAEjfw span')

                career = "정보 없음"
                work_type = "정보 없음"
                # 상세 정보 파싱 (예외적인 '외' 글자 처리 포함)
                for info in info_items:
                    text = info.get_text(strip=True)
                    if '년' in text or '신입' in text or '무관' in text:
                        career = text
                    elif '정규' in text or '계약' in text:
                        work_type = text
                
                job_list.append({
                    '회사명': '카카오페이',
                    '공고명': title,
                    '경력': career,
                    '근무형태': work_type,
                    '링크': link
                })

            except Exception as e:
                print(f"  ㄴ 개별 채용 정보 파싱 오류: {e}")
                continue
    
    except Exception as e:
        print(f"크롤링 프로세스 중 오류 발생: {e}")
        return []

    finally:
        if driver:
            driver.quit()
            
    print(f"\n카카오페이 크롤링 완료: 총 {len(job_list)}개의 공고를 수집했습니다.")
    return job_list

def main():
    print("="*40)
    kakaopay_jobs = crawl_kakaopay()
    print("="*40)

    if kakaopay_jobs:
        print(f"\n[최종 크롤링 결과: {len(kakaopay_jobs)}개]\n")
        for job in kakaopay_jobs:
            print(f"회사명: {job['회사명']}\n공고명: {job['공고명']}\n경력: {job['경력']}\n근무형태: {job['근무형태']}\n링크: {job['링크']}\n")
    else:
        print("\n크롤링된 데이터가 없습니다.")


if __name__ == "__main__":
    main()