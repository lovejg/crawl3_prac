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
    options.add_argument("--headless")  # 브라우저 창을 띄우지 않음
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={UserAgent().chrome}")

    driver = None
    job_details = {}  # 크롤링 결과를 담을 딕셔너리

    try:
        # WebDriver 자동 설정 및 실행
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        print("페이지 로딩 중...")

        # 주요 컨텐츠 영역이 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section.JobContent_JobContent__Qb6DR"))
        )

        try:
            more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.Button_Button__root__MS62F"))
            )
            
            # 버튼이 화면에 보이도록 스크롤
            driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
            time.sleep(1)
            
            # 클릭 시도
            try:
                more_button.click()
            except:
                # 일반 클릭이 안되면 JavaScript로 클릭
                driver.execute_script("arguments[0].click();", more_button)
            
        except Exception:
            print("'상세정보 더보기' 버튼을 찾지 못했거나 이미 내용이 모두 표시되어 있습니다.")

        # 버튼 클릭 후 새로운 콘텐츠가 로드될 때까지 충분히 대기
        time.sleep(3)
        
        # 추가 콘텐츠가 로드되었는지 확인
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.wds-h4ga6o"))
            )
            print("추가 콘텐츠 로드 완료")
        except:
            print("추가 콘텐츠 로드 대기 중 오류 발생")

        # 동적으로 로드된 전체 페이지 소스를 BeautifulSoup으로 파싱
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # --- 데이터 추출 시작 ---
        html = soup.select_one("section.JobContent_JobContent__Qb6DR")
        header = html.select_one("header.JobHeader_JobHeader__TZkW3")
        main = html.select_one("section.JobContent_descriptionWrapper__RMlfm")
        
        # 기본 정보 추출
        job_details['공고 제목'] = header.select_one("h1.wds-58fmok").text.strip()
        job_details['회사 이름'] = header.select_one("a.JobHeader_JobHeader__Tools__Company__Link__NoBQI").text.strip()
        
        company_info = header.select("span.JobHeader_JobHeader__Tools__Company__Info__b9P4Y")
        job_details['위치'] = company_info[0].text.strip() if len(company_info) > 0 else '정보 없음'
        job_details['경력'] = company_info[1].text.strip() if len(company_info) > 1 else '정보 없음'
        
        job_details['마감일'] = main.select_one("span.wds-1u1yyy").text.strip()
        job_details['정확한 회사 위치'] = main.select_one("span.wds-1td1qmv").text.strip()

        # 상세 정보 (주요업무, 자격요건, 우대사항 등) 추출
        details = main.select("span.wds-h4ga6o")
        job_details['포지션 상세'] = details[0].text.strip() if len(details) > 0 else '정보 없음'
        job_details['주요업무'] = details[1].text.strip() if len(details) > 1 else '정보 없음'
        job_details['자격요건'] = details[2].text.strip() if len(details) > 2 else '정보 없음'
        job_details['우대사항'] = details[3].text.strip() if len(details) > 3 else '정보 없음'
        job_details['혜택 및 복지'] = details[4].text.strip() if len(details) > 4 else '정보 없음'
        job_details['채용 전형'] = details[5].text.strip() if len(details) > 5 else '정보 없음'
        
        try:
            # 태그가 포함된 <article> 영역을 선택
            tags_article = soup.select_one("article.CompanyTags_CompanyTags__OpNto")
            if tags_article:
                # 각 태그 버튼에서 'data-tag-name' 속성 값을 추출
                tag_buttons = tags_article.select("button[data-attribute-id='company__tag__click']")
                tags_list = [button.get('data-tag-name') for button in tag_buttons if button.get('data-tag-name')]
                job_details['회사 태그'] = ', '.join(tags_list) # 리스트를 하나의 문자열로 합침
            else:
                job_details['회사 태그'] = '정보 없음'
        except Exception as e:
            print(f"태그 정보 추출 오류: {e}")
            job_details['회사 태그'] = '정보 없음'
        
        print("모든 정보 추출 완료.")
        return job_details

    except Exception as e:
        print(f"크롤링 실패: {e}")
        return None

    finally:
        # 드라이버가 실행된 경우, 반드시 종료
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