import logging
import streamlit as st
from anthropic import Anthropic
import time
from functools import lru_cache

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'website_code' not in st.session_state:
    st.session_state.website_code = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

def init_anthropic_client(api_key):
    return Anthropic(api_key=api_key)

@lru_cache(maxsize=100)
def generate_response(prompt, api_key):
    """Generate a response using Claude API with retry logic and caching."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = init_anthropic_client(api_key)
            message = client.messages.create(
                model="claude-2.1",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            if "overloaded" in str(e).lower() and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logging.warning(f"API 과부하. {wait_time}초 후 재시도합니다.")
                time.sleep(wait_time)
            else:
                logging.error(f"API 호출 중 오류 발생: {str(e)}")
                st.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
                return None
    return None

def generate_website_code(requirements, api_key):
    """Generate website HTML code based on user requirements."""
    prompt = f"""당신은 웹 개발자입니다. 다음 요구사항을 바탕으로 완전한 HTML 웹사이트를 만들어주세요: {requirements}

    반드시 다음 사항을 지켜주세요:
    1. 응답은 완전한 HTML 구조여야 합니다. <!DOCTYPE html>, <html>, <head>, <body> 태그를 모두 포함해야 합니다.
    2. <style> 태그 내에 기본적인 CSS를 포함하고, 반응형 디자인을 위한 미디어 쿼리도 추가해주세요.
    3. 설명이나 주석은 생략하고 순수한 HTML 코드만 제공해 주세요.
    4. 응답은 반드시 <!DOCTYPE html>로 시작해야 합니다.
    5. 요구사항에 맞는 실제 콘텐츠를 포함해야 합니다.
    6. 네비게이션 메뉴, 헤더, 푸터 등 기본적인 웹사이트 구조를 포함해주세요.

    HTML 코드만 제공해 주세요. 다른 설명은 필요 없습니다."""
    
    logging.info(f"프롬프트 내용: {prompt}")
    
    response = generate_response(prompt, api_key)
    
    if response:
        logging.info(f"API 응답 길이: {len(response)}")
        html_code = response.strip()
        if "<!DOCTYPE html>" in html_code:
            html_code = html_code[html_code.index("<!DOCTYPE html>"):]
        return html_code
    
    return "<!-- 웹사이트 코드를 생성할 수 없습니다 -->"

# Streamlit UI
st.title("AI 웹사이트 생성기 (Claude 버전)")

# API 키 입력 부분은 그대로 유지

if st.session_state.api_key:
    # 입력 유효성 검사 함수
    def validate_input(input_text, field_name):
        if not input_text.strip():
            st.error(f"{field_name}을(를) 입력해주세요.")
            return False
        return True

    with st.form("company_info"):
        company_name = st.text_input("회사명을 입력해주세요:")
        industry = st.text_input("업종을 입력해주세요:")
        submit_button = st.form_submit_button("대화 시작하기")
    
    if submit_button and validate_input(company_name, "회사명") and validate_input(industry, "업종"):
        st.session_state.messages.append({
            "role": "system", 
            "content": f"새로운 대화가 {industry} 산업의 {company_name}에 대해 시작되었습니다."
        })
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if len(message["content"]) > 500:
                with st.expander("전체 메시지 보기"):
                    st.markdown(message["content"])
            else:
                st.markdown(message["content"])
    
    prompt = st.chat_input("웹사이트에 대한 요구사항을 말씀해주세요:")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner('AI가 응답을 생성 중입니다...'):
            response = generate_response(prompt, st.session_state.api_key)
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    if st.button("웹사이트 생성하기"):
        website_requirements = "\n".join([m["content"] for m in st.session_state.messages if m["role"] != "system"])
        with st.spinner('웹사이트를 생성 중입니다...'):
            progress_bar = st.progress(0)
            for percent_complete in range(100):
                time.sleep(0.1)  # 실제 생성 시간에 맞게 조정 필요
                progress_bar.progress(percent_complete + 1)
            st.session_state.website_code = generate_website_code(website_requirements, st.session_state.api_key)
        st.session_state.website_requirements = website_requirements  # 요구사항 저장
    
    # 디버그 정보 및 생성된 코드 표시
    if 'website_code' in st.session_state and st.session_state.website_code:
        with st.expander("디버그 정보", expanded=False):
            if 'website_requirements' in st.session_state:
                st.write("웹사이트 요구사항:", st.session_state.website_requirements)
            st.write("생성된 HTML 코드 길이:", len(st.session_state.website_code))
        
        with st.expander("생성된 HTML 코드 보기", expanded=False):
            st.code(st.session_state.website_code, language="html")
        
        if st.session_state.website_code.startswith("<!DOCTYPE html>"):
            st.subheader("웹사이트 미리보기")
            st.components.v1.html(st.session_state.website_code, height=600, scrolling=True)
        else:
            st.error("유효한 HTML 코드가 생성되지 않았습니다.")

    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.session_state.website_code = ""
        if 'website_requirements' in st.session_state:
            del st.session_state.website_requirements
        st.experimental_rerun()
else:
    st.warning("애플리케이션을 사용하려면 Anthropic API 키를 입력해주세요.")