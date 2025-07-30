import time
import requests
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

# --- 1. DB 설정 및 연결 함수 ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'recruit',
    'port': 3307
}

def create_connection(config):
    """DB 연결 생성"""
    connection = None
    try:
        connection = mysql.connector.connect(**config)
        print("🎉 MySQL DB에 성공적으로 연결되었습니다.")
    except Error as e:
        print(f"DB 연결 중 오류 발생: {e}")
    return connection

def insert_job_data(cursor, data):
    """크롤링한 데이터를 DB에 삽입"""
    query = """
        INSERT INTO recruitment
        (title, company_name, company_location, is_regular, require_career, require_education,
         require_skill, detail_url, create_date, expire_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title=VALUES(title), company_location=VALUES(company_location), is_regular=VALUES(is_regular),
            require_career=VALUES(require_career), require_education=VALUES(require_education),
            require_skill=VALUES(require_skill), create_date=VALUES(create_date), expire_date=VALUES(expire_date);
    """
    try:
        cursor.execute(query, data)
        print(f"  ✅ [DB 저장/업데이트 완료] {data[0]}")
    except Error as e:
        print(f"  ❌ [DB 저장 실패] {data[0]} - {e}")

# --- 2. 상세 페이지 크롤링 함수 (Requests + BeautifulSoup) ---
def scrape_detail_page(url):
    """
    주어진 URL의 상세 정보를 Requests를 이용해 크롤링.
    """
    details = {}
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 클래스 이름이 불안정하므로 구조적 선택자 사용
        header = soup.select_one("main > div:nth-child(3) > div > div > div:nth-child(1)")
        if not header:
            return None

        details['title'] = header.select_one("h1.break-all").text.strip()
        details['company_name'] = header.select_one("span.w-fit").text.strip()
        details['expire_date'] = header.select_one("div.font-semibold").text.strip()
        details['create_date'] = header.select_one("div.font-normal").text.strip()

        info_divs = header.select("div.text-black")
        details['require_career'] = info_divs[0].text.strip() if len(info_divs) > 0 else ''
        details['company_location'] = info_divs[1].text.strip() if len(info_divs) > 1 else ''
        details['require_education'] = info_divs[2].text.strip() if len(info_divs) > 2 else ''
        details['is_regular'] = info_divs[3].text.strip() if len(info_divs) > 3 else ''
        details['require_skill'] = info_divs[4].text.strip() if len(info_divs) > 4 else ''
        
        return details

    except Exception as e:
        print(f"    상세 페이지 파싱 오류: {e}")
        return None

# --- 3. 메인 실행 로직 ---
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
    options.add_argument(f"user-agent={UserAgent().chrome}")
    
    driver = None
    try:
        # --- 목록 페이지 크롤링 (Selenium) ---
        print("직행 목록 페이지 로딩 및 스크롤 중...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        url = f"https://zighang.com/all?q={keyword}"
        driver.get(url)

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/recruitment/"]')))
        
        # 스크롤을 내려서 더 많은 공고를 로드
        for _ in range(3): # 3회 정도 스크롤
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        items = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/recruitment/"]')
        
        job_urls = list(set([item.get_attribute('href') for item in items])) # 중복 URL 제거

        print(f"\n총 {len(job_urls)}개의 채용 공고를 발견했습니다. 상세 정보 크롤링을 시작합니다.")

        # --- 상세 페이지 순회 및 데이터 통합/저장 (Requests) ---
        for i, job_url in enumerate(job_urls):
            print(f"\n({i+1}/{len(job_urls)}) {job_url} 처리 중...")
            
            # 상세 페이지는 Requests로 크롤링
            detail_data = scrape_detail_page(job_url)

            if detail_data:
                # DB 형식에 맞춰 최종 데이터 조합
                final_data = (
                    detail_data.get('title', ''),
                    detail_data.get('company_name', ''),
                    detail_data.get('company_location', ''),
                    detail_data.get('is_regular', ''),
                    detail_data.get('require_career', ''),
                    detail_data.get('require_education', ''),
                    detail_data.get('require_skill', ''),
                    job_url,
                    detail_data.get('create_date', ''),
                    detail_data.get('expire_date', '')
                )
                insert_job_data(cursor, final_data)
            else:
                 print(f"  - 상세 정보 수집 실패. 건너뜁니다.")


    except Exception as e:
        print(f"전체 크롤링 과정에서 오류 발생: {e}")
    finally:
        if driver:
            driver.quit()
        if conn and conn.is_connected():
            conn.commit()
            cursor.close()
            conn.close()
            print("\n모든 작업 완료. DB 연결을 종료합니다.")

if __name__ == "__main__":
    main()