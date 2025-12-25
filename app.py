import streamlit as st
from rembg import remove
from PIL import Image, ImageDraw, ImageFont
import io

# 앱 설정
st.set_page_config(page_title="엄마의 프리미엄 AI 비서")
st.title("🕯️ 엄마의 프리미엄 AI 비서")
st.write("사진에 작가님의 성함까지 예쁘게 넣어드려요.")

st.divider()

# --- 설정: 작가 이름 정하기 ---
st.sidebar.header("⚙️ 기본 설정")
author_name = st.sidebar.text_input("작가님 성함이나 공방 이름", value="엄마작가")

# --- 1단계: 고급 설정샷 + 이름표 만들기 ---
st.header("📸 1. 프리미엄 사진 만들기")
uploaded_file = st.file_uploader("작품 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="원본 사진", width=300)
    
    if st.button("✨ 고급 배경 + 이름표 넣기"):
        with st.spinner("AI 작가가 작업 중입니다..."):
            # 1. 배경 제거
            input_bytes = uploaded_file.getvalue()
            output_bytes = remove(input_bytes)
            subject = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
            
            # 2. 고급스러운 베이지톤 배경 생성
            bg_color = (242, 235, 225) 
            canvas = Image.new("RGBA", subject.size, bg_color)
            canvas.paste(subject, (0, 0), subject)
            
            # 3. 작가 이름표(도장) 넣기
            draw = ImageDraw.Draw(canvas)
            # 오른쪽 하단에 이름 넣기
            text = f"Handmade by {author_name}"
            # 글자 크기를 사진 크기에 맞춰 조절
            width, height = canvas.size
            margin = int(width * 0.05)
            
            # 폰트 설정 (기본 폰트 사용, 크기만 조절)
            draw.text((width - margin - 250, height - margin - 50), text, fill=(142, 115, 91, 180))
            
            final_img = canvas.convert("RGB")
            st.image(final_img, caption="완성된 작가님 전용 사진!", width=400)
            
            # 저장 버튼
            buf = io.BytesIO()
            final_img.save(buf, format="JPEG", quality=95)
            st.download_button("📥 도장 찍힌 사진 저장하기", buf.getvalue(), "artist_photo.jpg")

st.divider()

# --- 2단계: 친절한 상품 설명 (동일) ---
st.header("✍️ 2. 정성 가득한 설명 쓰기")
name = st.text_input("제품 이름")
detail = st.text_area("작품에 담긴 정성")

if st.button("🪄 친절한 설명글 만들기"):
    if name and detail:
        full_text = f"안녕하세요, **{author_name}** 작가입니다. 😊\n\n이번 작품은 **[{name}]**입니다.\n\n{detail}\n\n작가인 제가 직접 검수하여 정성껏 보내드립니다. 🌸"
        st.success("글 완성!")
        st.text_area("복사하기", value=full_text, height=250)
