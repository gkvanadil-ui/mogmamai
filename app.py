import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io
import openai
import base64
import json

# 1. 앱 페이지 기본 설정
st.set_page_config(page_title="엄마의 AI 명품 비서", layout="wide")

# 사이드바에서 API 키 관리
st.sidebar.header("⚙️ AI 설정")
api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")
st.sidebar.info("💡 API 키가 있어야 AI 보정과 글쓰기 보완 기능이 작동합니다.")

st.title("🕯️ 엄마작가님을 위한 AI 통합 비서")
st.write("사진은 AI가 직접 보고 보정하며, 짧은 메모는 풍성한 판매글로 바꿔드립니다.")

st.divider()

# --- 이미지 처리를 위한 헬퍼 함수 ---
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# --- 1. 사진 일괄 AI 지능형 보정 ---
st.header("📸 1. AI 지능형 사진 보정")
st.write("여러 장의 사진을 올리면 AI가 사진마다 최적의 화사함을 찾아냅니다.")

uploaded_files = st.file_uploader("보정할 사진들을 선택하세요 (최대 10장)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    if not api_key:
        st.warning("왼쪽 메뉴에 API 키를 먼저 입력해주세요.")
    elif st.button("🚀 모든 사진 AI 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        cols = st.columns(len(uploaded_files))
        
        for idx, file in enumerate(uploaded_files):
            with st.spinner(f"{idx+1}번 사진 분석 중..."):
                img_bytes = file.getvalue()
                base64_image = encode_image(img_bytes)
                
                # AI(GPT-4o)가 사진을 보고 보정 수치 결정
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "이 사진을 분석해서 가장 화사하고 고급스럽게 보정할 밝기(b), 채도(c), 선명도(s) 수치를 0.8~1.6 사이로 결정해줘. JSON으로만 답해. 예: {'b': 1.2, 'c': 1.1, 's': 1.3}"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ],
                        }
                    ],
                    response_format={ "type": "json_object" }
                )
                
                res = json.loads(response.choices[0].message.content)
                b, c, s = res.get('b', 1.1), res.get('c', 1.1), res.get('s', 1.2)
                
                # 결정된 수치로 실제 이미지 보정
                img = Image.open(io.BytesIO(img_bytes))
                edited = ImageEnhance.Brightness(img).enhance(b)
                edited = ImageEnhance.Color(edited).enhance(c)
                edited = ImageEnhance.Sharpness(edited).enhance(s)
                
                with cols[idx]:
                    st.image(edited, caption=f"AI 보정 완료", use_container_width=True)
                    buf = io.BytesIO()
                    edited.save(buf, format="JPEG", quality=95)
                    st.download_button(f"📥 저장 {idx+1}", buf.getvalue(), f"photo_{idx+1}.jpg")

st.divider()

# --- 2. AI 문장 보완 상세페이지 작성 ---
st.header("✍️ 2. 상세페이지 내용 채우기")
st.write("각 칸에 핵심 단어만 짧게 적어보세요. AI가 문장을 자연스럽게 보완해드립니다.")

with st.container():
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        name = st.text_input("📦 작품 이름", placeholder="예: 린넨 에코백")
        keys = st.text_area("🔑 핵심 특징/키워드", placeholder="예: 가볍다, 수납이 좋다, 디자인이 깔끔하다")
        mat = st.text_input("🧵 소재/재질", placeholder="예: 워싱 린넨")
    with col_w2:
        size = st.text_input("📏 크기/사이즈", placeholder="예: 가로 30 세로 20")
        process = st.text_area("🛠️ 제작 과정", placeholder="예: 하나하나 손바느질로 꼼꼼하게 만듦")
        care = st.text_input("💡 관리/세탁법", placeholder="예: 찬물 손세탁")

if st.button("🪄 AI에게 문장 보완 및 글쓰기 요청"):
    if not api_key:
        st.warning("API 키를 먼저 입력해주세요.")
    elif not name:
        st.warning("작품 이름을 입력해주세요.")
    else:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        당신은 감성 핸드메이드 마켓의 전문 카피라이터입니다. 
        작가가 입력한 짧은 메모들을 바탕으로, 아주 자연스럽고 풍성한 판매글을 작성하세요.
        
        작품명: {name}
        특징: {keys}
        소재: {mat}
        사이즈: {size}
        제작과정: {process}
        관리법: {care}
        
        [지시사항]
        1. 엄마 작가가 짧게 쓴 메모를 AI가 문맥에 맞게 풍성한 문장으로 보완할 것.
        2. 말투는 1인칭 시점에서 다정하고 신뢰감 있게 작성할 것.
        3. 맞춤법과 띄어쓰기를 완벽하게 교정할 것.
        4. 구성: [인사말] - [작품의 매력(특징 보완)] - [상세 정보(소재, 크기, 과정)] - [관리 방법] - [맺음말]
        """
        
        with st.spinner("AI 작가가 문장을 다듬고 맞춤법을 검토하는 중..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", # 더 정교한 문장 생성을 위해 4o 사용
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success("✨ 판매글이 예쁘게 완성되었습니다!")
                st.text_area("결과 (복사해서 바로 사용하세요)", value=response.choices[0].message.content, height=500)
            except Exception as e:
                st.error(f"오류 발생: {e}")
