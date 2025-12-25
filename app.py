import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io
import openai
import base64
import json

# 1. 앱 페이지 설정
st.set_page_config(page_title="엄마의 AI 명품 비서", layout="wide")

# 사이드바 API 설정
st.sidebar.header("⚙️ AI 설정")
api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")

st.title("🕯️ 엄마작가님을 위한 AI 통합 비서")
st.write("사진은 화사하게! 글은 깔끔하고 밝게! AI가 엄마의 작업을 도와드려요.")

st.divider()

# --- 1. 사진 일괄 AI 보정 ---
st.header("📸 1. 사진 한 번에 보정하기")
uploaded_files = st.file_uploader("보정할 사진들을 선택하세요 (최대 10장)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

if uploaded_files and api_key:
    if st.button("🚀 모든 사진 AI 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        cols = st.columns(len(uploaded_files))
        for idx, file in enumerate(uploaded_files):
            with st.spinner(f"{idx+1}번 분석 중..."):
                img_bytes = file.getvalue()
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [{"type": "text", "text": "이 사진을 분석해서 화사하고 선명하게 보정할 b, c, s 수치를 0.8~1.6 사이 JSON으로 줘. 예: {'b': 1.2, 'c': 1.1, 's': 1.3}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}]}],
                    response_format={ "type": "json_object" }
                )
                res = json.loads(response.choices[0].message.content)
                img = Image.open(io.BytesIO(img_bytes))
                edited = ImageEnhance.Brightness(img).enhance(res.get('b', 1.1))
                edited = ImageEnhance.Color(edited).enhance(res.get('c', 1.1))
                edited = ImageEnhance.Sharpness(edited).enhance(res.get('s', 1.2))
                with cols[idx]:
                    st.image(edited, use_container_width=True)
                    buf = io.BytesIO()
                    edited.save(buf, format="JPEG")
                    st.download_button(f"📥 저장 {idx+1}", buf.getvalue(), f"img_{idx+1}.jpg")

st.divider()

# --- 2. AI 문장 보완 상세페이지 (가독성 & 캐주얼 톤) ---
st.header("✍️ 2. 상세페이지 글 만들기")
st.write("빈칸에 단어만 적어보세요. 읽기 편하고 기분 좋은 문장으로 만들어드릴게요!")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 기본 정보")
        name = st.text_input("📦 작품 이름", placeholder="예: 린넨 앞치마")
        keys = st.text_area("🔑 핵심 특징/키워드", placeholder="예: 가볍다, 주머니 큼, 색이 예쁨")
        mat = st.text_input("🧵 소재/재질", placeholder="예: 워싱 린넨 100%")
    with col2:
        st.subheader("🛠️ 상세 정보")
        size = st.text_input("📏 크기/사이즈", placeholder="예: 프리사이즈")
        process = st.text_area("🛠️ 제작 과정", placeholder="예: 직접 재단하고 봉제함")
        care = st.text_input("💡 관리/세탁법", placeholder="예: 울코스 세탁기 가능")

if st.button("🪄 AI에게 글쓰기 부탁하기"):
    if not api_key:
        st.warning("왼쪽 메뉴에 API 키를 입력해주세요!")
    elif not name:
        st.warning("작품 이름을 입력해주세요!")
    else:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        당신은 핸드메이드 마켓의 센스 있는 카피라이터입니다. 
        작가가 입력한 단어들을 바탕으로 읽기 편하고 기분 좋은 판매글을 작성하세요.
        
        [데이터]
        작품명: {name} / 특징: {keys} / 소재: {mat} / 사이즈: {size} / 과정: {process} / 관리: {care}
        
        [지시사항]
        1. 말투: 아부하는 느낌의 과한 포장은 금지. 밝고 경쾌한 '캐주얼 톤'으로 작성. (~해요, ~입니다 등)
        2. 가독성: 문장을 짧고 간결하게 끊어 쓰고, 불필요한 미사여구는 삭제할 것.
        3. 보완: 엄마가 쓴 단어를 문맥에 맞게 자연스럽게 풀어서 쓸 것.
        4. 구성: [인사말] - [작품 포인트(간결하게)] - [상세 정보 요약] - [세탁 및 관리] - [맺음말]
        5. 맞춤법을 완벽하게 교정할 것.
        """
        
        with st.spinner("AI가 깔끔하게 글을 정리 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success("✨ 읽기 좋은 판매글이 완성되었습니다!")
                st.text_area("완성 결과", value=response.choices[0].message.content, height=500)
            except Exception as e:
                st.error(f"오류 발생: {e}")
