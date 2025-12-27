import streamlit as st
import pandas as pd
import openai
from streamlit_gsheets import GSheetsConnection
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일: 가독성 높고 깔끔한 배치 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 20px !important; font-weight: bold !important; color: #8D6E63 !important; }
    .stTextInput input, .stTextArea textarea { font-size: 19px !important; border-radius: 12px !important; border: 2px solid #D7CCC8 !important; padding: 15px !important; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3.5em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 18px !important; }
    h1 { color: #8D6E63 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 설정
api_key = st.secrets.get("OPENAI_API_KEY")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1tz4pYbxyV8PojkzYtPz82OhiAGD2XoWVZqlTpwAebaA/edit?usp=sharing"

# 세션 상태 초기화
if 'm_name' not in st.session_state: st.session_state.m_name = ""
if 'm_mat' not in st.session_state: st.session_state.m_mat = ""
if 'm_per' not in st.session_state: st.session_state.m_per = ""
if 'm_tar' not in st.session_state: st.session_state.m_tar = ""
if 'm_det' not in st.session_state: st.session_state.m_det = ""
if 'texts' not in st.session_state: st.session_state.texts = {"인스타": "", "아이디어스": "", "스토어": ""}
if 'chat_log' not in st.session_state: st.session_state.chat_log = []

# --- 3. 메인 화면: 정보 입력 및 [창고 저장] ---
st.title("🌸 모그 작가님 AI 비서 🌸")
st.header("1️⃣ 작품 정보를 입력해주세요")

c1, c2 = st.columns(2)
with c1:
    st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.m_name)
    st.session_state.m_mat = st.text_input("🧵 사용한 소재", value=st.session_state.m_mat)
with c2:
    st.session_state.m_per = st.text_input("⏳ 제작 소요 기간", value=st.session_state.m_per)
    st.session_state.m_tar = st.text_input("🎁 추천 선물 대상", value=st.session_state.m_tar)
st.session_state.m_det = st.text_area("✨ 정성 포인트와 상세 설명", value=st.session_state.m_det, height=150)

# [창고 저장하기 버튼]
if st.button("💾 이 작품 정보 창고에 저장하기"):
    if not st.session_state.m_name:
        st.error("작품 이름을 입력해 주셔요🌸")
    else:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(spreadsheet=SHEET_URL, ttl=0)
            new_data = pd.DataFrame([{"name":st.session_state.m_name, "material":st.session_state.m_mat, "period":st.session_state.m_per, "target":st.session_state.m_tar, "keys":st.session_state.m_det}])
            conn.update(spreadsheet=SHEET_URL, data=pd.concat([df, new_data], ignore_index=True))
            st.success(f"'{st.session_state.m_name}' 정보가 창고에 잘 보관되었습니다! 🌸")
        except:
            st.error("저장 중 오류가 발생했습니다. 구글 시트 주소와 권한을 확인해주세요.")

st.divider()

# --- [함수: AI 로직] ---
def ask_mog_ai(type, user_in="", img_file=None):
    client = openai.OpenAI(api_key=api_key)
    
    if type == "보정":
        # 이미지 업로드 -> AI가 분석 후 보정된 느낌의 새 이미지를 생성하는 로직
        # (현실적으로 원본 픽셀을 직접 보정하는 라이브러리 연동보다, AI가 사진을 보고 보정된 버전으로 재생성하는 것이 결과가 더 좋습니다)
        base64_img = base64.b64encode(img_file.getvalue()).decode('utf-8')
        # 1. 사진 분석
        analysis = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [{"type": "text", "text": "이 사진을 더 화사하고 따뜻하게 보정하려면 어떤 요소가 필요할까? 상세히 묘사해줘."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}]}]
        ).choices[0].message.content
        # 2. 분석 내용을 바탕으로 보정된 이미지 생성
        result_img = client.images.generate(
            model="dall-e-3",
            prompt=f"A professional product photo of {st.session_state.m_name}. Based on this analysis: {analysis}. Cinematic lighting, very bright and warm, high resolution, handmade aesthetic.",
            size="1024x1024"
        )
        return result_img.data[0].url
    elif type == "상담":
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":"다정한 동료 작가 모그입니다."},{"role":"user","content":user_in}])
        return res.choices[0].message.content
    else:
        info = f"작품:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 설명:{st.session_state.m_det}"
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":"작가 모그입니다."},{"role":"user","content":f"정보: {info} / {user_in}"}])
        return res.choices[0].message.content

# --- 4. 기능 탭 ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 AI 사진 보정", "💬 고민 상담소", "📂 작품 창고"])

with tabs[0]: # 판매글 쓰기
    c1, c2, c3 = st.columns(3)
    if c1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타", "감성 일기 스타일")
    if c2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스", "정성 강조 스타일")
    if c3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스토어", "친절한 안내 스타일")
    for k, v in st.session_state.texts.items():
        if v: st.text_area(f"📍 {k}", value=v, height=200)

with tabs[1]: # 📸 AI 사진 보정 (실제 보정된 결과물 출력)
    st.header("📸 AI 사진 보정기")
    st.write("원본 사진을 올려주시면 AI가 화사하게 보정하여 새로운 사진을 드립니다.")
    up_img = st.file_uploader("보정할 사진을 올려주세요", type=["jpg", "png", "jpeg"])
    if up_img and st.button("✨ 보정된 사진 받기"):
        with st.spinner("AI가 정성껏 보정 중입니다..."):
            final_url = ask_mog_ai("보정", img_file=up_img)
            st.subheader("✅ 보정 결과")
            st.image(final_url, caption="AI가 보정한 새로운 작품 사진")

with tabs[2]: # 고민 상담소
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 무엇이든 말씀하셔요..."):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()

with tabs[3]: # 📂 작품 창고 (리스트 및 불러오기)
    st.header("📂 나의 저장된 작품들")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        for i, r in df.iterrows():
            with st.expander(f"📦 {r['name']}"):
                st.write(f"**소재:** {r['material']} | **제작기간:** {r['period']}")
                if st.button("📥 불러오기", key=f"get_{i}"):
                    st.session_state.m_name, st.session_state.m_mat = r['name'], r['material']
                    st.session_state.m_per, st.session_state.m_tar = r['period'], r['target']
                    st.session_state.m_det = r['keys']
                    st.rerun()
    except: st.warning("창고가 비어있거나 주소가 올바르지 않아요🌸")
