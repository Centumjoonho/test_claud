import logging
import streamlit as st
from openai import OpenAI
import re
import requests

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'website_code' not in st.session_state:
    st.session_state.website_code = ""
if 'company_name' not in st.session_state:
    st.session_state.company_name = ""
if 'industry' not in st.session_state:
    st.session_state.industry = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# Unsplash API 키를 하드코딩
UNSPLASH_CLIENT_ID = "AUo2EDi70vyR0pB5floEOnNAKq0SQjhvJFto0150dRM"  # 여기에 실제 Unsplash API 키를 입력하세요

def init_openai_client(api_key):
    return OpenAI(api_key=api_key)

def generate_response(prompt, api_key):
    """Generate a response using OpenAI API."""
    try:
        client = init_openai_client(api_key)
        max_tokens = 16384 

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            # model="ft:gpt-3.5-turbo-1106:personal:jyweb10opts2:9stXUoA9",
            # gpt-4o- FinTuning 은 구독 날짜로 14일 이후에 가능  - MaxToken 이슈가 있음
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
        return None

def search_unsplash_images(query, count=1):
    """Search Unsplash for images based on a query."""
    url = f"https://api.unsplash.com/search/photos"
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_CLIENT_ID}"
    }
    params = {
        "query": query,
        "per_page": count
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        if 'results' in data and data['results']:
            return [result['urls']['regular'] for result in data['results']]
    except requests.exceptions.RequestException as e:
        logging.error(f"Unsplash API 요청 중 오류가 발생했습니다: {str(e)}")
    except ValueError as e:
        logging.error(f"JSON 해석 중 오류가 발생했습니다: {str(e)}")
    
    return ["https://via.placeholder.com/800x600"] * count  # Fallback placeholder images


def get_image_url(query):
    """Get a valid image URL from Unsplash or a placeholder."""
    return search_unsplash_images(query)

def is_valid_url(url):
    """Check if the URL is valid and returns an image."""
    try:
        response = requests.head(url, allow_redirects=True)
        content_type = response.headers.get('content-type')
        return response.status_code == 200 and 'image' in content_type
    except requests.RequestException:
        return False

def generate_website_code(conversation_history, company_name, industry, primary_color, api_key):
    """Generate website HTML code based on conversation history."""
    
    # Fetch images using Unsplash API for different products
    hero_image_url = search_unsplash_images("tech company headquarters, modern office", 1)[0]
    product_image_urls = search_unsplash_images(f"innovative {industry}, cutting-edge products", 4)
    about_image_url = search_unsplash_images("professional team meeting, tech workspace", 1)[0]
    # Ensure we have enough images to replace placeholders
    if len(product_image_urls) < 4:
        product_image_urls.extend(["https://via.placeholder.com/800x600"] * (4 - len(product_image_urls)))


    prompt = f"""웹 개발자와 디자이너로서, 아래 정보를 기반으로 현대적이고 전문적인 HTML 웹사이트를 만들어주세요:

    회사명: {company_name}
    업종: {industry}
    주 색상: {primary_color}
    대화내용: {conversation_history}

    HTML5 구조의 단일 페이지 웹사이트를 다음 요구사항에 맞춰 만들어주세요:

    1. 구조:
    a. 반응형 네비게이션 바: 로고, 메뉴 항목 (회사소개, 사업영역, 상시채용, 회사소식, CONTACT)
    b. 히어로 구역: 전체 화면 배경 이미지, 회사 슬로건, CTA 버튼
    c. 제품/서비스 소개: 3-4개 주요 항목을 카드 형식으로 표시
    d. 회사 소개: 이미지와 텍스트로 간단히 소개
    e. 고객 후기: 규격화 된 동적인 디자인
    f. 뉴스레터 구독 양식: 고객이 이메일 주소가 편리한 간결하면서도 전문적인 디자인
    g. 푸터: 회사 정보, 빠른 링크, 소셜 미디어 아이콘
    h. 구역별 비율: 헤더 10%, 히어로 40%, 메인 내용 25%, 추가 구역 20%, 푸터 5%

    2. 이미지와 내용:
    a. Unsplash URL 사용
    b. 적절한 대체 텍스트 제공
    c. 히어로 구역:
        - 배경: {hero_image_url}
        - 슬로건: "{company_name} - {industry}의 혁신적 솔루션"
        - 간단한 회사 소개 (1-2문장)
    d. 제품/서비스 카드:
        - 이미지: {product_image_urls}
        - 각 항목별 이름과 설명 (2-3문장)
    e. 회사 소개:
        - 이미지: {about_image_url}
        - 미션, 비전, 핵심 가치 설명 (3-4문장)
    f. 고객 후기: 2-3개 (각 1-2문장, 이름과 직책 포함)
    g. 블로그/뉴스: 3-4개 포스트 제목과 요약 (각 1-2문장), 관련 이미지 포함

    3. 디자인:
    a. 주 색상 {primary_color} 사용, 보조 색상 제안
    b. 최신의 트렌디한 디자인, 여백 활용 (구체적 수치 제시)
    c. 히어로 구역과 버튼에 그라데이션 적용 (색상 코드 제시)
    d. 카드와 버튼에 그림자 효과 (구체적 수치 제시)
    e. 버튼과 카드에 호버 효과 (구체적 설명)
    f. Font Awesome 아이콘 활용 하여 페이지 적절한 곳에 특징적인 아이콘 표시 
    g. Scrolling Animation 효과 활용 (구체적 코드 제시)
    h. 헤더, 히어로, 메인 내용, 추가 구역, 푸터 디자인을 주 색상을 활용하여 디자인 하고 사용되는 텍스트의 색상은 주색상에 대비되어 잘 보이는 색상으로 선택

    4. 글꼴:
    a. 제목용 'Roboto', 본문용 'Open Sans' 사용 (굵기 명시)
    b. 글자 크기와 줄 간격 구체적 제시

    5. 반응형 디자인:
    a. 모바일, 태블릿, 데스크탑 기준점 제시
    b. 모바일용 햄버거 메뉴 구현 (JavaScript 코드 포함)

    6. 상호작용 요소:
    a. 스크롤 시 나타나는 효과 (JavaScript 코드 제공)
    b. 제품/서비스 구역에 탭 또는 아코디언 메뉴 (코드 제공)
    c. 고객 후기 슬라이더 (코드 제공)

    7. 성능과 접근성:
    a. 이미지 지연 로딩 적용
    b. ARIA 레이블과 역할 사용 (예시 제공)
    c. 키보드 탐색 지원 (예시 제공)

    8. 검색 최적화:
    a. 메타 태그 제공 (제목, 설명, 키워드)
    b. Open Graph 태그 내용 제공
    c. 의미있는 HTML 구조 사용 (예시 제공)

    9. 추가 기능:
    a. 쿠키 동의 배너 (코드 포함)
    b. 연락처 양식 (기본 유효성 검사 포함)
    c. 블로그 포스트 미리보기 구역 (HTML 구조 제공)

    10. 내용 일관성:
        a. {industry} 관련 전문 용어 3-5개 이상 사용
        b. 모든 텍스트는 완성된 문장으로 작성 (임시 텍스트 사용 금지)

    스타일은 <style> 태그에, JavaScript는 <script> 태그에 포함해주세요. Bootstrap과 Font Awesome 최신 CDN 링크 사용. 결과물은 즉시 사용 가능한 단일 HTML 파일이어야 합니다.

    페이지 로딩 속도, 웹 표준, 브라우저 호환성을 고려해 최적화해주세요. 코드에 주석을 달아 설명해주세요.

    {company_name}의 특성을 반영한 완전한 웹사이트 코드를 제공하고, 쉽게 수정할 수 있도록 변수나 클래스명을 직관적으로 작성해주세요.
    """
    
    logging.info(f"프롬프트 내용: {prompt}")
    
    response = generate_response(prompt, api_key)
    
    if response:
        logging.info(f"API 응답 길이: {len(response)}")
        cleaned_html = clean_html(response)
        return validate_image_urls(cleaned_html, product_image_urls)
    
    return '<!-- 웹사이트 코드를 생성할 수 없습니다 -->'

def clean_html(html):
    """Clean and validate HTML code."""
    # Remove any non-HTML content before <!DOCTYPE html>
    html = re.sub(r'^.*?<!DOCTYPE html>', '<!DOCTYPE html>', html, flags=re.DOTALL)
    
    # Remove any content after closing </html> tag
    html = re.sub(r'</html>.*$', '</html>', html, flags=re.DOTALL)
    
    # Ensure the HTML structure is complete
    if not html.strip().startswith('<!DOCTYPE html>') or not html.strip().endswith('</html>'):
        return None
    
    return html

def validate_image_urls(html, product_image_urls):
    """Replace placeholders in HTML with actual image URLs."""
    # Use regular expression to find all img tags and extract URLs
    img_pattern = re.compile(r'<img\s+[^>]*src="([^"]+)"')
    matches = img_pattern.findall(html)

    # Replace invalid URLs with Unsplash image URLs
    for i, url in enumerate(matches):
        if not is_valid_url(url) and i < len(product_image_urls):
            valid_url = product_image_urls[i]
            html = html.replace(url, valid_url, 1)  # Replace one occurrence at a time

    return html

# Streamlit UI
st.set_page_config(layout="wide")
st.title("AI 웹사이트 생성기 (OpenAI 버전)")

# API 키 입력
api_key = st.text_input("OpenAI API 키를 입력해주세요:", type="password", value=st.session_state.api_key)
if api_key:
    st.session_state.api_key = api_key
    try:
        client = init_openai_client(api_key)
        st.success("API 키가 유효합니다.")
    except Exception as e:
        st.error(f"API 키가 유효하지 않습니다: {str(e)}")
        st.session_state.api_key = ""

if st.session_state.api_key:
    if not st.session_state.company_name or not st.session_state.industry:
        with st.form("company_info"):
            company_name = st.text_input("회사명을 입력해주세요:")
            industry = st.text_input("업종을 입력해주세요:")
            submit_button = st.form_submit_button("대화 시작하기")
        
        if submit_button:
            st.session_state.company_name = company_name
            st.session_state.industry = industry
            st.session_state.messages.append({
                "role": "system", 
                "content": f"새로운 대화가 {industry} 산업의 {company_name}에 대해 시작되었습니다."
            })
            
    # 현재 설정된 정보 표시
    st.sidebar.write(f"회사명: {st.session_state.get('company_name', '미설정')}")
    st.sidebar.write(f"업종: {st.session_state.get('industry', '미설정')}")

    # 색상 변경 옵션
    new_color = st.sidebar.color_picker("주 색상 변경", st.session_state.get('primary_color', '#000000'))
    if new_color != st.session_state.get('primary_color'):
        st.session_state.primary_color = new_color
        st.session_state.messages.append({
            "role": "system",
            "content": f"주 색상이 {new_color}로 변경되었습니다."
        })
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    prompt = st.chat_input("웹사이트에 대한 요구사항을 말씀해주세요:")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = generate_response(prompt, st.session_state.api_key)
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # 대화 내용을 바탕으로 웹사이트 코드 생성 또는 업데이트
        conversation_history = "\n".join([m["content"] for m in st.session_state.messages if m["role"] != "system"])
        st.session_state.website_code = generate_website_code(
            conversation_history, 
            st.session_state.company_name, 
            st.session_state.industry, 
            st.session_state.primary_color,
            st.session_state.api_key
        )
    
    # 생성된 코드 표시
    if st.session_state.website_code:
        with st.expander("생성된 HTML 코드 보기", expanded=False):
            st.code(st.session_state.website_code, language="html")
        
        if st.session_state.website_code.strip().startswith("<!DOCTYPE html>"):
            st.subheader("웹사이트 미리보기")
            st.components.v1.html(st.session_state.website_code, height=1200, scrolling=True)
        else:
            st.error("유효한 HTML 코드가 생성되지 않았습니다.")

    if st.button("대화 초기화"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()