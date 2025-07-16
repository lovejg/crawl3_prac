from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time
import datetime

def crawl_kakaobank():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={UserAgent().chrome}")

    job_list = []
    driver = None
    
    types = ['Infra', 'Frontend', 'Server', 'AI', 'Engineering', 'Security', 'Data', 'Mobile']
    
    print("카카오뱅크 페이지 로딩 중...")
    nowDate = datetime.datetime.now().strftime('%Y-%m-%d')
    print(f"현재 날짜: {nowDate}")
    
    for type in types:
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            url = f'https://recruit.kakaobank.com/jobs?recruitClassName={type}'
            driver.get(url)

            selector = 'ul.list_board > li'
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))) # 컨테이너 뼈대 로딩

            items = driver.find_elements(By.CSS_SELECTOR, selector)

            for item in items:
                try:
                    
                    info = item.find_element(By.CSS_SELECTOR, '.recruit_desc').text.strip().splitlines()
                    
                    title = info[0] if len(info) > 0 else "" # 공고 제목
                    deadline = info[1] if len(info) > 1 else "" # 데드라인
                    category = info[2] if len(info) > 2 else "" # 카테고리
                    
                    # 상세페이지 URL
                    link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')

                    job_list.append({
                        '공고명': title,
                        '카테고리': category,
                        '데드라인': deadline,
                        '링크': link
                    })

                except Exception as e:
                    print(f"채용 정보 파싱 오류: {e}")
                    continue

        except Exception as e:
            print(f"카카오뱅크 크롤링 실패: {e}")
            return []

        finally:
            if driver:
                driver.quit()
                
    print(f"카카오뱅크 크롤링 결과: {len(job_list)}개 수집")
    return job_list

def main():
    print("채용정보 크롤링 시작")

    kakaobank_jobs = crawl_kakaobank()

    print("\n=== 크롤링 결과 ===")
    print(f"{len(kakaobank_jobs)}개")

    if kakaobank_jobs:
        print("\n=== 크롤링된 채용 정보 ===")
        for job in kakaobank_jobs:
            print(f"공고 제목: {job['공고명']}\n카테고리: {job['카테고리']}\n데드라인: {job['데드라인']}\n상세페이지 URL: {job['링크']}\n")
    else:
        print("\n 크롤링된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
