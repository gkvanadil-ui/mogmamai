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
st.write("엄마의 따뜻한 말투 그대로, AI가 사진과 글을 완성해 드려요.")

st.divider()

# --- 1. 사진 일괄 AI 지능형 보정 ---
st.header("📸 1. 사진 한 번에 보정하기")
uploaded_files = st.file_uploader("보정할 사진들을 선택하세요 (최대 10장)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

if uploaded_files and api_key:
    if st.button("🚀 모든 사진 AI 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        cols = st.columns(len(uploaded_files))
        for idx, file in enumerate(uploaded_files):
            with st.spinner(f"{idx+1}번 사진 분석 중..."):
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

# --- 2. 엄마 말투 학습 AI 상세페이지 작성 ---
st.header("✍️ 2. 상세페이지 글 만들기")
st.write("빈칸에 단어만 적어보세요. 엄마가 평소 쓰시는 다정한 말투로 바꿔드릴게요!")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 기본 정보")
        name = st.text_input("📦 작품 이름", placeholder="예: 뜨왈 스트링 파우치")
        keys = st.text_area("🔑 핵심 특징/쓰임새", placeholder="예: 가벼운 외출 ok, 파우치로도 좋음, 작지만 수납 잘됨")
        mat = st.text_input("🧵 원단/소재", placeholder="예: 도톰한 린넨, 안감도 20수 린넨")
    with col2:
        st.subheader("🛠️ 상세 정보")
        size = st.text_input("📏 사이즈/색상", placeholder="예: 28*30, 블랙그림은 블랙안감")
        process = st.text_area("🛠️ 제작 포인트", placeholder="예: 바닥을 만들어주어 소지품 넣기 좋음")
        care = st.text_input("💡 세탁/관리", placeholder="예: 찬물 손세탁")

if st.button("🪄 엄마 말투로 글 완성하기"):
    if not api_key:
        st.warning("왼쪽 메뉴에 API 키를 입력해주세요!")
    elif not name:
        st.warning("작품 이름을 입력해주세요!")
    else:
        client = openai.OpenAI(api_key=api_key)
        
        # 엄마의 말투 샘플을 프롬프트에 직접 주입
        prompt = f"""
        당신은 핸드메이드 작가님의 SNS 판매글 작성을 돕는 비서입니다. 
        아래의 [작가님 말투 샘플]을 완벽하게 학습하여 글을 작성하세요.

        [작가님 말투 샘플]
        - 가벼운 외출도 ok👭 가방속에도 쏙하여 때로는 파우치로도 좋아요🌻
        - 도톰한 린넨원단에 빈티지스러우면서도 아름다운 원단으로 만들었어요.
        - 흐물거리지 않고 모양이 잡혀서 좋지요👍 튤립이나 하트 이모지를 적절히 사용함.
        - 과한 수식어보다는 '쓰임새'와 '원단 퀄리티'를 솔직하게 강조함.

        [입력 데이터]
        제품명: {name} / 특징: {keys} / 소재: {mat} / 사이즈: {size} / 제작포인트: {process} / 관리: {care}

        [지시사항]
        1. 한 줄씩 읽기 편하게 줄바꿈을 자주 할 것.
        2. 말투는 샘플처럼 다정하고 경쾌한 '엄마 작가님' 말투로 (~해요, ~이지요, ok👭 등).
        3. 과한 포장이나 아부는 생략하고, 원단의 느낌과 실용성을 담백하게 강조할 것.
        4. 중간중간 🌻, 🌸, 🌷, 👍, 🧡 같은 이모지를 적절히 섞어줄 것.
        5. 구성: [첫인사 및 쓰임새] - [원단과 디자인 설명] - [사이즈 및 디테일] - [안감/색상 안내] - [끝인사]
        """
        
        with st.spinner("엄마의 말투로 예쁘게 글을 다듬고 있어요..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success("✨ 엄마 맞춤형 판매글이 완성되었습니다!")
                st.text_area("결과 (복사해서 사용하세요)", value=response.choices[0].message.content, height=550)
            except Exception as e:
                st.error(f"오류 발생: {e}")
