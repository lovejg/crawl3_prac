import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
import datetime

keyURL = input("URL 입력: ")
print("크롤링 시작")

try:
    soup = requests.get(keyURL, headers={'User-Agent': 'Mozilla/5.0'})
    html = BeautifulSoup(soup.text, 'html.parser').select_one("section.JobContent_JobContent__Qb6DR")
    # print(html) # 테스트
    
    header = html.select_one("header.JobHeader_JobHeader__TZkW3")
    # print(header) # 테스트
    main = html.select_one("section.JobContent_descriptionWrapper__RMlfm")
    # print(main) # 테스트
    
    nowDate = datetime.datetime.now().strftime('%Y-%m-%d') 
    print(f"현재 날짜: {nowDate}")
    
    title = header.select_one("h1.wds-58fmok").text.strip()
    print(f"공고 제목: {title}")
    
    company = header.select_one("a.JobHeader_JobHeader__Tools__Company__Link__NoBQI").text.strip() # 회사 이름
    print(f"회사 이름: {company}")
    
    location = header.select("span.JobHeader_JobHeader__Tools__Company__Info__b9P4Y")[0].text.strip() # 위치
    print(f"위치: {location}")
    
    career = header.select("span.JobHeader_JobHeader__Tools__Company__Info__b9P4Y")[1].text.strip() # 위치
    print(f"경력: {career}")
    
    deadline = main.select_one("span.wds-1u1yyy").text.strip() # 마감일
    print(f"마감일: {deadline}")
    
    detail_location = main.select_one("span.wds-1td1qmv").text.strip() # 정확한 회사 위치
    print(f"정확한 회사 위치: {detail_location}")
    print('\n')
    
    position_detail = main.select("span.wds-h4ga6o")[0].text.strip()
    print(f"포지션 상세: {position_detail}")
    print('\n')
    
    main_work = main.select("span.wds-h4ga6o")[1].text.strip()
    print(f"주요업무: {main_work}")
    print('\n')
    
    requirement = main.select("span.wds-h4ga6o")[2].text.strip()
    print(f"자격요건: {requirement}")
            
except Exception:
    pass