import os
import time
from dotenv import load_dotenv
import pymysql
import pika

load_dotenv()
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
CONS_PAUSE_CODE = os.getenv("CONS_PAUSE_CODE")
CONS_WORK_CODE = os.getenv("CONS_WORK_CODE")

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
    try:
        channel = connection.channel()
        channel.queue_declare(queue=topic)
        channel.basic_publish(exchange='', routing_key=topic, body=str(message))
    finally:
        channel.close()
        connection.close()

def queue_process():
    credentials = pika.PlainCredentials(RMQ_USERNAME, RMQ_PASSWORD)
    parameters = pika.ConnectionParameters(RMQ_HOST_NAME, RMQ_PORT, RMQ_VIRTUAL_HOST, credentials)
    connection = pika.BlockingConnection(parameters)
    # Process 1. REQUEST AI 서버 큐 소비
    channel_request = connection.channel()
    channel_request.queue_declare(queue=THIS_REQUEST_CODE)
    # Process 2. COMPLETE AI 서버 큐 소비
    channel_complete = connection.channel()
    channel_complete.queue_declare(queue=THIS_COMPLETE_CODE)

    def callback_request(ch, method, properties, body):
        print("Message is Arrived {0} ({1})".format(THIS_REQUEST_CODE, eval(body)))
        # Process 1. REQUEST AI 서버 큐 소비 후, REQUEST AI 서버 큐 생성
        msq_body = eval(body)
        analysis_id = msq_body['analysis_id']
        aiserver_code = msq_body['aiserver_code']

        # TODO: 이미지 분석, 분석 이미지 정보 Table 조회

        # TODO: S3에서 이미지 갖고오기

        # TODO: AI 도커 컨테이너 실행
        # 실행되는 도커 이미지가 자신의 ID를 알기 위해 전달해야 함
        # TMP_THIS_SERVER_CODE = 'AIS101'

        # REQUEST-ID 큐 생성
        # TODO: Payload 수정. 이미지분석KEY, 작업 AI 서버, AI PT 파일 경로, 원본 이미지 경로
        RMQSend(CONS_REQUEST_CODE + '-' + aiserver_code, msq_body)

    # Process 1. REQUEST AI 서버 큐 소비
    channel_request.basic_consume(queue=THIS_REQUEST_CODE,
                          on_message_callback=callback_request,
                          auto_ack=True)

    def callback_complete(ch, method, properties, body):
        print("Message is Arrived {0} ({1})".format(THIS_COMPLETE_CODE, eval(body)))
        # Process 2. COMPLETE AI 서버 큐 소비 소비 후, 사용이 끝난 AI 서버를 다시 휴지 상태로 변경
        msq_body = eval(body)
        analysis_id = msq_body['analysis_id']
        aiserver_code = msq_body['aiserver_code']

        # TODO: S3에 분석 이미지 저장

        # TODO: 이미지 분석, 분석 이미지 정보 Table 저장

        # 사용이 끝난 AI 서버를 휴지 상태로 변경
        dbconn = connect_to_database()
        if not dbconn:
            return print('DB Connection Error.')
        dbcur = dbconn.cursor()

        try:
            sql = "update aidot_com_aiserver " \
                "   set ais_status_code = %s " \
                " where ais_code = %s"
            dbcur.execute(sql, (CONS_PAUSE_CODE, aiserver_code))
            dbconn.commit()
        finally:
            dbcur.close()
            dbconn.close()

    # Process 2. COMPLETE AI 서버 큐 소비
    channel_complete.basic_consume(queue=THIS_COMPLETE_CODE,
                          on_message_callback=callback_complete,
                          auto_ack=True)

    try:
        print("Waiting for messages.")
        channel_request.start_consuming()
        channel_complete.start_consuming()
    except KeyboardInterrupt:
        print('Ctrl+C is Pressed.')
    finally:
        channel_request.close()
        channel_complete.close()
        connection.close()

if __name__ == '__main__':
    # NOTICE: AI 서버 그룹('AIG101')은 .ENV에 정의되어 있어야 함
    THIS_AI_SERVER_GROUP = os.getenv("THIS_AI_SERVER_GROUP")
    THIS_REQUEST_CODE = CONS_REQUEST_CODE + '-' + THIS_AI_SERVER_GROUP
    THIS_COMPLETE_CODE = CONS_COMPLETE_CODE + '-' + THIS_AI_SERVER_GROUP
    
    queue_process()
