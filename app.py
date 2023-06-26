import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for, make_response
import pymysql
import random
from flask_cors import CORS, cross_origin
import json
import datetime
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
CORS(app)

#메인페이지
@app.route('/')
def home():
    return render_template('index.html')

#로그인
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

#signin
@app.route('/signin', methods=['post'])
def signin():
    userId = request.form['username_give']
    password = request.form['password_give']

    connection = pymysql.connect(
    host='127.0.0.1', user='lotto', password='lotto',
    db='lottoDB', charset='utf8'
        ) # 데이터베이스 접속
    cursor = connection.cursor()
    sql = '''
        select id, userId, userpw
        from member
        where userId = %s 
        AND userpw = %s
    '''
    enc_pwd = encrypt_password(password)
    cursor.execute(sql, (userId, enc_pwd)) # SQL 실행
    rows = cursor.fetchall()
    print(rows)
    if rows == ():
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

    cursor.close()
    connection.close()
        
    response = make_response(jsonify({'result': 'success'}))
    response.set_cookie('member_id', str(rows[0][0]))
    return response
    

#회원가입
@app.route('/signup')
def signup():
    return render_template('signup.html')

def encrypt_password(password):
    # 문자열을 UTF-8 형식으로 인코딩
    encoded_password = password.encode('utf-8')
    # SHA-256 해시 객체 생성
    sha256_hash = hashlib.sha256()
    # 해시 객체에 비밀번호 추가
    sha256_hash.update(encoded_password)
    # 해시값 추출
    encrypted_password = sha256_hash.hexdigest()
    return encrypted_password

#아이디 중복검사
@app.route('/sign_up/check_dup', methods=['POST'])
def sign_up_check_dup():
    id = request.form['username_give']
    conn = pymysql.connect(
    host='127.0.0.1', user='lotto', password='lotto',
    db='lottoDB', charset='utf8'
        ) # 데이터베이스 접속
    cursor = conn.cursor() # 커서 객체 생성
    sql = '''
        select id, userId
          from member
         where userId = %s
    '''

    cursor.execute(sql, (id, )) # SQL 실행
    rows = cursor.fetchall()
    print(rows)
    # for row in rows:
    #     print(row.get('ename'), row.get('cnt'))

    conn.commit() # 실행내용 저장

    cursor.close() # 커서 객체 종료
    conn.close() # 접속 해제

    exists = bool(rows)
    print(rows, exists)
    return jsonify({'result': 'success', 'exists': exists})
    
    
# 회원가입 유저정보 제출 
@app.route('/sign_up/save', methods=['post'])
def signup_save():
    userId = request.form['userId']
    userpw = request.form['userpw']

    crypted = encrypt_password(userpw)

    conn = pymysql.connect(
         host='127.0.0.1', user='lotto', password='lotto',
         db='lottoDB', charset='utf8'
    ) # 데이터베이스 접속
    cursor = conn.cursor() # 커서 객체 생성
    
    sql = '''
        insert into member (userId, userpw) 
        values (%s, %s)
    '''
    cursor.execute(sql, (userId, crypted)) # SQL 실행
    conn.commit()

    cursor.close() # 커서 객체 종료
    conn.close() # 접속 해제

    return jsonify({'result': 'success'})

        # select 발급번호, lotto_ID, 당첨번호1, 당첨번호2, 당첨번호3
        #      , 당첨번호4, 당첨번호5, 당첨번호6
        # from number


#마이페이지
@app.route('/mypage')
def mypage():
    return render_template('mypage.html')

# 메인 페이지 로또 번호
@app.route('/index_lottery', methods = ['POST'])
def main_lottery():
    lotto_m = random.sample(range(1, 46), 7) #메인 페이지의 로또 넘버
    print("로또번호: {}".format(lotto_m))
    lotto_m = sorted(lotto_m)
    return jsonify(lotto_m)


## 마이페이지 로또 번호
@app.route('/mypage_lottery', methods=['POST'])
def generate_lottery():
    # 유저의 쿠키값 받아오기
    id = request.cookies.get('member_id')

    # 7자리 로또 번호 생성
    random_number = random.sample(range(1, 46), 7)
    random_number = sorted(random_number)

    random_num = str(random_number).replace('[', '').replace(']', '')
    print(random_num)
    # DB 접속
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            user='lotto',
            password='lotto',
            db='lottodb'
        )
        cursor = conn.cursor()

        # 새로운 로또 번호를 DB에 넣기
        sql_insert = '''
        INSERT INTO lotto_number (lotto, member_id)
        VALUES (%s, %s)
        '''
        # db에 값 넣기 id의 값은 자동으로 1씩 증가함
        cursor.execute(sql_insert, (random_num, id))
        conn.commit()

        cursor.close()
        conn.close()  # db close

        return jsonify({'data': random_num})

    except Exception as e:
        return jsonify({'error': str(e)})
    
# 1등 당첨번호
@app.route('/mypage_lotto', methods=['GET'])
def get_latest_lotto_numbers():
    url = 'https://www.dhlottery.co.kr/gameResult.do?method=byWin'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    numbers = soup.select('div.num.win p span')
    bonus_number = soup.select_one('div.num.bonus p span')
    numbers = [int(number.text) for number in numbers]
    bonus_number = int(bonus_number.text)
    numbers.append(bonus_number)
    return jsonify({'data': numbers  })

@app.route('/mypage_list', methods=['GET'])
def mypage_list():
    id = request.cookies.get('member_id')  # 유저 쿠키 이름 적기
    conn = pymysql.connect(
        host='127.0.0.1',
        user='lotto',
        password='lotto',
        db='lottodb'
    )
    cursor = conn.cursor()
    
    # 데이터베이스에서 데이터 가져오기
    sql = '''
    SELECT lotto 
    FROM lotto_number 
    WHERE member_id = %s
    ORDER BY id desc
    '''
    cursor.execute(sql, (id,))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    # JSON 형식으로 데이터 반환
    return jsonify({'data': data})

# 회원 운세정보 가져오기
@app.route('/luck', methods=['GET'])
def luck():
    if request.cookies.get('luck') == None:
        conn = pymysql.connect(
        host='127.0.0.1',
        user='lotto',
        password='lotto',
        db='lottodb'
        )
        cursor = conn.cursor()
        
        # 데이터베이스에서 데이터 가져오기
        sql = '''
        SELECT luck FROM luk
        '''
        cursor.execute(sql)
        data = cursor.fetchall()
        num = random.sample(range(1, 26), 1)
        result = data[num[0]]

        expires = datetime.datetime.now() + datetime.timedelta(days=1)

        response = make_response(jsonify({'data': result[0]}))
        response.set_cookie('luck', value=result[0], expires=expires)

        return response
    else:
        luck = request.cookies.get('luck')
        return jsonify({'data': luck})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)