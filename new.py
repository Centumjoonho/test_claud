import logging
import streamlit as st
from openai import OpenAI
import re


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

def init_openai_client(api_key):
    return OpenAI(api_key=api_key)

def generate_response(prompt, api_key):
    """Generate a response using OpenAI API."""
    try:
        client = init_openai_client(api_key)
        response = client.chat.completions.create(
            model="gpt-4",  # 또는 원하는 모델
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
        return None

def generate_website_code(conversation_history, company_name, industry, primary_color, api_key):
    """Generate website HTML code based on conversation history."""
    
    prompt = f"""당신은 숙련된 웹 개발자이자 디자이너입니다. 
    다음 정보와 템플릿을 바탕으로 현대적이고 전문적인 HTML 웹사이트를 만들어주세요:

    회사명: {company_name}
    업종: {industry}
    주 색상: {primary_color}
    대화 내용: {conversation_history} 
    다음은 참고해야 할 웹사이트 템플릿 구조입니다:

    1. DOCTYPE 선언과 HTML 구조:
       <!DOCTYPE HTML>
       <HTML class="Userpage" lang="ko" dir="ltr">

    2. 헤드 섹션:
       <head>
           <meta charset="UTF-8">
           <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
           <title>{company_name}</title>
           <!-- SEO 메타 태그 -->
           <!-- CSS 및 JS 파일 링크 -->
       </head>

    3. 바디 구조:
       <body>
           <div id="skipNavi">
               <!-- 접근성을 위한 스킵 네비게이션 -->
           </div>
           <div id="fullpage">
               <div class="wrapper">
                   <!-- 헤더 섹션 -->
                   <div class="header_wrap" id="header">
                       <!-- 로고, 네비게이션 메뉴 등 -->
                   </div>
                   
                   <!-- 메인 비주얼 섹션 -->
                   <div class="visual section">
                       <!-- 메인 비주얼 내용 -->
                   </div>
                   
                   <!-- 사업 분야 섹션 -->
                   <div class="section business_bg">
                       <!-- 사업 분야 소개 -->
                   </div>
                   
                   <!-- 회사 소개 섹션 -->
                   <div class="section section4">
                       <!-- 회사 소개 내용 -->
                   </div>
                   
                   <!-- 추가 정보 섹션 -->
                   <div class="section fp-auto-height section5">
                       <!-- 오시는 길, 고객사 정보 등 -->
                   </div>
                   
                   <!-- 문의 섹션 -->
                   <div class="section fp-auto-height">
                       <!-- 문의 및 브로슈어 다운로드 -->
                   </div>
                   
                   <!-- 푸터 섹션 -->
                   <div class="section fp-auto-height">
                       <div class="footer" id="footer">
                           <!-- 푸터 내용 -->
                       </div>
                   </div>
               </div>
           </div>
       </body>

    이 구조를 기반으로, 다음 사항을 준수하여 웹사이트를 생성해주세요:

    이전에 생성된 웹사이트 코드가 있다면, 그것을 기반으로 업데이트하고 개선해주세요.
    새로운 요구사항이 있다면 그에 맞게 웹사이트를 수정하고 확장해주세요.

    반드시 다음 사항을 지켜주세요:

    1. 완전한 HTML5 구조를 사용하세요. <!DOCTYPE html>, <html>, <head>, <body> 태그를 모두 포함해야 합니다.

    2. <style> 태그 내에 최신 CSS 기술을 활용한 스타일을 포함하세요. Flexbox와 Grid를 사용하여 레이아웃을 구성하고,
       반응형 디자인을 위한 미디어 쿼리를 추가하여 모바일, 태블릿, 데스크톱 화면 크기를 고려하세요.

    3. 현대적이고 전문적인 디자인을 적용하세요. 그라데이션, 그림자 효과, 부드러운 애니메이션 등을 적절히 사용하세요.

    4. 기본적인 웹사이트 구조를 포함하세요: 
       - 헤더: 로고, 네비게이션 메뉴
       - 메인 콘텐츠 영역: 홈페이지, 제품/서비스 소개, 회사 소개 등
       - 푸터: 저작권 정보, 연락처, 소셜 미디어 링크

    5. 주 색상으로 {primary_color}를 사용하고, 이에 어울리는 보조 색상을 선택하여 조화로운 색상 팔레트를 구성하세요.

    6. Font Awesome 아이콘을 활용하여 시각적 요소를 추가하세요. 
       (CDN 링크: https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css)

    7. 다음과 같은 기본적인 JavaScript 기능을 추가하세요:
       - 스크롤 애니메이션: 페이지 스크롤 시 요소들이 부드럽게 나타나도록 구현
       - 간단한 이미지 슬라이더 또는 캐러셀
       - 모바일 환경을 위한 햄버거 메뉴

    8. 회사의 업종과 목표 고객을 고려한 적절한 콘텐츠를 작성하세요. 필요한 경우 일반적인 더미 텍스트를 사용하세요.

    9. SEO를 위한 기본적인 메타 태그와 오픈 그래프 태그를 포함하세요.

    10. 웹 접근성 가이드라인(WCAG)의 기본 원칙을 준수하세요. 적절한 대체 텍스트, 키보드 네비게이션, 
        충분한 색상 대비 등을 고려하세요.

    11. 가독성이 좋은 sans-serif 계열의 폰트를 사용하세요. Google Fonts에서 적절한 폰트를 선택하여 적용해주세요.

    12. 페이지 로딩 속도를 고려하여 최적화된 코드를 작성해주세요.

    HTML 코드만 제공해 주세요. 다른 설명은 필요 없습니다.
    """
    
    logging.info(f"프롬프트 내용: {prompt}")
    
    response = generate_response(prompt, api_key)
    
    if response:
        logging.info(f"API 응답 길이: {len(response)}")
        return clean_html(response)
    
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
            primary_color = st.color_picker("주 색상을 선택해주세요:", "#000000")
            submit_button = st.form_submit_button("대화 시작하기")
        
        if submit_button:
            st.session_state.company_name = company_name
            st.session_state.industry = industry
            st.session_state.primary_color = primary_color
            st.session_state.messages.append({
                "role": "system", 
                "content": f"새로운 대화가 {industry} 산업의 {company_name}에 대해 시작되었습니다."
            })
            
    # 현재 설정된 정보 표시
    st.sidebar.write(f"회사명: {st.session_state.get('company_name', '미설정')}")
    st.sidebar.write(f"업종: {st.session_state.get('industry', '미설정')}")
    st.sidebar.write(f"주 색상: {st.session_state.get('primary_color', '미설정')}")

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
            st.components.v1.html(st.session_state.website_code, height=800, scrolling=True, width=None)
        else:
            st.error("유효한 HTML 코드가 생성되지 않았습니다.")

    if st.button("대화 초기화"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()