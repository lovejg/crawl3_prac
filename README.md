# crawl_prac

일단 잡코리아, 사람인, 원티드 크롤링 예정

잡코리아: 대부분 정적 HTML, 일부는 JS 로딩 => requests + BeautifulSoup
원티드: React 기반, JS 렌더링 + 무한스크롤 => Selenium
사람인: HTML 기반이긴 한데, URL 파라미터가 좀 복잡 => requests + BeautifulSoup

상세 페이지는 크롤링을 하진 않고, 그냥 URL 정도만 따놓음. 일단 메인 페이지(목록 페이지) 정보 크롤링

- 상세페이지 크롤링 예정!

잡코리아의 경우에는 검색창에서 검색할 때랑, navbar에 있는 카테고리(필터링) 기능 이용해서 들어갈 때랑 태그들이 달라서 일단 검색창 검색 기준으로 구현함

사람인은 잡코리아랑 거의 동일하게 구현함

원티드는 일단 페이지가 여러개 있는게 아니고(즉 페이지 번호 X) 무한 스크롤임. 그리고 JS 렌더링(동적)이라서 selenium으로 구현해야 됨
그리고 크롬 드라이버가 필요. 따라서 아래 3개의 명령어를 순차적으로 터미널에 입력함으로써 크롬 드라이버를 다운받기
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt update
sudo apt install -y ./google-chrome-stable_current_amd64.deb
