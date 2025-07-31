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

# --- 1. DB 설정 및 연결 함수 ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'recruit',
    'port': 3307,
    'charset': 'utf8mb4'
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
        (title, company_name, company_location, require_career, detail_url, detail, expire_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title=VALUES(title), company_location=VALUES(company_location),
            detail=VALUES(detail), expire_date=VALUES(expire_date);
    """
    try:
        cursor.execute(query, data)
        print(f"  ✅ [DB 저장/업데이트 완료] {data[0]}")
    except Error as e:
        print(f"  ❌ [DB 저장 실패] {data[0]} - {e}")

def scrape_detail_page(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section.JobContent_JobContent__Qb6DR"))
        )
        time.sleep(3)

        try:
            buttons = driver.execute_script("""
                return Array.from(document.querySelectorAll('button')).filter(
                    btn => btn.textContent.includes('더보기') || btn.textContent.includes('상세정보')
                );
            """)
            if buttons:
                driver.execute_script("arguments[0].click();", buttons[0])
                time.sleep(3)
        except Exception as e:
            print(f"    더보기 버튼 클릭 실패: {e}")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        main_content = soup.select_one("section.JobContent_descriptionWrapper__RMlfm")
        header_content = soup.select_one("header.JobHeader_JobHeader__TZkW3")
        if not main_content or not header_content:
            print("    주요 컨텐츠 영역을 찾을 수 없습니다.")
            return None

        details = {}

        # 제목
        title_elem = header_content.select_one("h1.wds-58fmok")
        details['title'] = title_elem.text.strip() if title_elem else ''

        # 회사명
        company_elem = header_content.select_one("a.JobHeader_JobHeader__Tools__Company__Link__NoBQI")
        details['company'] = company_elem.text.strip() if company_elem else ''

        # 경력
        career_elem = header_content.select("span.JobHeader_JobHeader__Tools__Company__Info__b9P4Y")[1]
        details['career'] = career_elem.text.strip() if (career_elem) else ''

        # 마감일
        expire_elem = main_content.select_one("span.wds-1u1yyy")
        details['expire_date'] = expire_elem.text.strip() if expire_elem else ''
        
        # 위치
        location_elem = main_content.select_one("span.wds-1td1qmv")
        details['location'] = location_elem.text.strip() if location_elem else ''

         # ✅ 상세 정보 파트별 추출
        part_sections = main_content.select("section[class*='JobContent'] span[class*='wds-']")
        section_labels = ['포지션 상세', '주요업무', '자격요건', '우대사항', '혜택 및 복지', '채용 전형']
        section_data = {}

        for i, label in enumerate(section_labels):
            section_data[label] = part_sections[i].text.strip() if i < len(part_sections) else '정보 없음'

        # ✅ 회사 태그
        try:
            tags_article = soup.select_one("article.CompanyTags_CompanyTags__OpNto")
            if tags_article:
                tag_buttons = tags_article.select("button[data-attribute-id='company__tag__click']")
                tags_list = [btn.get('data-tag-name') for btn in tag_buttons if btn.get('data-tag-name')]
                section_data['회사 태그'] = ', '.join(tags_list) if tags_list else '정보 없음'
            else:
                section_data['회사 태그'] = '정보 없음'
        except:
            section_data['회사 태그'] = '정보 없음'
            
        # ✅ detail 문자열로 조립
        detail_text = ""
        for label in section_labels + ['회사 태그']:
            detail_text += f"## {label}\n{section_data[label]}\n\n"

        details['detail_text'] = detail_text.strip()

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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(f"user-agent={UserAgent().chrome}")

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        url = f"https://www.wanted.co.kr/search?query={keyword}&tab=position"
        driver.get(url)

        print("원티드 목록 페이지 로딩 및 스크롤 중...")

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.JobCard_container__zQcZs'))
            )
        except Exception as e:
            print(f"페이지 로딩 실패: {e}")
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-cy="job-card"]'))
                )
                print("대안 선택자로 페이지 로딩 성공")
            except:
                print("페이지 로딩에 실패했습니다.")
                return

        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print(f"스크롤 {i+1}/5 완료")

        selectors = [
            'div.JobCard_container__zQcZs',
            '[data-cy="job-card"]',
            'div[class*="JobCard"]'
        ]

        items = []
        for selector in selectors:
            items = driver.find_elements(By.CSS_SELECTOR, selector)
            if items:
                print(f"선택자 '{selector}'로 {len(items)}개 요소 발견")
                break

        if not items:
            print("채용 공고를 찾을 수 없습니다.")
            return

        job_links = []
        seen_links = set()

        for item in items:
            try:
                link_elem = item.find_element(By.TAG_NAME, 'a')
                link = link_elem.get_attribute('href')

                if link and link not in seen_links:
                    seen_links.add(link)
                    job_links.append({'url': link})
            except Exception as e:
                print(f"항목 파싱 오류: {e}")
                continue

        print(f"\n총 {len(job_links)}개의 채용 공고를 발견했습니다. 상세 정보 크롤링을 시작합니다.")

        if not job_links:
            print("수집된 채용 공고가 없습니다.")
            return

        for i, job in enumerate(job_links):
            print(f"\n({i+1}/{len(job_links)}) 상세 정보 크롤링 중...")

            detail_data = scrape_detail_page(driver, job['url'])

            if detail_data:
                print(f"    ▶ 공고 제목: {detail_data.get('title', '')}")
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
                print(f"  ⚠️ 상세 정보 크롤링 실패, 기본 정보만 저장")
                basic_data = (
                    '', '', '', '', job['url'], '', ''
                )
                insert_job_data(cursor, basic_data)

            time.sleep(1)

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
