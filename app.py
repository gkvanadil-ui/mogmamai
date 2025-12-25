import streamlit as st
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 앱 페이지 설정
st.set_page_config(page_title="모그 AI 스튜디오 Ver 2.0", layout="wide")

# --- API 키 설정 (Secrets 자동 로드) ---
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.sidebar.header("⚙️ AI 설정")
    api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")
else:
    st.sidebar.success("✅ 모그 AI 연결 완료")

st.title("🕯️ 모그(Mog) AI 콘텐츠 스튜디오")
st.write("'세상에 단 하나뿐인 온기'를 전하는 작가님의 콘텐츠 제작을 돕습니다.")

st.divider()

# --- [공통 입력 구역] 작품의 기본 정보 ---
with st.expander("📦 작업할 작품 정보 입력", expanded=True):
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        name = st.text_input("제품명", placeholder="예: 앤과 푸우 보스턴백")
        keys = st.text_area("특징/스토리", placeholder="예: 여행을 꿈꾸며 만든 단 하나뿐인 패치워크")
    with col_in2:
        mat = st.text_input("소재/사이즈", placeholder="예: 유럽 리넨, 가죽 손잡이, 30x40cm")
        process = st.text_area("제작 디테일", placeholder="예: 손바느질 자국, 정성스러운 안감 처리")

# --- [메인 기능] 3개 탭 구성 ---
tabs = st.tabs(["✍️ 글쓰기 센터", "🎨 이미지 스튜디오", "🎬 영상 스튜디오"])

# --- [Tab 1: 글쓰기 센터] ---
with tabs[0]:
    st.subheader("매체별 맞춤 판매글")
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["인스타그램", "아이디어스", "스마트스토어"])
    
    def generate_moog_text(platform, prompt_extra):
        if not api_key or not name:
            st.warning("정보를 모두 입력해주세요.")
            return
        client = openai.OpenAI(api_key=api_key)
        full_prompt = f"""당신은 브랜드 '모그'의 작가입니다. 직접 대화하듯 [{platform}] 글을 작성하세요.
        [지침] 별표(**) 금지, 작가님 특유의 다정한 말투(~이지요, ~했답니다), 본론부터 시작.
        [정보] 제품:{name}, 특징:{keys}, 소재:{mat}, 디테일:{process}
        {prompt_extra}"""
        with st.spinner("작가님의 목소리로 글 쓰는 중..."):
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
            st.text_area(f"{platform} 결과", value=res.choices[0].message.content.replace("**", ""), height=500)

    with sub_tab1:
        if st.button("🪄 인스타 글 생성"):
            generate_moog_text("인스타그램", "요약해서 짧고 감성적으로, 해시태그 포함.")
    with sub_tab2:
        if st.button("🪄 아이디어스 글 생성"):
            generate_moog_text("아이디어스", "한 줄에 한 문장씩 줄바꿈 필수, 제작 스토리 강조.")
    with sub_tab3:
        if st.button("🪄 스마트스토어 글 생성"):
            generate_moog_text("스마트스토어", "구분선과 불렛포인트로 친절하고 상세하게.")

# --- [Tab 2: 이미지 스튜디오] ---
with tabs[1]:
    col_img1, col_img2 = st.columns([1, 1])
    
    with col_img1:
        st.subheader("📸 지능형 사진 보정")
        uploaded_files = st.file_uploader("보정할 사진 선택", type=["jpg", "png"], accept_multiple_files=True)
        if uploaded_files and api_key and st.button("🚀 사진 일괄 보정"):
            # (기존 보정 로직)
            client = openai.OpenAI(api_key=api_key)
            cols = st.columns(2)
            for idx, file in enumerate(uploaded_files):
                img_bytes = file.getvalue()
                encoded = base64.b64encode(img_bytes).decode('utf-8')
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [{"type": "text", "text": "보정 수치 JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}]}],
                    response_format={"type": "json_object"}
                )
                vals = json.loads(res.choices[0].message.content)
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageEnhance.Brightness(img).enhance(vals.get('b', 1.1))
                img = ImageEnhance.Color(img).enhance(vals.get('c', 1.1))
                with cols[idx % 2]:
                    st.image(img, use_container_width=True)
    
    with col_img2:
        st.subheader("📐 상세페이지 설계")
        if st.button("📐 레이아웃 기획안 생성"):
            client = openai.OpenAI(api_key=api_key)
            prompt = f"모그 작가로서 {name}의 상세페이지 구성안을 짜주세요. 섹션 제목, 이미지 배치 제안, 들어갈 문구를 별표 없이 순수 텍스트로 알려주세요."
            with st.spinner("디자인 기획 중..."):
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.text_area("기획안", value=res.choices[0].message.content.replace("**", ""), height=500)

# --- [Tab 3: 영상 스튜디오] ---
with tabs[2]:
    st.subheader("🎬 릴스/쇼츠 동영상 기획")
    v_style = st.radio("어떤 느낌의 영상인가요?", ["작업 과정 ASMR", "작품 스토리텔링", "스타일링 제안"], horizontal=True)
    
    if st.button("🎬 촬영 콘티 및 자막 생성"):
        client = openai.OpenAI(api_key=api_key)
        prompt = f"모그 작가로서 {name}를 홍보할 {v_style} 릴스 콘티를 짜주세요. 초단위 촬영 가이드, 화면 자막, 추천 BGM을 별표 없이 알려주세요."
        with st.spinner("영상 기획 중..."):
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
            st.text_area("릴스 기획안", value=res.choices[0].message.content.replace("**", ""), height=600)
