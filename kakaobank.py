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
from selenium.common.exceptions import TimeoutException

def crawl_kakaobank():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={UserAgent().chrome}")

    driver = None 
    job_list = []
    processed_links = set()  # 중복 공고 방지용 set

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        types = ['Infra', 'Frontend', 'Server', 'AI', 'Engineering', 'Security', 'Data', 'Mobile']
        
        print("카카오뱅크 채용 정보 크롤링을 시작합니다.")
        nowDate = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"현재 날짜: {nowDate}\n")
        
        for job_type in types:
            url = f'https://recruit.kakaobank.com/jobs?recruitClassName={job_type}'
            print(f"'{job_type}' 카테고리를 확인 중...")
            driver.get(url)

            try:
                selector = 'ul.list_board > li'
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                items = driver.find_elements(By.CSS_SELECTOR, selector)

                for item in items:
                    try:
                        link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                        if link in processed_links:
                            continue  # 이미 처리된 공고는 건너뛰기
                        processed_links.add(link)

                        deadline_element = item.find_element(By.CSS_SELECTOR, '.tit_date')
                        deadline = deadline_element.text.strip()

                        title_full_text = item.find_element(By.CSS_SELECTOR, '.tit_board').text
                        title = title_full_text.replace(deadline, '').strip()
                        
                        category = item.find_element(By.CSS_SELECTOR, '.txt_desc').text.strip()
                        
                        job_list.append({
                            '공고명': title,
                            '카테고리': category,
                            '데드라인': deadline,
                            '링크': link
                        })

                    except Exception as e:
                        print(f"  ㄴ 개별 채용 정보 파싱 오류: {e}")
                        continue
            
            except TimeoutException:
                print(f"  -> '{job_type}' 카테고리에 진행중인 공고가 없습니다.")
                continue

    except Exception as e:
        print(f"크롤링 프로세스 중 오류 발생: {e}")
        return []

    finally:
        if driver:
            driver.quit()
            
    print(f"\n카카오뱅크 크롤링 완료: 총 {len(job_list)}개의 고유한 공고를 수집했습니다.")
    return job_list

def main():
    print("="*40)
    kakaobank_jobs = crawl_kakaobank()
    print("="*40)

    if kakaobank_jobs:
        print(f"\n[최종 크롤링 결과: {len(kakaobank_jobs)}개]\n")
        for job in kakaobank_jobs:
            print(f"공고 제목: {job['공고명']}\n카테고리: {job['카테고리']}\n데드라인: {job['데드라인']}\n상세페이지 URL: {job['링크']}\n")
    else:
        print("\n크롤링된 데이터가 없습니다.")

if __name__ == "__main__":
    main()