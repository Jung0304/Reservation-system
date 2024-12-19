import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 사용자 정보를 저장할 JSON 파일
USER_DATA_FILE = "users.json"
RESERVATIONS_FILE = "reservations.json"  # 예약 정보를 저장할 파일

# 가상의 공간 데이터
spaces = ["GRAY", "BLUE", "SILVER", "GOLD", "GLAB1", "GLAB2"]

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

# 회원가입 페이지
def register():
    st.header("회원가입")
    new_username = st.text_input("새 사용자명", key="register_username")
    new_student_id = st.text_input("학번", key="register_student_id")  # 학번 입력 추가
    new_phone_number = st.text_input("전화번호", key="register_phone_number")  # 전화번호 입력 추가
    
    if st.button("가입하기"):
        if new_username in users:
            st.error("이미 존재하는 사용자명입니다.")
        else:
            # 학번을 사용자명으로 사용하여 저장 (비밀번호 없음)
            users[new_username] = new_student_id  # 학번을 비밀번호 대신 저장
            save_users(users)
            st.success("회원가입과 로그인이 완료되었습니다! 예약 시스템 페이지로 이동하세요.")
            # 로그인 상태 업데이트
            st.session_state.logged_in = True
            st.session_state.username = new_username  # 자동 로그인 처리
            st.session_state.student_id = new_student_id  # 학번도 세션에 저장

# 로그인 페이지
def login():
    st.header("로그인")
    username = st.text_input("사용자명", key="login_username")
    student_id = st.text_input("학번", key="login_student_id")  # 학번 입력 추가
    
    if st.button("로그인"):
        if username in users and users[username] == student_id:  # 비밀번호 체크 시 학번 사용
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.student_id = student_id  # 학번도 세션에 저장
            st.success(f"환영합니다, {username}님!")
            
            # 로그인 후 예약 페이지로 이동
            reservation_system()  # 예약 시스템 함수 호출

        else:
            st.error("로그인 실패: 사용자명 또는 학번이 잘못되었습니다.")

# 예약 타임테이블 생성
def create_timetable():
    hours = [f"{i:02d}:00-{i+1:02d}:00" for i in range(9, 21)]  # 9AM to 9PM (1시간 단위)
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
    
    # 페이지 제목 및 환영 메시지
    st.title("당일 공간 예약 시스템")
    st.write(f"안녕하세요, {st.session_state.username}님!")
    
    today = datetime.now().date()
    st.subheader(f"오늘 날짜: {today}")

    timetable = create_timetable()

    # 예약 현황 표시 (세션 상태에서 가져오기)
    for space in spaces:
        if space in st.session_state.reservations:
            for time, user in st.session_state.reservations[space].items():
                timetable.at[time, space] = user

    # 타임테이블을 표 형식으로 표시하고 버튼 추가
    cols = st.columns(len(spaces))  # 공간 수

    # 첫 번째 행에 공간 이름 표시 
    for i, space in enumerate(spaces):
        cols[i].write(f"<h3 style='text-align: center;'>{space}</h3>", unsafe_allow_html=True)  # 공간 이름 표시

    # 각 공간에 대해 버튼 생성 (시간은 버튼 안에 포함)
    for time in timetable.index:
        cols = st.columns(len(spaces))  # 공간 수
        
        for i, space in enumerate(spaces):
            button_text = f"{time}"  # 버튼 안에 시간 표시
            
            # 예약된 경우 예약자 이름 표시
            if space in st.session_state.reservations and time in st.session_state.reservations[space]:
                cols[i].write(f"🔒 {st.session_state.reservations[space][time]}")
                cols[i].markdown("<span style='color: red;'>예약 완료</span>", unsafe_allow_html=True)
            else:
                # 예약 가능한 경우 버튼 표시 (버튼 크기 조정)
                if cols[i].button(button_text, key=f"{space}-{time}", help=f"{space} 예약하기"):
                    # 예약 가능 여부 체크
                    if not can_reserve(st.session_state.username):
                        st.warning("하루에 최대 4시간까지만 예약할 수 있습니다.")
                        return
                    
                    # 예약 데이터 저장 (세션 상태에 저장)
                    if space not in st.session_state.reservations:
                        st.session_state.reservations[space] = {}
                    st.session_state.reservations[space][time] = st.session_state.username
                    
                    # 성공 메시지 및 파일에 저장 후 페이지 새로고침 없이 유지하도록 설정합니다.
                    save_reservations(st.session_state.reservations)  # 파일에 저장 
                    st.success(f"{space} - {time} 예약이 완료되었습니다!")

# 매일 자정마다 예약 초기화 기능 추가 
def daily_reset():
   if 'last_reset' not in st.session_state or datetime.now().date() > datetime.fromisoformat(st.session_state.last_reset).date():
       # 오늘 날짜로 업데이트하고 세션 상태 초기화 
       st.session_state.last_reset = datetime.now().isoformat()
       st.session_state.reservations.clear()  # 모든 예약 정보 초기화 

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

# 메인 함수 업데이트
def main():
   daily_reset()  # 매일 자정마다 초기화 기능 호출

   # Streamlit 페이지 설정 및 배경 색상 추가
   st.set_page_config(page_title="공간 예약 시스템", page_icon="📅", layout="wide")

   # CSS 스타일 추가 (배경 색상 및 폰트 스타일)
   hide_st_style = """
       <style>
       .main {
           background-color: #f0f0f5;
           font-family: 'Arial', sans-serif;
       }
       </style>
       """
   
   # CSS 스타일 적용
   st.markdown(hide_st_style, unsafe_allow_html=True)

   # 사이드바 메뉴 설정 - 로그인 페이지를 먼저 보여주기 위해 순서 변경 
   menu_options = ["로그인", "회원가입", "예약 시스템", "내 예약 현황"]
   
   page = st.sidebar.selectbox("페이지 선택", menu_options)

   # 선택된 페이지에 따라 함수 호출
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
