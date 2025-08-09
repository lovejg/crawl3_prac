import time
import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import mysql.connector
from mysql.connector import Error

# --- DB 설정 ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'recruit',
    'port': 3307,
    'charset': 'utf8mb4'
}

def create_connection(config):
    try:
        conn = mysql.connector.connect(**config)
        print("🎉 DB 연결 성공")
        return conn
    except Error as e:
        print(f"DB 연결 오류: {e}")
        return None

def insert_job_data(cursor, data):
    query = """
        INSERT INTO recruitment
        (title, company_name, company_location, require_career, detail_url, detail, expire_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title=VALUES(title), company_location=VALUES(company_location),
            detail=VALUES(detail), expire_date=VALUES(expire_date);
    """
    try:
        cursor.execute(query, data)
    except Error as e:
        print(f"❌ DB 저장 실패: {data[0]} - {e}")

def scrape_detail_page(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section.JobContent_JobContent__Qb6DR"))
        )

        # 더보기 버튼 클릭
        try:
            more_button = driver.find_elements(By.XPATH, "//button[contains(text(), '더보기') or contains(text(), '상세정보')]")
            if more_button:
                more_button[0].click()
                WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "section.JobContent_descriptionWrapper__RMlfm"))
                )
        except:
            pass

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        main_content = soup.select_one("section.JobContent_descriptionWrapper__RMlfm")
        header_content = soup.select_one("header.JobHeader_JobHeader__TZkW3")
        if not main_content or not header_content:
            return None

        details = {}
        details['title'] = header_content.select_one("h1.wds-58fmok").text.strip() if header_content.select_one("h1.wds-58fmok") else ''
        details['company'] = header_content.select_one("a.JobHeader_JobHeader__Tools__Company__Link__NoBQI").text.strip() if header_content.select_one("a.JobHeader_JobHeader__Tools__Company__Link__NoBQI") else ''
        career_elem = header_content.select("span.JobHeader_JobHeader__Tools__Company__Info__b9P4Y")
        details['career'] = career_elem[1].text.strip() if len(career_elem) > 1 else ''
        details['expire_date'] = main_content.select_one("span.wds-1u1yyy").text.strip() if main_content.select_one("span.wds-1u1yyy") else ''
        details['location'] = main_content.select_one("span.wds-1td1qmv").text.strip() if main_content.select_one("span.wds-1td1qmv") else ''

        part_sections = main_content.select("section[class*='JobContent'] span[class*='wds-']")
        section_labels = ['포지션 상세', '주요업무', '자격요건', '우대사항', '혜택 및 복지', '채용 전형']
        section_data = {label: (part_sections[i].text.strip() if i < len(part_sections) else '정보 없음') for i, label in enumerate(section_labels)}

        # 회사 태그
        tags_article = soup.select_one("article.CompanyTags_CompanyTags__OpNto")
        if tags_article:
            tag_buttons = tags_article.select("button[data-attribute-id='company__tag__click']")
            tags_list = [btn.get('data-tag-name') for btn in tag_buttons if btn.get('data-tag-name')]
            section_data['회사 태그'] = ', '.join(tags_list) if tags_list else '정보 없음'
        else:
            section_data['회사 태그'] = '정보 없음'

        details['detail_text'] = "\n\n".join([f"## {label}\n{section_data[label]}" for label in section_labels + ['회사 태그']])
        return details

    except:
        return None

def main():
    keyword = input("검색할 키워드를 입력하세요: ").strip()

    conn = create_connection(db_config)
    if not conn:
        return
    cursor = conn.cursor()

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(f"user-agent={UserAgent().chrome}")

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        url = f"https://www.wanted.co.kr/search?query={keyword}&tab=position"
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.JobCard_container__zQcZs, [data-cy="job-card"]'))
        )

        job_links = []
        seen_links = set()
        target_count = 12

        for _ in range(5):
            items = driver.find_elements(By.CSS_SELECTOR, 'div.JobCard_container__zQcZs, [data-cy="job-card"]')
            for item in items:
                try:
                    link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    if link and link not in seen_links:
                        seen_links.add(link)
                        job_links.append({'url': link})
                        if len(job_links) >= target_count:
                            break
                except:
                    continue
            if len(job_links) >= target_count:
                break
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

        print(f"총 {len(job_links)}개 공고 수집. 상세 페이지 크롤링 시작...")

        for i, job in enumerate(job_links, start=1):
            print(f"[{i}/{len(job_links)}] {job['url']}")
            detail_data = scrape_detail_page(driver, job['url'])
            if detail_data:
                final_data = (
                    detail_data.get('title', ''),
                    detail_data.get('company', ''),
                    detail_data.get('location', ''),
                    detail_data.get('career', ''),
                    job['url'],
                    detail_data.get('detail_text', ''),
                    detail_data.get('expire_date', '')
                )
                insert_job_data(cursor, final_data)
            else:
                insert_job_data(cursor, ('', '', '', '', job['url'], '', ''))

        conn.commit()
        print("✅ 모든 데이터 저장 완료")

    finally:
        if driver:
            driver.quit()
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("DB 연결 종료")

if __name__ == "__main__":
    main()
