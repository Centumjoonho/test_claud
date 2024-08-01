import logging
import streamlit as st
from openai import OpenAI
import tiktoken

# Streamlit components를 명시적으로 임포트
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
        return 0  # 오류 발생 시 0을 반환

def init_openai_client(api_key):
    return OpenAI(api_key=api_key)

def generate_response(prompt, api_key, max_tokens=4000):
    """Generate a response using OpenAI API with token limit consideration."""
    try:
        client = init_openai_client(api_key)
        prompt_tokens = count_tokens(prompt)
        available_tokens = 8192 - prompt_tokens - 100  # 100 토큰의 여유를 둡니다
        completion_tokens = min(available_tokens, max_tokens)
        
        if completion_tokens <= 0:
            raise ValueError("프롬프트가 너무 깁니다. 대화 내용을 줄여주세요.")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=completion_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
        st.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
        return None

def generate_website_code(conversation_history, company_name, industry, api_key):
    """Generate website HTML code based on conversation history."""
    
    # 대화 내용 요약 또는 최근 N개의 메시지만 사용
    recent_messages = conversation_history.split("\n")[-5:]  # 최근 5개의 메시지만 사용
    summarized_history = "\n".join(recent_messages)
    
    prompt = f"""당신은 숙련된 웹 개발자이자 디자이너입니다. 
                다음 정보를 바탕으로 현대적이고 전문적인 HTML 웹사이트를 만들어주세요:
                
                회사명: {company_name}
                업종: {industry}
                최근 대화 내용:
                {summarized_history}

                요구사항:
                1. HTML5 구조 (<!DOCTYPE html>, <html>, <head>, <body>)
                2. 반응형 디자인 (Flexbox/Grid, 미디어 쿼리)
                3. 모던한 디자인 (그라데이션, 그림자, 애니메이션)
                4. 기본 구조 (헤더, 네비게이션, 메인 콘텐츠, 푸터)
                5. 업종에 맞는 색상
                6. Font Awesome 아이콘 사용
                7. 간단한 JavaScript로 동적 요소 추가
                8. SEO 메타태그와 오픈 그래프 태그
                9. 웹 접근성 준수

                HTML 코드만 제공해 주세요.
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
                # HTML을 직접 렌더링
                st_html(html_code, height=1000, scrolling=True)
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