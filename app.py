import streamlit as st
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 앱 페이지 설정
st.set_page_config(page_title="핸드메이드 잡화점 모그 AI 비서", layout="wide")

# 사이드바 API 설정
st.sidebar.header("⚙️ AI 설정")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

st.title("🕯️ 작가 '모그(Mog)' 전용 AI 통합 비서")
st.write("'세상에 단 하나뿐인 온기'를 전하는 모그 작가님의 철학을 문장에 담아드립니다.")

st.divider()

# --- 1. 사진 일괄 AI 지능형 보정 (기능 유지) ---
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
                    messages=[{"role": "user", "content": [{"type": "text", "text": "화사하고 선명한 보정 수치 JSON."},
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

# --- 2. 매체별 맞춤형 상세 글 생성 섹션 ---
st.header("✍️ 2. 모그(Mog) 작가님의 진심이 담긴 글 작성")

col_in1, col_in2 = st.columns(2)
with col_in1:
    name = st.text_input("📦 작품 이름", placeholder="예: 앤과 숲속 푸우 패치워크 보스턴백")
    keys = st.text_area("🔑 핵심 특징/이야기", placeholder="예: 여행을 꿈꾸며 만든 야무진 백, 세상에 단 하나뿐인 패치워크")
    mat = st.text_input("🧵 원단/소재", placeholder="예: 유럽 햄프리넨, 오일 워싱 원단, 가죽 손잡이")
with col_in2:
    size = st.text_input("📏 사이즈/수납", placeholder="예: 높이 31 폭 42, 노트북 수납 가능, 뒷포켓 있음")
    process = st.text_area("🛠️ 제작 포인트", placeholder="예: 손바느질 스티치, 리넨 파우치 증정, 모그 스타일 장식")
    care = st.text_input("💡 배송/포장", placeholder="예: 별도 요청 없어도 선물용으로 정성껏 포장")

tab1, tab2, tab3 = st.tabs(["📸 인스타그램", "🎨 아이디어스", "🛍️ 스마트스토어"])

def generate_text(platform_type, specific_prompt):
    if not api_key:
        st.warning("API 키를 넣어주세요.") return
    if not name:
        st.warning("이름을 입력해주세요.") return

    client = openai.OpenAI(api_key=api_key)
    full_prompt = f"""
    당신은 브랜드 '모그(Mog)'의 전담 카피라이터입니다. 
    아래 [모그 작가님의 작업 지침]을 바탕으로 [{platform_type}] 전용 판매글을 작성하세요.

    [모그 작가님의 작업 지침]
    1. 희소성 강조: "같은 디자인은 다시 만들지 않습니다. 세상에 단 하나뿐인 작품입니다."
    2. 손맛의 미학: "일정하지 않은 스티치와 바느질 자국은 기계가 흉내 낼 수 없는 손작업의 온기입니다."
    3. 실용적인 다정함: "뒷포켓의 편리함, 안감 처리된 튼튼한 파우치, 야무진 수납" 등 사용자를 배려한 포인트를 언급하세요.
    4. 포장: "별도 요청 없어도 소중한 친구에게 선물하는 마음으로 정성껏 포장합니다."
    5. 어투: 밝고 산뜻하며, "~이지요^^", "~만들어봤어요" 처럼 친근한 어투를 사용하세요.

    [데이터 정보]
    제품명: {name} / 특징: {keys} / 소재: {mat} / 사이즈: {size} / 제작진심: {process} / 주의사항: {care}

    {specific_prompt}
    """
    
    with st.spinner(f"작가 '모그'의 진심을 담아 작성 중..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": full_prompt}]
        )
        return response.choices[0].message.content

with tab1:
    st.subheader("인스타그램: 감성 소통 스타일")
    if st.button("🪄 인스타용 글 만들기"):
        instr = """
        - 말투: 작가님의 샘플처럼 문장 중간에 #해시태그 사용. "~이지요^^", "도통 오지 않는 가을을 기다리며ㅠㅠ" 같은 솔직한 감성.
        - 내용: 여행을 꿈꾸는 마음, 혹은 작업실의 일상 이야기로 시작할 것.
        - 구성: 감성 도입 -> 작품의 유니크함(세상에 하나뿐!) 강조 -> 상세 사이즈 -> 하단 해시태그 모음.
        """
        result = generate_text("인스타그램", instr)
        st.text_area("인스타 결과", value=result, height=550)

with tab2:
    st.subheader("아이디어스: 작가의 정성 스타일")
    if st.button("🪄 아이디어스용 글 만들기"):
        instr = """
        - 말투: 작가님의 샘플 어투 "가벼운 외출도 ok👭", "모양이 잡혀서 좋지요👍" 적극 활용.
        - 내용: 조각천을 잇는 과정(패치워크)의 즐거움과 원단의 퀄리티(유럽 리넨 등)를 상세히 설명.
        - 구성: 작가 인사(모그의 작업 방식 소개) -> 패치워크와 장식 이야기 -> 수납과 실용성(안감, 파우치) -> 선물 포장 안내.
        - 줄바꿈을 자주 하고 꽃(🌸), 하트(🧡) 이모지를 섞어줄 것.
        """
        result = generate_text("아이디어스", instr)
        st.text_area("아이디어스 결과", value=result, height=600)

with tab3:
    st.subheader("스마트스토어: 친절한 상세 가이드")
    if st.button("🪄 스마트스토어용 글 만들기"):
        instr = """
        - 말투: 체계적이면서도 다정함이 느껴지는 안내형.
        - 구성: 
          1. 🌸 제목 및 한 줄 요약 (사탕 같은/야무진/단 하나뿐인 등의 표현)
          2. ⸻ (구분선)
          3. 🧵 디자인 & 소재 (조각천 패치워크, 리넨, 가죽 스트랩의 조화)
          4. 🛠️ 핸드메이드 감성 디테일 (손바느질 자국, 뜨개 모티브 장식)
          5. 📏 사이즈 가이드 (수납 예시: 노트북 수납 가능 등)
          6. 🧼 관리 방법 및 주의사항 (리넨 특성 설명)
          7. 🎁 선물 포장 서비스 안내 (모그의 마음)
        - 특징: 불렛 포인트(•)를 사용하되, 문장을 짧지 않게 친절하게 풀어서 쓸 것.
        """
        result = generate_text("스마트스토어", instr)
        st.text_area("스토어 결과", value=result, height=700)
