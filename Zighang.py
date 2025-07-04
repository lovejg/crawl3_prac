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

def crawl_zighang(keyword):
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
        url = f"https://zighang.com/all?q={keyword}"
        driver.get(url)

        print("직행 페이지 로딩 중...")
        selector = 'a[href^="/recruitment/"]'
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        time.sleep(2)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        items = driver.find_elements(By.CSS_SELECTOR, selector)
        
        nowDate = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"현재 날짜: {nowDate}")

        for item in items:
            try:
                summary_divs = item.find_elements(By.CSS_SELECTOR, 'div.ds-web-summary')
            
                if len(summary_divs) < 2:
                    continue
                    
                # 회사명
                company = summary_divs[0].text.strip()

                # 상세 정보
                details = summary_divs[1].text.strip()
                parts = details.split('·')
                cleaned_parts = [p.strip().splitlines()[0] for p in parts]
                formatted_details = ", ".join(cleaned_parts)
                
                # 공고 제목
                title_elem = item.find_element(By.CSS_SELECTOR, 'p.ds-web-title2')
                title = title_elem.text.strip()

                # 상세페이지 URL
                link = item.get_attribute('href')
                
                # 데드라인
                deadline_elem = item.find_element(By.CSS_SELECTOR, 'div.ds-web-subtitle1')
                deadline = deadline_elem.text.strip()
                
                # 중복 제거: 이미 본 링크면 skip
                if link in seen_links:
                    continue
                seen_links.add(link)
                
                job_data = {
                    '회사명': company,
                    '공고명': title,
                    '링크': link,
                    '상세정보': formatted_details,
                    '데드라인': deadline
                }
                job_list.append(job_data)

                # 원하는 개수만큼만 수집
                if len(job_list) >= 20:
                    break

            except Exception as e:
                print(f"채용 정보 파싱 오류: {e}")
                continue

        print(f"직행 크롤링 결과: {len(job_list)}개 수집")
        return job_list

    except Exception as e:
        print(f"직행 크롤링 실패: {e}")
        return []

    finally:
        if driver:
            driver.quit()

def main():
    keyword = input("키워드 입력: ").strip()
    print(f"키워드 '{keyword}'로 채용정보 크롤링 시작")

    wanted_jobs = crawl_zighang(keyword)

    print("\n=== 크롤링 결과 ===")
    print(f"{len(wanted_jobs)}개")

    if wanted_jobs:
        print("\n=== 크롤링된 채용 정보 ===")
        for job in wanted_jobs:
            print(f"회사명: {job['회사명']}\n공고 제목: {job['공고명']}\n상세페이지 URL: {job['링크']}\n상세정보: {job['상세정보']}\n데드라인: {job['데드라인']}\n")
    else:
        print("\n 크롤링된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
