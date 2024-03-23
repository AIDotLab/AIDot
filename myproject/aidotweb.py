import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from markupsafe import escape
from werkzeug.utils import secure_filename
from flask import Flask, render_template, url_for, redirect, request
import boto3
import pymysql
import pika

app = Flask(__name__)
#app = Flask(__name__,
#            static_folder='static')

load_dotenv()
UPLOAD_ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_REGION = os.getenv("AWS_S3_BUCKET_REGION")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWD = os.getenv("MYSQL_PASSWD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET")

RMQ_USERNAME = os.getenv("RMQ_USERNAME")
RMQ_PASSWORD = os.getenv("RMQ_PASSWORD")
RMQ_HOST_NAME = os.getenv("RMQ_HOST_NAME")
RMQ_PORT = os.getenv("RMQ_PORT")
RMQ_VIRTUAL_HOST = os.getenv("RMQ_VIRTUAL_HOST")

CONS_REQUEST_CODE = os.getenv("CONS_REQUEST_CODE")
CONS_COMPLETE_CODE = os.getenv("CONS_COMPLETE_CODE")
CONS_AI_SERVER_CODE = os.getenv("CONS_AI_SERVER_CODE")

def s3_connection():
    try:
        s3 = boto3.client(
            service_name='s3',
            region_name=AWS_S3_BUCKET_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        print("s3 bucket connected!")
        return s3
    except Exception as e:
        print(e)
        #exit(ERROR_S3_CONNECTION_FAILED)
        return None

def connect_to_database():
    try:
        conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, passwd=MYSQL_PASSWD, db=MYSQL_DB, charset=MYSQL_CHARSET)
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def RMQSend(topic, message):
    credentials = pika.PlainCredentials(RMQ_USERNAME, RMQ_PASSWORD)
    parameters = pika.ConnectionParameters(RMQ_HOST_NAME, RMQ_PORT, RMQ_VIRTUAL_HOST, credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    try:
        channel = connection.channel()
        channel.queue_declare(queue=topic)
        channel.basic_publish(exchange='', routing_key=topic, body=str(message))
    finally:
        channel.close()
        connection.close()

def upload_allowed_extension(filename):
    extension = filename.split('.')[-1]
    return extension in UPLOAD_ALLOWED_EXTENSIONS

def upload_file_name(filename):
    sec_file_name = secure_filename(filename)
    mod_file_name_f = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '-' + sec_file_name.split('.')[0]
    mod_file_name_b = sec_file_name.split('.')[-1]
    mod_file_name = mod_file_name_f + '.' + mod_file_name_b
    return mod_file_name

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload')
def upload_file():
    dbconn = connect_to_database()
    if not dbconn:
        return render_template('error.html')
    dbcur = dbconn.cursor()

    try:
        sql = "SELECT * " \
              "  FROM aidot_com_code " \
              " WHERE cod_set = 'AIModel' " \
              "   AND cod_use_flag = 'Y' " \
              " ORDER BY cod_order"

        dbcur.execute(sql)
        aimodel_list = dbcur.fetchall()
    finally:
        dbcur.close()
        dbconn.close()

    return render_template('upload.html', aimodel_list=aimodel_list)

@app.route('/uploader', methods=['GET', 'POST'])
def uploader_file():
    if request.method == 'POST':
        ana_title = request.form['analysis_title']
        ana_description = request.form['analysis_description']
        ana_aimodel = request.form['analysis_aimodel']
        ana_file = request.files['analysis_file']

        if ana_title and len(ana_title) > 5 and \
            ana_description and len(ana_description) > 5 and \
            ana_aimodel and len(ana_aimodel) > 5 and \
            ana_file and upload_allowed_extension(ana_file.filename):

            # STEP 1. 로컬 서버에 저장
            ori_file_name = ana_file.filename
            mod_file_name = upload_file_name(ori_file_name)
            save_file_path = os.path.join('uploads', mod_file_name)
            ana_file.save(save_file_path)
            save_s3_path = os.path.join('uploads', datetime.now().strftime('%Y%m%d%H'), mod_file_name)
            s3_image_url = f'https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_BUCKET_REGION}.amazonaws.com/{save_s3_path}'

            # STEP 2. S3에 저장
            s3 = s3_connection()
            try:
                s3.upload_file(save_file_path, AWS_S3_BUCKET_NAME, save_s3_path)
            except Exception as e:
                print(e)
                return render_template('error.html')

            # 서버에 있는 파일 삭제
            try:
                if (os.path.isfile(save_file_path)):
                    os.remove(save_file_path)
            except OSError as e:
                print("Error: %s : %s" % (f, e.strerror))   

            # STEP 3. 분석 요청을 DB Table에 저장
            dbconn = connect_to_database()
            if not dbconn:
                return render_template('error.html')
            dbcur = dbconn.cursor()

            try:
                # STEP 3-1. ana_analysis_no 조회
                sql = "SELECT IFNULL(MAX(ana_analysis_no), 1000000000) + 1 AS NEWNO " \
                      "  FROM aidot_ana_analysis"
                dbcur.execute(sql)
                analysis_no_new = dbcur.fetchall()[0][0]
                analysis_id = uuid.uuid1()

                # STEP 3-2. 분석 요청 저장
                #INSERT INTO aidot_ana_analysis values ('1000000001', 'c33e8032-e11f-11ee-8c68-b11980472f07'
                #, '강아지 YOLOv8 기본 모델', 'YOLOv8 기본 모델을 사용해서 강아지를 탐지합니다.', 'YOLOv8Base', 'AI101', 'REQUEST'
                #, '2024-03-04 13:10:15', '2024-03-04 13:10:16'
                #, 'dog.jpg', 'dog.jpg', 'demo/dog.jpg', 'https://aidot2024.s3.ap-northeast-2.amazonaws.com/demo/dog.jpg'
                #, 'demo/dog-a.jpg', 'https://aidot2024.s3.ap-northeast-2.amazonaws.com/demo/dog-a.jpg'
                #, 'Y', 'Y', '1', 'Y');
                sql = "INSERT INTO aidot_ana_analysis VALUES (%s, %s, %s, %s, %s, %s, %s, SYSDATE(), '', %s, %s, %s, %s, '', '', 'Y', 'Y', '1', 'Y')"
                dbcur.execute(sql, (analysis_no_new, analysis_id, ana_title, ana_description, ana_aimodel, CONS_AI_SERVER_CODE, CONS_REQUEST_CODE, ori_file_name, mod_file_name, save_s3_path, s3_image_url))
                dbconn.commit()

            finally:
                dbcur.close()
                dbconn.close()

            # STEP 4. 분석 요청 큐 생성
            RMQSend('REQUEST', {'analysis_id': str(analysis_id)})
        
        return redirect(url_for('result'))

@app.route('/result')
def result():
    dbconn = connect_to_database()
    if not dbconn:
        return render_template('error.html')
    dbcur = dbconn.cursor()

    try:
        sql = "SELECT * " \
              "  FROM aidot_ana_analysis_v " \
              " WHERE ana_public_flag = 'Y' " \
              "   AND ana_use_flag = 'Y' " \
              " ORDER BY ana_analysis_no DESC"
        dbcur.execute(sql)
        ana_analysis_list = dbcur.fetchall()
    finally:
        dbcur.close()
        dbconn.close()

    return render_template('result.html', ana_analysis_list=ana_analysis_list)

@app.route('/result/<ana_id>')
def resultdetail(ana_id):
    dbconn = connect_to_database()
    if not dbconn:
        return render_template('error.html')
    dbcur = dbconn.cursor()

    try:
        sql = "SELECT * " \
              "  FROM aidot_ana_analysis_v " \
              " WHERE ana_public_flag = 'Y' " \
              "   AND ana_use_flag = 'Y' " \
              "   AND ana_analysis_id = %s "
        #print(sql)
        dbcur.execute(sql, ana_id)
        ana_analysis = dbcur.fetchall()
    finally:
        dbcur.close()
        dbconn.close()

    if len(ana_analysis) == 0:
        return render_template('error.html')

    return render_template('resultdetail.html', ana_analysis=ana_analysis[0])

@app.route('/result/<ana_id>/rerequest')
def resultrerequest(ana_id):
    dbconn = connect_to_database()
    if not dbconn:
        return render_template('error.html')
    dbcur = dbconn.cursor()

    try:
        # STEP 1. 분석 정보 초기화
        sql = "update aidot_ana_analysis " \
              "   set ana_aiserver_code = %s " \
              "     , ana_status_code = %s " \
              "     , ana_request_date = SYSDATE() " \
              "     , ana_complete_date = '' " \
              "     , ana_ana_s3_path = '' " \
              "     , ana_ana_s3_url = '' " \
              " where ana_analysis_id = %s"
        #print(sql)
        dbcur.execute(sql, (CONS_AI_SERVER_CODE, CONS_REQUEST_CODE, ana_id))
        dbconn.commit()

        # STEP 2. 데이터 조회
        sql = "SELECT ana_analysis_id " \
              "  FROM aidot_ana_analysis_v " \
              " WHERE ana_analysis_id = %s "
        #print(sql)
        dbcur.execute(sql, ana_id)
        ana_analysis = dbcur.fetchall()

        if len(ana_analysis) == 0:
            return render_template('error.html')

        # STEP 3. 분석 요청 큐 생성
        RMQSend('REQUEST', {'analysis_id': str(ana_analysis[0][0])})
        
    finally:
        dbcur.close()
        dbconn.close()

    return redirect(url_for('resultdetail', ana_id=ana_id))

@app.route('/result/<ana_id>/delete')
def resultdelete(ana_id):
    dbconn = connect_to_database()
    if not dbconn:
        return render_template('error.html')
    dbcur = dbconn.cursor()

    try:
        sql = "update aidot_ana_analysis " \
              "   set ana_use_flag = 'N' " \
              " where ana_analysis_id = %s"
        #print(sql)
        dbcur.execute(sql, (ana_id))
        dbconn.commit()

    finally:
        dbcur.close()
        dbconn.close()

    return redirect(url_for('result'))

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host= '0.0.0.0', debug=True)
