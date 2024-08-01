import logging
import streamlit as st
from openai import OpenAI
import tiktoken
from streamlit.components.v1 import html as st_html

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

def count_tokens(text):
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))
    except Exception as e:
        logging.error(f"토큰 계산 중 오류 발생: {str(e)}")
        return 0

def init_openai_client(api_key):
    return OpenAI(api_key=api_key)

def generate_response(prompt, api_key, max_tokens=4000):
    try:
        client = init_openai_client(api_key)
        prompt_tokens = count_tokens(prompt)
        available_tokens = 8192 - prompt_tokens - 100
        completion_tokens = min(available_tokens, max_tokens)
        
        if completion_tokens <= 0:
            raise ValueError("프롬프트가 너무 깁니다. 대화 내용을 줄여주세요.")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a skilled web developer and designer. Provide only HTML code in your response."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=completion_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"API 호출 중 오류 발생: {str(e)}")
        return None

def generate_website_code(conversation_history, company_name, industry, api_key):
    recent_messages = conversation_history.split("\n")[-5:]
    summarized_history = "\n".join(recent_messages)
    
    prompt = f"""Create a modern, professional HTML website for:
                Company: {company_name}
                Industry: {industry}
                Recent conversation: {summarized_history}

                Requirements:
                1. Full HTML5 structure (<!DOCTYPE html>, <html>, <head>, <body>)
                2. Responsive design (Flexbox/Grid, media queries)
                3. Modern design (gradients, shadows, animations)
                4. Basic structure (header, navigation, main content, footer)
                5. Industry-appropriate color scheme
                6. Font Awesome icons (use CDN)
                7. Simple JavaScript for dynamic elements
                8. SEO meta tags and Open Graph tags
                9. Web accessibility compliance

                Provide only the complete HTML code.
                """
    
    logging.info(f"Generating website code with prompt length: {len(prompt)}")
    response = generate_response(prompt, api_key)
    
    if response:
        logging.info(f"Generated HTML code length: {len(response)}")
        return response
    return None

def is_valid_html(html_code):
    return (html_code.strip().startswith("<!DOCTYPE html>") or html_code.strip().lower().startswith("<html")) and "<body>" in html_code.lower() and "</body>" in html_code.lower()

# Streamlit UI
st.title("AI 웹사이트 생성기 (OpenAI 버전)")

# API 키 입력
api_key = st.text_input("OpenAI API 키를 입력해주세요:", type="password", value=st.session_state.api_key)
if api_key:
    st.session_state.api_key = api_key
    try:
        init_openai_client(api_key)
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
        
        if submit_button and company_name and industry:
            st.session_state.company_name = company_name
            st.session_state.industry = industry
            st.session_state.messages.append({
                "role": "system", 
                "content": f"새로운 대화가 {industry} 산업의 {company_name}에 대해 시작되었습니다."
            })
            st.rerun()
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    prompt = st.chat_input("웹사이트에 대한 요구사항을 말씀해주세요:")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = generate_response(prompt, st.session_state.api_key)
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        conversation_history = "\n".join([m["content"] for m in st.session_state.messages if m["role"] != "system"])
        website_code = generate_website_code(
            conversation_history, 
            st.session_state.company_name, 
            st.session_state.industry, 
            st.session_state.api_key
        )
        
        if website_code:
            st.session_state.website_code = website_code
            st.rerun()
    
    if st.session_state.website_code:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("생성된 HTML 코드")
            st.code(st.session_state.website_code, language="html")

        with col2:
            st.subheader("웹사이트 미리보기")
            if is_valid_html(st.session_state.website_code):
                st_html(st.session_state.website_code, height=600, scrolling=True)
                st.success("HTML 코드가 성공적으로 생성되었습니다.")
            else:
                st.error("유효한 HTML 코드가 생성되지 않았습니다.")
                st.text("생성된 코드의 시작 부분:")
                st.code(st.session_state.website_code[:500], language="html")

    if st.button("대화 초기화"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()