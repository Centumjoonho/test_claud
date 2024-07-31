import logging
import streamlit as st
from anthropic import Anthropic
import re

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

def generate_response_with_artifacts(prompt, api_key):
    """Generate a response using Claude API with artifact support."""
    try:
        client = init_anthropic_client(api_key)
        message = client.messages.create(
            model="claude-3-opus-20240229",  # 최신 모델 사용
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        if isinstance(message.content, list) and len(message.content) > 0:
            return message.content[0].text
        else:
            logging.error(f"예상치 못한 응답 형식: {message.content}")
            return None
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
        return None

def extract_artifact(response):
    """Extract artifact content from the API response."""
    if not isinstance(response, str):
        logging.error(f"응답이 문자열이 아닙니다. 타입: {type(response)}")
        return None
    
def generate_website_code(requirements, api_key):
    """Generate website HTML code based on user requirements."""
    
    prompt = f"""Human: 다음 요구사항에 맞는 웹페이지의 HTML artifact를 만들어주세요: {requirements}

    Assistant: 네, 말씀하신 요구사항에 맞는 웹페이지의 HTML artifact를 만들어 드리겠습니다.

    <ANTARTIFACTLINK identifier="custom-webpage" type="text/html" title="맞춤 웹페이지" isClosed="true" />

    웹페이지의 HTML artifact를 생성했습니다. 요구사항에 맞는 완전한 HTML 구조와 적절한 스타일, 내용을 포함하고 있습니다. 이 artifact를 필요에 따라 확인하고 수정할 수 있습니다.

    Human: 감사합니다! 이 웹페이지의 HTML 코드를 보여주실 수 있나요?

    Assistant: 물론이죠! 다음은 웹페이지의 HTML 코드입니다:

    <ANTARTIFACTLINK identifier="custom-webpage" type="text/html" title="맞춤 웹페이지" isClosed="true" />

    이것은 웹페이지의 기본 구조입니다. 특정 요구사항에 따라 더 커스터마이즈할 수 있습니다.

    Human: 좋아 보이네요! 이를 현재 애플리케이션에 어떻게 구현할 수 있는지 설명해 주시겠어요?"""
    
    logging.info(f"프롬프트 내용: {prompt}")
    
    response = generate_response_with_artifacts(prompt, api_key)
    
    if response:
        logging.info(f"API 응답 타입: {type(response)}")
        logging.info(f"API 응답 내용: {response[:500]}...")  # 처음 500자만 로깅
        html_code = extract_artifact(response)
        if html_code:
            return html_code
        else:
            logging.error("HTML 코드를 추출할 수 없습니다.")
    else:
        logging.error("API 응답이 없습니다.")
    
    return "<!-- 웹사이트 코드를 생성할 수 없습니다 -->"

# Streamlit UI
st.title("AI 웹사이트 생성기 (Claude Artifact 버전)")

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
        response = generate_response_with_artifacts(prompt, st.session_state.api_key)
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
        
        st.subheader("웹사이트 미리보기")
        artifact_html = st.session_state.website_code
        if artifact_html:
            st.components.v1.html(artifact_html, height=600, scrolling=True)
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