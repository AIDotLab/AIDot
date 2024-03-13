import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask import Flask, render_template, url_for, redirect, request
import boto3
import pymysql
import pika

#app = Flask(__name__)
app = Flask(__name__,
            static_folder='uploads')

load_dotenv()
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

RMQ_HOST_NAME = os.getenv("RMQ_HOST_NAME")

def connect_to_database():
    try:
        conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, passwd=MYSQL_PASSWD, db=MYSQL_DB, charset=MYSQL_CHARSET)
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def RMQSend(topic, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RMQ_HOST_NAME))
    try:
        channel = connection.channel()
        # props = BasicProperties(content_type='text/plain', delivery_mode=1)
        # channel.basic_publish('incoming', topic, message, props) # incoming exchange로 publish
        channel.queue_declare(queue=topic)
        channel.basic_publish(exchange='', routing_key=topic, body=message)
    finally:
        connection.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['GET', 'POST'])
def uploader_file():
    if request.method == 'POST':
        # TODO: 원본 파일 이름 DB 저장
        # TODO: 안전한 이름으로 변경해서, 서버에 저장
        # TODO: S3에 저장
        # TODO: 관련 정보를 DB Table에 저장
        f = request.files['file']
        #f.save(secure_filename(f.filename))
        f.save('uploads/ori.jpg')
        #return 'file uploaded successfully'

        if os.path.isfile('uploads/inf_a.jpg'):
            os.remove('uploads/inf_a.jpg')
        if os.path.isfile('uploads/inf_b.jpg'):
            os.remove('uploads/inf_b.jpg')

        RMQSend('REQUEST_A', 'request model A')
        RMQSend('REQUEST_B', 'request model B')
        
        return redirect(url_for('result'))

@app.route('/result')
def result():
    conn = connect_to_database()
    if not conn:
        return render_template('error.html')
    cur = conn.cursor()

    try:
        sql = "SELECT * FROM myTable"
        cur.execute(sql)

        data_list = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return render_template('result.html', data_list=data_list)

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host= '0.0.0.0', debug=True)
