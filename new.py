import logging
import streamlit as st
from openai import OpenAI
import html

# 로깅 설정
logging.basicConfig(level=logging.INFO)
st.set_page_config(layout="wide")

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
            max_tokens=10000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
        return None

def generate_website_code(conversation_history, company_name, industry, api_key):
    """Generate website HTML code based on conversation history."""
    
    prompt = f"""당신은 숙련된 웹 개발자이자 디자이너입니다. 
    
                다음 대화 내용을 바탕으로 현대적이고 전문적인 HTML 웹사이트를 만들어주세요:
                
                회사명: {company_name}
                업종: {industry}
                대화 내용:
                {conversation_history}

                이전에 생성된 웹사이트 코드가 있다면, 그것을 기반으로 업데이트하고 개선해주세요.
                새로운 요구사항이 있다면 그에 맞게 웹사이트를 수정하고 확장해주세요.

                반드시 다음 사항을 지켜주세요:
                
                1. 응답은 완전한 HTML5 구조여야 합니다. <!DOCTYPE html>, <html>, <head>, <body> 태그를 모두 포함해야 합니다.
                
                2. <style> 태그 내에 최신 CSS 기술을 활용한 스타일을 포함하세요. Flexbox나 Grid를 사용하여 레이아웃을 구성하고,
                   반응형 디자인을 위한 미디어 쿼리를 반드시 추가해주세요.
                
                3. 모던한 디자인 트렌드를 반영하여 시각적으로 매력적인 웹사이트를 만들어주세요.
                   (예: 그라데이션, 그림자 효과, 부드러운 애니메이션 등)
                
                4. 헤더, 네비게이션 메뉴, 메인 콘텐츠 영역, 사이드바(필요시), 푸터 등 기본적인 웹사이트 구조를 포함해주세요.
                
                5. 회사의 특성과 업종을 고려한 적절한 색상 스키마를 사용하세요.
                
                6. Font Awesome 아이콘을 활용하여 시각적 요소를 추가하세요. (CDN 링크: https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css)
                
                7. 간단한 JavaScript를 사용하여 동적 요소를 추가하세요. (예: 스크롤 애니메이션, 모달 팝업 등)
                
                8. 요구사항에 맞는 실제 콘텐츠를 포함하되, 필요한 경우 적절한 더미 텍스트로 채워넣으세요.
                
                9. SEO를 위한 메타 태그와 오픈 그래프 태그를 포함하세요.
                
                10. 웹 접근성 가이드라인을 준수하여 모든 사용자가 이용할 수 있는 웹사이트를 만들어주세요.

                HTML 코드만 제공해 주세요. 다른 설명은 필요 없습니다.
                """
    
    logging.info(f"프롬프트 내용: {prompt}")
    
    response = generate_response(prompt, api_key)
    
    if response:
        logging.info(f"API 응답 길이: {len(response)}")
        return response
    
    return '<!-- 웹사이트 코드를 생성할 수 없습니다 -->'

# Streamlit UI
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
            st.session_state.api_key
        )
    
    
    # 생성된 코드 표시
    if st.session_state.website_code:
        col1, col2 = st.columns([1, 3])  # 1:3 비율로 컬럼 분할
        
        with col1:
            with st.expander("생성된 HTML 코드 보기", expanded=False):
                st.code(st.session_state.website_code, language="html")

        with col2:
            html_code = st.session_state.website_code.strip()
            if html_code.startswith("<!DOCTYPE html>") or html_code.lower().startswith("<html"):
                st.subheader("웹사이트 미리보기")
                # 안전한 HTML 렌더링을 위해 html.escape 사용
                safe_html = html.escape(html_code)
                st.components.v1.html(safe_html, height=1000, scrolling=True)  # 높이를 1000px로 증가
            else:
                st.error("유효한 HTML 코드가 생성되지 않았습니다.")
                st.text("생성된 코드 (처음 500자):")
                st.text(html_code[:500] + ("..." if len(html_code) > 500 else ""))

        # HTML 구조 분석
        if "<body>" in html_code.lower() and "</body>" in html_code.lower():
            st.success("HTML 구조가 올바르게 생성되었습니다.")
        else:
            st.warning("HTML 구조가 완전하지 않을 수 있습니다. <body> 태그를 확인해주세요.")
            
    if st.button("대화 초기화"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()