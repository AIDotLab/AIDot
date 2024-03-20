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

# TODO: .ENV와 DOCKER안의 변수를 사용해서 조합
THIS_AI_SERVER = os.getenv("THIS_AI_SERVER") # 'AI101'
THIS_REQUEST_CODE = CONS_REQUEST_CODE + '-' + THIS_AI_SERVER + '-' + '0000'
THIS_COMPLETE_CODE = CONS_COMPLETE_CODE + '-' + THIS_AI_SERVER

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
        tmp_body = eval(body)
        analysis_id = tmp_body['analysis_id']
        aiserver_code = tmp_body['aiserver_code']
        
        # TODO: AI 분석을 수행하고, 분석 이미지를 저장
        time.sleep(1) # AI 분석 작업후, 이 코드는 삭제

        # COMPLETE AI 서버 큐 생성
        RMQSend(THIS_COMPLETE_CODE, eval(body))

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
    queue_process()
