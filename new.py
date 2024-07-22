import streamlit as st
from anthropic import Anthropic

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
            model="claude-2.1",  # 여기를 "claude-2.1"로 변경
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
        return None

def generate_website_code(requirements, api_key):
    """Generate website HTML code based on user requirements."""
    prompt = f"다음 요구사항을 바탕으로 간단한 HTML 웹사이트를 만들어주세요: {requirements}. HTML 코드만 제공해 주시고, 설명은 생략해 주세요."
    response = generate_response(prompt, api_key)
    if response:
        return response
    return "<!-- 웹사이트 코드를 생성할 수 없습니다 -->"

# Streamlit UI
st.title("AI 웹사이트 생성기 (Claude 버전)")

# API 키 입력
api_key = st.text_input("Anthropic API 키를 입력해주세요:", type="password")
if api_key:
    st.session_state.api_key = api_key
    try:
        # API 키 유효성 검사
        client = init_anthropic_client(api_key)
        st.success("API 키가 유효합니다.")
    except Exception as e:
        st.error(f"API 키가 유효하지 않습니다: {str(e)}")
        st.session_state.api_key = ""

if st.session_state.api_key:
    # User input form
    with st.form("company_info"):
        company_name = st.text_input("회사명을 입력해주세요:")
        industry = st.text_input("업종을 입력해주세요:")
        submit_button = st.form_submit_button("대화 시작하기")
    
    if submit_button:
        st.session_state.messages.append({
        "role": "system", 
        "content": f"새로운 대화가 {industry} 산업의 {company_name}에 대해 시작되었습니다."
    })
    
    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("웹사이트에 대한 요구사항을 말씀해주세요:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate response
        response = generate_response(prompt, st.session_state.api_key)
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Ask if the user wants to generate the website
        if st.button("웹사이트 생성하기"):
            website_requirements = "\n".join([m["content"] for m in st.session_state.messages if m["role"] != "system"])
            st.session_state.website_code = generate_website_code(website_requirements, st.session_state.api_key)
            
            # Display generated code
            st.code(st.session_state.website_code, language="html")
            
            # Display website preview
            st.subheader("웹사이트 미리보기")
            st.components.v1.html(st.session_state.website_code, height=600)
    
    # Reset conversation
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.session_state.website_code = ""
        st.experimental_rerun()
else:
    st.warning("애플리케이션을 사용하려면 Anthropic API 키를 입력해주세요.")