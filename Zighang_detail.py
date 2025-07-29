import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
import datetime

keyURL = input("URL 입력: ")
print("크롤링 시작")

try:
    soup = requests.get(keyURL, headers={'User-Agent': 'Mozilla/5.0'})
    html = BeautifulSoup(soup.text, 'html.parser').select_one("main > div:nth-child(3) > div > div") # 클래스 이름이 너무 겹쳐서(이름에 특징이 없음) 이렇게 할 수 밖에 없음..
    # print(html) # 테스트
    
    header = html.select_one("div:nth-child(1)")
    # print(header) # 테스트
    # main = html.select_one("div:nth-child(4)") # 얘는 메인 내용이 사진으로 돼 있어서 크롤링 하는게 의미가 없을듯...? 어쩌지
    # print(main) # 테스트
    
    nowDate = datetime.datetime.now().strftime('%Y-%m-%d') 
    print(f"현재 날짜: {nowDate}")
    
    title = header.select_one("h1.break-all").text.strip() # 공고 제목
    print(f"공고 제목: {title}")
    
    company = header.select_one("span.w-fit").text.strip() # 회사 이름
    print(f"회사 이름: {company}")
    
    deadline = header.select_one("div.font-semibold").text.strip() # 데드라인
    print(f"데드라인: {deadline}")
    
    upload_date = header.select_one("div.font-normal").text.strip() # 게시 날짜
    print(f"게시날짜: {upload_date}")
    
    career = header.select("div.text-black")[0].text.strip() # 경력
    print(f"경력: {career}")
    
    location = header.select("div.text-black")[1].text.strip() # 근무지역
    print(f"근무지역: {location}")
    
    edu_career = header.select("div.text-black")[2].text.strip() # 학력
    print(f"학력: {edu_career}")
    
    work_type = header.select("div.text-black")[3].text.strip() # 근무형태
    print(f"근무형태: {work_type}")
    
    stack = header.select("div.text-black")[4].text.strip() # 직군(기술 스택)
    print(f"직군: {stack}")
    
            
except Exception:
    pass