import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
import datetime

keyURL = input("URL 입력: ")
print("크롤링 시작")

try:
    soup = requests.get(keyURL, headers={'User-Agent': 'Mozilla/5.0'})
    html = BeautifulSoup(soup.text, 'html.parser').select_one("section#container")
    # print(html) # 테스트
    
    main_info = html.select_one('section.secReadSummary')
    detail_info = html.select_one('div.divDetailWrap')
    # print(main_info) # 테스트
    # print(detail_info) # 테스트
    test = html.select_one('.detailed-summary-contents')
    
    nowDate = datetime.datetime.now().strftime('%Y-%m-%d')
    print(f"현재 날짜: {nowDate}")
    
    company = main_info.select_one('span.coName').text.strip() # 회사 이름
    print(f"회사 이름: {company}")
    
    # 내부 태그 제외하고 텍스트만 추출하는 방식 이용(텍스트 노드) => NavigableString 이용
    h3_tag = main_info.select_one('h3.hd_3') # 태그가 바뀔 시 여기 부분을 수정해주면 됨
    text = [t for t in h3_tag.contents if isinstance(t, NavigableString)]
    title = ''.join(text).strip()
    print(f"공고 제목: {title}")
    
    career = main_info.select('strong.col_1')[0].text.strip()
    print(f"경력: {career}")
    
    edu_career = main_info.select('strong.col_1')[1].text.strip()
    print(f"학력: {edu_career}")
    
    # dl 태그 안에서 dt 중 "스킬"인 항목을 찾고, 그 다음 dd를 추출
    dl_tag1 = main_info.select('dl.tbList')[0]
    dt_tags = dl_tag1.find_all('dt') # dt 태그 다 찾고

    # 기술 스택 => 구조가 좀 뭐같아서 좀 힘들게 뽑아내야 됨
    skills = ""
    for dt in dt_tags: # 찾은 dt 태그들 순회해서
        if dt.text.strip() == "스킬": # 스킬이라고 된 애 찾으면
            dd = dt.find_next_sibling('dd') # 바로 다음 형제인 dd를 가져옴(구조 보면 왜 이렇게 하는지 알 수 있음)
            skills = dd.get_text(strip=True) # 텍스트 추출
            break
    print(f"기술 스택: {skills}")

    regular = main_info.select_one('ul.addList').text.strip()
    # print(f"정규직 여부: {regular}")
    
    # 각종 정보들 얻는 과정인데 얘도 구조가 좀 뭐같아서 뽑기 쉽지 않음
    dl_tag2 = main_info.select('dl.tbList')[1]

    for dt in dl_tag2.find_all('dt'):
        category = dt.get_text(strip=True)
        dd = dt.find_next_sibling('dd')
        
        # 공고 정보(급여, 위치, 일하는 시간, 직급)
        if category == "급여":
            # 내부 span과 em 태그 텍스트를 각각 수집
            pay = []
            if dd.find('em'):
                pay.append(dd.find('em').get_text(strip=True))
            if dd.find('span'):
                pay.append(dd.find('span').get_text(strip=True) + "만원")
            # " - 면접 후 결정" 같은 꼬리 텍스트도 추출
            tail_text = dd.get_text(" ", strip=True)
            if '-' in tail_text:
                tail = tail_text.split('-')[-1].strip()
                pay.append(f"- {tail}")
            print(f"급여: {' '.join(pay)}")

        elif category == "지역":
            location_text = dd.get_text(" ", strip=True)
            location = location_text.split("지도")[0].strip().rstrip(",")
            print(f"위치: {location}")

        elif category == "시간":
            time_temp = []
            for content in dd.contents:
                if isinstance(content, str):
                    if content.strip():
                        time_temp.append(content.strip())
                elif content.name == "span":
                    time_temp.append(content.get_text(strip=True))
                elif content.name == "ul":
                    time_temp.extend(li.get_text(strip=True) for li in content.find_all("li"))
            work_time = ", ".join([t for t in time_temp if t])
            print(f"시간: {work_time}")

        elif category == "직급":
            grade = dd.get_text(strip=True)
            print(f"직급: {grade}")


    # 여기도 같은 방식
    dl_tag3 = main_info.select('dl.tbList')[2]

    for dt in dl_tag3.find_all('dt'):
        category = dt.get_text(strip=True)
        dd = dt.find_next_sibling('dd')

        # 기업 정보(업종, 사원수, 설립년도, 기업형태, 홈페이지 URL)
        if category == "산업(업종)":
            industry = dd.get_text(strip=True)
            print(f"산업(업종): {industry}")

        elif category == "사원수":
            employees = dd.get_text(strip=True)
            print(f"사원수: {employees}")

        elif category == "설립년도":
            year_established = dd.get_text(strip=True).replace(" ", "")
            print(f"설립년도: {year_established}")

        elif category == "기업형태":
            company_type = dd.get_text(separator=" ", strip=True)
            company_type = ' '.join(company_type.split())  # 다중 공백 제거
            print(f"기업형태: {company_type}")

        elif category == "홈페이지":
            homepage_tag = dd.find('a')
            homepage = homepage_tag.get_text(strip=True) if homepage_tag else ''
            print(f"홈페이지: {homepage}")
            
    
    # 아래 메인 내용들(잡코리아가 가려놨는지 전혀 안됨)
    # detail = detail_info.select_one('article.artReadStrategy')
    
    # if detail:
    #     text = detail.get_text(separator=' ', strip=True)
    #     text = ' '.join(text.split())
    #     print(text)
            
except Exception:
    pass