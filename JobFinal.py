import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
import mysql.connector
from mysql.connector import Error
import time

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'recruit',
    'port': 3307,
}

def create_connection(config):
    connection = None
    try:
        connection = mysql.connector.connect(**config)
        print("MySQL DB에 성공적으로 연결되었습니다.")
    except Error as e:
        print(f"DB 연결 중 오류 발생: {e}")
    return connection

def crawl_detail_page(detail_url):
    try:
        time.sleep(1)
        soup = requests.get(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
        html = BeautifulSoup(soup.text, 'html.parser').select_one("section#container")
        
        if not html:
            return {}
        
        main_info = html.select_one('section.secReadSummary')
        if not main_info:
            return {}
        
        detail_data = {}
        
        dl_tag1 = main_info.select('dl.tbList')
        if dl_tag1:
            dt_tags = dl_tag1[0].find_all('dt')
            skills = ""
            for dt in dt_tags:
                if dt.text.strip() == "스킬":
                    dd = dt.find_next_sibling('dd')
                    if dd:
                        skills = dd.get_text(strip=True)
                    break
            detail_data['skills'] = skills
        
        return detail_data
        
    except Exception as e:
        print(f"상세페이지 크롤링 중 오류 발생: {e}")
        return {}

def insert_job_data(cursor, data):
    query = """
        INSERT INTO recruitment
        (title, company_name, company_location, is_regular, require_career, 
         require_education, advantage, detail_url, expire_date) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, data)
        print(f"데이터 삽입 완료: {data[0]}")
    except Error as e:
        print(f"데이터 삽입 중 오류 발생: {e}")

keyword = input("키워드 입력: ")
pageNum = input("몇 페이지까지 출력할지(크롤링할지): ")
print(f"키워드 '{keyword}'로 채용정보 크롤링을 시작")

conn = create_connection(db_config)
if conn is None:
    exit()

cursor = conn.cursor()

total_jobs = 0

for n in range(1, int(pageNum)+1):
    try:
        print(f"{n}페이지 크롤링 중...")
        soup = requests.get('https://www.jobkorea.co.kr/Search/?stext={}&Page_No={}'.format(keyword, str(n)),
                            headers={'User-Agent': 'Mozilla/5.0'})
        html = BeautifulSoup(soup.text, 'html.parser').select_one(".Tabs_content__1cw1bssl")
        
        if not html:
            print(f"{n}페이지: 데이터를 찾을 수 없습니다.")
            continue
        
        jobs = html.select('.h7nnv10')
        
        for job in jobs:
            try:
                company = job.select_one('span.Typography_variant_size16__344nw26').text.strip()
                title = job.select_one('a.sn28bt0').text.strip()
                url = job.find('a')['href']
                
                if not url.startswith('http'):
                    url = 'https://www.jobkorea.co.kr' + url
                
                items = job.select('span.Typography_color_gray700__344nw2m')
                start_index = -1
                for i, item in enumerate(items):
                    if item.text.strip().startswith(('경력', '신입')):
                        start_index = i
                        break
                
                if start_index != -1:
                    info_list = items[start_index:]
                else:
                    continue
                
                if len(info_list) < 5:
                    continue
                
                career = info_list[0].text.strip()
                edu_career = info_list[1].text.strip()
                regular = info_list[2].text.strip()
                location = info_list[3].text.strip()
                deadline = info_list[4].text.strip()
                
                benefit_tags = job.select('span.Typography_variant_size13__344nw29')
                benefit = ', '.join([tag.text.strip() for tag in benefit_tags]) if benefit_tags else ''
                
                job_data = (
                    title, company, location, regular, career, 
                    edu_career, benefit, url, deadline
                )
                
                insert_job_data(cursor, job_data)
                total_jobs += 1
                
            except Exception as e:
                print(f"개별 공고 처리 중 오류: {e}")
                continue
                
    except Exception as e:
        print(f"{n}페이지 크롤링 중 오류 발생: {e}")
        continue

conn.commit()
cursor.close()
conn.close()

print(f"모든 크롤링 및 DB 저장이 완료되었습니다!")
print(f"총 {total_jobs}개의 채용공고가 처리되었습니다.")