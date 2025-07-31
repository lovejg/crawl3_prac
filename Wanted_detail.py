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

def crawl_job_details(url):
    """
    주어진 URL의 채용 공고 상세 정보를 크롤링하는 함수.
    '상세정보 더보기'를 클릭하여 숨겨진 정보까지 모두 가져옵니다.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={UserAgent().chrome}")

    driver = None
    job_details = {}

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)

        # 주요 컨텐츠 영역이 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section.JobContent_JobContent__Qb6DR"))
        )

        # JavaScript로 더보기 버튼 찾고 클릭
        try:
            buttons = driver.execute_script("""
                return Array.from(document.querySelectorAll('button')).filter(
                    btn => btn.textContent.includes('더보기') || btn.textContent.includes('상세정보')
                );
            """)
            if buttons:
                driver.execute_script("arguments[0].click();", buttons[0])
                time.sleep(2)
        except:
            pass

        # 페이지 소스를 BeautifulSoup으로 파싱
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # 데이터 추출
        html = soup.select_one("section.JobContent_JobContent__Qb6DR")
        header = html.select_one("header.JobHeader_JobHeader__TZkW3")
        main = html.select_one("section.JobContent_descriptionWrapper__RMlfm")

        # 기본 정보 추출
        job_details['공고 제목'] = header.select_one("h1.wds-58fmok").text.strip()
        job_details['회사 이름'] = header.select_one("a.JobHeader_JobHeader__Tools__Company__Link__NoBQI").text.strip()
        
        company_info = header.select("span.JobHeader_JobHeader__Tools__Company__Info__b9P4Y")
        job_details['위치'] = company_info[0].text.strip()
        job_details['경력'] = company_info[1].text.strip()
        
        job_details['마감일'] = main.select_one("span.wds-1u1yyy").text.strip()
        job_details['정확한 회사 위치'] = main.select_one("span.wds-1td1qmv").text.strip()

        # 상세 정보 추출 (대안 선택자 사용)
        details = main.select("section[class*='JobContent'] span[class*='wds-']")
        
        detail_labels = ['포지션 상세', '주요업무', '자격요건', '우대사항', '혜택 및 복지', '채용 전형']
        for i, label in enumerate(detail_labels):
            job_details[label] = details[i].text.strip() if i < len(details) else '정보 없음'

        # 회사 태그 추출
        try:
            tags_article = soup.select_one("article.CompanyTags_CompanyTags__OpNto")
            if tags_article:
                tag_buttons = tags_article.select("button[data-attribute-id='company__tag__click']")
                tags_list = [button.get('data-tag-name') for button in tag_buttons if button.get('data-tag-name')]
                job_details['회사 태그'] = ', '.join(tags_list)
            else:
                job_details['회사 태그'] = '정보 없음'
        except:
            job_details['회사 태그'] = '정보 없음'

        return job_details

    except Exception as e:
        print(f"크롤링 실패: {e}")
        return None

    finally:
        if driver:
            driver.quit()

def main():
    keyURL = input("URL 입력: ").strip()
    print("크롤링을 시작합니다...\n")

    job_data = crawl_job_details(keyURL)
    nowDate = datetime.datetime.now().strftime('%Y-%m-%d')

    print("\n" + "="*15 + " 크롤링 결과 " + "="*15)
    print(f"(조회 날짜: {nowDate})")
    
    if job_data:
        for key, value in job_data.items():
            print(f"\n## {key}")
            print(value)
    else:
        print("\n크롤링된 데이터가 없습니다.")

if __name__ == "__main__":
    main()