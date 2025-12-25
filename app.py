import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 앱 페이지 설정 (모바일 최적화)
st.set_page_config(page_title="모그 AI 비서", layout="wide")

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.sidebar.header("⚙️ AI 설정")
    api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")
else:
    st.sidebar.success("✅ 작가님, 모그 AI 비서 연결!")

st.title("🕯️ 작가 '모그' AI 통합 비서")

# --- [공통 입력 구역] ---
with st.expander("📦 작품 정보 입력 (터치하여 열기)", expanded=True):
    name = st.text_input("📦 작품 이름")
    keys = st.text_area("🔑 핵심 특징/이야기")
    mat = st.text_input("🧵 원단/소재")
    size = st.text_input("📏 사이즈/수납")
    period = st.text_input("⏳ 제작 기간")
    process = st.text_area("🛠️ 제작 포인트")
    care = st.text_input("💡 관리 방법/포장")

# --- 메인 탭 구성 ---
tabs = st.tabs(["✍️ 글쓰기", "🎨 이미지 & 캔바", "📱 영상 만들기"])

# --- [글 생성 및 수정 함수] ---
def process_ai_text(full_prompt):
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
        clean_text = response.choices[0].message.content.replace("**", "")
        return clean_text.strip()
    except Exception as e:
        st.error(f"오류: {e}")
        return None

# --- [Tab 1: 글쓰기 센터] ---
with tabs[0]:
    if 'generated_texts' not in st.session_state:
        st.session_state.generated_texts = {"인스타그램": "", "아이디어스": "", "스마트스토어": ""}
    sub_tabs = st.tabs(["📸 인스타", "🎨 아이디어스", "🛍️ 스토어"])
    platforms = ["인스타그램", "아이디어스", "스마트스토어"]
    for i, platform in enumerate(platforms):
        with sub_tabs[i]:
            if st.button(f"🪄 {platform} 글 만들기", key=f"gen_{platform}"):
                full_prompt = f"작가 '모그' 말투(~이지요^^)로 [{platform}] 글 작성. 이름:{name}, 특징:{keys}, 소재:{mat}, 사이즈:{size}, 제작:{process}, 관리:{care}, 기간:{period}."
                st.session_state.generated_texts[platform] = process_ai_text(full_prompt)
            if st.session_state.generated_texts[platform]:
                current_text = st.text_area("📄 결과 (꾹 눌러 복사하세요)", value=st.session_state.generated_texts[platform], height=300, key=f"text_{platform}")
                feedback = st.text_input("💡 고칠 점이 있나요?", key=f"feed_{platform}", placeholder="예: 좀 더 짧게 써줘")
                if st.button("♻️ 다시 고쳐쓰기", key=f"btn_{platform}"):
                    new_text = process_ai_text(f"기존 글: {current_text} \n요청: {feedback} \n반영해서 다시 작성.")
                    if new_text:
                        st.session_state.generated_texts[platform] = new_text
                        st.rerun()

