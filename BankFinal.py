import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
        (title, company_name, company_location, category, detail_url, detail, expire_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title=VALUES(title), category=VALUES(category),
            detail=VALUES(detail), expire_date=VALUES(expire_date);
    """
    try:
        cursor.execute(query, data)
        print(f"  ✅ [DB 저장/업데이트 완료] {data[0]}")
    except Error as e:
        print(f"  ❌ [DB 저장 실패] {data[0]} - {e}")

# --- 2. 상세 페이지 크롤링 함수 ---
def scrape_detail_page(driver):
    """
    현재 드라이버가 위치한 페이지의 상세 정보를 크롤링.
    """
    try:
        # 페이지 로딩 대기
        time.sleep(2)
        
        # 메인 컨테이너 대기
        main_container_selector = ".recruit_detail"
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, main_container_selector))
        )
        
        detail_container = driver.find_element(By.CSS_SELECTOR, main_container_selector)
        
        # 기본 정보 추출
        title = "정보 없음"
        category = "정보 없음"
        expire_date = "정보 없음"
        
        try:
            title = detail_container.find_element(By.CSS_SELECTOR, 'h3.tit_intro').text.strip()
        except NoSuchElementException:
            pass
            
        try:
            category = detail_container.find_element(By.CSS_SELECTOR, 'div.info_desc > span').text.strip()
        except NoSuchElementException:
            pass
            
        try:
            expire_date = detail_container.find_element(By.CSS_SELECTOR, 'div.item_card').text.strip()
        except NoSuchElementException:
            pass
        
        print(f"    제목: {title}")
        
        # 상세 정보 추출
        detail_text = ""
        desc_containers = detail_container.find_elements(By.CSS_SELECTOR, 'div.desc_cont')
        
        # 중요한 섹션만 필터링
        important_keywords = [
            "담당업무", "업무", "역할", "책임", "주요업무", "업무내용",
            "자격요건", "우대사항", "필수", "우대", "요구사항", "지원자격",
            "근무조건", "근무환경", "혜택", "복리후생", "근무형태",
            "채용절차", "전형절차", "지원", "절차"
        ]
        
        for container in desc_containers:
            try:
                section_title = container.find_element(By.CSS_SELECTOR, 'div.tit').text.strip()
                content = container.find_element(By.CSS_SELECTOR, 'div.cont').text.strip()
                
                if not section_title or not content:
                    continue
                
                # 중요한 섹션만 포함
                if any(keyword in section_title for keyword in important_keywords):
                    detail_text += f"## {section_title}\n{content}\n\n"
                    
            except NoSuchElementException:
                continue
        
        # 구조화된 파싱이 실패한 경우 전체 텍스트 추출
        if not detail_text.strip():
            print("    구조화된 파싱 실패, 전체 텍스트 추출")
            try:
                full_text = detail_container.text
                lines = [line.strip() for line in full_text.splitlines() if line.strip()]
                detail_text = '\n'.join(lines)
                
                # 길이 제한
                if len(detail_text) > 3000:
                    detail_text = detail_text[:3000] + "\n...(이하 생략)"
            except Exception as e:
                print(f"    전체 텍스트 추출 실패: {e}")
                return None, None, None, None
        
        if title != "정보 없음" and detail_text.strip():
            print(f"    ✅ 성공 - 상세내용 길이: {len(detail_text)}")
            return title, category, expire_date, detail_text.strip()
        else:
            return None, None, None, None
            
    except Exception as e:
        print(f"    ❌ 크롤링 실패: {e}")
        return None, None, None, None

# --- 3. 메인 실행 로직 ---
def main():
    conn = create_connection(db_config)
    if not conn:
        return
    cursor = conn.cursor()

    options = Options()
    options.add_argument("--headless")  # 크롬 창 숨김
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(f"user-agent={UserAgent().chrome}")
    
    driver = None
    processed_links = set()  # 중복 공고 방지
    
    try:
        print("카카오뱅크 채용 정보 크롤링을 시작합니다.")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        main_window = driver.current_window_handle
        
        # 카테고리별 크롤링
        types = ['Infra', 'Frontend', 'Server', 'AI', 'Engineering', 'Security', 'Data', 'Mobile']
        jobs_to_crawl = []
        
        for job_type in types:
            url = f'https://recruit.kakaobank.com/jobs?recruitClassName={job_type}'
            print(f"'{job_type}' 카테고리 확인 중...")
            driver.get(url)
            time.sleep(2)

            try:
                selector = 'ul.list_board > li'
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                items = driver.find_elements(By.CSS_SELECTOR, selector)

                for item in items:
                    try:
                        link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                        if link in processed_links:
                            continue
                        processed_links.add(link)

                        deadline_element = item.find_element(By.CSS_SELECTOR, '.tit_date')
                        deadline = deadline_element.text.strip()

                        title_full_text = item.find_element(By.CSS_SELECTOR, '.tit_board').text
                        title = title_full_text.replace(deadline, '').strip()
                        
                        category = item.find_element(By.CSS_SELECTOR, '.txt_desc').text.strip()
                        
                        jobs_to_crawl.append({
                            'url': link,
                            'title': title,
                            'category': category,
                            'deadline': deadline
                        })

                    except Exception as e:
                        print(f"  개별 공고 파싱 오류: {e}")
                        continue
            
            except TimeoutException:
                print(f"  -> '{job_type}' 카테고리에 진행중인 공고가 없습니다.")
                continue
        
        print(f"\n총 {len(jobs_to_crawl)}개의 채용 공고를 발견했습니다. 상세 정보 크롤링을 시작합니다.")
        
        success_count = 0
        for i, job in enumerate(jobs_to_crawl):
            print(f"\n({i+1}/{len(jobs_to_crawl)}) 공고 처리 중...")
            print(f"URL: {job['url']}")
            
            try:
                # 새 탭에서 상세 페이지 열기
                driver.switch_to.new_window('tab')
                driver.get(job['url'])
                
                detail_title, detail_category, detail_expire, detail_text = scrape_detail_page(driver)

                # 작업 후 새 탭 닫고 메인 탭으로 돌아오기
                driver.close()
                driver.switch_to.window(main_window)

                if detail_title and detail_text:
                    # 상세 페이지에서 추출한 정보 우선 사용, 없으면 목록에서 가져온 정보 사용
                    final_title = detail_title if detail_title != "정보 없음" else job['title']
                    final_category = detail_category if detail_category != "정보 없음" else job['category']
                    final_expire = detail_expire if detail_expire != "정보 없음" else job['deadline']
                    
                    final_data = (
                        final_title,
                        '카카오뱅크',
                        '경기도 성남시 분당구 분당내곡로 131, 11층(백현동, 판교테크원)',
                        final_category,
                        job['url'],
                        detail_text,
                        final_expire
                    )
                    insert_job_data(cursor, final_data)
                    success_count += 1
                else:
                    print(f"  - 상세 정보 수집 실패. 건너뜁니다.")
                    
            except Exception as e:
                print(f"  - 공고 처리 중 오류 발생: {e}")
                # 에러 발생 시에도 메인 탭으로 돌아가기
                try:
                    driver.switch_to.window(main_window)
                except:
                    pass
        
        print(f"\n크롤링 완료: {success_count}/{len(jobs_to_crawl)}개 성공")

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