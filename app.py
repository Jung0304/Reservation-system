import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 사용자 정보를 저장할 JSON 파일
USER_DATA_FILE = "users.json"
RESERVATIONS_FILE = "reservations.json"  # 예약 정보를 저장할 파일

# 가상의 공간 데이터
spaces = ["GRAY", "BLUE", "SILVER", "GOLD", "GLAB1", "BLAB2"]

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
        return {}

def save_reservations(reservations):
    with open(RESERVATIONS_FILE, "w") as file:
        json.dump(reservations, file)

# 사용자 데이터 로드
users = load_users()

# 회원가입 페이지
def register():
    st.header("회원가입")
    new_username = st.text_input("새 사용자명", key="register_username")
    new_student_id = st.text_input("학번", key="register_student_id")
    new_phone_number = st.text_input("전화번호", key="register_phone_number")

    if st.button("가입하기"):
        if new_username in users:
            st.error("이미 존재하는 사용자명입니다.")
        else:
            users[new_username] = new_student_id
            save_users(users)
            st.success("회원가입과 로그인이 완료되었습니다! 예약 페이지로 이동하세요.")
            st.session_state.logged_in = True
            st.session_state.username = new_username
            st.session_state.student_id = new_student_id

# 로그인 페이지
def login():
    st.header("로그인")
    username = st.text_input("사용자명", key="login_username")
    student_id = st.text_input("학번", key="login_student_id")

    if st.button("로그인"):
        if username in users and users[username] == student_id:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.student_id = student_id
            st.success(f"환영합니다, {username}님!")
        else:
            st.error("로그인 실패: 사용자명 또는 학번이 잘못되었습니다.")

# 예약 타임테이블 생성
def create_timetable():
    hours = [f"{i:02d}:00-{i+1:02d}:00" for i in range(9, 21)]
    df = pd.DataFrame(index=hours, columns=spaces)
    return df

# 하루 최대 4시간 예약 제한 체크
def can_reserve(username):
    reserved_hours = sum(1 for space in spaces if space in st.session_state.reservations for user in st.session_state.reservations[space].values() if user == username)
    return reserved_hours < 4

# 예약 시스템 페이지
def reservation_system():
    if not st.session_state.logged_in:
        st.warning("로그인 후 이용 가능합니다.")
        return

    # 예약 정보 로드 (최신 데이터 동기화)
    if not st.session_state.reservations:
        st.session_state.reservations = load_reservations()

    st.title("당일 공간 예약 시스템")
    st.write(f"안녕하세요, {st.session_state.username}님!")

    today = datetime.now().date()
    st.subheader(f"오늘 날짜: {today}")

    timetable = create_timetable()

    for space in spaces:
        if space in st.session_state.reservations:
            for time, user in st.session_state.reservations[space].items():
                timetable.at[time, space] = user

    cols = st.columns(len(spaces))
    for i, space in enumerate(spaces):
        cols[i].write(f"<h3 style='text-align: center;'>{space}</h3>", unsafe_allow_html=True)

    for time in timetable.index:
        cols = st.columns(len(spaces))
        for i, space in enumerate(spaces):
            button_text = f"{time}"
            if space in st.session_state.reservations and time in st.session_state.reservations[space]:
                cols[i].write(f"🔒 {st.session_state.reservations[space][time]}")
            else:
                if cols[i].button(button_text, key=f"{space}-{time}"):
                    if can_reserve(st.session_state.username):
                        if space not in st.session_state.reservations:
                            st.session_state.reservations[space] = {}
                        st.session_state.reservations[space][time] = st.session_state.username
                        save_reservations(st.session_state.reservations)
                        st.success(f"{space} - {time} 예약이 완료되었습니다!")
                    else:
                        st.warning("하루에 최대 4시간까지만 예약할 수 있습니다.")

# 매일 자정 초기화 기능
def daily_reset():
    current_date = datetime.now().date()
    if 'last_reset' not in st.session_state or datetime.fromisoformat(st.session_state.last_reset).date() < current_date:
        st.session_state.last_reset = datetime.now().isoformat()
        st.session_state.reservations.clear()
        save_reservations({})

def view_reservations():
    if not st.session_state.logged_in:
        st.warning("로그인 후 이용 가능합니다.")
        return

    st.header("내 예약 현황")

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
    daily_reset()
    st.set_page_config(page_title="공간 예약 시스템", page_icon="📅", layout="wide")

    hide_st_style = """
        <style>
        .main {
            background-color: #f0f0f5;
            font-family: 'Arial', sans-serif;
        }
        </style>
        """
    st.markdown(hide_st_style, unsafe_allow_html=True)

    menu_options = ["로그인", "회원가입", "예약 시스템", "내 예약 현황"]
    page = st.sidebar.selectbox("페이지 선택", menu_options)

    if page == "회원가입":
        register()
    elif page == "로그인":
        login()
    elif page == "예약 시스템":
        reservation_system()
    elif page == "내 예약 현황":
        view_reservations()

if __name__ == "__main__":
    main()
