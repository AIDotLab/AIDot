import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, url_for, redirect, request
from flask_cors import CORS
import pika

app = Flask(__name__)
CORS(app)

load_dotenv()
UPLOAD_ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

RMQ_HOST_NAME = os.getenv("RMQ_HOST_NAME")

CONS_REQUEST_CODE = '1000000004' # REQUEST
CONS_COMPLETE_CODE = '1000000005' # COMPLETE
CONS_REQUEST_SERVER_AI101 = '1000000006' # AI101
CONS_REQUEST_SERVER_AI102 = '1000000007' # AI102

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

def request_process():
    print('request_process')
    # STEP 1. 분석 요청 큐 소비
    # STEP 2. 분석 요청 AI 서버 큐 생성
    #RMQSend('REQUEST', str(ana_analysis_newno))

def complete_process():
    print('request_process')

@app.route('/')
def echo():
    return 'AIDOT ENGINE MAIN'

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host= '0.0.0.0', debug=True, port=5001, ssl_context=('cert.pem', 'key.pem'))
