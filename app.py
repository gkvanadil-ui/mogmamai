import streamlit as st
from rembg import remove
from PIL import Image
import io
import requests

# 앱 설정
st.set_page_config(page_title="엄마의 프리미엄 AI 비서")
st.title("☕ 카페 설정샷 자동 완성")
st.write("작품 사진만 올리세요. AI가 카페 테이블로 옮겨드립니다!")

# 고급 배경 이미지 리스트 (무료 이미지 주소)
# 1. 따뜻한 원목 테이블, 2. 하얀 대리석 테이블
BG_URLS = {
    "따뜻한 나무 테이블": "https://images.unsplash.com/photo-1517705008128-361805f42e86?q=80&w=1000&auto=format&fit=crop",
    "깔끔한 화이트 대리석": "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?q=80&w=1000&auto=format&fit=crop"
}

st.divider()

# --- 설정: 작가 이름 및 배경 선택 ---
st.sidebar.header("⚙️ 연출 설정")
author_name = st.sidebar.text_input("작가 이름", value="엄마작가")
selected_bg = st.sidebar.selectbox("배경 스타일 선택", list(BG_URLS.keys()))

# --- 1단계: 카페 설정샷 만들기 ---
st.header("📸 1. 사진 변형하기")
uploaded_file = st.file_uploader("작품 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="원본 사진", width=300)
    
    if st.button("✨ 카페 설정샷으로 변신!"):
        with st.spinner("배경을 바꾸고 소품을 배치 중입니다..."):
            # 1. 엄마 사진 배경 제거
            input_bytes = uploaded_file.getvalue()
            subject_bytes = remove(input_bytes)
            subject = Image.open(io.BytesIO(subject_bytes)).convert("RGBA")
            
            # 2. 선택한 카페 배경 불러오기
            response = requests.get(BG_URLS[selected_bg])
            background = Image.open(io.BytesIO(response.content)).convert("RGBA")
            
            # 3. 배경 크기에 맞게 작품 크기 조절 (배경의 약 50% 크기로)
            bg_w, bg_h = background.size
            ratio = (bg_w * 0.5) / subject.width
            new_size = (int(subject.width * ratio), int(subject.height * ratio))
            subject = subject.resize(new_size, Image.LANCZOS)
            
            # 4. 배경 정중앙에 배치 (약간 아래쪽으로)
            paste_x = (bg_w - subject.width) // 2
            paste_y = (bg_h - subject.height) // 2 + 100
            
            # 합성
            background.paste(subject, (paste_x, paste_y), subject)
            
            # 5. 작가 이름표 넣기 (이미지 하단)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(background)
            text = f"Handmade by {author_name}"
            draw.text((bg_w - 400, bg_h - 100), text, fill=(255, 255, 255, 150))
            
            final_img = background.convert("RGB")
            st.image(final_img, caption="카페 설정샷 완성!", use_container_width=True)
            
            # 저장 버튼
            buf = io.BytesIO()
            final_img.save(buf, format="JPEG", quality=90)
            st.download_button("📥 완성된 사진 저장하기", buf.getvalue(), "cafe_style.jpg")

st.divider()
# (글쓰기 기능은 이전과 동일하게 유지)
st.header("✍️ 2. 상세페이지 글쓰기")
st.write("이름과 정성을 입력하면 친절한 문구로 바꿔드려요.")
