import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io
import openai
import base64
import json

# 1. 앱 설정
st.set_page_config(page_title="엄마의 AI 명품 비서", layout="wide")

# 사이드바 API 설정
st.sidebar.header("⚙️ AI 설정")
api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")

st.title("🕯️ 엄마작가님을 위한 AI 통합 비서")
st.write("사진 보정부터 상세페이지 작성까지, AI가 엄마의 일을 도와드려요.")

st.divider()

# --- 이미지 분석을 위한 변환 함수 ---
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# --- 1. 사진 일괄 AI 보정 섹션 ---
st.header("📸 1. AI 지능형 일괄 보정")
st.write("여러 장의 사진을 올리면 AI가 각 사진에 맞춰 최적으로 보정합니다.")

uploaded_files = st.file_uploader("사진들을 선택하세요 (최대 10장)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    if not api_key:
        st.info("💡 왼쪽 사이드바에 API 키를 입력하면 AI 보정이 시작됩니다.")
    elif st.button("🚀 모든 사진 AI 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        cols = st.columns(len(uploaded_files))
        
        for idx, file in enumerate(uploaded_files):
            with st.spinner(f"{idx+1}번 사진 분석 중..."):
                img_bytes = file.getvalue()
                base64_image = encode_image(img_bytes)
                
                # AI에게 사진 분석 요청 (GPT-4o 모델 사용)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "이 상품 사진을 분석해서 가장 화사하고 선명하게 보정할 수 있는 밝기(brightness), 채도(color), 선명도(sharpness) 수치를 0.8~1.6 사이로 결정해줘. JSON 형식으로만 답해줘. 예: {'b': 1.2, 'c': 1.1, 's': 1.3}"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ],
                        }
                    ],
                    response_format={ "type": "json_object" }
                )
                
                res = json.loads(response.choices[0].message.content)
                b, c, s = res.get('b', 1.1), res.get('c', 1.1), res.get('s', 1.2)
                
                # 실제 보정 적용
                img = Image.open(io.BytesIO(img_bytes))
                edited = ImageEnhance.Brightness(img).enhance(b)
                edited = ImageEnhance.Color(edited).enhance(c)
                edited = ImageEnhance.Sharpness(edited).enhance(s)
                
                with cols[idx]:
                    st.image(edited, caption=f"AI 보정완료 {idx+1}", use_container_width=True)
                    buf = io.BytesIO()
                    edited.save(buf, format="JPEG", quality=95)
                    st.download_button(f"📥 저장 {idx+1}", buf.getvalue(), f"photo_{idx+1}.jpg")

st.divider()

# --- 2. AI 스마트 상세페이지 작성 섹션 ---
st.header("✍️ 2. AI 스마트 상세페이지 작성")
st.write("키워드만 툭툭 던져주세요. AI가 맞춤법과 문맥을 맞춰 완벽한 글을 씁니다.")

with st.container():
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        name = st.text_input("📦 작품 이름", placeholder="예: 구름 담은 린넨 에코백")
        keys = st.text_area("🔑 핵심 특징/키워드", placeholder="예: 가벼움, 튼튼한 어깨끈, 정성 가득한 자수, 선물용")
        mat = st.text_input("🧵 소재/재질", placeholder="예: 워싱 린넨 100%")
    with col_w2:
        size = st.text_input("📏 크기/사이즈", placeholder="예: 가로 35cm 세로 40cm")
        process = st.text_area("🛠️ 제작 과정", placeholder="예: 원단 세척부터 바느질까지 3일간 정성을 다함")
        care = st.text_input("💡 관리/세탁법", placeholder="예: 찬물 중성세제 손세탁")

if st.button("🪄 AI 작가에게 글쓰기 부탁하기"):
    if not api_key:
        st.warning("API 키를 먼저 입력해주세요.")
    elif name and keys:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        당신은 감성적인 핸드메이드 마켓의 전문 작가입니다. 
        아래 정보를 바탕으로 네이버 스마트스토어 판매글을 작성해주세요.
        
        - 이름: {name}
        - 키워드: {keys}
        - 소재: {mat}
        - 사이즈: {size}
        - 제작과정: {process}
        - 관리법: {care}
        
        [요구사항]
        1. 키워드를 자연스러운 문장으로 풀어서 설명할 것.
        2. 말투는 다정하고 신뢰감 있는 말투로 작성할 것.
        3. 완벽한 맞춤법 검사를 수행하여 오타가 없게 할 것.
        4. [작품 소개], [제작 과정], [소재 및 크기], [관리 방법]으로 분류할 것.
        """
        
        with st.spinner("AI가 정성껏 글을 다듬고 있습니다..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                final_text = response.choices[0].message.content
                st.success("자연스러운 상세페이지 문구가 완성되었습니다!")
                st.text_area("결과 (복사해서 사용하세요)", value=final_text, height=500)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
