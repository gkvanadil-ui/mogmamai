import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import io
import openai
import base64
import json

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="centered")

# --- CSS: 다크모드 시인성 및 버튼 크기 최적화 ---
st.markdown("""
    <style>
    /* 기본 글자색 및 배경 대응 */
    html, body, [data-testid="stAppViewContainer"] { color: inherit; }
    h1, h2, h3 { color: #D4A373 !important; font-weight: bold !important; margin-bottom: 12px; }
    
    /* 50대 사용자를 위한 큰 버튼 스타일 */
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.8em;
        background-color: #7d6e63; color: white !important;
        font-weight: bold; font-size: 18px !important;
        border: none; margin-bottom: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* 텍스트 입력 영역 가독성 보강 */
    .stTextArea textarea {
        font-size: 17px !important;
        line-height: 1.6 !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: inherit !important;
        border: 1px solid #7d6e63 !important;
    }
    
    /* 탭 메뉴 디자인 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 55px; border-radius: 10px 10px 0 0;
        padding: 5px 20px; font-weight: bold; font-size: 16px !important;
    }
    
    hr { border-top: 1px solid #7d6e63; opacity: 0.3; }
    </style>
    """, unsafe_allow_html=True)

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

st.title("🕯️ 모그(Mog) 작가 전용 비서")
st.write("<p style='text-align: center;'>작가님의 따스한 손길이 담긴 작품을 세상에 알립니다🌸</p>", unsafe_allow_html=True)

# --- [1단계: 공통 정보 입력] ---
st.header("1️⃣ 작품 정보 입력")
with st.expander("📝 이곳을 터치해서 정성껏 내용을 적어주세요", expanded=True):
    name = st.text_input("📦 작품 이름", placeholder="예: 빈티지 튤립 뜨개 파우치")
    c1, c2 = st.columns(2)
    with c1:
        mat = st.text_input("🧵 소재", placeholder="코튼 100%")
        size = st.text_input("📏 크기", placeholder="20*15cm")
    with c2:
        period = st.text_input("⏳ 제작 기간", placeholder="주문 후 3일")
        care = st.text_input("💡 세탁 방법", placeholder="미온수 손세탁 권장")
    keys = st.text_area("🔑 작품 특징", placeholder="색감이 화사해서 포인트 아이템으로 좋아요.")
    process = st.text_area("🛠️ 제작 포인트", placeholder="안감까지 꼼꼼히 제작했습니다.")

st.divider()

# --- AI 처리 함수 ---
def process_ai_text(full_prompt):
    if not api_key: return None
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
        # 볼드체(**) 제거 및 정제하여 출력
        return response.choices[0].message.content.replace("**", "").strip()
    except: return "오류가 발생했습니다. 다시 시도해 주세요."

# --- [2단계: 작업실 선택] ---
st.header("2️⃣ 작업실 선택")
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진보정", "💡 캔바 & 에픽"])

# --- Tab 1: 판매글 쓰기 (어투 프롬프트 완벽 복구) ---
with tabs[0]:
    st.subheader("✍️ 작가님 말투 판매글")
    st.write("💡 아래 버튼을 누르면 '모그 작가' 말투로 글이 써집니다.")
    
    if 'texts' not in st.session_state:
        st.session_state.texts = {"인스타그램": "", "아이디어스": "", "네이버 스마트스토어": ""}

    btn_col1, btn_col2, btn_col3 = st.columns(3)
    platform = None
    
    if btn_col1.button("📸 인스타"): platform = "인스타그램"
    if btn_col2.button("🎨 아이디어스"): platform = "아이디어스"
    if btn_col3.button("🛍️ 스토어"): platform = "네이버 스마트스토어"

    if platform:
        with st.spinner(f"[{platform}]용 글을 다정하게 작성 중..."):
            # 플랫폼별 맞춤 가이드
            guide_text = ""
            if platform == "인스타그램": guide_text = "해시태그를 포함하고, 계절 인사를 섞은 감성 일기처럼 써주세요."
            elif platform == "아이디어스": guide_text = "문장을 짧게 끊고 줄바꿈을 아주 자주 하세요. 꽃과 하트 이모지를 풍성하게 써주세요."
            else: guide_text = "구분선(⸻)을 활용해 정보를 깔끔하게 정리해 주세요."

            # 복구된 작가님 전용 프롬프트
            full_prompt = f"""
            당신은 핸드메이드 브랜드 '모그(Mog)'를 운영하는 작가입니다. 
            [{platform}] 에 올릴 상세 판매글을 정성스럽게 작성하세요.

            [말투 지침 - 반드시 준수]
            1. 엄마처럼 다정한 말투를 사용하세요 (~이지요^^, ~해요, ~좋아요, ~보내드려요).
            2. 절대로 별표(*)나 볼드체 기호를 사용하지 마세요. (순수한 텍스트만 출력)
            3. 문장 끝에 '^^'를 적절히 사용하고, 꽃(🌸,🌻), 반짝이(✨) 이모지를 섞어주세요.

            [플랫폼 지침]
            {guide_text}

            [작품 정보]
            이름: {name} / 특징: {keys} / 소재: {mat} / 사이즈: {size} / 제작: {process} / 관리: {care} / 기간: {period}
            """
            st.session_state.texts[platform] = process_ai_text(full_prompt)
    
    for p_key in ["인스타그램", "아이디어스", "네이버 스마트스토어"]:
        if st.session_state.texts[p_key]:
            st.write(f"---")
            st.write(f"**✅ {p_key} 결과**")
            st.text_area(f"{p_key}용 글 (꾹 눌러 복사)", value=st.session_state.texts[p_key], height=350, key=f"txt_{p_key}")

