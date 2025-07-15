import requests
from bs4 import BeautifulSoup
import datetime

print("채용정보 크롤링을 시작 \n")

try:
    soup = requests.get('https://recruit.kakaobank.com/jobs?recruitClassName=Infra&recruitClassName=Frontend&recruitClassName=Server&recruitClassName=AI&recruitClassName=Engineering&recruitClassName=Security&recruitClassName=Data&recruitClassName=Mobile', headers={'User-Agent': 'Mozilla/5.0'})
    html = BeautifulSoup(soup.text, 'html.parser').select_one(".Tabs_content__1cw1bssi") # 상위 class 입력
    # print(html) # 테스트
    
    jobs = html.select('.h7nnv10') # 각 요소별 클래스 입력
    # print(len(jobs)) # 테스트 => 페이지당 20개씩 있음
    
    nowDate = datetime.datetime.now().strftime('%Y-%m-%d')
    print(f"현재 날짜: {nowDate}")
    print('\n')
    
    for job in jobs:
        company = job.select_one('span.Typography_variant_size16__344nw26').text.strip() # 회사 이름
        print(f"회사 이름: {company}")
        
        title = job.select_one('a.h7nnv12').text.strip() # 공고 제목
        print(f"공고 제목: {title}")
        
        url = job.find('a')['href'] # 상세페이지 url
        print(f"상세페이지 URL: {url}")
        
        # 경력, 학력 등 각종 정보 뽑는 소스인데, 원래 간단했는데 이번에 뭔 ㅈ같은게 좀 추가돼서 처리하느냐고 ㅈㄴ 복잡해짐(경력이 [0]이 아니고 딴거인 경우가 생김)
        # 그리고 양식 정확히 안 맞추고 정보가 한 두개씩 빠져있는 케이스도 있어서 그것도 처리해줘야 됨(일단은 해당 공고는 무시하고 넘기는걸로 처리함)
        items = job.select('span.Typography_color_gray800__344nw2l')
        start_index = -1
        for i, item in enumerate(items):
            if item.text.strip().startswith('경력'):
                start_index = i
                break

        if start_index != -1:
            info_list = items[start_index:]
            
        if len(info_list) < 5:
            continue # 정보가 하나라도 부족하면 일단 해당 공고 패스
        
        career = info_list[0].text.strip() # 경력
        edu_career = info_list[1].text.strip() # 학력
        regular = info_list[2].text.strip() # 정규직 여부
        location = info_list[3].text.strip() # 위치
        deadline = info_list[4].text.strip() # 마감

        print(f"경력: {career}")
        print(f"학력: {edu_career}")
        print(f"정규직 여부: {regular}")
        print(f"위치: {location}")
        print(f"마감: {deadline}")
        
        benefit = job.select('span.Typography_variant_size13__344nw28') # 장점(태그) => 없는 공고들도 있음(빈 배열이면 없는거임)
        print("장점: ")
        for ben in benefit:
            print(ben.text.strip())
        
        # 지원방식
        apply = job.select_one('span.Flex_align_center__i0l0hl8').text.strip()
        print(f"지원 방식: {apply}")
        
        # 공고별 구분선
        print("-" * 20)
        print('\n')
            
except Exception:
    pass