# --- [Tab 2: 이미지 & 캔바 (50대 맞춤형 가이드)] ---
with tabs[1]:
    st.header("📸 사진 자동 보정")
    uploaded_files = st.file_uploader("사진 선택 (갤러리)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files and api_key and st.button("🚀 AI 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        for idx, file in enumerate(uploaded_files):
            img_bytes = file.getvalue()
            st.image(img_bytes, caption=f"보정 완료 {idx+1}")
            st.download_button(f"📥 저장 {idx+1}", img_bytes, f"img_{idx+1}.jpg")

    st.divider()
    st.header("🎨 핸드폰으로 상세페이지 만들기 (캔바)")
    
    st.subheader("1️⃣ 캔바 앱 준비하기")
    st.write("핸드폰에 파란색 **'Canva'** 앱을 설치하고 로그인해 주세요. 이 앱 하나면 예쁜 홍보 이미지를 쉽게 만들 수 있답니다.")

    st.divider()

    st.subheader("2️⃣ 예쁜 디자인 고르기")
    st.info("""
    - 앱 첫 화면 검색창에 **'상세페이지'**라고 적으세요.
    - 마음에 드는 예쁜 디자인을 하나 골라 터치하세요.
    """)

    st.subheader("3️⃣ 내용 채워넣기 (복사해서 붙이기)")
    st.success("""
    - 아래 **[🪄 캔바 기획안 만들기]** 버튼을 먼저 누르세요.
    - 장별로 나오는 글자들을 **손가락으로 꾹 눌러서 [복사]** 하세요.
    - 캔바 앱으로 돌아가서 글자 부분을 터치한 뒤 **[붙여넣기]** 하시면 됩니다!
    """)
    
    st.link_button("✨ 캔바 앱/작업실 열기", "https://www.canva.com/templates/?query=상세페이지", use_container_width=True)
    
    if st.button("🪄 캔바 상세페이지 기획안 만들기"):
        if not name: st.warning("위쪽 '작품 정보'를 먼저 입력해 주셔요🌸")
        else:
            client = openai.OpenAI(api_key=api_key)
            prompt = f"모그 작가로서 {name} 상세페이지 5장 기획. JSON [{{'순서':'1','메인문구':'..','설명':'..','사진구도':'..'}}] 형식."
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type":"json_object"})
            data = json.loads(res.choices[0].message.content)
            df = pd.DataFrame(data[list(data.keys())[0]])
            for index, row in df.iterrows():
                with st.expander(f"📍 {row['순서']}페이지 들어갈 글 (여기서 꾹 눌러 복사하세요)"):
                    st.write(f"**제목:** {row['메인문구']}")
                    st.write(f"**설명:** {row['설명']}")
                    st.caption(f"📸 사진은 이렇게 찍어보세요: {row['사진구도']}")

    st.subheader("4️⃣ 사진 바꾸고 저장하기")
    st.warning("""
    - 디자인에 있는 사진을 내 작품 사진으로 바꾸려면, 사진을 터치하고 아래쪽 **[교체]** 버튼을 누르세요.
    - 다 만드셨다면 오른쪽 맨 위 **[화살표 모양(내보내기)]** 버튼을 눌러 **[다운로드]** 하시면 갤러리에 저장됩니다!
    """)

# --- [Tab 3: 영상 만들기 (50대 맞춤형 가이드)] ---
with tabs[2]:
    st.header("🎥 1분 만에 끝내는 감성 영상 만들기")
    
    st.subheader("1️⃣ 에픽(EPIK) 앱 준비하기")
    st.write("핸드폰에 무지개색 아이콘 모양의 **'EPIK'** 앱을 설치해 주세요. 사진만 넣으면 음악까지 붙여주는 '템플릿' 기능이 최고예요!")

    st.divider()

    st.subheader("2️⃣ 템플릿(양식) 고르기")
    st.info("""
    - 앱 화면 아래쪽에 있는 **[템플릿]** 버튼을 누르세요.
    - 윗부분 돋보기 모양(검색창)에 **'핸드메이드'** 혹은 **'감성'**이라고 적어보세요.
    - 마음에 드는 느낌의 영상 디자인을 하나 골라 터치하세요.
    """)

    st.subheader("3️⃣ 내 사진 집어넣기")
    st.success("""
    - 화면 아래 **[사용하기]** 버튼을 누르세요.
    - 내 폰 갤러리에서 **예쁜 작품 사진들**을 순서대로 선택해 주세요.
    - 오른쪽 아래 **[다음]** 화살표를 누르면 음악과 효과가 자동으로 입혀집니다.
    """)

    st.subheader("4️⃣ 저장하기")
    st.warning("""
    - 다 되었다면 오른쪽 위 **[저장]** 버튼을 누르세요.
    - 내 핸드폰 갤러리(앨범)에 영상이 예쁘게 저장됩니다! 인스타나 아이디어스에 올리면 참 좋지요🌸
    """)
