import streamlit as st
import openai
from PIL import Image
import io
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일 가이드 (가독성 및 심미성 강화) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    
    /* 기본 배경 및 폰트 설정 */
    html, body, [data-testid="stAppViewContainer"] { 
        background-color: #FCF9F6; 
        font-family: 'Noto Sans KR', sans-serif; 
    }
    
    /* 헤더 및 라벨 스타일 */
    label p { font-size: 24px !important; font-weight: bold !important; color: #5D4037 !important; }
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 30px; font-weight: 800; }
    h3 { color: #A1887F !important; margin-top: 20px; }

    /* 입력창 스타일 */
    .stTextInput input, .stTextArea textarea { 
        font-size: 22px !important; 
        border-radius: 15px !important; 
        border: 2px solid #E0D4CC !important; 
        padding: 20px !important;
        background-color: #FFFFFF !important;
    }

    /* 버튼 스타일 (큼직하고 따뜻하게) */
    .stButton>button { 
        width: 100%; 
        border-radius: 20px; 
        height: 4.5em; 
        background-color: #8D6E63 !important; 
        color: white !important; 
        font-weight: bold; 
        font-size: 22px !important; 
        border: none;
        transition: 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { background-color: #6D4C41 !important; transform: translateY(-2px); }

    /* 결과물 박스 스타일 */
    .result-card {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 25px;
        border-left: 10px solid #D7CCC8;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* 탭 메뉴 폰트 확대 */
    .stTabs [data-baseweb="tab-list"] button { font-size: 26px !important; font-weight: bold !important; padding: 15px 30px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 설정
api_key = st.secrets.get("OPENAI_API_KEY")

# 세션 상태 초기화
for key in ['texts', 'chat_log', 'm_name', 'm_mat', 'm_per', 'm_size', 'm_det', 'img_analysis']:
    if key not in st.session_state:
        if key == 'texts': st.session_state[key] = {"인스타": "", "아이디어스": "", "스토어": ""}
        elif key == 'chat_log': st.session_state[key] = []
        elif key == 'img_analysis': st.session_state[key] = ""
        else: st.session_state[key] = ""

# --- [로직 1: 사진 특징 분석] ---
def analyze_image(img_file):
    client = openai.OpenAI(api_key=api_key)
    base64_image = base64.b64encode(img_file.getvalue()).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "이 사진은 핸드메이드 작가 모그의 작품입니다. 사진의 색감, 질감, 디테일을 1인칭 작가 시점에서 아주 다정하게 묘사해줘."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }]
    )
    return response.choices[0].message.content

# --- [로직 2: 모그 작가님 전용 글쓰기 엔진 (1인칭 고정)] ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    base_style = """
    [절대 규칙: 1인칭 작가 시점]
    - 당신은 작가 '모그(Mog)' 본인입니다. AI 비서 멘트 금지.
    - 말투: ~이지요^^, ~해요 등 다정한 50대 여성 작가 어투.
    - 특수기호(*, **) 절대 금지. 줄바꿈은 넉넉하게.
    """
    
    if platform == "인스타그램":
        system_p = f"{base_style} [📸 인스타그램] 감성 문구로 시작해 제작 일기와 상세 정보를 자연스럽게 연결하세요."
    elif platform == "아이디어스":
        system_p = f"""{base_style} [🎨 아이디어스 에세이 모드] 
        포맷 유지(💡상세설명, 🍀Add info., 🔉안내, 👍🏻작가보증). 작가님의 정성을 구구절절 에세이처럼 길게 작성하세요."""
    elif platform == "스마트스토어":
        system_p = f"""{base_style} [🛍️ 스토어 상세 모드] 
        양식 유지(💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리, 📍추천). 다정하고 풍성하게 설명하세요."""
    elif platform == "상담":
        system_p = f"{base_style} [💬 상담소] 고민에 깊이 공감하고 따뜻한 격려를 건네는 선배 작가가 되어주세요."

    info = f"작품명:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 사이즈:{st.session_state.m_size}, 정성:{st.session_state.m_det}"
    if st.session_state.img_analysis:
        info += f"\n[사진 디테일]: {st.session_state.img_analysis}"

    content = f"수정 요청: {feedback}\n기존 내용: {user_in}" if feedback else f"정보: {info} / {user_in}"
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 3. 메인 화면 ---
st.title("🌸 모그 작가님 AI 비서 🌸")

# 상단: 사진 및 기본 정보 입력 (깔끔한 레이아웃)
with st.container():
    col1, col2 = st.columns([1, 1.5], gap="large")
    with col1:
        st.header("📸 작품 사진")
        up_img = st.file_uploader("작품 사진을 올려주세요^^", type=["jpg", "png", "jpeg"])
        if up_img:
            st.image(up_img, use_container_width=True, caption="현재 등록된 사진")
            if st.button("🔍 사진 분석 시작하기"):
                with st.spinner("작가님의 시선으로 살피는 중..."):
                    st.session_state.img_analysis = analyze_image(up_img)
                    st.rerun()
    with col2:
        st.header("📝 작품 정보")
        c1, c2 = st.columns(2)
        st.session_state.m_name = c1.text_input("📦 작품 이름", value=st.session_state.m_name)
        st.session_state.m_mat = c2.text_input("🧵 소재", value=st.session_state.m_mat)
        c3, c4 = st.columns(2)
        st.session_state.m_per = c3.text_input("⏳ 제작 기간", value=st.session_state.m_per)
        st.session_state.m_size = c4.text_input("📏 사이즈", value=st.session_state.m_size)
        st.session_state.m_det = st.text_area("✨ 정성 포인트와 설명", value=st.session_state.m_det, height=120)

st.divider()

# --- 4. 메인 기능 탭 ---
tabs = st.tabs(["✍️ 판매글 쓰기", "💬 고민 상담소"])

with tabs[0]: # 판매글 쓰기 탭 (UI 개선 핵심)
    st.markdown("### 🚀 어떤 플랫폼에 올릴 글을 써볼까요?")
    st.info(f"현재 입력된 정보: **{st.session_state.m_name or '없음'}** ({st.session_state.m_mat or '소재 미입력'})")
    
    b1, b2, b3 = st.columns(3)
    if b1.button("📸 인스타그램\n(감성 일기)"): 
        st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if b2.button("🎨 아이디어스\n(정성 에세이)"): 
        st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if b3.button("🛍️ 스마트스토어\n(친절 가이드)"): 
        st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    # 결과물 섹션 (카드 레이아웃)
    for p_name, key in [("인스타그램", "인스타"), ("아이디어스", "아이디어스"), ("스마트스토어", "스토어")]:
        if st.session_state.texts[key]:
            st.markdown(f"---")
            st.markdown(f"### ✨ 완성된 {p_name} 글입니다^^")
            
            # 텍스트 카드
            with st.container():
                st.markdown(f'<div class="result-card">{st.session_state.texts[key].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                
                # 수정 요청 일체형 UI
                col_f1, col_f2 = st.columns([4, 1])
                feedback = col_f1.text_input(f"✍️ {p_name} 글에서 더 보강하고 싶은 점이 있으신가요?", key=f"f_{key}", placeholder="예: 소재 설명을 좀 더 길게 해줘")
                if col_f2.button("🚀 반영하기", key=f"b_{key}"):
                    with st.spinner("다시 정성껏 적는 중..."):
                        st.session_state.texts[key] = ask_mog_ai(p_name, user_in=st.session_state.texts[key], feedback=feedback)
                        st.rerun()

with tabs[1]: # 고민 상담소
    st.header("💬 작가님 고민 상담소")
    st.markdown("혼자 작업하며 답답할 때, 동료 작가인 제가 들어드릴게요.")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    if pr := st.chat_input("작가님, 어떤 고민이 있으신가요?"):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()
