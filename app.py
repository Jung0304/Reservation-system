import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 사용자 정보를 저장할 SQLite 데이터베이스
DATABASE_FILE = "users.db"
RESERVATIONS_FILE = "reservations.db"  # 예약 정보를 저장할 데이터베이스 파일

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

# 데이터베이스 초기화 및 테이블 생성
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            phone_number TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            space TEXT,
            time TEXT,
            username TEXT,
            PRIMARY KEY (space, time),
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# 회원가입 페이지
def register():
    st.header("회원가입")
    new_username = st.text_input("새 사용자명", key="register_username")
    new_student_id = st.text_input("학번", key="register_student_id")
    new_phone_number = st.text_input("전화번호", key="register_phone_number")
    
    if st.button("가입하기"):
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO users (username, student_id, phone_number) VALUES (?, ?, ?)",
                      (new_username, new_student_id, new_phone_number))
            conn.commit()
            st.success("회원가입이 완료되었습니다! 로그인 페이지로 이동하세요.")
            # 로그인 상태 업데이트
            st.session_state.logged_in = True
            st.session_state.username = new_username  # 자동 로그인 처리
            st.session_state.student_id = new_student_id
            
        except sqlite3.IntegrityError:
            st.error("이미 존재하는 사용자명입니다.")
        
        conn.close()

# 로그인 페이지
def login():
    st.header("로그인")
    username = st.text_input("사용자명", key="login_username")
    student_id = st.text_input("학번", key="login_student_id")
    
    if st.button("로그인"):
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        c.execute("SELECT student_id FROM users WHERE username=?", (username,))
        result = c.fetchone()
        
        if result and result[0] == student_id:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.student_id = student_id
            st.success(f"환영합니다, {username}님!")
            
            # 로그인 후 예약 페이지로 이동
            reservation_system()  
            
        else:
            st.error("로그인 실패: 사용자명 또는 학번이 잘못되었습니다.")
        
        conn.close()

# 예약 타임테이블 생성
def create_timetable():
    hours = [f"{i:02d}:00-{i+1:02d}:00" for i in range(9, 21)]  # 9AM to 9PM (1시간 단위)
    df = pd.DataFrame(index=hours, columns=spaces)
    return df

# 하루 최대 4시간 예약 제한 체크
def can_reserve(username):
    reserved_hours = sum(1 for space in spaces if space in st.session_state.reservations for user in 
                         st.session_state.reservations[space].values() if user == username)
    
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

    # 예약 현황 표시 (데이터베이스에서 가져오기)
    conn = sqlite3.connect(RESERVATIONS_FILE)
    c = conn.cursor()

    for space in spaces:
        c.execute("SELECT time, username FROM reservations WHERE space=?", (space,))
        reserved_times = c.fetchall()
        for time, user in reserved_times:
            timetable.at[time, space] = user

    conn.close()

    # 타임테이블을 표 형식으로 표시하고 버튼 추가
    cols = st.columns(len(spaces))  # 공간 수

    # 첫 번째 행에 공간 이름 표시 
    for i, space in enumerate(spaces):
        cols[i].write(f"<h3 style='text-align: center;'>{space}</h3>", unsafe_allow_html=True)

    # 각 공간에 대해 버튼 생성 (시간은 버튼 안에 포함)
    for time in timetable.index:
        cols = st.columns(len(spaces))  # 공간 수
        
        for i, space in enumerate(spaces):
            button_text = f"{time}"  # 버튼 안에 시간 표시
            
            # 예약된 경우 예약자 이름 표시
            if space in timetable.columns and time in timetable.index and timetable.at[time, space]:
                cols[i].write(f"🔒 {timetable.at[time, space]}")
                cols[i].markdown("<span style='color: red;'>예약 완료</span>", unsafe_allow_html=True)
            else:
                # 예약 가능한 경우 버튼 표시 
                if cols[i].button(button_text, key=f"{space}-{time}", help=f"{space} 예약하기"):
                    # 예약 가능 여부 체크
                    if not can_reserve(st.session_state.username):
                        st.warning("하루에 최대 4시간까지만 예약할 수 있습니다.")
                        return
                    
                    # 예약 데이터 저장 (데이터베이스에 저장)
                    conn = sqlite3.connect(RESERVATIONS_FILE)
                    c = conn.cursor()
                    c.execute("INSERT INTO reservations (space, time, username) VALUES (?, ?, ?)",
                              (space, time, st.session_state.username))
                    conn.commit()
                    conn.close()

                    # 성공 메시지 및 페이지 새로고침 없이 유지하도록 설정합니다.
                    st.success(f"{space} - {time} 예약이 완료되었습니다!")

# 매일 자정마다 예약 초기화 기능 추가 
def daily_reset():
   if 'last_reset' not in st.session_state or datetime.now().date() > datetime.fromisoformat(st.session_state.last_reset).date():
       # 오늘 날짜로 업데이트하고 세션 상태 초기화 
       st.session_state.last_reset = datetime.now().isoformat()
       conn = sqlite3.connect(RESERVATIONS_FILE)
       c = conn.cursor()
       c.execute("DELETE FROM reservations")  # 모든 예약 정보 초기화 
       conn.commit()
       conn.close()

def view_reservations(): 
   if not st.session_state.logged_in: 
       st.warning("로그인 후 이용 가능합니다.") 
       return 
    
   user_reservations={space: times for space, times in st.session_state.reservations.items() if any(user == st.session_state.username for user in times.values())} 
    
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
   hide_st_style="""  
       <style>  
       .main {  
           background-color:#f0f0f5;  
           font-family:'Arial',sans-serif;  
       }  
       </style>  
       """
   
   # CSS 스타일 적용
   st.markdown(hide_st_style, unsafe_allow_html=True)

   # 사이드바 메뉴 설정 - 로그인 페이지를 먼저 보여주기 위해 순서 변경 
   menu_options=["로그인","회원가입","예약 시스템","내 예약 현황"]  

   page=st.sidebar.selectbox("페이지 선택", menu_options)  

   # 선택된 페이지에 따라 함수 호출
   if page=="회원가입":  
       register()  
       
   elif page=="로그인":  
       login()  

   elif page=="예약 시스템":  
       reservation_system()  

   elif page=="내 예약 현황":  
       view_reservations()  

if __name__ == "__main__":  
   main()  
