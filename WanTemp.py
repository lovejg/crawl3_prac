import time
import datetime
import mysql.connector
from mysql.connector import Error
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# DB 설정
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'recruit',
    'port': 3307
}

def create_connection(config):
    try:
        conn = mysql.connector.connect(**config)
        print("✅ DB 연결 성공")
        return conn
    except Error as e:
        print(f"DB 연결 실패: {e}")
        return None

def insert_job(cursor, data):
    query = """
        INSERT INTO recruitment 
        (title, company_name, company_location, require_career, require_skill, 
         detail_url, detail, expire_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, data)
        print(f"📥 저장 성공: {data[0]}")
    except Error as e:
        print(f"❌ 저장 실패: {e}")

# 상세 페이지 크롤링
def crawl_job_detail(detail_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={UserAgent().chrome}")
    driver = None

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(detail_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.JobContent_JobContent__Qb6DR")))
        time.sleep(2)

        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        html = soup.select_one("section.JobContent_JobContent__Qb6DR")
        main = html.select_one("section.JobContent_descriptionWrapper__RMlfm")

        # 기술 스택
        tags_article = soup.select_one("article.CompanyTags_CompanyTags__OpNto")
        tag_buttons = tags_article.select("button[data-attribute-id='company__tag__click']") if tags_article else []
        skills = ', '.join([btn.get('data-tag-name') for btn in tag_buttons if btn.get('data-tag-name')])

        # 상세 정보
        details = main.select("span.wds-h4ga6o")
        full_detail = "\n".join([d.text.strip() for d in details])

        # 마감일
        deadline = main.select_one("span.wds-1u1yyy")
        expire = deadline.text.strip() if deadline else '정보 없음'

        return skills, full_detail, expire

    except Exception as e:
        print(f"❌ 상세 페이지 오류: {e}")
        return '', '', ''
    finally:
        if driver:
            driver.quit()

# 메인 크롤링
def crawl_wanted(keyword):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={UserAgent().chrome}")

    driver = None
    seen_links = set()
    results = []

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(f"https://www.wanted.co.kr/search?query={keyword}&tab=position")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.JobCard_container__zQcZs')))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        items = driver.find_elements(By.CSS_SELECTOR, 'div.JobCard_container__zQcZs')

        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, 'strong.JobCard_title___kfvj').text.strip()
                info = item.find_elements(By.CSS_SELECTOR, 'span.wds-nkj4w6')
                if len(info) < 2:
                    continue

                company = info[0].text.strip()
                career = info[1].text.strip()
                link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')

                if link in seen_links:
                    continue
                seen_links.add(link)

                skills, detail, expire = crawl_job_detail(link)

                # 회사 위치는 상세 페이지에서 같이 가져올 수도 있음 → 일단은 "정보 없음"
                results.append((title, company, '정보 없음', career, skills, link, detail, expire))

            except Exception as e:
                print(f"⚠️ 개별 항목 오류: {e}")
                continue

    except Exception as e:
        print(f"❌ 메인 크롤링 실패: {e}")
    finally:
        if driver:
            driver.quit()
    return results

# 메인 실행
def main():
    keyword = input("키워드 입력: ").strip()
    print(f"\n🔍 '{keyword}' 키워드로 원티드 크롤링 시작")
    conn = create_connection(db_config)
    if not conn:
        return
    cursor = conn.cursor()

    jobs = crawl_wanted(keyword)
    print(f"\n✅ 총 {len(jobs)}개의 공고 수집됨")

    for job in jobs:
        insert_job(cursor, job)

    conn.commit()
    cursor.close()
    conn.close()
    print("\n🎉 모든 데이터 저장 완료. DB 연결 종료.")

if __name__ == "__main__":
    main()
