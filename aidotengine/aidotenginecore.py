import os
import time
from dotenv import load_dotenv
import pika

load_dotenv()
RMQ_USERNAME = os.getenv("RMQ_USERNAME")
RMQ_PASSWORD = os.getenv("RMQ_PASSWORD")
RMQ_HOST_NAME = os.getenv("RMQ_HOST_NAME")
RMQ_PORT = os.getenv("RMQ_PORT")
RMQ_VIRTUAL_HOST = os.getenv("RMQ_VIRTUAL_HOST")

CONS_REQUEST_CODE = os.getenv("CONS_REQUEST_CODE")
CONS_COMPLETE_CODE = os.getenv("CONS_COMPLETE_CODE")
CONS_PAUSE_CODE = os.getenv("CONS_PAUSE_CODE")
CONS_WORK_CODE = os.getenv("CONS_WORK_CODE")

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
    channel.queue_declare(queue=THIS_REQUEST_CODE)

    def callback_request(ch, method, properties, body):
        print("Message is Arrived {0} ({1})".format(THIS_REQUEST_CODE, eval(body)))
        msq_body = eval(body)
        analysis_id = msq_body['analysis_id']
        aiserver_code = msq_body['aiserver_code']

        # TODO: AI 분석을 수행하고, 분석 이미지를 저장
        time.sleep(3) # AI 분석 작업후, 이 코드는 삭제

        # COMPLETE AI 서버 큐 생성
        RMQSend(THIS_COMPLETE_CODE, msq_body)

    # REQUEST-ID 큐 소비
    channel.basic_consume(queue=THIS_REQUEST_CODE,
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
    # NOTICE: AI 서버 그룹('AIG101')은 .ENV에 정의되어 있어야 함
    THIS_AI_SERVER_GROUP = os.getenv("THIS_AI_SERVER_GROUP") # AIG101
    
    # NOTICE: 현재 AI Server Code('AIS101')는 전체 시스템 내에서 인스턴스별로 유니크해야 함
    # Docker Image에 저장되는 코드이고, 여러 AI 서버 인스턴스들이 공통으로 사용하는 코드이기때문에
    # .ENV 혹은 코드 수정으로 불가능하고
    # AIDOT ENGINE SUB Process에서 AIDOT ENGINE CORE Process로 전달되어야 함
    # TODO: AIS101은 AIDOT ENGINE SUB Process에서 AIDOT ENGINE CORE Process로 전달되어야 함
    TMP_THIS_SERVER_CODE = 'AIS101'

    THIS_REQUEST_CODE = CONS_REQUEST_CODE + '-' + THIS_AI_SERVER_GROUP + '-' + TMP_THIS_SERVER_CODE
    THIS_COMPLETE_CODE = CONS_COMPLETE_CODE + '-' + THIS_AI_SERVER_GROUP

    queue_process()
