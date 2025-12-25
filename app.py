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

st.title("🕯️ 엄마작가님 전용 AI 통합 비서")
st.write("엄마의 따뜻한 진심이 매체별로 가장 잘 전달되도록 AI가 글을 다듬어드려요.")

st.divider()

# --- 1. 사진 일괄 AI 지능형 보정 ---
st.header("📸 1. 사진 한 번에 보정하기")
uploaded_files = st.file_uploader("보정할 사진들을 선택하세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

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
                    messages=[{"role": "user", "content": [{"type": "text", "text": "화사하고 선명한 보정 수치 JSON으로 줘. 예: {'b': 1.2, 'c': 1.1, 's': 1.3}"},
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

# --- 2. 매체별 맞춤형 상세페이지 작성 ---
st.header("✍️ 2. 매체별 맞춤 글 만들기")

# 입력 영역
col_in1, col_in2 = st.columns(2)
with col_in1:
    name = st.text_input("📦 작품 이름", placeholder="예: 토끼 자수 브로치")
    keys = st.text_area("🔑 핵심 특징/감성", placeholder="예: 가을을 기다리며 만든 블라우스, 내 몸에 감기는 느낌")
    mat = st.text_input("🧵 원단/소재", placeholder="예: 수입 리넨, 텐셜레이온 합사")
with col_in2:
    size = st.text_input("📏 사이즈/디테일", placeholder="예: 5.5*6.5cm, 손으로 만들어 조금씩 달라요")
    process = st.text_area("🛠️ 제작 포인트/진심", placeholder="예: 하나하나에 들어간 정성의 총량은 일정하답니다")
    care = st.text_input("💡 주의사항", placeholder="예: 리넨 특성상 표면 돌출은 불량이 아닙니다")

# 매체별 탭 생성
tab1, tab2, tab3 = st.tabs(["📸 인스타그램", "🎨 아이디어스", "🛍️ 스마트스토어"])

def generate_text(platform_type, specific_prompt):
    if not api_key:
        st.warning("사이드바에 API 키를 입력해주세요.")
        return
    if not name:
        st.warning("작품 이름을 입력해주세요.")
        return

    client = openai.OpenAI(api_key=api_key)
    
    full_prompt = f"""
    당신은 핸드메이드 작가님의 판매를 돕는 전문 카피라이터입니다. 
    엄마 작가님의 진심과 정성이 전달되도록 [{platform_type}] 전용 판매글을 작성하세요.

    [공통 지침]
    - 과한 미사여구와 아부성 표현은 자제할 것.
    - 문단을 가독성 좋게 나누고 짧게 끊어서 작성할 것.
    - 판매자의 진심이 느껴지는 따뜻하고 다정한 어투를 사용할 것.
    - 맞춤법을 완벽하게 검수할 것.

    [데이터 정보]
    작품명: {name} / 특징: {keys} / 소재: {mat} / 사이즈: {size} / 제작진심: {process} / 주의사항: {care}

    {specific_prompt}
    """
    
    with st.spinner(f"{platform_type} 스타일에 맞춰 정성을 담는 중..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": full_prompt}]
        )
        return response.choices[0].message.content

with tab1:
    st.subheader("인스타그램: 감성 & 소통 스타일")
    if st.button("🪄 인스타용 글 만들기"):
        instr = """
        - 어투: 주신 샘플처럼 문장 사이사이에 #해시태그를 섞고, '~이지요?', '~했어요ㅠㅠ', '^^' 같은 친근한 표현 사용.
        - 구성: 감성적인 도입부(날씨나 기분 등) -> 작품의 촉감과 느낌 설명 -> 상세 사이즈와 정보 -> 하단 해시태그 모음.
        - 포인트: '토끼같은..' 같은 따뜻한 문구와 이모지를 활용해 작가님의 개성을 드러낼 것.
        """
        result = generate_text("인스타그램", instr)
        st.text_area("인스타 결과", value=result, height=500)

with tab2:
    st.subheader("아이디어스: 작가 스토리 스타일")
    if st.button("🪄 아이디어스용 글 만들기"):
        instr = """
        - 어투: 기존 샘플처럼 '다정하고 정중한' 어투. 작품의 쓰임새와 가치를 강조.
        - 구성: 작품을 만들게 된 동기 -> 원단의 특별함 -> 사용자를 향한 배려 -> 정성스러운 마무리 멘트.
        - 포인트: "가벼운 외출도 ok👭", "모양이 잡혀서 좋지요👍" 처럼 작가의 경험이 담긴 표현 사용.
        """
        result = generate_text("아이디어스", instr)
        st.text_area("아이디어스 결과", value=result, height=500)

with tab3:
    st.subheader("스마트스토어: 정보 전달 & 신뢰 스타일")
    if st.button("🪄 스마트스토어용 글 만들기"):
        instr = """
        - 어투: 군더더기 없이 깔끔하고 신뢰감을 주는 어투. 
        - 구성: [상품 요약] -> [상세 특징] -> [소재 및 규격] -> [세탁 및 관리안내].
        - 포인트: 불렛 포인트(•)를 적극 활용하여 구매자가 정보를 즉시 확인할 수 있도록 가독성 극대화. 
        - 주의사항(리넨 특성 등)을 정확하게 전달하여 신뢰를 높일 것.
        """
        result = generate_text("스마트스토어", instr)
        st.text_area("스마트스토어 결과", value=result, height=500)
