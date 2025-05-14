import requests
from bs4 import BeautifulSoup
import datetime

keyword = input("키워드 입력: ")
pageNum = input("몇 페이지까지 출력할지(크롤링할지): ")
print(f"키워드 '{keyword}'로 채용정보 크롤링을 시작")

for n in range(1, int(pageNum)+1):
    try:
        soup = requests.get('https://www.jobkorea.co.kr/Search/?stext={}&tabType=recruit&Page_No={}'.format(keyword, str(n)),
                                                                                                            headers={'User-Agent': 'Mozilla/5.0'})
        html = BeautifulSoup(soup.text, 'html.parser').select_one("article.list")
        # print(html) # 테스트
        
        jobs = html.select('article.list-item')
        # print(len(jobs)) # 테스트 => 페이지당 20개씩 있음
        
        nowDate = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"현재 날짜: {nowDate}")
        
        for job in jobs:
            company = job.select_one('a.corp-name-link').text.strip() # 회사 이름
            print(f"회사 이름: {company}")
            
            title = job.select_one('a.information-title-link').text.strip() # 공고 제목
            print(f"공고 제목: {title}")
            
            url = 'https://www.jobkorea.co.kr/' + job.find('a')['href'] # 상세페이지 url
            print(f"상세페이지 URL: {url}")
            
            items = job.select('li.chip-information-item')
            career = items[0].text.strip() # 경력
            print(f"경력: {career}")
            edu_career = items[1].text.strip() # 학력
            print(f"학력: {edu_career}")
            regular = items[2].text.strip() # 정규직
            print(f"정규직 여부: {regular}")
            location = items[3].text.strip() # 위치
            print(f"위치: {location}")
            deadline = items[4].text.strip() # 마감까지 남은 시간
            print(f"마감까지 {deadline}")
            
            benefit = [item.text.strip() for item in job.select('li.chip-benefit-item')] # 장점(태그) => 없는 공고들도 있음(빈 배열이면 없는거임)
            print("장점:")
            for item in benefit:
                print(f"- {item}")
            
            # 지원방식 => 얘는 즉시지원, 홈페이지 지원으로 나뉘는데, 둘이 클래스가 달라서 이렇게 조건문으로 처리해줌
            apply_button = job.select_one('button.button-apply-now')
            if apply_button is None:
                apply_button = job.select_one('button.button-apply-homepage')
            apply = apply_button.text.strip() if apply_button else "지원 방식 정보 없음"
            print(f"지원 방식: {apply}")
            print('\n')
                
    except Exception:
        pass