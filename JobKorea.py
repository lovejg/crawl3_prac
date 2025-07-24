import requests
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error

db_config = {
    'host': 'localhost', # DB 서버 주소 (e.g., '127.0.0.1')
    'user': 'root',  # DB 사용자 이름
    'password': '1234', # DB 비밀번호
    'database': 'recruit', # 사용할 데이터베이스 이름
    'port': 3307
}

# DB 연결 생성 및 커넥션 객체 반환
def create_connection(config):
    connection = None
    try:
        connection = mysql.connector.connect(**config)
        print("🎉 MySQL DB에 성공적으로 연결되었습니다.")
    except Error as e:
        print(f"DB 연결 중 오류 발생: {e}")
    return connection

# 크롤링한 데이터를 DB에 삽입
def insert_job_data(cursor, data):
    query = """
        INSERT INTO recruitment
        (company_name, title, detail_url, require_career, require_education, is_regular, company_location, expire_date, advantage) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, data)
        print(f"✅ 데이터 삽입 완료: {data[1]}")
    except Error as e:
        print(f"데이터 삽입 중 오류 발생: {e}")

keyword = input("키워드 입력: ")
pageNum = input("몇 페이지까지 출력할지(크롤링할지): ")
print(f"키워드 '{keyword}'로 채용정보 크롤링을 시작")

conn = create_connection(db_config)
if conn is None:
    exit() # DB 연결 실패 시 프로그램 종료
    
cursor = conn.cursor()

for n in range(1, int(pageNum)+1):
    try:
        soup = requests.get('https://www.jobkorea.co.kr/Search/?stext={}&tabType=recruit&Page_No={}'.format(keyword, str(n)),
                                                                                                            headers={'User-Agent': 'Mozilla/5.0'})
        html = BeautifulSoup(soup.text, 'html.parser').select_one(".Tabs_content__1cw1bssi") # 상위 class 입력
        
        jobs = html.select('.h7nnv10') # 각 요소별 클래스 입력
        
        for job in jobs:
            company = job.select_one('span.Typography_variant_size16__344nw26').text.strip() # 회사 이름
            
            title = job.select_one('a.h7nnv12').text.strip() # 공고 제목
            
            url = job.find('a')['href'] # 상세페이지 url
            
            # 경력, 학력 등 각종 정보 뽑는 소스인데, 원래 간단했는데 이번에 뭔 ㅈ같은게 좀 추가돼서 처리하느냐고 ㅈㄴ 복잡해짐(경력이 [0]이 아니고 딴거인 경우가 생김)
            # 그리고 양식 정확히 안 맞추고 정보가 한 두개씩 빠져있는 케이스도 있어서 그것도 처리해줘야 됨(일단은 해당 공고는 무시하고 넘기는걸로 처리함)
            items = job.select('span.Typography_color_gray800__344nw2l')
            start_index = -1
            for i, item in enumerate(items):
                if item.text.strip().startswith(('경력', '신입')):
                    start_index = i
                    break

            if start_index != -1:
                info_list = items[start_index:]
                
            if len(info_list) < 5:
                continue # 정보가 하나라도 부족하면 일단 해당 공고 패스
            
            career = info_list[0].text.strip() # 경력
            print(career)
            edu_career = info_list[1].text.strip() # 학력
            print(edu_career)
            regular = info_list[2].text.strip() # 정규직 여부
            print(regular)
            location = info_list[3].text.strip() # 위치
            print(location)
            deadline = info_list[4].text.strip() # 마감
            print(deadline)
            
            benefit_tags = job.select('span.Typography_variant_size13__344nw28') # 장점(태그) => 없는 공고들도 있음(빈 배열이면 없는거임)
            benefit = ', '.join([tag.text.strip() for tag in benefit_tags]) if benefit_tags else ''
            
            job_data = (
                    company, title, url, career, edu_career, 
                    regular, location, deadline, benefit
                )
            
            insert_job_data(cursor, job_data)
                
    except Exception:
        pass
    
# 최종 저장
conn.commit()  # 모든 변경사항을 DB에 최종 반영
cursor.close()
conn.close()
print("\n 모든 크롤링 및 DB 저장이 완료되었습니다. MySQL 연결을 종료합니다.")