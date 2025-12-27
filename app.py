import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import io
import openai
import base64
import json

# 1. 페이지 설정 (아이콘과 제목)
st.set_page_config(page_title="모그 AI 비서", layout="centered", page_icon="🕯️")

# --- ✨ UI/UX: 엄마를 위한 따뜻하고 큰 글씨 스타일 ---
st.markdown("""
    <style>
    /* 전체 배경색과 폰트 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FCF9F6; /* 따뜻한 아이보리 배경 */
        font-family: 'Noto Sans KR', sans-serif;
        color: #4A3E3E;
    }
    
    /* 헤더 스타일 */
    h1, h2, h3 { color: #8D6E63 !important; font-weight: 700 !important; }
    
    /* 버튼 스타일: 큼직하고 둥글게 */
    .stButton>button {
        width: 100%; 
        border-radius: 20px; 
        height: 4em;
        background-color: #8D6E63 !important; 
        color: white !important;
        font-weight: bold; font-size: 20px !important;
        border: none;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #6D4C41 !important; transform: scale(1.02); }

    /* 입력창 글씨 키우기 */
    .stTextInput input, .stTextArea textarea {
        font-size: 18px !important;
        border-radius: 12px !important;
        border: 1px solid #D7CCC8 !important;
        background-color: white !important;
    }

    /* 탭 메뉴 글씨 키우기 */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 10px 20px;
    }
    
    /* 강조 박스(info) 스타일 */
    .stAlert { border-radius: 15px; border: none; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- API 키 설정 (보안) ---
api_key = st.secrets.get("OPENAI_API_KEY")

# --- 상단 타이틀 ---
st.title("🕯️ 모그(Mog) 작가님 전용 비서")
st.write("### 안녕하세요 작가님! 오늘도 정성 가득한 하루 보내셔요 🌸")

# --- [공통 함수: AI 글쓰기 두뇌] ---
def process_mog_ai(platform_guide):
    if not api_key: return "API 키를 확인해주세요🌸"
    client = openai.OpenAI(api_key=api_key)
    
    mog_tone_prompt = f"""
    당신은 핸드메이드 브랜드 '모그(Mog)'를 운영하는 작가입니다. 
    다음 지침을 반드시 지켜서 [{platform_guide['name']}] 글을 작성하세요.

    [어투 지침]
    - 말투: 50대 여성 작가의 다정하고 따뜻한 말투 (~이지요^^, ~해요, ~보내드려요)
    - 금기 사항: 절대로 별표(*)나 볼드체(**) 같은 특수 기호를 사용하지 마세요. 
    - 이모지: 꽃(🌸,🌻), 구름(☁️), 반짝이(✨)를 적절히 사용하세요.

    [플랫폼 지침] {platform_guide['desc']}
    [작품 정보] 이름: {st.session_state.get('name', '작품')} / 특징: {st.session_state.get('keys', '')}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": mog_tone_prompt}]
        )
        return response.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except:
        return "오류가 발생했어요. 잠시 후 다시 눌러주세요🌸"

# --- [1단계: 정보 입력 섹션] ---
with st.container():
    st.header("1️⃣ 어떤 작품을 소개할까요?")
    with st.expander("📝 작품 정보를 여기에 적어주세요 (클릭)", expanded=True):
        st.session_state.name = st.text_input("📦 작품의 예쁜 이름", placeholder="예: 빈티지 튤립 뜨개 파우치")
        st.session_state.keys = st.text_area("🔑 이 작품의 정성 포인트", placeholder="예: 한 코 한 코 직접 뜬 꽃무늬가 참 화사해요. 안감까지 꼼꼼히 챙겼답니다.")

st.divider()

# --- [2단계: 작업실 선택 섹션] ---
st.header("2️⃣ 무엇을 도와드릴까요?")
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진 보정법", "💬 고민 상담소"])

# --- Tab 1: 판매글 쓰기 (원본/수정본 분리형) ---
with tabs[0]:
    if 'texts' not in st.session_state: st.session_state.texts = {"인스타": "", "아이디어스": "", "스토어": ""}
    if 'refined' not in st.session_state: st.session_state.refined = {"인스타": "", "아이디어스": "", "스토어": ""}

    st.write("#### 💡 버튼을 누르면 작가님 말투로 글이 써집니다.")
    c1, c2, c3 = st.columns(3)
    
    if c1.button("📸 인스타그램"): 
        st.session_state.texts["인스타"] = process_mog_ai({"name": "인스타그램", "desc": "감성적인 첫 문장과 해시태그 포함"})
    if c2.button("🎨 아이디어스"): 
        st.session_state.texts["아이디어스"] = process_mog_ai({"name": "아이디어스", "desc": "정성을 강조한 짧은 문장 위주"})
    if c3.button("🛍️ 스마트스토어"): 
        st.session_state.texts["스토어"] = process_mog_ai({"name": "스마트스토어", "desc": "깔끔한 정보 정리"})

    for k in ["인스타", "아이디어스", "스토어"]:
        if st.session_state.texts[k]:
            st.info(f"📍 {k} 첫 번째 글이지요^^")
            st.text_area(f"{k} 원본", value=st.session_state.texts[k], height=200, key=f"orig_{k}")
            
            with st.expander(f"✨ 이 글을 다르게 고쳐볼까요?"):
                feed = st.text_input("어떻게 고칠까요?", placeholder="예: 좀 더 짧게 써줘", key=f"f_{k}")
                if st.button("♻️ 다시 정성껏 쓰기", key=f"re_{k}"):
                    st.session_state.refined[k] = process_mog_ai({"name": k, "desc": f"원래 글: {st.session_state.texts[k]}\n요청: {feed}"})
                    st.rerun()
            
            if st.session_state.refined[k]:
                st.success(f"✨ 요청하신 대로 다시 써봤어요!")
                st.text_area(f"{k} 수정본", value=st.session_state.refined[k], height=250, key=f"new_{k}")

# --- Tab 2: 사진 보정법 (세상에서 제일 쉬운 가이드) ---
with tabs[1]:
    st.header("📸 사진 보정, 어렵지 않아요!")
    st.info("엄마! 복잡한 기능 대신 **'자동'** 버튼 하나만 기억하세요🌸")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        #### 💚 네이버 편집기 (가장 쉬움)
        - 스마트스토어 사진 올릴 때 바로 가능!
        - **[편집]** 누르고 **[자동보정]** 클릭
        - 평소 블로그 하시던 대로 하면 돼요^^
        """)
    with col_b:
        st.markdown("""
        #### 🪄 포토(Fotor) AI 보정
        - AI가 사진 조명을 알아서 켜줘요.
        - **[AI 원클릭 보정]** 버튼 하나면 끝!
        """)
        st.link_button("👉 포토 사이트 열기", "https://www.fotor.com/kr/")

# --- Tab 3: 고민 상담소 (카톡 채팅방 형식) ---
with tabs[2]:
    st.header("💬 작가님 고민 상담소")
    if "chat_history" not in st.session_state: st.session_state.chat_history = []

    # 채팅 내역 표시
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.write(m["content"])

    # 입력창
    if prompt := st.chat_input("작가님, 무엇이든 물어보세요..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("생각 중이지요..."):
                ans = process_mog_ai({"name": "상담소", "desc": f"고민 상담: {prompt}. 선배 작가처럼 다정하게 조언해줘."})
                st.write(ans)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()

    if st.button("♻️ 대화 지우기"):
        st.session_state.chat_history = []
        st.rerun()
