# crawl_prac

잡코리아: 대부분 정적 HTML, 일부는 JS 로딩 => requests + BeautifulSoup
원티드: React 기반, JS 렌더링 + 무한스크롤 => Selenium
사람인: HTML 기반이긴 한데, URL 파라미터가 좀 복잡 => requests + BeautifulSoup (얘는 지금 밴 당해서 나는 테스트 불가능)

상세 페이지는 크롤링을 하진 않고, 그냥 URL 정도만 따놓음. 일단 메인 페이지(목록 페이지) 정보 크롤링 => 상세페이지 크롤링 예정!

잡코리아의 경우에는 검색창에서 검색할 때랑, navbar에 있는 카테고리(필터링) 기능 이용해서 들어갈 때랑 태그들이 달라서 일단 검색창 검색 기준으로 구현함

사람인은 잡코리아랑 거의 동일하게 구현함

원티드는 일단 페이지가 여러개 있는게 아니고(즉 페이지 번호 X) 무한 스크롤임. 그리고 JS 렌더링(동적)이라서 selenium으로 구현해야 됨
그리고 크롬 드라이버가 필요. 따라서 아래 3개의 명령어를 순차적으로 터미널에 입력함으로써 크롬 드라이버를 다운받기
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt update
sudo apt install -y ./google-chrome-stable_current_amd64.deb

상세페이지의 경우, 어차피 공고 목록에서 클릭해서 들어가는 방식일거고, 메인 페이지 크롤링 파트에서 상세페이지 URL 다 갖고 있기 때문에, 그거 이용해서 들어가는 방식으로 하면 될듯.
결론적으로는 URL 넣으면 해당 페이지에 대한 크롤링 진행하는 방식으로 구현 예정(실제 사용시에는 공고 목록 클릭하면 해당 공고의 상세페이지 URL을 그대로 넣는 방식)

잡코리아: 상세페이지를 못 가져옴(막아놨음)
원티드: 뭔가뭔가 조금씩 문제가 있는데 잘 하면 해결 할 수 있을듯?(근데 일단 가져오긴 해. 에러 발생은 아니야)
직행: 문제없는데, 상세페이지가 사진으로 돼있어서 못 가져옴

카카오뱅크: 메인페이지는 requests로 가능하고, 상세페이지는 selenium 써야됨
카카오: 메인페이지는 selenium 써야되고, 상세페이지는 requests로 가능
카카오페이: 메인페이지는 requests로 가능하고, 상세페이지는 selenium 써야됨

https://recruit.kakaobank.com/jobs(requests 쓰면 되고, recruitClassName=Fronted&recruitClassName=AI& 이런식으로recruitClassName=&붙여서 늘리면 됨)
디테일은 selenium

https://kakaopay.career.greetinghr.com/ko/main?occupations=%EA%B8%B0%EC%88%A0(requests로 가능)
디테일은 selenium
