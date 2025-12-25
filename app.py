import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io
import openai
import base64
import json

# 1. 앱 페이지 설정
st.set_page_config(page_title="엄마의 AI 명품 비서", layout="wide")

# 사이드바 API 설정
st.sidebar.header("⚙️ AI 설정")
api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")

st.title("🕯️ 엄마작가님을 위한 AI 통합 비서")
st.write("빈칸에 짧은 단어만 적어주세요. AI가 정성 가득한 판매글로 완성해 드립니다.")

st.divider()

# --- 1. 사진 일괄 AI 보정 (이전 기능 유지) ---
st.header("📸 1. AI 지능형 사진 보정")
uploaded_files = st.file_uploader("보정할 사진들을 선택하세요 (최대 10장)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

if uploaded_files and api_key:
    if st.button("🚀 모든 사진 AI 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        cols = st.columns(len(uploaded_files))
        for idx, file in enumerate(uploaded_files):
            with st.spinner(f"{idx+1}번 분석 중..."):
                img_bytes = file.getvalue()
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [{"type": "text", "text": "이 사진을 분석해서 화사하고 선명하게 보정할 b, c, s 수치를 0.8~1.6 사이 JSON으로 줘. 예: {'b': 1.2, 'c': 1.1, 's': 1.3}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}]}],
                    response_format={ "type": "json_object" }
                )
                res = json.loads(response.choices[0].message.content)
                img = Image.open(io.BytesIO(img_bytes))
                edited = ImageEnhance.Brightness(img).enhance(res.get('b', 1.1))
                edited = ImageEnhance.Color(edited).enhance(res.get('c', 1.1))
                edited = ImageEnhance.Sharpness(edited).enhance(res.get('s', 1.2))
                with cols[idx]:
                    st.image(edited, use_container_width=True)
                    buf = io.BytesIO()
                    edited.save(buf, format="JPEG")
                    st.download_button(f"📥 저장 {idx+1}", buf.getvalue(), f"img_{idx+1}.jpg")

st.divider()

# --- 2. AI 문장 보완 상세페이지 작성 (요청하신 개별 입력창 버전) ---
st.header("✍️ 2. 상세페이지 내용 채우기")
st.write("각 칸에 생각나는 단어들만 툭툭 적어보세요. 나머지는 AI가 예쁘게 써드릴게요!")

# 입력창을 그룹별로 배치
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 기본 정보")
        name = st.text_input("📦 작품 이름", placeholder="예: 린넨 앞치마")
        keys = st.text_area("🔑 핵심 특징/키워드", placeholder="예: 가벼움, 통기성 좋음, 넉넉한 주머니")
        mat = st.text_input("🧵 소재/재질", placeholder="예: 워싱 린넨 100%")
        
    with col2:
        st.subheader("🛠️ 상세 정보")
        size = st.text_input("📏 크기/사이즈", placeholder="예: 프리사이즈 (총장 80cm)")
        process = st.text_area("🛠️ 제작 과정", placeholder="예: 1인 작가가 직접 재단하고 봉제함")
        care = st.text_input("💡 관리/세탁법", placeholder="예: 울코스 단독 세탁 권장")

if st.button("🪄 AI에게 문장 보완 및 글쓰기 요청"):
    if not api_key:
        st.warning("왼쪽 메뉴에 API 키를 입력해주세요!")
    elif not name:
        st.warning("작품 이름을 입력해주세요!")
    else:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        당신은 핸드메이드 작가를 돕는 전문 카피라이터입니다. 
        작가가 입력한 '짧은 메모'를 바탕으로 내용을 풍성하게 보충하여 다정한 판매글을 작성하세요.
        
        [입력 데이터]
        - 작품명: {name}
        - 특징: {keys}
        - 소재: {mat}
        - 사이즈: {size}
        - 제작과정: {process}
        - 관리방법: {care}
        
        [작성 지침]
        1. 작가의 짧은 메모를 감성적이고 전문적인 문장으로 확장할 것. 
           (예: '가벼움' -> '장시간 착용해도 어깨에 무리가 가지 않는 놀라운 가벼움을 선사합니다')
        2. 말투는 정중하고 따스한 1인칭 작가 시점으로 작성할 것.
        3. 완벽한 맞춤법 검사를 수행할 것.
        4. 구성: [작가 인삿말] - [작품의 매력 포인트] - [상세 규격(소재, 크기, 과정)] - [오래 쓰는 관리법] - [끝인사]
        """
        
        with st.spinner("AI 작가가 엄마의 메모를 명품 문장으로 다듬는 중..."):
            try:
                # 최신 gpt-4o 모델을 사용하여 더 자연스러운 문장 생성
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success("✨ 판매글이 예쁘게 완성되었습니다!")
                st.text_area("완성된 결과 (복사해서 사용하세요)", value=response.choices[0].message.content, height=500)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
