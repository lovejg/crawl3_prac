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

# --- DB 설정 및 연결 함수 ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'recruit',
    'port': 3307
}

def create_connection(config):
    """DB 연결 생성"""
    try:
        connection = mysql.connector.connect(**config)
        print("DB 연결 성공")
        return connection
    except Error as e:
        print(f"DB 연결 실패: {e}")
        return None

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
        print(f"✅ DB 저장 완료: {data[0]}")
    except Error as e:
        print(f"❌ DB 저장 실패: {data[0]} - {e}")

def scrape_detail_page(driver, url):
    """상세 페이지 크롤링"""
    try:
        driver.get(url)
        time.sleep(3)
        
        # 제목 추출
        title = None
        title_selectors = [
            "span.eLNvYc",
            "h1",
            "h2"
        ]
        
        for selector in title_selectors:
            try:
                title_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                title = title_element.text.strip()
                if title:
                    break
            except:
                continue
        
        if not title:
            return None, None
        
        # 상세 정보 추출
        detail_text = ""
        
        # 방법 1: ql-editor 영역 JavaScript 파싱
        try:
            editor_element = driver.find_element(By.CSS_SELECTOR, "div.ql-editor")
            
            script = """
            var element = arguments[0];
            var text = '';
            var walker = document.createTreeWalker(
                element,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            var node;
            while(node = walker.nextNode()) {
                if(node.textContent.trim()) {
                    text += node.textContent.trim() + '\\n';
                }
            }
            return text;
            """
            detail_text = driver.execute_script(script, editor_element)
            
            if detail_text.strip():
                detail_text = detail_text.strip()
            else:
                raise Exception("빈 텍스트")
                
        except:
            # 방법 2: 구조화된 파싱
            try:
                editor_element = driver.find_element(By.CSS_SELECTOR, "div.ql-editor")
                all_children = editor_element.find_elements(By.XPATH, "./*")
                
                sections = {}
                current_title = None
                current_content = []
                
                for element in all_children:
                    if element.tag_name.lower() in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        if current_title and current_content:
                            sections[current_title] = '\n'.join(current_content)
                        
                        current_title = element.text.strip().replace("⎥", "").strip()
                        current_content = []
                    else:
                        text = element.text.strip()
                        if text:
                            current_content.append(text)
                
                if current_title and current_content:
                    sections[current_title] = '\n'.join(current_content)
                
                if sections:
                    for title, content in sections.items():
                        if title and content:
                            detail_text += f"## {title}\n{content}\n\n"
                else:
                    raise Exception("섹션 없음")
            
            except:
                # 방법 3: 전체 페이지 텍스트 추출
                try:
                    container = driver.find_element(By.CSS_SELECTOR, "div.ql-editor")
                    soup = BeautifulSoup(container.get_attribute('innerHTML'), 'html.parser')
                    
                    for unwanted in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        unwanted.decompose()
                    
                    text = soup.get_text(separator='\n', strip=True)
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    detail_text = '\n'.join(lines)
                    
                    if not detail_text or len(detail_text) < 100:
                        raise Exception("텍스트 없음")
                        
                except:
                    return None, None
        
        # 텍스트 정리
        if detail_text:
            detail_text = '\n'.join([line for line in detail_text.split('\n') if line.strip()])
            
            if len(detail_text) > 5000:
                detail_text = detail_text[:5000] + "\n...(내용이 길어 일부 생략됨)"
            
            return title, detail_text
        else:
            return None, None
            
    except Exception as e:
        print(f"❌ 크롤링 실패: {e}")
        return None, None

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
    options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        print("카카오페이 채용 정보 크롤링 시작")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        url = 'https://kakaopay.career.greetinghr.com/ko/main?occupations=기술'
        driver.get(url)
        
        print("메인 페이지 로딩 중...")
        time.sleep(5)

        # 스크롤 다운
        print("전체 공고 로딩 중...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(8):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        items = soup.select("ul.ffGmZN > a")
        
        if not items:
            print("채용 공고를 찾을 수 없습니다.")
            return

        jobs_to_crawl = []
        for item in items:
            try:
                href = item.get('href', '')
                if not href:
                    continue
                    
                link = f"https://kakaopay.career.greetinghr.com{href}"
                
                career = "정보 없음"
                work_type = "정보 없음"
                
                try:
                    info_items = item.select('.gAEjfw span')
                    for info in info_items:
                        text = info.get_text(strip=True)
                        if '년' in text or '신입' in text or '무관' in text:
                            career = text
                        elif '정규' in text or '계약' in text:
                            work_type = text
                except:
                    pass
                
                jobs_to_crawl.append({
                    'url': link, 
                    'career': career, 
                    'work_type': work_type
                })
                
            except Exception as e:
                continue
        
        print(f"총 {len(jobs_to_crawl)}개 공고 발견")
        print("상세 정보 수집 중...")
        
        success_count = 0
        for i, job in enumerate(jobs_to_crawl):
            print(f"({i+1}/{len(jobs_to_crawl)}) 처리 중...")
            
            try:
                detail_title, detail_text = scrape_detail_page(driver, job['url'])

                if detail_title and detail_text:
                    final_data = (
                        detail_title, 
                        '카카오페이', 
                        '경기도 성남시 분당구 판교역로 152 (백현동) 알파돔타워 12층',
                        job['work_type'], 
                        job['career'], 
                        job['url'], 
                        detail_text
                    )
                    insert_job_data(cursor, final_data)
                    success_count += 1
                else:
                    print(f"❌ 상세 정보 수집 실패")
                    
            except Exception as e:
                print(f"❌ 처리 실패: {e}")
        
        print(f"\n크롤링 완료: {success_count}/{len(jobs_to_crawl)}개 성공")

    except Exception as e:
        print(f"전체 크롤링 오류: {e}")
    finally:
        if driver:
            driver.quit()
        if conn and conn.is_connected():
            conn.commit()
            cursor.close()
            conn.close()
            print("작업 완료")

if __name__ == "__main__":
    main()