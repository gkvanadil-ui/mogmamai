import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 페이지 설정 (제목을 크게, 레이아웃은 모바일 맞춤형)
st.set_page_config(page_title="모그 AI 비서", layout="centered")

# --- CSS를 이용한 모바일 가독성 강화 (글씨 크기 및 간격) ---
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
        background-color: #f3ece4;
        color: #7d6e63;
        border: 1px solid #7d6e63;
    }
    h1 { color: #5d524a; font-size: 28px !important; text-align: center; }
    h2 { color: #5d524a; font-size: 22px !important; border-bottom: 2px solid #e0d7cf; padding-bottom: 10px; }
    h3 { font-size: 19px !important; color: #8e7f74; }
    p, li { font-size: 17px !important; line-height: 1.6; }
    .stTextArea textarea { font-size: 16px !important; }
    .stExpander { border: 1px solid #e0d7cf; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

st.title("🕯️ 핸드메이드 모그 AI 비서")
st.write("<p style='text-align: center; color: #8e7f74;'>엄마의 정성을 예쁜 문장과 영상으로 바꿔드릴게요🌸</p>", unsafe_allow_html=True)

st.divider()

# --- [1단계: 작품 정보 입력] ---
st.header("1️⃣ 작품 정보 적기")
with st.container():
    name = st.text_input("📦 작품 이름", placeholder="예: 뜨왈 스트링 파우치")
    
    col1, col2 = st.columns(2)
    with col1:
        mat = st.text_input("🧵 원단/소재", placeholder="예: 도톰한 린넨")
        size = st.text_input("📏 사이즈", placeholder="예: 가로 28 * 세로 30")
    with col2:
        period = st.text_input("⏳ 제작 기간", placeholder="예: 평일 기준 3~5일")
        care = st.text_input("💡 세탁/관리", placeholder="예: 부분 손세탁 권장")
        
    keys = st.text_area("🔑 작품 이야기/특징", placeholder="예: 가방 속에 쏙 들어가는 크기예요. 빈티지한 풍경이 그려져 있어 참 예쁘답니다.")
    process = st.text_area("🛠️ 제작 포인트 (진심 담기)", placeholder="예: 안감도 톡톡한 린넨을 써서 모양이 잘 잡혀요.")

st.divider()

# --- [2단계: 원하는 작업 선택] ---
st.header("2️⃣ 하고 싶은 작업 선택")
tabs = st.tabs(["✍️ 판매글 쓰기", "🎨 캔바/상세페이지", "🎥 영상 가이드"])

# --- [글 생성 및 수정 함수] ---
def process_ai_text(full_prompt):
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
        return response.choices[0].message.content.replace("**", "").strip()
    except Exception as e:
        st.error(f"오류가 발생했어요. 다시 시도해 주세요.")
        return None

# --- [Tab 1: 글쓰기 센터] ---
with tabs[0]:
    if 'generated_texts' not in st.session_state:
        st.session_state.generated_texts = {"인스타": "", "아이디어스": "", "스토어": ""}
    
    st.info("💡 아래 버튼을 누르면 작가님 말투로 글이 완성됩니다.")
    
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        if st.button("📸 인스타"): platform = "인스타그램"
    with sub_col2:
        if st.button("🎨 아디스"): platform = "아이디어스"
    with sub_col3:
        if st.button("🛍️ 스토어"): platform = "스마트스토어"
    
    # 버튼 클릭 시 생성 로직 (매칭)
    if 'platform' in locals():
        full_prompt = f"모그 작가 말투(~이지요^^)로 [{platform}] 글 작성. 이름:{name}, 특징:{keys}, 소재:{mat}, 사이즈:{size}, 제작:{process}, 관리:{care}, 기간:{period}."
        st.session_state.generated_texts[platform[:3]] = process_ai_text(full_prompt)

    # 결과물 표시
    for p_name in ["인스타", "아이디어스", "스마트스토어"]:
        short_key = p_name[:3]
        if st.session_state.generated_texts.get(short_key):
            st.subheader(f"✅ {p_name} 글 결과")
            current_text = st.text_area(f"{p_name} 글 (복사 가능)", value=st.session_state.generated_texts[short_key], height=300, key=f"area_{short_key}")
            
            with st.expander("✨ 여기서 글을 더 고치고 싶다면?"):
                feedback = st.text_input("어떻게 고칠까요?", placeholder="예: 조금 더 짧게 고쳐줘", key=f"feed_{short_key}")
                if st.button("♻️ 고쳐쓰기 실행", key=f"btn_{short_key}"):
                    new_text = process_ai_text(f"기존 글: {current_text}\n요청: {feedback}\n반영해서 다시 써줘.")
                    if new_text:
                        st.session_state.generated_texts[short_key] = new_text
                        st.rerun()

# --- [Tab 2: 캔바 상세페이지] ---
with tabs[1]:
    st.subheader("🎨 핸드폰으로 상세페이지 만들기")
    
    st.markdown("""
    1. **기획안 만들기** 버튼을 누르세요.
    2. 아래 박스에 나오는 글자를 **꾹 눌러 복사**하세요.
    3. **캔바 앱**에 가서 글자 자리에 붙여넣으세요!
    """)
    
    st.link_button("✨ 캔바 앱 열기", "https://www.canva.com/templates/?query=상세페이지", use_container_width=True)
    
    if st.button("🪄 캔바 기획안 만들기"):
        if not name: st.warning("작품 이름을 먼저 적어주셔요🌸")
        else:
            client = openai.OpenAI(api_key=api_key)
            prompt = f"모그 작가로서 {name} 상세페이지 5장 기획. JSON [{{'순서':'1','메인문구':'..','설명':'..','사진구도':'..'}}] 형식."
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type":"json_object"})
            data = json.loads(res.choices[0].message.content)
            df = pd.DataFrame(data[list(data.keys())[0]])
            
            for index, row in df.iterrows():
                with st.expander(f"📍 {row['순서']}번 화면에 넣을 글"):
                    st.write(f"**큰 글씨:** {row['메인문구']}")
                    st.write(f"**작은 설명:** {row['설명']}")
                    st.caption(f"📸 사진 추천: {row['사진구도']}")

# --- [Tab 3: 영상 가이드] ---
with tabs[2]:
    st.subheader("🎥 1분 감성 영상 제작법")
    
    with st.expander("1️⃣ 에픽(EPIK) 앱 설치하기", expanded=True):
        st.write("핸드폰에서 **무지개색 아이콘(EPIK)** 앱을 찾아서 눌러주세요.")

    with st.expander("2️⃣ 예쁜 양식(템플릿) 고르기"):
        st.write("아래쪽 **[템플릿]** 누르고, 위쪽 검색창에 **'감성'**이나 **'핸드메이드'**를 검색해서 마음에 드는 영상을 고르세요.")

    with st.expander("3️⃣ 내 사진 넣고 저장하기"):
        st.write("아래쪽 **[사용하기]** 누르고, 내 작품 사진들을 골라주세요. 다 되면 오른쪽 위 **[저장]**을 누르면 갤러리에 저장됩니다!")
