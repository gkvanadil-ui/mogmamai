import streamlit as st
import openai
from PIL import Image, ImageEnhance
import io
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 22px !important; font-weight: bold !important; color: #8D6E63 !important; }
    .stTextInput input, .stTextArea textarea { font-size: 20px !important; border-radius: 12px !important; border: 2px solid #D7CCC8 !important; padding: 15px !important; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3.8em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 20px !important; }
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] button { font-size: 22px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 설정
api_key = st.secrets.get("OPENAI_API_KEY")

# 세션 상태 초기화
for key in ['texts', 'chat_log', 'm_name', 'm_mat', 'm_per', 'm_size', 'm_det']:
    if key not in st.session_state:
        if key == 'texts': st.session_state[key] = {"인스타": "", "아이디어스": "", "스토어": ""}
        elif key == 'chat_log': st.session_state[key] = []
        else: st.session_state[key] = ""

# --- [로직 1: AI 자동 사진 보정 엔진] ---
def ai_auto_enhance(img_file):
    client = openai.OpenAI(api_key=api_key)
    base64_image = base64.b64encode(img_file.getvalue()).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [{"type": "text", "text": "사진 분석해서 'B:수치, C:수치, S:수치' 형식으로 보정값만 골라줘."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
    )
    img = Image.open(img_file)
    img = ImageEnhance.Brightness(img).enhance(1.3)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = ImageEnhance.Color(img).enhance(1.2)
    return img

# --- [로직 2: 모그 작가님 전용 어투 (아이디어스/스토어 분량 확대 적용)] ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    
    system_p = """
    1️⃣ [공통] 모그 작가님 기본 어투 규칙
    정체성: 50대 여성 핸드메이드 작가의 다정하고 따뜻한 마음.
    대표 어미: ~이지요^^, ~해요, ~좋아요, ~보내드려요 등 부드러운 말투.
    특수기호 금지: 별표(*)나 볼드체(**) 같은 마크다운 기호는 절대 사용 금지.
    감성 이모지: 꽃(🌸, 🌻), 구름(☁️), 반짝이(✨)를 과하지 않게 섞어서 사용.
    """
    
    if platform == "인스타그램":
        system_p += """
        2️⃣ [플랫폼별 특화 - 📸 인스타그램]
        지침: 사진을 보자마자 마음이 따뜻해지는 문구로 시작.
        구성: [첫 줄 감성 문구] + [작가님의 제작 일기] + [작품 상세 정보] + [다정한 인사] + [해시태그].
        특징: 줄바꿈을 아주 넉넉히 하고 해시태그는 10개 내외.
        """
    elif platform == "아이디어스":
        system_p += """
        2️⃣ [플랫폼별 특화 - 🎨 아이디어스 (분량: 아주 길게)]
        지침: 작가님의 수고와 정성이 고객에게 고스란히 전달되도록 '긴 호흡의 에세이'처럼 작성할 것. 절대 내용을 축약하지 말고 풍성하게 늘려쓸 것.
        구성: [제작 동기 및 영감] + [소재를 고른 까다로운 기준] + [한 땀 한 땀 만드는 상세한 과정] + [사용 추천 상황].
        내용: '한 땀 한 땀', '밤새 고민하며', '정성을 다해' 등의 표현을 사용하여 감동적으로 상세하게 서술.
        """
    elif platform == "스토어":
        system_p += """
        2️⃣ [플랫폼별 특화 - 🛍️ 스마트스토어 (분량: 아주 길게)]
        지침: 정보를 단순히 나열하지 말고, 친절한 상담원이 옆에서 설명하듯 문장으로 길게 풀어쓸 것. 고객이 궁금해할 모든 내용을 미리 상세하게 설명.
        구성: [상품의 매력 포인트 3가지 상세 설명] + [소재 및 촉감에 대한 자세한 이야기] + [사이즈 및 핏 가이드] + [오래 쓰는 관리법].
        특징: 구분선(⸻)을 사용하되, 각 항목의 설명은 최대한 구체적이고 길고 다정하게 작성.
        """
    elif platform == "상담":
        system_p += """
        3️⃣ [상담소 고민 상담 전용 로직]
        역할: 핸드메이드 작가들의 든든한 선배이자 다정한 동료 '모그 AI'.
        규칙: 엄마의 고민에 깊이 공감해주고, 실질적인 도움을 줄 것.
        마무리: 항상 작가님의 활동을 진심으로 응원하는 따뜻한 격려 멘트 필수.
        """

    if feedback:
        u_content = f"기존 글: {user_in}\n\n수정 요청사항: {feedback}\n\n위 요청을 반영해서 내용을 더 풍성하고 다정하게 다시 써주셔요🌸"
    else:
        info = f"작품명:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 사이즈:{st.session_state.m_size}, 정성포인트:{st.session_state.m_det}"
        u_content = f"정보: {info} / {user_in}"

    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":u_content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 3. 메인 화면 ---
st.title("🌸 모그 작가님 AI 비서 🌸")
st.header("1️⃣ 작품 정보를 입력해주세요")

c1, c2 = st.columns(2)
with c1:
    st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.m_name)
    st.session_state.m_mat = st.text_input("🧵 소재", value=st.session_state.m_mat)
with c2:
    st.session_state.m_per = st.text_input("⏳ 제작 기간", value=st.session_state.m_per)
    st.session_state.m_size = st.text_input("📏 사이즈", value=st.session_state.m_size)
st.session_state.m_det = st.text_area("✨ 정성 포인트와 설명", value=st.session_state.m_det, height=150)

st.divider()

# --- 4. 기능 탭 (저장 기능 삭제됨) ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 AI 자동 사진 보정", "💬 고민 상담소"])

with tabs[0]: 
    sc1, sc2, sc3 = st.columns(3)
    if sc1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if sc2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if sc3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스토어")
    
    for k, v in st.session_state.texts.items():
        if v:
            st.markdown(f"### ✨ 완성된 {k} 글이 완성되었어요^^")
            # 글 길게 나오도록 높이 조절
            st.text_area(f"{k} 결과", value=v, height=500, key=f"area_{k}")
            
            feed = st.text_input(f"✍️ {k} 글에서 수정하고 싶은 부분이 있으신가요?", key=f"feed_{k}")
            if st.button(f"🚀 {k} 글 다시 수정하기", key=f"btn_{k}"):
                with st.spinner("내용을 더 풍성하게 다듬는 중이에요..."):
                    st.session_state.texts[k] = ask_mog_ai(k, user_in=v, feedback=feed)
                    st.rerun()

with tabs[1]: 
    st.header("📸 AI 자동 사진 보정")
    up_img = st.file_uploader("사진을 올려주시면 AI가 화사하게 직접 보정해드릴게요 🌸", type=["jpg", "png", "jpeg"])
    if up_img and st.button("✨ 보정 시작하기"):
        with st.spinner("작품을 화사하게 만드는 중이에요..."):
            e_img = ai_auto_enhance(up_img)
            col1, col2 = st.columns(2)
            col1.image(up_img, caption="보정 전")
            col2.image(e_img, caption="AI 보정 결과")
            buf = io.BytesIO(); e_img.save(buf, format="JPEG")
            st.download_button("📥 보정된 사진 저장하기", buf.getvalue(), "mogs_fixed.jpg", "image/jpeg")

with tabs[2]: 
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 어떤 고민이 있으신가요?"):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()
