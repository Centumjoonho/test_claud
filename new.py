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
        prompt_template = f"""숙련된 웹 개발자이자 디자이너로서, 다음 정보를 바탕으로 현대적이고 전문적인 HTML 웹사이트를 만들어주세요:

        회사명: {company_name}
        업종: {industry}
        주 색상: {primary_color}

        완전한 HTML5 구조의 단일 페이지 웹사이트를 생성해주세요. 다음 요구사항을 반드시 포함하여 구현해주세요:

        1. 레이아웃 구조:
        a. 반응형 네비게이션 바: 로고, 메뉴 항목 (Home, Products, About Us, Blog, Contact)
        b. 히어로 섹션: 전체 화면 배경 이미지, 회사 슬로건, 눈에 띄는 CTA 버튼
        c. 제품/서비스 하이라이트: 3-4개의 주요 제품/서비스를 카드 형식으로 표시
        d. 회사 소개: 이미지와 텍스트를 사용한 간략한 소개
        e. 고객 후기 또는 파트너사 로고 섹션
        f. 뉴스레터 구독 양식
        g. 푸터: 회사 정보, 빠른 링크, 소셜 미디어 아이콘

        2. 이미지 사용 및 콘텐츠:
        a. 히어로 섹션: 
            - 배경: {industry}를 대표하는 고품질 이미지 사용
            - 슬로건: "{company_name} - {industry}의 혁신적인 솔루션" (1-2문장의 간단한 회사 소개 포함)
        b. 제품/서비스 카드: 
            - 각 제품/서비스를 대표하는 아이콘 또는 이미지
            - 제품/서비스명과 2-3문장의 설명
            - 예시: "에코 스마트홈 시스템", "태양광 충전 기기", "에너지 효율 컨설팅" 등 {industry}에 적합한 제품/서비스
        c. 회사 소개 섹션: 
            - 팀워크 또는 회사 가치를 나타내는 이미지
            - 회사의 미션, 비전, 핵심 가치에 대한 3-4문장 설명
        d. 고객 후기 섹션: 
            - 2-3개의 짧은 고객 후기 (각 1-2문장)
            - 고객 프로필 이미지 또는 회사 로고
        e. 블로그/뉴스 섹션: 
            - 3-4개의 최신 글 제목과 요약 (각 1-2문장)
            - 관련 썸네일 이미지

        모든 이미지에 설명적이고 의미 있는 alt 텍스트를 포함하세요. 이미지 최적화를 위해 적절한 크기와 형식(WebP)을 사용하고, lazy loading을 적용하세요.

        3. 디자인 요소:
        a. {primary_color}를 주 색상으로 사용하고, 이에 어울리는 보조 색상 팔레트 생성
        b. 모던하고 깔끔한 디자인, 충분한 여백 사용
        c. 그라데이션 배경을 히어로 섹션과 CTA 버튼에 적용
        d. 그림자 효과를 카드와 버튼에 사용하여 깊이감 부여
        e. 호버 애니메이션을 버튼과 카드에 적용
        f. Font Awesome 아이콘을 내비게이션, 제품 카드, 소셜 미디어 링크에 사용

        4. 타이포그래피:
        a. Google Fonts에서 'Roboto'를 제목용, 'Open Sans'를 본문용으로 사용
        b. 제목은 굵게, 본문은 가독성 좋게 설정

        5. 반응형 디자인:
        a. 모바일, 태블릿, 데스크탑 버전 구현
        b. 모바일에서는 햄버거 메뉴 사용

        6. 인터랙티브 요소:
        a. 스크롤 시 요소들이 부드럽게 나타나는 애니메이션 효과
        b. 제품/서비스 섹션에 탭 또는 아코디언 메뉴 구현
        c. 고객 후기를 위한 캐러셀 슬라이더

        7. 성능 및 접근성:
        a. 이미지에 lazy loading 적용
        b. ARIA 레이블과 역할을 적절히 사용 (예: 버튼, 메뉴 항목)
        c. 키보드 네비게이션 지원 (탭 순서 최적화)

        8. SEO 최적화:
        a. 적절한 메타 태그 (title, description) 사용
        b. Open Graph 태그 포함
        c. 시맨틱 HTML 구조 사용 (header, nav, main, section, footer 등)

        9. 추가 기능:
        a. 쿠키 동의 배너
        b. 간단한 연락처 양식
        c. 블로그 포스트 미리보기 섹션

        10. 콘텐츠 일관성:
            a. {industry}에 적합한 전문적이고 신뢰할 수 있는 톤앤보이스 유지
            b. 업계 관련 용어를 적절히 사용하되, 일반 사용자도 이해할 수 있도록 설명

        모든 스타일은 <style> 태그 내에, JavaScript는 <script> 태그 내에 포함해주세요. 외부 리소스는 CDN을 통해 불러와주세요 (예: Bootstrap, Font Awesome). 최종 결과물은 단일 HTML 파일이어야 합니다.

        페이지 로딩 속도를 고려하여 코드를 최적화하고, 웹 표준과 크로스 브라우저 호환성을 준수해주세요. {company_name}과 {industry}에 적합한 실제적인 콘텐츠를 생성하여 사용하세요. 필요한 경우, 이미지는 관련성 있는 무료 스톡 이미지 사이트의 URL을 사용하여 제안해주세요.

        최종 결과물에는 {company_name}의 특성을 반영한 완전한 웹사이트 코드가 포함되어야 하며, 실제 구현 시 쉽게 customizing할 수 있도록 해주세요.
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