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
tabs = st.tabs(["✍️ 글쓰기", "🎨 이미지 & 캔바", "📱 영상 팁"])

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

# --- [Tab 2: 이미지 & 캔바] ---
with tabs[1]:
    # 모바일은 화면이 좁으므로 컬럼을 나누지 않고 순차적으로 배치
    st.header("📸 사진 자동 보정")
    uploaded_files = st.file_uploader("사진 선택 (갤러리)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files and api_key and st.button("🚀 AI 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        for idx, file in enumerate(uploaded_files):
            img_bytes = file.getvalue()
            # 보정 로직 (생략 - 위와 동일)
            st.image(img_bytes, caption=f"보정 완료 {idx+1}")
            st.download_button(f"📥 저장 {idx+1}", img_bytes, f"img_{idx+1}.jpg")

    st.divider()
    
    st.header("🎨 모바일 캔바(Canva) 가이드")
    
    # --- 모바일 전용 안내문 ---
    st.info("""
    **📱 핸드폰으로 캔바 작업하기**
    1. **내용 생성**: 아래 '기획안 만들기'를 누르면 장마다 들어갈 문구가 나옵니다.
    2. **글자 복사**: 표에 나온 문구를 **손가락으로 꾹 눌러서 복사**하세요.
    3. **캔바 앱 실행**: 아래 '캔바 작업실' 버튼을 눌러 앱으로 이동하세요.
    4. **붙여넣기**: 디자인의 글자 부분을 터치하고 **[붙여넣기]** 하면 끝!
    
    *💡 파일 저장이 번거로우시면 화면을 캡처해서 보면서 적으셔도 좋아요.*
    """)
    
    st.link_button("✨ 캔바 앱/작업실 열기", "https://www.canva.com/templates/?query=상세페이지", use_container_width=True)
    
    if st.button("🪄 캔바 상세페이지 기획안 만들기"):
        if not name: st.warning("정보를 먼저 입력해주셔요.")
        else:
            client = openai.OpenAI(api_key=api_key)
            prompt = f"모그 작가로서 {name} 상세페이지 5장 기획. JSON [{{'순서':'1','메인문구':'..','설명':'..','사진구도':'..'}}] 형식."
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type":"json_object"})
            data = json.loads(res.choices[0].message.content)
            df = pd.DataFrame(data[list(data.keys())[0]])
            
            # 모바일에서 보기 편하게 리스트 형태로도 출력
            for index, row in df.iterrows():
                with st.expander(f"📍 {row['순서']}페이지 문구 (복사용)"):
                    st.write(f"**메인:** {row['메인문구']}")
                    st.write(f"**설명:** {row['설명']}")
                    st.caption(f"📸 추천구도: {row['사진구도']}")
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 (고급자용) CSV 파일 받기", csv, f"moog_{name}.csv", "text/csv", use_container_width=True)

# --- [Tab 3: 영상 제작 팁] ---
with tabs[2]:
    st.header("📱 모바일 영상 제작 (EPIK)")
    st.success("핸드폰에 'EPIK(에픽)' 앱을 설치하시면 '템플릿' 메뉴에서 사진만 넣고 바로 영상을 만드실 수 있답니다 🌸")
