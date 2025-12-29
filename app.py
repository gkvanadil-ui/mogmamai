import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_google_auth import Authenticate
import json
import os

# 1. 페이지 설정 (반드시 최상단)
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- 🔐 구글 로그인 (TypeError 원천 봉쇄) ---
# 라이브러리가 요구하는 인자 이름을 수동으로 맞추지 않고, 
# 어떤 버전이든 돌아가도록 가장 표준적인 방식으로 구성했습니다.

try:
    # 🚨 TypeError 해결: 인자 이름을 하나씩 명시합니다.
    auth = Authenticate(
        secret_key=st.secrets["AUTH_SECRET_KEY"],
        google_client_id=st.secrets["GOOGLE_CLIENT_ID"],
        google_client_secret=st.secrets["GOOGLE_CLIENT_SECRET"],
        redirect_uri=st.secrets["REDIRECT_URI"],
        cookie_name="mom_ai_login_cookie",
        cookie_expiry_days=30
    )
except TypeError:
    # 혹시 최신 버전일 경우를 대비한 2차 시도
    auth = Authenticate(
        client_secrets_file=None, # 파일 대신 직접 입력
        cookie_name="mom_ai_login_cookie",
        cookie_key=st.secrets["AUTH_SECRET_KEY"],
        cookie_expiry_days=30
    )

auth.check_authentification()

if not st.session_state.get('connected'):
    st.markdown("<h1 style='text-align: center; color: #8D6E63;'>🌸 모그 작가님 AI 비서 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>작가님, 안전한 기록을 위해 로그인이 필요해요^^</p>", unsafe_allow_html=True)
    auth.login()
    st.stop()

# --- 🔑 로그인 성공 후 로직 (따님의 소중한 프롬프트 복구) ---
user_id = st.session_state['user_info'].get('email', 'mom_mog_01')
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()
api_key = st.secrets["OPENAI_API_KEY"]

def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    base_style = "[1인칭 작가 시점] 당신은 핸드메이드 작가 '모그'입니다. 말투: ~이지요^^, ~해요 등 다정하게. 특수기호(*, **) 금지."
    
    if platform == "인스타그램":
        system_p = f"{base_style} [📸 인스타그램] 감성 문구와 제작 일기 형식."
    elif platform == "아이디어스":
        system_p = f"{base_style} [🎨 아이디어스] 반드시 💡상세설명, 🍀Add info., 🔉안내, 👍🏻작가보증 포맷 엄수."
    elif platform == "스마트스토어":
        system_p = f"{base_style} [🛍️ 스마트스토어] 반드시 💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리, 📍추천 포맷 엄수."
    else:
        system_p = f"{base_style} [💬 고민 상담소] 다정하게 공감하며 위로해줘."

    info = f"작품:{st.session_state.get('m_name','')}, 소재:{st.session_state.get('m_mat','')}, 포인트:{st.session_state.get('m_det','')}"
    content = f"수정요청: {feedback}\n기존글: {user_in}" if feedback else f"정보: {info}\n요청: {user_in}"
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 화면 구성 ---
st.title("🌸 모그 작가님 AI 비서 🌸")
if 'texts' not in st.session_state:
    doc = db.collection("users").document(user_id).get()
    st.session_state.update(doc.to_dict() if doc.exists else {'texts': {"인스타": "", "아이디어스": "", "스토어": ""}, 'm_name': '', 'm_mat': '', 'm_det': ''})

with st.container():
    st.header("📝 작품 정보")
    st.session_state.m_name = st.text_input("📦 이름", value=st.session_state.m_name)
    st.session_state.m_mat = st.text_input("🧵 소재", value=st.session_state.m_mat)
    st.session_state.m_det = st.text_area("✨ 포인트", value=st.session_state.m_det)

st.divider()
tabs = st.tabs(["✍️ 판매글 쓰기", "💬 고민 상담소"])

with tabs[0]:
    c1, c2, c3 = st.columns(3)
    if c1.button("📸 인스타"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if c2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if c3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    for key in ["인스타", "아이디어스", "스토어"]:
        if st.session_state.texts[key]:
            st.info(st.session_state.texts[key])