# --- Tab 2: 사진보정 (AI 자율 분석 프롬프트 복구) ---
with tabs[1]:
    st.subheader("📸 AI 자율 분석 보정")
    st.write("AI가 사진을 직접 보고 어두운 부분과 색감을 스스로 판단하여 고쳐드립니다.")
    uploaded_files = st.file_uploader("보정할 사진 선택", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files and api_key and st.button("🚀 AI 자동 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        for idx, file in enumerate(uploaded_files):
            img_bytes = file.getvalue()
            try:
                b64_img = base64.b64encode(img_bytes).decode('utf-8')
                # 복구된 자율 분석 프롬프트
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": """이 사진은 핸드메이드 제품 사진입니다. 
                        사진의 밝기, 대비, 채도, 선명도를 분석하여 가장 깔끔하고 화사하게 보정할 수 있는 수치를 JSON으로 답하세요.
                        - 밝기(b): 어두우면 1.2, 너무 밝으면 0.9 / 대비(c): 0.9~1.2 / 채도(s): 1.0~1.2 / 선명도(sh): 1.0~2.0
                        형식: {"b": 수치, "c": 수치, "s": 수치, "sh": 수치}"""},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]}],
                    response_format={ "type": "json_object" }
                )
                res = json.loads(response.choices[0].message.content)
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageOps.exif_transpose(img) # 사진 회전 방지
                
                # AI 제안 수치로 보정 적용
                img = ImageEnhance.Brightness(img).enhance(res.get('b', 1.1))
                img = ImageEnhance.Contrast(img).enhance(res.get('c', 1.0))
                img = ImageEnhance.Color(img).enhance(res.get('s', 1.0))
                img = ImageEnhance.Sharpness(img).enhance(res.get('sh', 1.2))
                
                st.image(img, caption=f"AI 분석 보정 완료 {idx+1}")
                buf = io.BytesIO(); img.save(buf, format="JPEG")
                st.download_button(f"📥 {idx+1}번 사진 저장", buf.getvalue(), f"mog_img_{idx+1}.jpg")
            except: st.error(f"{idx+1}번 사진 보정 실패")

# --- Tab 3: 캔바 & 에픽 ---
with tabs[2]:
    st.subheader("🎨 상세페이지 & 영상 꿀팁")
    st.link_button("✨ 캔바(Canva) 앱 열기", "https://www.canva.com/templates/?query=상세페이지")
    
    if st.button("🪄 상세페이지 기획안 만들기"):
        if not name: st.warning("위쪽 '작품 정보'를 먼저 입력해 주셔요🌸")
        else:
            with st.spinner("기획안을 짜고 있어요..."):
                prompt = f"모그 작가 말투로 {name} 작품의 상세페이지 5장 기획안을 작성해 주세요. JSON 형식이 아닌 읽기 편한 텍스트로 답해줘."
                res_canva = process_ai_text(prompt)
                st.write(res_canva)
    
    st.divider()
    
    st.subheader("🎥 감성 영상 제작 (에픽)")
    with st.expander("📺 에픽(EPIK) 사용 방법"):
        st.info("""
        1. **에픽 앱**을 켜고 하단 **[템플릿]** 메뉴를 누르세요.
        2. 검색창에 **'감성'**이나 **'핸드메이드'**를 검색합니다.
        3. 맘에 드는 양식을 골라 **[사용하기]**를 누르고, 사진을 선택하세요.
        4. 오른쪽 위 **[저장]**을 누르면 끝! 🌸
        """)
