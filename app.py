import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="centered")

# --- CSS: 다크모드 대응 및 시인성 ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { color: inherit; }
    h1, h2, h3 { color: #D4A373 !important; font-weight: bold !important; }
    p, li, label, .stMarkdown { font-size: 18px !important; line-height: 1.6; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: #7d6e63; color: white !important;
        font-weight: bold; font-size: 18px !important;
        border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .stTextInput input, .stTextArea textarea { font-size: 16px !important; }
    hr { border-top: 2px solid #7d6e63; opacity: 0.3; }
    </style>
    """, unsafe_allow_html=True)

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

st.title("🕯️ 모그(Mog) 작가 전용 비서")
st.write("<p style='text-align: center;'>작가님의 따뜻한 진심이 글에 그대로 담기도록 도와드려요🌸</p>", unsafe_allow_html=True)

# --- [1단계: 공통 작품 정보 입력] ---
st.header("1️⃣ 작품 정보 입력")
with st.expander("📝 이곳을 터치해서 내용을 채워주세요", expanded=True):
    name = st.text_input("📦 작품 이름", placeholder="예: 빈티지 튤립 뜨개 파우치")
    col1, col2 = st.columns(2)
    with col1:
        mat = st.text_input("🧵 소재", placeholder="예: 코튼 100%")
        size = st.text_input("📏 크기", placeholder="예: 가로 20cm 세로 15cm")
    with col2:
        period = st.text_input("⏳ 제작 기간", placeholder="예: 주문 후 3일")
        care = st.text_input("💡 세탁법", placeholder="예: 미온수 손세탁")
    keys = st.text_area("🔑 작품 특징", placeholder="예: 색감이 화사해서 포인트 아이템으로 좋아요.")
    process = st.text_area("🛠️ 제작 포인트", placeholder="예: 안감까지 꼼꼼히 박음질했습니다.")

st.divider()

# --- [2단계: 작업실 선택] ---
st.header("2️⃣ 작업실 선택")
tabs = st.tabs(["✍️ 글쓰기", "📸 사진보정", "💡 홍보 꿀팁"])

# --- AI 텍스트 처리 함수 (어투 프롬프트 복구) ---
def process_ai_text(full_prompt):
    if not api_key: return None
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
        # 볼드체(**) 제거 및 정제
        return response.choices[0].message.content.replace("**", "").strip()
    except: return None

# --- [Tab 1: 글쓰기] ---
with tabs[0]:
    if 'generated_texts' not in st.session_state:
        st.session_state.generated_texts = {"인스타그램": "", "아이디어스": "", "스마트스토어": ""}
    
    st.write("💡 아래 버튼을 누르면 작가님 말투로 글이 써집니다.")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("📸 인스타"): platform = "인스타그램"
    with c2: 
        if st.button("🎨 아디스"): platform = "아이디어스"
    with c3: 
        if st.button("🛍️ 스토어"): platform = "스마트스토어"

    if 'platform' in locals():
        # 복구된 상세 지침
        platform_guides = {
            "인스타그램": "해시태그 포함, 계절 인사와 함께하는 감성 일기 스타일.",
            "아이디어스": "짧은 문장 위주, 줄바꿈 매우 자주, 꽃과 하트 이모지를 풍성하게 사용.",
            "스마트스토어": "구분선(⸻)을 활용한 가독성 강조, 카테고리별 정보 정리, 마지막에 관련 태그 포함."
        }
        
        # 작가님 전용 어투 프롬프트 복구
        full_prompt = f"""
        당신은 핸드메이드 브랜드 '모그(Mog)'를 운영하는 작가입니다. 
        [{platform}] 에 올릴 상세 판매글을 작성하세요.

        [작가님 전용 말투 지침]
        - 반드시 다정한 엄마/작가 어투를 사용하세요 (~이지요^^, ~해요, ~좋아요, ~보내드려요).
        - 절대로 별표(*)나 볼드체 기호를 사용하지 마세요.
        - 꽃(🌸, 🌻), 구름(☁️), 반짝이(✨) 등 따뜻한 이모지를 적절히 섞어주세요.

        [플랫폼별 지침]
        {platform_guides[platform]}

        [작품 정보]
        이름: {name} / 특징: {keys} / 소재: {mat} / 사이즈: {size} / 제작: {process} / 관리: {care} / 기간: {period}
        """
        st.session_state.generated_texts[platform] = process_ai_text(full_prompt)

    for p in ["인스타그램", "아이디어스", "스마트스토어"]:
        if st.session_state.generated_texts.get(p):
            st.subheader(f"✅ {p} 결과")
            txt = st.text_area(f"{p} (꾹 눌러 복사)", value=st.session_state.generated_texts[p], height=350, key=f"area_{p}")
            with st.expander("✨ 여기서 글을 조금 더 고치고 싶다면?"):
                feedback = st.text_input("수정 요청", placeholder="예: 원단의 부드러움을 더 강조해줘", key=f"f_{p}")
                if st.button("♻️ 고쳐쓰기 실행", key=f"b_{p}"):
                    refine_prompt = f"기존에 작성한 글: {txt}\n\n작가님의 수정요청: {feedback}\n\n위 요청을 반영하되, 모그 작가님 특유의 다정한 말투(~이지요^^)는 꼭 유지해서 다시 써주세요."
                    st.session_state.generated_texts[p] = process_ai_text(refine_prompt)
                    st.rerun()

# --- [Tab 2: 사진보정] ---
with tabs[1]:
    st.subheader("📸 사진 자동 보정")
    uploaded_files = st.file_uploader("갤러리에서 사진 선택", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files and api_key and st.button("🚀 사진 화사하게 보정 시작"):
        def encode_image(image_bytes): return base64.b64encode(image_bytes).decode('utf-8')
        client = openai.OpenAI(api_key=api_key)
        for idx, file in enumerate(uploaded_files):
            img_bytes = file.getvalue()
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [{"type": "text", "text": "화사한 보정 수치 JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}]}],
                    response_format={ "type": "json_object" }
                )
                res = json.loads(response.choices[0].message.content)
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageEnhance.Brightness(img).enhance(res.get('b', 1.15))
                img = ImageEnhance.Color(img).enhance(res.get('c', 1.1))
                st.image(img, caption=f"보정 완료 {idx+1}")
                buf = io.BytesIO(); img.save(buf, format="JPEG")
                st.download_button(f"📥 사진 {idx+1} 저장", buf.getvalue(), f"img_{idx+1}.jpg")
            except: st.error("보정 실패")

# --- [Tab 3: 홍보 꿀팁] ---
with tabs[2]:
    st.subheader("🎨 상세페이지 기획 (캔바)")
    st.link_button("✨ 캔바(Canva) 앱 열기", "https://www.canva.com/templates/?query=상세페이지")
    if st.button("🪄 상세페이지 기획안 만들기"):
        if not name: st.warning("정보를 먼저 입력해 주셔요🌸")
        else:
            client = openai.OpenAI(api_key=api_key)
            prompt = f"모그 작가로서 {name} 상세페이지 5장 기획 JSON."
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type":"json_object"})
            data = json.loads(res.choices[0].message.content)
            df = pd.DataFrame(data[list(data.keys())[0]])
            for index, row in df.iterrows():
                with st.expander(f"📍 {row['순서']}번 화면 (꾹 눌러 복사)"):
                    st.write(f"**제목:** {row['메인문구']}\n\n**설명:** {row['설명']}")
                    st.caption(f"📸 촬영 팁: {row['사진구도']}")
    st.divider()
    st.subheader("🎥 영상 제작 (에픽)")
    with st.expander("📺 에픽(EPIK) 사용 순서 보기"):
        st.info("1. 에픽 앱 실행 -> 2. [템플릿]에서 '감성' 검색 -> 3. 사진 넣기 -> 4. 저장! 🌸")
