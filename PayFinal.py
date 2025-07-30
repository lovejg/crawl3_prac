import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from selenium.common.exceptions import TimeoutException
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
        (title, company_name, company_location, is_regular, require_career, detail_url, detail)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title=VALUES(title), is_regular=VALUES(is_regular),
            require_career=VALUES(require_career), detail=VALUES(detail);
    """
    try:
        cursor.execute(query, data)
        print(f"  ✅ [DB 저장/업데이트 완료] {data[0]}")
    except Error as e:
        print(f"  ❌ [DB 저장 실패] {data[0]} - {e}")

# --- 2. 상세 페이지 크롤링 함수 (최적화) ---
def scrape_detail_page(driver):
    """
    현재 드라이버가 위치한 페이지의 상세 정보를 크롤링.
    빠른 처리를 위해 단일 시도로 최적화
    """
    try:
        # 핵심 요소 로딩 대기 (시간 단축)
        time.sleep(2)
        
        # 제목 추출 - 가장 확실한 셀렉터부터 시도
        title = None
        try:
            title_element = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.eLNvYc"))
            )
            title = title_element.text.strip()
        except:
            # 백업 방법
            try:
                title_element = driver.find_element(By.TAG_NAME, "h1")
                title = title_element.text.strip()
            except:
                pass
        
        if not title:
            return None, None
        
        print(f"    제목: {title}")
        
        # 상세 정보 파싱 - 효율적인 방법 우선 시도
        detail_text = ""
        
        try:
            # 메인 콘텐츠 영역 찾기
            editor_element = driver.find_element(By.CSS_SELECTOR, "div.ql-editor")
            all_children = editor_element.find_elements(By.XPATH, "./*")
            
            if all_children:
                print(f"    구조화된 콘텐츠 파싱 중... (요소 수: {len(all_children)})")
                
                job_details_dict = {}
                current_section_title = None
                current_section_content = []
                
                # 중요한 섹션만 필터링
                important_keywords = [
                    "담당업무", "업무", "역할", "책임", "주요업무",
                    "자격요건", "우대사항", "필수", "우대", "요구사항",
                    "근무조건", "근무환경", "혜택", "복리후생",
                    "채용절차", "전형절차", "지원"
                ]

                for element in all_children:
                    if element.tag_name in ['h1', 'h2', 'h3', 'h4']:
                        # 이전 섹션 저장 (중요한 섹션만)
                        if current_section_title and current_section_content:
                            if any(keyword in current_section_title for keyword in important_keywords):
                                job_details_dict[current_section_title] = "\n".join(current_section_content).strip()
                        
                        # 새 섹션 시작
                        current_section_title = element.text.strip().replace("⎥", "").strip()
                        current_section_content = []
                    else:
                        text = element.text.strip()
                        if text and len(text) > 3:  # 너무 짧은 텍스트 제외
                            current_section_content.append(text)
                
                # 마지막 섹션 저장
                if current_section_title and current_section_content:
                    if any(keyword in current_section_title for keyword in important_keywords):
                        job_details_dict[current_section_title] = "\n".join(current_section_content).strip()

                # 구조화된 텍스트 조합
                if job_details_dict:
                    for key, value in job_details_dict.items():
                        if key and value:
                            detail_text += f"## {key}\n{value}\n\n"
                    print(f"    구조화된 콘텐츠 추출 완료 (섹션 수: {len(job_details_dict)})")
                else:
                    print("    중요한 섹션을 찾지 못함")
        
        except Exception as e:
            print(f"    구조화 파싱 실패: {e}")
        
        # 구조화된 파싱이 실패했거나 내용이 부족한 경우에만 전체 텍스트 추출
        if not detail_text.strip():
            print("    전체 페이지 텍스트 추출로 전환")
            try:
                # 핵심 콘텐츠 영역만 추출
                main_content = driver.find_element(By.CSS_SELECTOR, "div.ql-editor")
                soup = BeautifulSoup(main_content.get_attribute('innerHTML'), 'html.parser')
                
                # 불필요한 요소 제거
                for unwanted in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    unwanted.decompose()
                
                # 텍스트 정리
                text = soup.get_text()
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                detail_text = '\n'.join(lines)
                
                # 길이 제한 (필요한 부분만)
                if len(detail_text) > 3000:
                    detail_text = detail_text[:3000] + "\n...(이하 생략)"
                    
            except Exception as e:
                print(f"    전체 텍스트 추출도 실패: {e}")
                return None, None
        
        if title and detail_text.strip():
            print(f"    ✅ 성공 - 상세내용 길이: {len(detail_text)}")
            return title, detail_text.strip()
        else:
            return None, None
            
    except Exception as e:
        print(f"    ❌ 크롤링 실패: {e}")
        return None, None

# --- 3. 메인 실행 로직 ---
def main():
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
        print("카카오페이 채용 정보 크롤링을 시작합니다.")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        url = 'https://kakaopay.career.greetinghr.com/ko/main?occupations=기술'
        driver.get(url)
        main_window = driver.current_window_handle
        
        print("메인 페이지 로딩 대기 중...")
        time.sleep(3)  # 대기시간 단축

        # 스크롤 다운 (최적화)
        print("페이지 끝까지 스크롤 중...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 5  # 횟수 줄임
        
        while scroll_attempts < max_scroll_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)  # 대기시간 단축
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        items = soup.select("ul.ffGmZN > a")
        
        if not items:
            print("채용 공고 목록을 찾지 못했습니다. 페이지 구조를 확인해주세요.")
            return

        jobs_to_crawl = []
        for item in items:
            try:
                link = f"https://kakaopay.career.greetinghr.com{item['href']}"
                info_items = item.select('.gAEjfw span')
                career = "정보 없음"
                work_type = "정보 없음"
                for info in info_items:
                    text = info.get_text(strip=True)
                    if '년' in text or '신입' in text or '무관' in text:
                        career = text
                    elif '정규' in text or '계약' in text:
                        work_type = text
                jobs_to_crawl.append({'url': link, 'career': career, 'work_type': work_type})
            except Exception as e:
                print(f"공고 정보 파싱 중 오류: {e}")
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
                
                detail_title, detail_text = scrape_detail_page(driver)

                # 작업 후 새 탭 닫고 메인 탭으로 돌아오기
                driver.close()
                driver.switch_to.window(main_window)

                if detail_title and detail_text:
                    final_data = (
                        detail_title, '카카오페이', '경기도 성남시 분당구 판교역로 152 (백현동) 알파돔타워 12층',
                        job['work_type'], job['career'], job['url'], detail_text
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