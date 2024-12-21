import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 사용자 정보를 저장할 JSON 파일
USER_DATA_FILE = "users.json"
RESERVATIONS_FILE = "reservations.json"  # 예약 정보를 저장할 파일

# 가상의 공간 데이터
spaces = ["GRAY", "BLUE", "SILVER", "GOLD", "GLAB1", "GLAB2"]

# Streamlit 페이지 설정
st.set_page_config(page_title="예공 과방 예약", page_icon="📅", layout="wide")

# CSS 스타일 추가 (배경 색상 및 폰트 스타일)
hide_st_style = """
    <style>
    .main {
        background-color: #f0f0f5;
        font-family: 'Arial', sans-serif;
    }
    h3 {
        font-size: 1.5em;  /* 제목 크기 조정 */
    }
    @media (max-width: 600px) {
        h3 {
            font-size: 1.2em;  /* 모바일에서 제목 크기 조정 */
        }
        .stButton {
            width: 100%;  /* 버튼을 화면 너비에 맞게 조정 */
        }
    }
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'student_id' not in st.session_state:
    st.session_state.student_id = None
if 'reservations' not in st.session_state:
    st.session_state.reservations = {}

# 사용자 정보 로드/저장 함수
def load_users():
    try:
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}  # 초기 관리자 계정 제공하지 않음

def save_users(users):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(users, file)

# 예약 정보 로드/저장 함수
def load_reservations():
    try:
        with open(RESERVATIONS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}  # 초기에는 예약 정보가 없으므로 빈 딕셔너리 반환

def save_reservations(reservations):
    with open(RESERVATIONS_FILE, "w") as file:
        json.dump(reservations, file)

# 사용자 데이터 로드
users = load_users()
# 예약 정보 로드
st.session_state.reservations = load_reservations()

# 예약 타임테이블 생성
def create_timetable():
    hours = [f"{i:02d}:00-{i+1:02d}:00" for i in range(9, 21)]
    df = pd.DataFrame(index=hours, columns=spaces)
    return df

# 하루 최대 4시간 예약 제한 체크
def can_reserve(username):
    reserved_hours = sum(1 for space in spaces if space in st.session_state.reservations for user in 
                         st.session_state.reservations[space].values() if user == username)
    return reserved_hours < 4

# 타임테이블 표시 및 예약/취소 로직
def display_timetable():
    today = datetime.now().date()
    st.subheader(f"오늘 날짜: {today}")

    timetable = create_timetable()

    # 예약 현황 표시
    for space in spaces:
        if space in st.session_state.reservations:
            for time, user in st.session_state.reservations[space].items():
                timetable.at[time, space] = user

    # 타임테이블을 표 형식으로 표시하고 버튼 추가
    cols = st.columns(len(spaces)) 

    # 첫 번째 행에 공간 이름 표시 
    for i, space in enumerate(spaces):
        cols[i].write(f"<h3 style='text-align: center;'>{space}</h3>", unsafe_allow_html=True)

    # 각 공간에 대해 버튼 생성 
    for time in timetable.index:
        cols = st.columns(len(spaces)) 
        for i, space in enumerate(spaces):
            button_text = f"{time}" 
            if space in st.session_state.reservations and time in st.session_state.reservations[space]:
                if st.session_state.reservations[space][time] == st.session_state.username:
                    if cols[i].button(f"예약 취소 {time}", key=f"cancel-{space}-{time}"):
                        del st.session_state.reservations[space][time]
                        save_reservations(st.session_state.reservations)
                        st.success(f"{space} - {time} 예약이 취소되었습니다.")
                else:
                    cols[i].write(f"🔒 {st.session_state.reservations[space][time]}")
                    cols[i].markdown("<span style='color: red;'>예약 완료</span>", unsafe_allow_html=True)
            else:
                if cols[i].button(button_text, key=f"{space}-{time}"):
                    if not can_reserve(st.session_state.username):
                        st.warning("하루에 최대 4시간까지만 예약할 수 있습니다.")
                    if space not in st.session_state.reservations:
                        st.session_state.reservations[space] = {}
                    st.session_state.reservations[space][time] = st.session_state.username
                    save_reservations(st.session_state.reservations)
                    st.success(f"{space} - {time} 예약이 완료되었습니다!")

# 회원가입 페이지
def register():
    st.header("회원가입")
    new_username = st.text_input("성함", key="register_username")
    new_student_id = st.text_input("학번", key="register_student_id")
    new_phone_number = st.text_input("전화번호", key="register_phone_number")

    if st.button("가입하기"):
        if new_username in users:
            st.error("이미 존재하는 사용자명입니다.")
        else:
            users[new_username] = new_student_id  # 학번을 비밀번호 대신 저장
            save_users(users)
            st.success("회원가입과 로그인이 완료되었습니다! 예약 시스템 페이지로 이동하세요.")
            st.session_state.logged_in = True
            st.session_state.username = new_username  
            st.session_state.student_id = new_student_id  

# 로그인 페이지
def login():
    st.header("로그인")
    username = st.text_input("성함", key="login_username")
    student_id = st.text_input("학번", key="login_student_id")

    if st.button("로그인"):
        if username in users:
            if users[username] == student_id:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.student_id = student_id
                st.success(f"환영합니다, {username}님!")
            else:
                st.error("로그인 실패: 학번이 일치하지 않습니다.")
        else:
            st.error("로그인 실패: 존재하지 않는 사용자명입니다.")

    if st.session_state.logged_in:
        st.subheader("예공 과방 예약")
        display_timetable()

# 예약 현황 페이지
def view_reservations():
    if not st.session_state.logged_in:
        st.warning("로그인 후 이용 가능합니다.")
        return

    user_reservations = {space: times for space, times in st.session_state.reservations.items() if any(user == st.session_state.username for user in times.values())}

    if not user_reservations:
        st.write("현재 예약된 공간이 없습니다.")
    else:
        for space, times in user_reservations.items():
            st.subheader(space)
            for time, user in times.items():
                if user == st.session_state.username:
                    st.write(f"예약 시간: {time}")

# 메인 함수
def main():
    menu_options = ["로그인", "회원가입", "예약 페이지", "내 예약 현황"]
    page = st.sidebar.selectbox("페이지 선택", menu_options)

    if page == "로그인":
        login()
    elif page == "회원가입":
        register()
    elif page == "예약 페이지":
        if st.session_state.logged_in:
            st.header("예약 페이지")
            display_timetable()
        else:
            st.warning("로그인 후 이용 가능합니다.")
    elif page == "내 예약 현황":
        view_reservations()

if __name__ == "__main__":
    main()
