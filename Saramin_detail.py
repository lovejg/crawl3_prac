from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def scrape_job_info(url):
    options = Options()
    options.add_argument('--headless')  # 창 띄워서 크롤링 할거면 주석처리
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(2)  # 페이지 로딩 대기

        container = driver.find_element(By.CLASS_NAME, "jv_header")

        # 회사 이름
        company = container.find_element(By.CSS_SELECTOR, "div.title_inner a.company").text.strip()

        # 공고 제목
        job_title = container.find_element(By.CSS_SELECTOR, "h1.tit_job").text.strip()

        # 채용중인 공고 수
        recruit_num = container.find_element(By.CSS_SELECTOR, "a.btn_careers span.num").text.strip()

        # 마감 날짜
        deadline = container.find_element(By.CSS_SELECTOR, "div.btn_apply span.dday").text.strip()

        # 출력
        print(f"회사 이름: {company}")
        print(f"공고 제목: {job_title}")
        print(f"채용중인 공고 수: {recruit_num}")
        print(f"마감 날짜: {deadline}")

    except Exception as e:
        print("데이터 추출 중 오류 발생:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    url = input("URL 입력: ").strip()
    print("크롤링 시작")
    scrape_job_info(url)
