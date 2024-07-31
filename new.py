import logging
import streamlit as st
from anthropic import Anthropic

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'website_code' not in st.session_state:
    st.session_state.website_code = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

def init_anthropic_client(api_key):
    return Anthropic(api_key=api_key)

def generate_response(prompt, api_key):
    """Generate a response using Claude API."""
    try:
        client = init_anthropic_client(api_key)
        message = client.messages.create(
            model="claude-2.1",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt.encode('utf-8').decode('utf-8')}
            ]
        )
        return message.content[0].text
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
        return None

def generate_website_code(requirements, api_key):
    """Generate website HTML code based on user requirements."""
    
    prompt = f"""당신은 웹 개발자입니다. 
    
                다음 요구사항을 바탕으로 완전한 HTML 웹사이트를 만들어주세요: {requirements}

                반드시 다음 사항을 지켜주세요:
                
                1. 응답은 완전한 HTML 구조여야 합니다.
                <!DOCTYPE html>, <html>, <head>, <body> 태그를 모두 포함해야 합니다.
                
                2. <style> 태그 내에 기본적인 CSS를 포함하고, 
                반응형 디자인을 위한 미디어 쿼리도 추가해주세요.
                
                3. 설명이나 주석은 생략하고 순수한 HTML 코드만 제공해 주세요.
                
                4. 응답은 반드시 <!DOCTYPE html>로 시작해야 합니다.
                
                5. 요구사항에 맞는 실제 콘텐츠를 포함해야 합니다.
                
                6. 네비게이션 메뉴, 헤더, 푸터 등 기본적인 웹사이트 구조를 포함해주세요.

                HTML 코드만 제공해 주세요. 다른 설명은 필요 없습니다.
                
                중요: 반드시 전체 HTML 코드를 <ANTARTIFACTLINK> 태그로 감싸서 제공해야 합니다. 
            예시:
            <ANTARTIFACTLINK identifier="generated-website" type="text/html" title="생성된 웹사이트">
            <!DOCTYPE html>
            <html>
            ...
            </html>
            </ANTARTIFACTLINK>

            오직 <ANTARTIFACTLINK> 태그로 감싼 HTML 코드만 제공하세요.
                
                """
    
    logging.info(f"프롬프트 내용: {prompt}")
    
    response = generate_response(prompt, api_key)
    
    if response:
        logging.info(f"API 응답 길이: {len(response)}")
        if isinstance(response, str):
            artifact_start = response.find("<ANTARTIFACTLINK")
            artifact_end = response.find("</ANTARTIFACTLINK>")
            
            if artifact_start != -1 and artifact_end != -1:
                html_code = response[artifact_start:artifact_end + len("</ANTARTIFACTLINK>")]
                return html_code
            else:
                logging.error("API 응답에서 <ANTARTIFACTLINK> 태그를 찾을 수 없습니다.")
        else:
            logging.error(f"예상치 못한 응답 형식: {type(response)}")

    return '<ANTARTIFACTLINK identifier="generated-website" type="text/html" title="생성된 웹사이트"><!-- 웹사이트 코드를 생성할 수 없습니다 --></ANTARTIFACTLINK>'

# Streamlit UI
st.title("AI 웹사이트 생성기 (Claude 버전)")

# API 키 입력
api_key = st.text_input("Anthropic API 키를 입력해주세요:", type="password")
if api_key:
    st.session_state.api_key = api_key
    try:
        client = init_anthropic_client(api_key)
        st.success("API 키가 유효합니다.")
    except Exception as e:
        st.error(f"API 키가 유효하지 않습니다: {str(e)}")
        st.session_state.api_key = ""

if st.session_state.api_key:
    with st.form("company_info"):
        company_name = st.text_input("회사명을 입력해주세요:")
        industry = st.text_input("업종을 입력해주세요:")
        submit_button = st.form_submit_button("대화 시작하기")
    
    if submit_button:
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
        response = generate_response(prompt, st.session_state.api_key)
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    if st.button("웹사이트 생성하기"):
        website_requirements = "\n".join([m["content"] for m in st.session_state.messages if m["role"] != "system"])
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
        
        # ANTARTIFACTLINK 태그에서 HTML 코드 추출
        html_start = st.session_state.website_code.find(">") + 1
        html_end = st.session_state.website_code.rfind("</ANTARTIFACTLINK")
        html_code = st.session_state.website_code[html_start:html_end].strip()
        
        if html_code.startswith("<!DOCTYPE html>"):
            st.subheader("웹사이트 미리보기")
            st.components.v1.html(html_code, height=600, scrolling=True)
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