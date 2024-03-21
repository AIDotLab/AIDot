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
    channel = connection.channel()
    channel.queue_declare(queue=CONS_REQUEST_CODE)

    def callback_request(ch, method, properties, body):
        print("Message is Arrived {0} ({1})".format(CONS_REQUEST_CODE, eval(body)))
        # 휴지 상태의 AI 서버를 검색하고, 없으면 0.5초후 다시 검색
        msq_body = eval(body)
        analysis_id = msq_body['analysis_id']
        aiserver_group_code = ''
        aiserver_code = ''
        aiserver_check = True
        
        dbconn = connect_to_database()
        if not dbconn:
            return print('DB Connection Error.')
        dbcur = dbconn.cursor()

        try:
            # 휴지 상태의 AI Server가 있을때까지 무한 순환
            while aiserver_check:
                # 휴지 상태의 AI Server 조회
                sql = "SELECT * " \
                    "  FROM aidot_com_aiserver " \
                    " WHERE ais_use_flag = 'Y' " \
                    "   AND ais_status_code = 'PAUSE' " \
                    " ORDER BY ais_order"
                dbcur.execute(sql)
                aiserver_list = dbcur.fetchall()

                if len(aiserver_list) == 0:
                    # 휴지 상태의 AI Server가 없으면 0.5초 후 재조회
                    time.sleep(0.5)
                    # NOTICE: 변경된 데이터를 갖고 오기위해서 COMMIT 함수 호출 필수
                    dbconn.commit()
                    print('NO AISERVER')
                else:
                    aiserver_check = False
                    aiserver_group_code = aiserver_list[0][1]
                    aiserver_code = aiserver_list[0][2]
                    print(aiserver_code)

                    # AI 서버를 가동 상태로 변경
                    sql = "update aidot_com_aiserver " \
                        "   set ais_status_code = %s " \
                        " where ais_code = %s"
                    dbcur.execute(sql, (CONS_WORK_CODE, aiserver_code))

                    # AI 분석에서 AI 서버도 변경
                    sql = "update aidot_ana_analysis " \
                        "   set ana_aiserver_code = %s " \
                        " where ana_analysis_id = %s"
                    dbcur.execute(sql, (aiserver_code, analysis_id))
                    dbconn.commit()
        finally:
            dbcur.close()
            dbconn.close()

        msq_body['aiserver_code'] = aiserver_code
        RMQSend(CONS_REQUEST_CODE + '-' + aiserver_group_code, msq_body)

    # REQUEST 큐 소비
    channel.basic_consume(queue=CONS_REQUEST_CODE,
                          on_message_callback=callback_request,
                          auto_ack=True)

    try:
        print("Waiting for messages.")
        channel.start_consuming()
    except KeyboardInterrupt:
        print('Ctrl+C is Pressed.')
    finally:
        channel.close()
        connection.close()

if __name__ == '__main__':
    queue_process()
