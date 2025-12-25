import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="centered")

# --- CSS: 버튼 및 가독성 디자인 ---
st.markdown("""
    <style>
    .main { background-color: #fdfbf7; }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #7d6e63;
        color: white;
        font-weight: bold;
        font-size: 18px !important;
        margin-bottom: 10px;
    }
    .stDownloadButton>button {
        width: 100%;
        background-color: #ffffff;
        color: #7d6e63;
        border: 1px solid #7d6e63;
        font-weight: bold;
    }
    h1 { color: #5d524a; font-size: 26px !important; text-align: center; }
    h2 { color: #5d524a; font-size: 20px !important; border-bottom: 2px solid #e0d7cf; padding-bottom: 8px; margin-top: 20px; }
    p, li { font-size: 16px !important; line-height: 1.5; }
    .stExpander { border: 1px solid #e0d7cf; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

st.title("🕯️ 모그(Mog) 작가 전용 비서")
st.write("<p style='text-align: center; color: #8e7f74;'>정성 담긴 작품을 더 빛나게 도와드려요🌸</p>", unsafe_allow_html=True)

# --- [1단계: 작품 정보 입력] ---
st.header("1️⃣ 작품 정보 입력")
with st.expander("여기를 눌러서 정보를 적어주세요", expanded=True):
    name = st.text_input("📦 작품 이름", placeholder="예: 뜨왈 스트링 파우치")
    col1, col2 = st.columns(2)
    with col1:
        mat = st.text_input("🧵 원단/소재", placeholder="예: 도톰한 린넨")
        size = st.text_input("📏 사이즈", placeholder="예: 28*30")
    with col2:
        period = st.text_input("⏳ 제작 기간", placeholder="예: 평일 기준 3~5일")
        care = st.text_input("💡 관리 방법", placeholder="예: 부분 손세탁")
    keys = st.text_area("🔑 작품 특징", placeholder="예: 가방 속에 쏙 들어가는 크기예요.")
    process = st.text_area("🛠️ 제작 포인트", placeholder="예: 안감도 20수 린넨이라 모양이 잘 잡혀요.")

st.divider()

# --- [2단계: 작업 선택] ---
st.header("2️⃣ 필요한 작업 선택")
tabs = st.tabs(["✍️ 판매글 쓰기", "🎨 디자인 작업실 (사진/캔바/영상)"])

# --- [AI 텍스트 처리 함수] ---
def process_ai_text(full_prompt):
    if not api_key: return None
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
        return response.choices[0].message.content.replace("**", "").strip()
    except: return None

# --- [Tab 1: 판매글 쓰기] ---
with tabs[0]:
    if 'generated_texts' not in st.session_state:
        st.session_state.generated_texts = {"인스타그램": "", "아이디어스": "", "스마트스토어": ""}
    
    st.write("💡 아래 버튼을 누르면 작가님 말투로 글이 작성됩니다.")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("📸 인스타"): platform = "인스타그램"
    with c2: 
        if st.button("🎨 아디스"): platform = "아이디어스"
    with c3: 
        if st.button("🛍️ 스토어"): platform = "스마트스토어"

    if 'platform' in locals():
        prompt_detail = "인스타그램: 해시태그/감성일기, 아이디어스: 줄바꿈/꽃이모지, 스마트스토어: 구분선/정보정리"
        full_prompt = f"모그 작가 말투(~이지요^^)로 [{platform}] 글 작성. 지침: {prompt_detail} 이름:{name}, 특징:{keys}, 소재:{mat}, 사이즈:{size}, 제작:{process}, 관리:{care}, 기간:{period}."
        st.session_state.generated_texts[platform] = process_ai_text(full_prompt)

    for p in ["인스타그램", "아이디어스", "스마트스토어"]:
        if st.session_state.generated_texts.get(p):
            st.subheader(f"✅ {p} 결과")
            txt = st.text_area(f"{p} (꾹 눌러 복사)", value=st.session_state.generated_texts[p], height=300, key=f"area_{p}")
            with st.expander("✨ 글 수정 요청하기"):
                feedback = st.text_input("어떻게 고칠까요?", placeholder="예: 조금 더 다정하게 써줘", key=f"f_{p}")
                if st.button("♻️ 다시 쓰기", key=f"b_{p}"):
                    st.session_state.generated_texts[p] = process_ai_text(f"기존글: {txt}\n요청: {feedback}\n작가님 말투로 다시 써줘.")
                    st.rerun()

# --- [Tab 2: 디자인 작업실] ---
with tabs[1]:
    # 1. 사진 보정
    st.subheader("📸 사진 자동 보정")
    st.write("AI가 사진을 화사하고 빈티지하게 보정해 드려요.")
    uploaded_files = st.file_uploader("사진 선택하기", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files and api_key and st.button("🚀 사진 자동 보정 시작"):
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

    st.divider()

    # 2. 캔바 (상세페이지)
    st.subheader("🎨 상세페이지 만들기 (캔바)")
    st.link_button("✨ 캔바(Canva) 앱 열기", "https://www.canva.com/templates/?query=상세페이지")
    if st.button("🪄 캔바 기획안 만들기"):
        if not name: st.warning("작품 정보를 먼저 적어주셔요🌸")
        else:
            client = openai.OpenAI(api_key=api_key)
            prompt = f"모그 작가로서 {name} 상세페이지 5장 기획 JSON."
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type":"json_object"})
            data = json.loads(res.choices[0].message.content)
            df = pd.DataFrame(data[list(data.keys())[0]])
            for index, row in df.iterrows():
                with st.expander(f"📍 {row['순서']}번 화면 글 (복사용)"):
                    st.write(f"**제목:** {row['메인문구']}\n\n**설명:** {row['설명']}")
                    st.caption(f"📸 사진 팁: {row['사진구도']}")

    st.divider()

    # 3. 에픽 (영상)
    st.subheader("🎥 감성 영상 만들기 (에픽)")
    with st.expander("📺 영상 제작 순서 보기 (터치)"):
        st.info("""
        1. **에픽(EPIK)** 앱을 실행하세요. (무지개색 아이콘)
        2. 하단 **[템플릿]**에서 **'감성'** 혹은 **'핸드메이드'**를 검색하세요.
        3. 마음에 드는 양식을 골라 **[사용하기]**를 누르세요.
        4. 위에서 보정한 사진들을 순서대로 넣으세요.
        5. 완료 후 오른쪽 위 **[저장]** 버튼을 누르면 갤러리에 저장됩니다! 🌸
        """)
