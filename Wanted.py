from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time

def crawl_wanted(keyword):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={UserAgent().chrome}")

    job_list = []
    seen_links = set()  # 중복 확인용
    driver = None

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        url = f"https://www.wanted.co.kr/search?query={keyword}&tab=position"
        driver.get(url)

        print("원티드 페이지 로딩 중...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.JobCard_container__zQcZs')))
        time.sleep(2)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        selector = 'div.JobCard_container__zQcZs'
        items = driver.find_elements(By.CSS_SELECTOR, selector)

        for item in items:
            try:
                # 공고 제목
                title_elem = item.find_element(By.CSS_SELECTOR, 'strong.JobCard_title___kfvj')
                title = title_elem.text.strip()
                if not title:
                    title = title_elem.get_attribute('textContent').strip()

                # 회사명
                company_elem = item.find_element(By.CSS_SELECTOR, 'span.JobCard_companyContent__lX5Lv')
                company = company_elem.text.strip()
                if not company:
                    company = company_elem.get_attribute('textContent').strip()

                # 상세페이지 URL
                link_elem = item.find_element(By.TAG_NAME, 'a')
                link = link_elem.get_attribute('href')

                # 중복 제거: 이미 본 링크면 skip
                if link in seen_links:
                    continue
                seen_links.add(link)

                job_list.append({
                    '회사명': company,
                    '공고명': title,
                    '링크': link
                })

                # 원하는 개수만큼만 수집 (20개로 했는데 왜인지는 모르겠는데 중복이 엄청 떠서 중복 제거하면 12개임(3줄))
                if len(job_list) >= 20:
                    break

            except Exception as e:
                print(f"채용 정보 파싱 오류: {e}")
                continue

        print(f"원티드 크롤링 결과: {len(job_list)}개 수집")
        return job_list

    except Exception as e:
        print(f"원티드 크롤링 실패: {e}")
        return []

    finally:
        if driver:
            driver.quit()

def main():
    keyword = input("키워드 입력: ").strip()
    print(f"키워드 '{keyword}'로 채용정보 크롤링 시작")

    wanted_jobs = crawl_wanted(keyword)

    print("\n=== 크롤링 결과 ===")
    print(f"{len(wanted_jobs)}개")

    if wanted_jobs:
        print("\n=== 크롤링된 채용 정보 ===")
        for job in wanted_jobs:
            print(f"회사명: {job['회사명']}\n공고 제목: {job['공고명']}\n상세페이지 URL: {job['링크']}\n")
    else:
        print("\n 크롤링된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
