import requests
from bs4 import BeautifulSoup
import datetime

keyword = input("키워드 입력: ")
pageNum = input("몇 페이지까지 출력할지(크롤링할지): ")
print(f"키워드 '{keyword}'로 채용정보 크롤링을 시작")

for n in range(1, int(pageNum)+1):
    try:
        soup = requests.get('https://www.saramin.co.kr/zf_user/search/recruit?search_area=main&search_done=y&search_optional_item=n&searchType=search&searchword={}&recruitPage={}'.format(keyword, str(n)),
                                                                                                            headers={'User-Agent': 'Mozilla/5.0'})
        html = BeautifulSoup(soup.text, 'html.parser').select_one("div.content")
        # print(html) # 테스트
        
        jobs = html.select('div.item_recruit')
        # print(len(jobs)) # 테스트 => 페이지당 40개씩 있음
        
        nowDate = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"현재 날짜: {nowDate}")
        
        for job in jobs:
            company = job.select_one('a.track_event').text.strip() # 회사 이름
            print(f"회사 이름: {company}")
            
            title = job.select_one('a.data_layer').text.strip() # 공고 제목
            print(f"공고 제목: {title}")
            
            # 공고 상세 페이지 URL => 패턴/속성 필터링 필요
            for a in job.find_all('a'):
                href = a.get('href')
                if href and href.startswith('/zf_user/jobs/relay/view?view_type='):
                    url = 'https://www.saramin.co.kr' + href
                    print(f"상세 페이지 URL: {url}")
                    break  # 원하는 링크를 찾았으면 반복 중단
            
            # 회사정보 페이지 URL => 패턴/속성 필터링 필요
            for a in job.find_all('a'):
                href = a.get('href')
                if href and href.startswith('/zf_user/company-info/view?csn='):
                    url = 'https://www.saramin.co.kr' + href
                    print(f"회사 정보 페이지 URL: {url}")
                    break  # 원하는 링크를 찾았으면 반복 중단
            
            deadline = job.select_one('span.date').text.strip() # 마감 날짜
            print(f"마감날짜: {deadline}")
            
            # 지원방식 => 얘는 즉시지원, 홈페이지 지원으로 나뉘는데, 둘이 클래스가 달라서 이렇게 조건문으로 처리해줌
            apply_button = job.select_one('button.sri_btn_xs')
            if apply_button is None:
                apply_button = job.select_one('a.sri_btn_xs')
            apply = apply_button.text.strip() if apply_button else "지원 방식 정보 없음"
            print(f"지원 방식: {apply}")
            
            items = job.select_one('div.job_condition')
            conditions = items.find_all('span')
            
            location = conditions[0].text.strip() # 위치
            print(f"위치: {location}")
            career = conditions[1].text.strip() # 경력
            print(f"경력: {career}")
            edu_career = conditions[2].text.strip() # 학력
            print(f"학력: {edu_career}")
            regular = conditions[3].text.strip() # 정규직
            print(f"정규직 여부: {regular}")
            
            job_sector = job.select_one('div.job_sector')
            tech_stacks = job_sector.find_all(['b', 'a'])  # <b>와 <a> 태그 모두 가져오기(섞여있음)

            # 기술 스택("외" 제외)
            tech_list = set() # 웹개발이 자꾸 중복돼서 중복 제거용 set
            for stack in tech_stacks:
                if stack.name in ['b', 'a']:  # <b> 또는 <a> 태그만 처리
                    tech = stack.text.strip()
                    if "외" not in tech:  # "외"가 포함되지 않은 경우만 출력
                        tech_list.add(tech)

            print(f"기술스택: {', '.join(tech_list)}") # 기술 스택 리스트
                        
            print('\n')
                
    except Exception:
        pass