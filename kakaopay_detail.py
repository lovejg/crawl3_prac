import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from selenium.common.exceptions import TimeoutException

def crawl_job_details(url):
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
        print("상세 페이지 로딩 중...")

        # ⭐️ 1. 수정된 부분: 제목이 나타날 때까지 명시적으로 대기
        title_selector = "span.eLNvYc"
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, title_selector))
            )
            print("콘텐츠 로드 완료.")
            job_details['공고 제목'] = driver.find_element(By.CSS_SELECTOR, title_selector).text.strip()
        except TimeoutException:
            print("공고 제목을 찾을 수 없습니다.")
            job_details['공고 제목'] = "정보 없음"
        except Exception as e:
            print(f"제목 추출 중 오류: {e}")
            job_details['공고 제목'] = "정보 없음"


        # 아래 전체가 상세 정보(detail)
        try:
            main_content_selector = "div.ql-editor"
            editor_element = driver.find_element(By.CSS_SELECTOR, main_content_selector)
            all_children = editor_element.find_elements(By.XPATH, "./*")
            
            current_section_title = None
            current_section_content = ""

            for element in all_children:
                if element.tag_name == 'h3':
                    # 이전 섹션 내용을 저장
                    if current_section_title and current_section_content.strip():
                        # ⭐️ 2. 수정된 부분: 핵심 키워드로 제외할 섹션인지 확인
                        if "크루들의 이야기" not in current_section_title:
                            job_details[current_section_title] = current_section_content.strip()
                    
                    # 새 섹션 시작
                    current_section_title = element.text.strip().replace("⎥", "").strip()
                    current_section_content = ""
                else:
                    current_section_content += element.text + "\n"
            
            # 마지막 섹션 내용 저장
            if current_section_title and current_section_content.strip():
                if "크루들의 이야기" not in current_section_title:
                    job_details[current_section_title] = current_section_content.strip()

        except Exception as e:
            print(f"섹션별 상세 내용 분리에 실패했습니다: {e}")

        print("모든 정보 추출 완료.")
        return job_details

    except Exception as e:
        print(f"크롤링 실패: {e}")
        return None

    finally:
        if driver:
            driver.quit()

def main():
    keyURL = input("상세 정보를 가져올 URL을 입력하세요: ").strip()
    print("크롤링을 시작합니다...\n")

    job_data = crawl_job_details(keyURL)
    
    nowDate = datetime.datetime.now().strftime('%Y-%m-%d')

    print("\n" + "="*15 + " 크롤링 결과 " + "="*15)
    print(f"(조회 날짜: {nowDate})")
    
    if job_data:
        for key, value in job_data.items():
            if key and value.strip(): # key와 value가 모두 내용이 있는 경우만 출력
                print(f"\n## {key}")
                print("-" * (len(key) + 3))
                print(value)
    else:
        print("\n크롤링된 데이터가 없습니다.")


if __name__ == "__main__":
    main()