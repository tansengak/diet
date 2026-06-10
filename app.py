import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="식단 기록 앱", layout="wide")

# 데이터 파일 관리
DATA_FILE = "diet_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "날짜", "끼니", "음식", "탄수화물", "단백질", "지방", "칼로리", "몸무게", "운동칼로리"
    ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# AI 분석 함수
def analyze_diet_with_ai(text, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    아래 텍스트를 분석해서 JSON 형식으로 추출해줘. 
    필드: 끼니(아침/점심/저녁/간식), 음식, 탄수화물(g), 단백질(g), 지방(g), 칼로리(kcal).
    값은 숫자만 넣고, 단위는 제외해.
    텍스트: {text}
    형식: {{"meal": "...", "food": "...", "carbs": 0, "protein": 0, "fat": 0, "calories": 0}}
    """
    response = model.generate_content(prompt)
    return json.loads(response.text.replace('```json', '').replace('```', ''))

# 사이드바: 설정
st.sidebar.title("설정")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

# 탭 구성
tab1, tab2 = st.tabs(["기록하기", "대시보드"])

df = load_data()

with tab1:
    st.header("오늘의 식단 기록")
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        diet_text = col1.text_input("식단 입력 (예: 아침에 닭가슴살 100g이랑 사과 하나 먹었어)")
        weight = col2.number_input("몸무게 (kg)", min_value=0.0, format="%.1f")
        exercise = col2.number_input("운동 소모 칼로리 (kcal)", min_value=0)
        
        submit = st.form_submit_button("기록 저장")
        
        if submit and api_key:
            try:
                data = analyze_diet_with_ai(diet_text, api_key)
                new_entry = {
                    "날짜": datetime.now().strftime("%Y-%m-%d"),
                    "끼니": data['meal'],
                    "음식": data['food'],
                    "탄수화물": data['carbs'],
                    "단백질": data['protein'],
                    "지방": data['fat'],
                    "칼로리": data['calories'],
                    "몸무게": weight,
                    "운동칼로리": exercise
                }
                df = pd.concat([pd.DataFrame([new_entry]), df], ignore_index=True)
                save_data(df)
                st.success("저장 완료!")
            except Exception as e:
                st.error(f"분석 오류: {e}")

    st.subheader("기록 수정 및 확인")
    edited_df = st.data_editor(df, num_rows="dynamic")
    if st.button("수정 내용 저장"):
        save_data(edited_df)
        st.experimental_rerun()

with tab2:
    st.header("대시보드")
    if not df.empty:
        df['날짜'] = pd.to_datetime(df['날짜'])
        
        # 일일 요약
        daily_df = df.groupby('날짜')[['탄수화물', '단백질', '지방', '칼로리']].sum()
        st.subheader("일일 섭취 요약")
        st.table(daily_df.sort_index(ascending=False).head(7))
        
        # 라인 차트
        st.subheader("칼로리 추세")
        st.line_chart(daily_df['칼로리'])
    else:
        st.write("데이터가 없습니다.")
