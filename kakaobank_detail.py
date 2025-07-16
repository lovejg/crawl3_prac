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
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def crawl_job_details(url):
    """
    주어진 URL에서 채용 공고 상세 정보를 크롤링합니다.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={UserAgent().chrome}")

    driver = None
    job_details = {}  # 크롤링 결과를 담을 딕셔너리

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        print("페이지로 이동 중...")
        
        main_container_selector = ".recruit_detail"

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, main_container_selector))
        )
        time.sleep(2) 
        print("페이지 로딩 완료. 데이터 추출을 시작합니다.")

        # --- 데이터 추출 시작 ---
        detail_container = driver.find_element(By.CSS_SELECTOR, main_container_selector)

        # 1. 기본 정보 추출 (공고 제목, 분야, 마감일)
        try:
            job_details['공고 제목'] = detail_container.find_element(By.CSS_SELECTOR, 'h3.tit_intro').text.strip()
        except NoSuchElementException:
            job_details['공고 제목'] = "정보 없음"
        
        try:
            job_details['분야'] = detail_container.find_element(By.CSS_SELECTOR, 'div.info_desc > span').text.strip()
        except NoSuchElementException:
            job_details['분야'] = "정보 없음"
            
        try:
            job_details['마감일'] = detail_container.find_element(By.CSS_SELECTOR, 'div.item_card').text.strip()
        except NoSuchElementException:
            job_details['마감일'] = "정보 없음"

        # 2. 상세 설명 섹션 추출 ('Recruiter Says', '담당할 업무' 등)
        # 'desc_cont' 클래스를 가진 모든 설명 컨테이너를 찾음
        desc_containers = detail_container.find_elements(By.CSS_SELECTOR, 'div.desc_cont')

        for container in desc_containers:
            try:
                title = container.find_element(By.CSS_SELECTOR, 'div.tit').text.strip()
                content = container.find_element(By.CSS_SELECTOR, 'div.cont').text.strip()

                if not title or not content:
                    continue
                
                job_details[title] = content
            
            except NoSuchElementException:
                continue
        
        print("모든 정보 추출 완료.")
        return job_details

    except TimeoutException:
        print("페이지 로딩 시간 초과: 메인 컨텐츠를 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        return None

    finally:
        if driver:
            driver.quit()

def main():
    keyURL = input("크롤링할 카카오뱅크 채용 공고 URL: ").strip()
    print("\n크롤링을 시작합니다...")

    job_data = crawl_job_details(keyURL)
    
    nowDate = datetime.datetime.now().strftime('%Y-%m-%d')

    print("\n" + "="*20 + " 크롤링 결과 " + "="*20)
    print(f"(조회 날짜: {nowDate})")
    
    if job_data:
        for key, value in job_data.items():
            print("\n" + "-"*40)
            print(f"✅ {key}")
            print("-"*(len(key)+3))
            print(value)
        print("\n" + "="*50)
    else:
        print("\n크롤링된 데이터가 없습니다. URL을 확인해주세요.")


if __name__ == "__main__":
    main()