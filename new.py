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
if 'primary_color' not in st.session_state:
    st.session_state.primary_color = "#000000"

def init_openai_client(api_key):
    return OpenAI(api_key=api_key)

def get_token_limit(model):
    model_token_limits = {
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "gpt-4": 8192,
        "gpt-4-32k": 32768
    }
    return model_token_limits.get(model, 4096)

def get_tiktoken_model_name(model):
    """OpenAI API 모델명을 tiktoken 모델명으로 변환"""
    model_mapping = {
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k": "gpt-3.5-turbo-16k",
        "gpt-4": "gpt-4",
        "gpt-4-32k": "gpt-4-32k",
    }
    return model_mapping.get(model, "gpt-3.5-turbo")

def calculate_token_count(text, model):
    """주어진 텍스트의 토큰 수를 계산."""
    try:
        tiktoken_model = get_tiktoken_model_name(model)
        encoder = tiktoken.encoding_for_model(tiktoken_model)
        return len(encoder.encode(text))
    except KeyError:
        logging.warning(f"Model {model} not found, using cl100k_base encoding.")
        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))
    except Exception as e:
        logging.error(f"토큰 계산 중 오류 발생: {str(e)}")
        return len(text.split())  # fallback: 단어 수로 대략적인 추정
    
    
def truncate_conversation_history(conversation_history, model, max_tokens):
    """대화 히스토리를 최대 토큰 수에 맞게 자릅니다."""
    try:
        tiktoken_model = get_tiktoken_model_name(model)
        encoder = tiktoken.encoding_for_model(tiktoken_model)
        tokenized_messages = encoder.encode(conversation_history)
        
        if len(tokenized_messages) <= max_tokens:
            return conversation_history
        
        truncated_messages = tokenized_messages[-max_tokens:]
        return encoder.decode(truncated_messages)
    except Exception as e:
        logging.error(f"대화 히스토리 자르기 중 오류 발생: {str(e)}")
        words = conversation_history.split()
        return " ".join(words[-max_tokens:])  # fallback: 단어 단위로 자르기

def generate_response(prompt, api_key, model):
    """OpenAI API를 사용하여 응답 생성."""
    max_total_tokens = get_token_limit(model)
    max_prompt_tokens = max_total_tokens // 2  # 프롬프트에 전체 토큰의 절반만 사용
    
    try:
        client = init_openai_client(api_key)
        
        prompt_tokens = calculate_token_count(prompt, model)
        if prompt_tokens > max_prompt_tokens:
            prompt = truncate_conversation_history(prompt, model, max_prompt_tokens)
            prompt_tokens = calculate_token_count(prompt, model)
        
        max_tokens = max_total_tokens - prompt_tokens - 100  # 안전 마진 100 토큰
        
        if max_tokens <= 0:
            st.error("프롬프트가 너무 길어서 응답을 생성할 수 없습니다.")
            return None
        
        logging.debug(f"Sending request to OpenAI API. Model: {model}, Max tokens: {max_tokens}")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"API 호출 중 오류 발생: {str(e)}")
        st.error(f"API 호출 중 오류가 발생했습니다: {str(e)}")
        return None

def generate_website_code(conversation_history, company_name, industry, primary_color, api_key, model):
    """Generate website HTML code based on conversation history."""
    try:  
        max_tokens = get_token_limit(model)
        prompt_template = f"""당신은 숙련된 웹 개발자이자 디자이너입니다.  
        다음 정보를 바탕으로 현대적이고 전문적인 HTML 웹사이트를 만들어주세요:

        회사명: {company_name}
        업종: {industry}
        주 색상: {primary_color}
        대화 내용: {conversation_history}

        이전에 생성된 웹사이트 코드가 있다면, 그것을 기반으로 업데이트하고 개선해주세요.
        새로운 요구사항이 있다면 그에 맞게 웹사이트를 수정하고 확장해주세요.

        다음 사항을 반드시 포함하여 완전한 HTML 코드를 제공해주세요:

        1. 완전한 HTML5 구조 (`<!DOCTYPE html>`, `<html>`, `<head>`, `<body>` 태그 포함)
        2. `<style>` 태그 내에 상세한 CSS 스타일 (Flexbox, Grid, 미디어 쿼리 사용)
        3. 현대적이고 전문적인 디자인 요소 (그라데이션, 그림자 효과, 애니메이션)
        4. 기본 웹사이트 구조 (헤더, 메인 콘텐츠, 푸터)
        5. {primary_color}를 주 색상으로 사용하고 이에 어울리는 보조 색상
        6. Font Awesome 아이콘 사용
        7. JavaScript 기능 (스크롤 애니메이션, 이미지 슬라이더, 햄버거 메뉴)
        8. SEO를 위한 메타 태그와 오픈 그래프 태그
        9. 웹 접근성 고려 (ARIA 속성, 키보드 네비게이션)
        10. Google Fonts 사용 (예: 'Roboto', 'Open Sans', 'Lato')
        11. 최적화된 코드로 페이지 로딩 속도 고려
        12. Bootstrap과 같은 CSS 프레임워크 사용 (선택적)

        각 섹션에 적절한 더미 텍스트와 이미지 플레이스홀더를 포함하여 완성된 웹사이트처럼 보이게 해주세요.
        모든 스타일, 스크립트, 콘텐츠를 포함한 완전한 HTML 코드를 제공해주세요.
        """
  
        # 대화 내용을 토큰 제한에 맞게 조정
        max_conversation_tokens = max_tokens - calculate_token_count(prompt_template.format(conversation=""), model) - 1000  # 여유 공간
        truncated_conversation = truncate_conversation_history(conversation_history, model, max_conversation_tokens)
        
        prompt = prompt_template.format(conversation=truncated_conversation)
        
        logging.info(f"프롬프트 토큰 수: {calculate_token_count(prompt, model)}")
        
        response = generate_response(prompt, api_key, model)
        
        if response:
            logging.info(f"API 응답 길이: {len(response)}")
            return clean_html(response)
            
        return '<!-- 웹사이트 코드를 생성할 수 없습니다 -->'
    except Exception as e:
            logging.error(f"웹사이트 코드 생성 중 오류 발생: {str(e)}")
            st.error(f"웹사이트 코드 생성 중 오류가 발생했습니다: {str(e)}")
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
    
    # 모델 선택 옵션
    model = st.sidebar.selectbox(
        "모델 선택:",
        ("gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k"),
        index=0
    )
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    prompt = st.chat_input("웹사이트에 대한 요구사항을 말씀해주세요:")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = generate_response(prompt, st.session_state.api_key, model)
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # 대화 내용을 바탕으로 웹사이트 코드 생성 또는 업데이트
        conversation_history = "\n".join([m["content"] for m in st.session_state.messages if m["role"] != "system"])
        st.session_state.website_code = generate_website_code(
            conversation_history, 
            st.session_state.company_name, 
            st.session_state.industry, 
            st.session_state.primary_color,
            st.session_state.api_key,
            model
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