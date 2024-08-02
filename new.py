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
    
    prompt = f"""숙련된 웹 개발자이자 디자이너로서, 다음 정보를 바탕으로 현대적이고 전문적인 HTML 웹사이트를 만들어주세요:

            회사명: {company_name}
            업종: {industry}
            주 색상: {primary_color}
            대화내용 : {conversation_history}

            완전한 HTML5 구조의 단일 페이지 웹사이트를 생성해주세요. 다음 요구사항을 반드시 포함하여 구현해주세요:

            1. 레이아웃 구조:
            a. 반응형 네비게이션 바: 로고, 메뉴 항목 (Home, Products, About Us, Blog, Contact)
            b. 히어로 섹션: 전체 화면 배경 이미지, 회사 슬로건, 눈에 띄는 CTA 버튼
            c. 제품/서비스 하이라이트: 3-4개의 주요 제품/서비스를 카드 형식으로 표시
            d. 회사 소개: 이미지와 텍스트를 사용한 간략한 소개
            e. 고객 후기 섹션
            f. 뉴스레터 구독 양식
            g. 푸터: 회사 정보, 빠른 링크, 소셜 미디어 아이콘

            2. 이미지 및 콘텐츠:
            a. 모든 이미지에 실제 Unsplash URL을 사용하세요. 예: https://images.unsplash.com/photo-xxxx
            b. 각 이미지에 적절한 alt 텍스트를 제공하세요.
            c. 히어로 섹션:
                - 배경: {industry}를 대표하는 고품질 이미지 사용
                - 슬로건: "{company_name} - {industry}의 혁신적인 솔루션"
                - 1-2문장의 간단한 회사 소개 포함
            d. 제품/서비스 카드:
                - 각 제품/서비스를 대표하는 실제 이미지 사용
                - 구체적인 제품/서비스명과 2-3문장의 설명 제공
            e. 회사 소개 섹션:
                - 팀워크 또는 회사 가치를 나타내는 실제 이미지 사용
                - 회사의 미션, 비전, 핵심 가치에 대한 3-4문장의 구체적인 설명
            f. 고객 후기 섹션:
                - 2-3개의 구체적인 고객 후기 (각 1-2문장, 고객 이름과 직책 포함)
            g. 블로그/뉴스 섹션:
                - 3-4개의 실제적인 블로그 포스트 제목과 요약 (각 1-2문장)
                - 각 포스트에 관련된 실제 썸네일 이미지 사용

            3. 디자인 요소:
            a. {primary_color}를 주 색상으로 사용하고, 이에 어울리는 구체적인 보조 색상 코드 제공
            b. 모던하고 깔끔한 디자인, 섹션 간 충분한 여백 사용 (구체적인 padding 값 제시)
            c. 히어로 섹션과 CTA 버튼에 그라데이션 배경 적용 (구체적인 색상 코드 제시)
            d. 카드와 버튼에 그림자 효과 적용 (구체적인 box-shadow 값 제시)
            e. 버튼과 카드에 호버 애니메이션 적용 (구체적인 transition 효과 설명)
            f. Font Awesome 아이콘을 사용하여 구체적인 아이콘 코드 제공

            4. 타이포그래피:
            a. Google Fonts에서 'Roboto'를 제목용, 'Open Sans'를 본문용으로 사용 (구체적인 font-weight 포함)
            b. 제목과 본문의 구체적인 font-size, line-height 값 제시

            5. 반응형 디자인:
            a. 모바일, 태블릿, 데스크탑 버전의 구체적인 breakpoint 제시
            b. 모바일에서 햄버거 메뉴 구현 (JavaScript 코드 포함)

            6. 인터랙티브 요소:
            a. 스크롤 시 요소들이 부드럽게 나타나는 애니메이션 효과 (구체적인 JavaScript 코드 제공)
            b. 제품/서비스 섹션에 탭 또는 아코디언 메뉴 구현 (구체적인 HTML, CSS, JavaScript 코드 제공)
            c. 고객 후기를 위한 캐러셀 슬라이더 구현 (구체적인 HTML, CSS, JavaScript 코드 제공)

            7. 성능 및 접근성:
            a. 모든 이미지에 lazy loading 적용 (loading="lazy" 속성 사용)
            b. ARIA 레이블과 역할을 적절히 사용 (구체적인 예시 코드 제공)
            c. 키보드 네비게이션 지원을 위한 구체적인 tabindex 사용 예시 제공

            8. SEO 최적화:
            a. 페이지 제목, 설명, 키워드를 포함한 구체적인 메타 태그 제공
            b. Open Graph 태그의 구체적인 내용 제공
            c. 시맨틱 HTML 구조 사용 (구체적인 태그 사용 예시 제공)

            9. 추가 기능:
            a. 쿠키 동의 배너 구현 (HTML, CSS, JavaScript 코드 포함)
            b. 간단한 연락처 양식 구현 (HTML 코드 및 기본적인 form validation 포함)
            c. 블로그 포스트 미리보기 섹션 구현 (구체적인 HTML 구조 제공)

            10. 콘텐츠 일관성:
                a. {industry}에 적합한 전문 용어를 3-5개 이상 사용하여 콘텐츠 생성
                b. 모든 텍스트 콘텐츠는 완성된 문장으로 제공 (빈칸이나 "Lorem ipsum" 사용 금지)

            모든 스타일은 <style> 태그 내에, JavaScript는 <script> 태그 내에 포함해주세요. Bootstrap과 Font Awesome은 최신 버전의 CDN 링크를 사용하세요. 최종 결과물은 복사하여 바로 사용할 수 있는 완전한 단일 HTML 파일이어야 합니다.

            페이지 로딩 속도를 고려하여 코드를 최적화하고, 웹 표준과 크로스 브라우저 호환성을 준수해주세요. CSS 및 JavaScript 코드에 주석을 달아 각 부분의 역할을 설명해주세요.

            최종 결과물에는 {company_name}의 특성을 반영한 완전한 웹사이트 코드가 포함되어야 하며, 실제 구현 시 쉽게 customizing할 수 있도록 변수나 클래스명을 직관적으로 작성해주세요.
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
            st.components.v1.html(st.session_state.website_code, height=800, scrolling=True)
        else:
            st.error("유효한 HTML 코드가 생성되지 않았습니다.")

    if st.button("대화 초기화"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()