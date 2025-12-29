import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_google_auth import Authenticate
import json
import os

# 1. 페이지 설정 (최상단 고정)
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- 🔐 구글 로그인 (TypeError 방어 로직) ---
client_secrets = {
    "web": {
        "client_id": st.secrets["GOOGLE_CLIENT_ID"],
        "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [st.secrets["REDIRECT_URI"]]
    }
}
with open("client_secrets.json", "w") as f:
    json.dump(client_secrets, f)

# 🚨 인자 이름을 명시적으로 지정하여 TypeError를 해결했습니다.
try:
    auth = Authenticate(
        secret_key=st.secrets["AUTH_SECRET_KEY"],
        google_client_id=st.secrets["GOOGLE_CLIENT_ID"],
        google_client_secret=st.secrets["GOOGLE_CLIENT_SECRET"],
        redirect_uri=st.secrets["REDIRECT_URI"],
        cookie_name="mom_ai_login_cookie",
        cookie_expiry_days=30
    )
except TypeError:
    # 라이브러리 버전이 다를 경우를 대비한 2차 시도
    auth = Authenticate(
        client_secrets_file="client_secrets.json",
        cookie_name="mom_ai_login_cookie",
        cookie_key=st.secrets["AUTH_SECRET_KEY"],
        cookie_expiry_days=30
    )

auth.check_authentification()

if not st.session_state.get('connected'):
    st.markdown("<h1 style='text-align: center; color: #8D6E63;'>🌸 모그 작가님 AI 비서 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>작가님, 안전한 기록 저장을 위해 로그인이 필요해요^^</p>", unsafe_allow_html=True)
    auth.login()
    st.stop()

# --- 🔑 로그인 성공 후 본문 ---
user_id = st.session_state['user_info'].get('email', 'mom_mog_01')

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()
api_key = st.secrets["OPENAI_API_KEY"]

# --- ✨ [복구] 작가님 전용 플랫폼별 프롬프트 로직 ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    # 작가님 특유의 다정한 1인칭 어투 고정
    base_style = "[절대 규칙: 1인칭 작가 시점] 당신은 핸드메이드 작가 '모그(Mog)' 본인입니다. 말투: ~이지요^^, ~해요, ~했답니다 등 다정하고 따뜻하게. 특수기호(*, **) 사용 금지."
    
    if platform == "인스타그램":
        system_p = f"{base_style} [📸 인스타그램] 감성 문구로 시작해 제작 과정을 일기처럼 다정하게 적고 해시태그를 붙여줘."
    elif platform == "아이디어스":
        system_p = f"{base_style} [🎨 아이디어스] 반드시 다음 4가지 포맷을 엄격히 지켜줘: \n💡상세설명: 작품의 특징\n🍀Add info.: 구매 팁\n🔉안내: 배송 및 주의사항\n👍🏻작가보증: 작가의 자부심"
    elif platform == "스마트스토어":
        system_p = f"{base_style} [🛍️ 스마트스토어] 반드시 다음 7가지 포맷을 엄격히 지켜줘: \n💐상품명\n🌸디자인\n👜기능성\n📏사이즈\n📦소재\n🧼관리\n📍추천"
    else:
        system_p = f"{base_style} [💬 고민 상담소] 다정한 선배 작가로서 진심으로 공감하고 따뜻하게 위로해줘."

    info = f"작품명:{st.session_state.get('m_name','')}, 소재:{st.session_state.get('m_mat','')}, 포인트:{st.session_state.get('m_det','')}"
    content = f"수정요청: {feedback}\n기존글: {user_in}" if feedback else f"정보: {info}\n요청내용: {user_in}"
    
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 화면 구성 ---
st.title("🌸 모그 작가님 AI 비서 🌸")
if 'texts' not in st.session_state:
    doc = db.collection("users").document(user_id).get()
    st.session_state.update(doc.to_dict() if doc.exists else {'texts': {"인스타": "", "아이디어스": "", "스토어": ""}, 'chat_log': [], 'm_name': '', 'm_mat': '', 'm_det': ''})

with st.container():
    st.header("📝 작품 정보 입력")
    st.session_state.m_name = st.text_input("📦 이름", value=st.session_state.m_name)
    st.session_state.m_mat = st.text_input("🧵 소재", value=st.session_state.m_mat)
    st.session_state.m_det = st.text_area("✨ 포인트", value=st.session_state.m_det)
    if st.button("💾 이 정보 저장하기"):
        db.collection("users").document(user_id).set({'m_name': st.session_state.m_name, 'm_mat': st.session_state.m_mat, 'm_det': st.session_state.m_det, 'texts': st.session_state.texts, 'chat_log': st.session_state.chat_log})
        st.success("작가님, 정보가 안전하게 저장되었어요^^ 🌸")

st.divider()
tabs = st.tabs(["✍️ 판매글 쓰기", "💬 고민 상담소"])

with tabs[0]:
    b1, b2, b3 = st.columns(3)
    if b1.button("📸 인스타"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if b2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if b3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    for p_name, key in [("인스타그램", "인스타"), ("아이디어스", "아이디어스"), ("스마트스토어", "스토어")]:
        if st.session_state.texts[key]:
            st.markdown(f"### ✨ 완성된 {p_name}")
            st.info(st.session_state.texts[key])
