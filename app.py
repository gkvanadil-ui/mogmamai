import streamlit as st
import openai
from PIL import Image
import io
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 작가님 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 디자인 개선 (따님이 원하신 세련된 스타일) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    
    /* 제목 및 텍스트 스타일 */
    h1 { color: #8D6E63 !important; text-align: center; font-weight: 800; margin-bottom: 40px; }
    label p { font-size: 22px !important; font-weight: bold !important; color: #5D4037 !important; }
    
    /* 입력창 디자인 */
    .stTextInput input, .stTextArea textarea { 
        font-size: 20px !important; border-radius: 12px !important; border: 1px solid #D7CCC8 !important; padding: 15px !important;
    }
    
    /* 버튼 디자인 (큼직하고 명확하게) */
    .stButton>button { 
        width: 100%; border-radius: 15px; height: 3.5em; background-color: #8D6E63 !important; 
        color: white !important; font-weight: bold; font-size: 20px !important; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #6D4C41 !important; transform: translateY(-2px); }
    
    /* 결과창 카드 스타일 */
    .result-box { 
        background-color: white; padding: 30px; border-radius: 20px; border-left: 10px solid #D7CCC8;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: 20px; line-height: 1.8; font-size: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 설정
api_key = st.secrets.get("OPENAI_API_KEY")

# 세션 상태 초기화 (따님 설계 로직 복구)
for key in ['texts', 'chat_log', 'm_name', 'm_mat', 'm_per', 'm_size', 'm_det', 'img_analysis']:
    if key not in st.session_state:
        if key == 'texts': st.session_state[key] = {"인스타": "", "아이디어스": "", "스토어": ""}
        elif key == 'chat_log': st.session_state[key] = []
        else: st.session_state[key] = ""

# --- [로직 1: 사진 분석] ---
def analyze_image(img_file):
    client = openai.OpenAI(api_key=api_key)
    base64_image = base64.b64encode(img_file.getvalue()).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "핸드메이드 작가 모그의 작품이야. 색감과 디테일을 1인칭 시점으로 다정하게 묘사해줘."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}]
    )
    return response.choices[0].message.content

# --- [로직 2: 글쓰기 엔진 (1인칭 엄마 말투)] ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    base_style = "[절대 규칙: 1인칭 작가 시점] 당신은 작가 '모그(Mog)' 본인입니다. 말투: ~이지요^^, ~해요 등 다정하게. 특수기호 금지."
    
    if platform == "인스타그램": system_p = f"{base_style} [📸 인스타 감성 일기]"
    elif platform == "아이디어스": system_p = f"{base_style} [🎨 아이디어스] 💡상세설명, 🍀Add info., 🔉안내, 👍🏻작가보증 포맷 엄수."
    elif platform == "스마트스토어": system_p = f"{base_style} [🛍️ 스토어] 💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리, 📍추천 엄수."
    else: system_p = f"{base_style} [💬 상담소]"

    info = f"작품:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 정성:{st.session_state.m_det}"
    if st.session_state.img_analysis: info += f"\n[사진 분석]: {st.session_state.img_analysis}"
    
    content = f"수정 요청: {feedback}\n기존: {user_in}" if feedback else f"정보: {info} / {user_in}"
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 3. 화면 구성 ---
st.title("🌸 모그 작가님 AI 비서 🌸")

with st.container():
    col1, col2 = st.columns([1, 1.5], gap="large")
    with col1:
        st.header("📸 사진 분석")
        up_img = st.file_uploader("작품 사진을 올려주세요^^", type=["jpg", "png", "jpeg"])
        if up_img:
            st.image(up_img, use_container_width=True)
            if st.button("🔍 분석 시작"):
                st.session_state.img_analysis = analyze_image(up_img)
                st.rerun()
    with col2:
        st.header("📝 정보 입력")
        st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.m_name)
        st.session_state.m_mat = st.text_input("🧵 소재", value=st.session_state.m_mat)
        st.session_state.m_det = st.text_area("✨ 정성 포인트", value=st.session_state.m_det, height=150)

st.divider()

tabs = st.tabs(["✍️ 판매글 쓰기", "💬 고민 상담소"])

with tabs[0]:
    b1, b2, b3 = st.columns(3)
    if b1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if b2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if b3.button("🛍️ 스마트스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    for p_name, key in [("인스타그램", "인스타"), ("아이디어스", "아이디어스"), ("스마트스토어", "스토어")]:
        if st.session_state.texts[key]:
            st.markdown(f"---")
            st.markdown(f"### ✨ 완성된 {p_name} 글")
            st.markdown(f'<div class="result-box">{st.session_state.texts[key].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            feed = st.text_input(f"✍️ {p_name} 수정 요청", key=f"f_{key}")
            if st.button(f"🚀 반영", key=f"b_{key}"):
                st.session_state.texts[key] = ask_mog_ai(p_name, user_in=st.session_state.texts[key], feedback=feed)
                st.rerun()

with tabs[1]:
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 어떤 고민이 있으신가요?"):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()
